from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from hivewatch.shell import BB, append_note, dispatch, minutes_since, seconds, setting
from hivewatch.promise import (
    OFF_TRACK_IDLE_MIN,
    normalize_ident,
    off_track_idle_age,
    promise_metrics,
    result_session_finished,
    result_verdict_key,
)
from hivewatch.ledger import clear_done_state, finish_closed_run, pause_automation
from hivewatch.collect import status_table


def evaluate(snapshot: dict, state: dict, env: dict[str, str], dry_run: bool) -> list[str]:
    now = snapshot["now"]
    host, server, sessions, bb, isa, evidence = (snapshot[k] for k in
        ("host", "server", "sessions", "bb", "isa", "evidence"))
    root = env.get("REPO", "")
    thread_id = env.get("ORCH_THREAD", "")
    pending = state.get("credit_stop_pending")
    try:
        package = Path(__file__).resolve()
        config = package.parents[1] / "credit-out.json"
        if not config.exists():
            config = package.parents[2] / "credit-out.json"
        patterns = json.loads(config.read_text())["patterns"]
        if not isinstance(patterns, list) or not all(isinstance(p, str) and p.strip() for p in patterns):
            raise ValueError("invalid credit patterns")
        errors = sessions.get("stop_errors", [])
        if sessions.get("valid") and "credit_stops_handled" not in state:
            state["credit_stops_handled"] = [error["id"] for error in errors]
        handled = set(state.get("credit_stops_handled", []))
        active_sessions = {env.get("ORCH_SESSION")} if bb.get("orch_status") == "active" else set()
        active_threads = {child.get("id") for child in bb.get("children", []) if child.get("status") == "active"}
        active_sessions.update(child["id"] for child in sessions.get("children", [])
                               if child.get("thread_id") in active_threads or
                               (child.get("time_idle") is None and child.get("idle_outcome") is None))
        matches = {error["id"] for error in sessions.get("stop_errors", [])
                   if error["id"] not in handled and error.get("session") in active_sessions and
                   any(re.search(pattern, error["message"], re.I) for pattern in patterns)}
    except (OSError, ValueError, TypeError, KeyError, re.error):
        matches = set()
        handled = set(state.get("credit_stops_handled", []))
    if matches or pending:
        ids = ([thread_id] if thread_id and bb.get("orch_status") == "active" else [])
        ids += [child["id"] for child in bb.get("children", [])
                if child.get("status") == "active" and child.get("id")]
        if pending:
            ids = (ids if matches - set(pending["matches"]) else []) + pending["ids"]
            matches |= set(pending["matches"])
        state["credit_stop_pending"] = {"matches": sorted(matches), "ids": list(dict.fromkeys(ids))}
        failed_ids = []
        for ident in dict.fromkeys(ids):
            if dry_run:
                print(f"DRY-RUN: would run bb thread stop {ident}")
            else:
                _, error = BB.command(["thread", "stop", ident], 8.0)
                if error:
                    failed_ids.append(ident)
                    print(f"WATCH ERROR: bb thread stop {ident} failed: {error}")
        state["credit_stop_pending"]["ids"] = failed_ids
        if not failed_ids:
            state["credit_pause_result"] = pause_automation(env, dry_run)
        alerted = set(state.get("credit_stops_alerted", []))
        if matches - alerted:
            append_note(root, "Usage credits exhausted; watchdog is pausing the run. Re-enable the automation to resume.", dry_run)
            state["credit_stops_alerted"] = sorted(alerted | matches)
        if not failed_ids and state["credit_pause_result"].startswith(("paused ", "would pause ")):
            state["credit_stops_handled"] = sorted(handled | matches)
            state.pop("credit_stop_pending", None)
        return ["credit-out"]
    run_status = snapshot.get("run_status")
    messages: list[str] = []
    notes: list[str] = []
    alert_tags: list[str] = []
    conditions = state.setdefault("conditions", {})

    asked = state.setdefault("asked", {})
    if not isinstance(asked, dict):
        asked = state["asked"] = {}
    urgent_keys: list[str] = []

    def action_fingerprint() -> dict:
        """What the orchestrator can visibly do about an alert: start a helper, change the ledger, commit."""
        return {"children": sorted(str(row.get("id")) for row in bb.get("children", []))
                if bb.get("list_valid") else None,
                "ledger": hashlib.sha256(json.dumps([isa.get("latest_verdicts", {}), isa.get("checked", []),
                                                     isa.get("parked", []), isa.get("verdict_count", 0)],
                                                    sort_keys=True).encode()).hexdigest()
                if not isa.get("error") else None,
                "head": snapshot.get("head") if snapshot.get("head_valid") else None}

    def acted_since(baseline: dict) -> bool:
        current = action_fingerprint()
        if current["children"] is not None and baseline.get("children") is not None and \
                set(current["children"]) - set(baseline["children"]):
            return True
        return any(current[k] is not None and baseline.get(k) is not None and current[k] != baseline[k]
                   for k in ("ledger", "head"))

    def record(key: str, tag: str, detail: str, urgent: bool, track: bool) -> None:
        if track:
            state["alert_seq"] = int(state.get("alert_seq", 0)) + 1
            aid = f"W{state['alert_seq']}"
            detail = f"{detail} (alert {aid})"
            asked[aid] = {"at": now, "key": key, "kind": tag, "urgent": urgent,
                          "baseline": action_fingerprint()}
        messages.append(detail)
        if urgent:
            urgent_keys.append(key)
        if tag not in alert_tags:
            alert_tags.append(tag)
        review["alerts"][tag] = review["alerts"].get(tag, 0) + 1

    def emit() -> None:
        if messages:
            if any("(alert W" in message for message in messages):
                messages.append("Answer each alert id under the run card's Answers: "
                                "`ANSWER <id>: <action> — <thread id, ledger line, or park line>`.")
            messages.extend(status_table(snapshot))
        mode = "queue"
        if messages and urgent_keys and now - float(state.get("last_interrupt", 0)) >= 600:
            mode = "auto"
            state["last_interrupt"] = now
        dispatch(thread_id, messages, dry_run, mode)

    review = state.setdefault("review", {"last_at": now, "alerts": {},
                                          "promise_agents": [], "other_agents": []})
    if not isinstance(review, dict):
        review = state["review"] = {"last_at": now, "alerts": {},
                                    "promise_agents": [], "other_agents": []}
    review.setdefault("last_at", now)
    review.setdefault("alerts", {})
    review.setdefault("promise_agents", [])
    review.setdefault("other_agents", [])

    isa_valid = not isa.get("error")
    prior_fail_lines: set[str] = set()
    if isa_valid:
        # FAIL lines seen on earlier checks; the first check is a baseline.
        current_fail_lines = {normalize_ident(ident) + ":" + signature
                              for ident, signature, *_ in isa.get("fails", [])}
        stored = state.get("fail_lines_seen")
        prior_fail_lines = set(stored) if isinstance(stored, list) else set(current_fail_lines)
        state["fail_lines_seen"] = sorted(prior_fail_lines | current_fail_lines)
        active_regressions = set(isa.get("regressions", []))
        for key in list(conditions):
            if key.startswith("regression:") and key.split(":", 1)[1] not in active_regressions:
                conditions.pop(key, None)
        alerted = set(state.get("regressions_alerted", []))
        state["regressions_alerted"] = sorted(alerted & active_regressions)
    if run_status == "running" and isa_valid and not isa.get("done"):
        clear_done_state(state)
    if run_status == "closed":
        finish_closed_run(state, env, dry_run)
        return alert_tags
    if state.get("done"):
        # Ledger-only completion stays paused until the run card is closed.
        state.pop("closed_pause_recorded", None)
        state.pop("closed_automation_id", None)
        state.pop("delete_result", None)
        state["pause_result"] = pause_automation(env, dry_run)
        return alert_tags
    if isa_valid and isa["done"]:
        summary = (f"{isa['pass']}/{isa['total']} PASS, {len(isa.get('parked', []))} parked "
                   f"(owner {isa['owner_done']}/{len(isa['owner'])}, blocked {len(isa['blocked'])})"
                   if isa_valid else "ledger unreadable")
        state["done"] = True
        state["pause_result"] = pause_automation(env, dry_run)
        messages.append(f"WATCH DONE: ledger complete or parked-only ({summary}); watchdog {state['pause_result']}. "
                        "Set the run card status to closed and send the owner the final report.")
        print(f"WATCH DONE: {summary}; {state['pause_result']}")
        emit()
        return alert_tags
    waiting = bool(run_status and run_status.startswith("waiting"))
    if state.get("last_run_status", "").startswith("waiting") and run_status == "running":
        state["continue"] = {}  # owner unblocked the run: nudging may resume
    state["last_run_status"] = run_status or ""

    def trigger(key: str, active: bool, detail: str, severity: int = 1, valid: bool = True,
                urgent: bool = False, track: bool = False) -> bool:
        if not valid:
            return False
        rec = conditions.setdefault(key, {"streak": 0, "last_alert": 0, "severity": 0})
        rec["streak"] = rec.get("streak", 0) + 1 if active else 0
        if not active:
            rec["last_alert"] = 0
            rec["severity"] = 0
        due = active and rec["streak"] >= 2 and not rec.get("last_alert")
        if due:
            rec["last_alert"] = now
            rec["severity"] = severity
            tag = {
                "high-load": "high load", "low-disk": "low disk", "big-file": "large file",
                "orphan-process": "orphan process", "stuck-builder-log": "stuck builder",
                "stuck-agent": "stuck agent", "unrecorded-pass": "unrecorded PASS",
                "long-agent": "long-running agent", "invisible-agent": "invisible agent",
                "ghost-agent": "ghost agent", "fail-load": "FAIL under load",
                "opencode-down": "server down", "sim-without-agent": "idle simulator",
                "off-track": "off track", "no-talkback": "no talk-back",
                "repeat-fail": "repeat failure", "unclaimed": "unclaimed work",
                "plateau": "plateau", "regression": "regression",
                "leftover-session": "leftover session", "drift": "code changed under QA",
                "free": "free items idle", "plan": "plan map out of date", "agent-switch": "agent switched",
            }.get(key.split(":", 1)[0], "alert")
            record(key, tag, detail, urgent, track)
        return due

    all_live_sessions = list(sessions.get("live", []))
    leftover_sessions = []
    can_check_bindings = (sessions.get("valid", False) and bb.get("list_valid", False) and
                          bb.get("binding_valid", False))
    if can_check_bindings:
        for sess in all_live_sessions:
            child_thread = sess.get("thread_id")
            thread = bb.get("by_id", {}).get(child_thread, {}) if child_thread else {}
            status = thread.get("status")
            if isinstance(status, str) and status.lower() in ("failed", "stopped", "idle"):
                leftover_sessions.append((sess, child_thread))
        if leftover_sessions:
            leftover_ids = {sess["id"] for sess, _ in leftover_sessions}
            sessions["live"] = [sess for sess in all_live_sessions if sess["id"] not in leftover_ids]
        active_leftovers = {"leftover-session:" + sess["id"] for sess, _ in leftover_sessions}
        for key in list(conditions):
            if key.startswith("leftover-session:") and key not in active_leftovers:
                trigger(key, False, "", valid=True)
    for sess, child_thread in leftover_sessions:
        trigger("leftover-session:" + sess["id"], True,
                f"LEFTOVER session {sess['id']} still running after its BB thread {child_thread} ended; "
                "interrupt it before relaunching. Ask: Was this helper resumed after it finished? "
                "Is its work already covered by a newer helper? Default: interrupt it and continue the "
                "work in a fresh visible BB child with a Delta.",
                valid=can_check_bindings, urgent=True, track=True)

    load = host.get("load")
    load_limit = setting(env, "WATCH_LOAD_LIMIT", 150)
    trigger("high-load", load is not None and load > load_limit,
            f"HOST load: 1-minute load {load:.1f} (>{load_limit:g}) on two checks; uptime reports this value."
            if load is not None else "HOST load: uptime reading unavailable.",
            int(load // load_limit) if load else 1, valid=host.get("uptime_valid", False),
            urgent=load is not None and load > 2 * load_limit)
    free = host.get("free_gb")
    disk_limit = setting(env, "WATCH_DISK_FREE_GB", 10)
    disk_valid = host.get("df_valid", False)
    critical_disk = free is not None and free < 5
    normal_disk = free is not None and free < disk_limit and not critical_disk
    if critical_disk:
        trigger("low-disk", False, "", valid=disk_valid)
        trigger("low-disk:critical", True,
                f"🚦 HOST disk: only {free:.1f} GB free on / (<5 GB); see df -h /.",
                2, valid=disk_valid, urgent=True)
    else:
        trigger("low-disk:critical", False, "", valid=disk_valid)
        trigger("low-disk", normal_disk,
                f"HOST disk: only {free:.1f} GB free on / (<{disk_limit:g} GB); see df -h /."
                if free is not None else "HOST disk: df reading unavailable.",
                1, valid=disk_valid)
    for f in host.get("recent_big", []):
        age = minutes_since(f["created"], now) or 0
        size_mb = f["size"] / 1_048_576
        trigger("big-file:" + f["path"], True,
                f"HOST large file: {f['path']} is {size_mb:.0f} MB, created {age:.0f} min ago.",
                max(1, int(size_mb // 100)), valid=host.get("recent_big_valid", False))
    orphan_state = state.setdefault("orphan_idle", {})
    no_agent_elapsed = None
    if sessions.get("valid", False):
        if sessions.get("live"):
            orphan_state["no_agent_since"] = None
        else:
            if orphan_state.get("no_agent_since") is None:
                orphan_state["no_agent_since"] = now
            no_agent_elapsed = (now - orphan_state["no_agent_since"]) / 60
    no_agent_long_enough = (no_agent_elapsed is not None and
                            no_agent_elapsed >= setting(env, "WATCH_GHOST_MIN", 15))
    for proc in host.get("processes", []):
        if proc["orphan"]:
            age = proc["age"] / 60
            trigger("orphan-process:" + str(proc["pid"]), no_agent_long_enough,
                    f"HOST orphan process: pid {proc['pid']} ppid {proc['ppid']}, {age:.0f} min; {proc['command'][:160]}.",
                    2 if proc["age"] > 3600 else 1,
                    valid=host.get("processes_valid", False) and sessions.get("valid", False))

    deduped_passes = state.get("unrecorded_passes")
    if not isinstance(deduped_passes, dict):
        deduped_passes = state["unrecorded_passes"] = {}
    for result in evidence["results"]:
        age_m = minutes_since(result["mtime"], now) or 0
        unchanged_or_finished = age_m >= 20 or result_session_finished(result, snapshot)
        rows = result.get("table_rows", [])
        if not rows:
            rows = [{"id": normalize_ident(ident), "status": status, "text": ""}
                    for ident, status in result.get("rows", [])]
        for row in rows:
            ident, status, text = row.get("id"), row.get("status"), row.get("text", "")
            if status != "PASS" or not ident:
                continue
            key = result_verdict_key(result["path"], ident, status, text)
            if key in deduped_passes:
                continue
            legacy = conditions.get(f"unrecorded-pass:{result['path']}:{ident}", {})
            if legacy.get("last_alert"):
                deduped_passes[key] = legacy["last_alert"]
                continue

            latest = isa.get("latest_verdicts", {}).get(ident)
            ledger_has_pass = latest is not None and latest.get("status") == "PASS"
            ledger_is_newer = (latest is not None and isa.get("ledger_mtime") is not None and
                               isa["ledger_mtime"] > result["mtime"])
            if ledger_has_pass or ledger_is_newer:
                trigger("unrecorded-pass:" + key, False, "",
                        valid=evidence.get("valid", False) and isa_valid)
                continue
            due = trigger("unrecorded-pass:" + key, unchanged_or_finished,
                          f"LEDGER {ident}: PASS in {result['path']} is not in a newer ledger entry; record it. "
                          "Ask: Did this tester check the exact committed candidate? Is anything blocking the "
                          "tick? Default: tick it with the commit id and evidence, or write why not.",
                          max(1, int(age_m // 60)),
                          valid=evidence.get("valid", False) and isa_valid, track=True)
            if due:
                deduped_passes[key] = now

    if sessions.get("valid", False):
        for sess in sessions.get("children", []):
            if sess.get("time_idle") is not None or sess.get("idle_outcome") is not None:
                trigger("off-track:" + sess["id"], False, "")
    for sess in sessions.get("live", []):
        if sess.get("time_idle") is not None or sess.get("idle_outcome") is not None:
            trigger("off-track:" + sess["id"], False, "",
                    valid=sessions.get("valid", False))
            continue
        promise = sess.get("promise")
        if not promise or not promise.get("valid"):
            quiet = minutes_since(sess.get("last_message") or sess.get("created"), now) or 0
            trigger("stuck-agent:" + sess["id"], quiet >= setting(env, "WATCH_AGENT_STUCK_MIN", 10),
                    f"AGENT {sess.get('agent', 'agent')} ({sess['id']}): no session activity for {quiet:.0f} min. "
                    "Ask: Is it waiting on a permission, a prompt or you? Would a fresh helper with a Delta "
                    "finish sooner? Default: ask it for its smallest provable part now; if no reply in 5 min, "
                    "restart it fresh with a Delta.",
                    max(1, int(quiet // 60)), valid=sessions.get("valid", False), urgent=True, track=True)
        metrics = promise_metrics(sess, snapshot, state)
        if metrics is None:
            continue
        child_id = sess.get("thread_id") or sess["id"]
        child = bb.get("by_id", {}).get(child_id, {})
        title = child.get("title") or sess.get("agent", "agent")
        role = sess.get("agent", "agent")
        unanswered = metrics["unanswered"]
        message_count = f"{unanswered} message{'s' if unanswered != 1 else ''} not acted on"
        idle = off_track_idle_age(sess, snapshot)
        detail = (f"OFF TRACK {title} ({role}) {child_id}: no evidence or session message for "
                  f"{idle:.0f} min (idle limit {OFF_TRACK_IDLE_MIN} min); "
                  f"{metrics['coverage']} rows answered; {metrics['placeholders']} placeholders; "
                  f"{message_count}. Ask: Is it still working toward its promise, or stuck waiting? "
                  "Would a fresh helper with a Delta land the smallest provable part faster? "
                  "Default: ask it to land its smallest provable part now; if it can't, restart it "
                  "fresh with a Delta.") if idle is not None else ""
        trigger("off-track:" + sess["id"],
                idle is not None and idle >= OFF_TRACK_IDLE_MIN, detail,
                valid=metrics["valid"] and idle is not None, urgent=True, track=True)

    # Builder sessions with a quiet build log are called out separately from result-file progress.
    for sess in sessions["live"]:
        age = minutes_since(sess.get("created"), now)
        if age is not None:
            max_hours = setting(env, "WATCH_AGENT_MAX_HOURS", 3)
            trigger("long-agent:" + sess["id"], age > max_hours * 60,
                    f"AGENT {sess['agent']} ({sess['id']}): active {age:.0f} min; wrap up and report.",
                    max(1, int(age // (max_hours * 60))), valid=sessions.get("valid", False))
        if not sess.get("visible"):
            idle = minutes_since(sess.get("last_message"), now) or 0
            follow_ups = len(sess.get("steers", []))
            trigger("invisible-agent:" + sess["id"], True,
                    f"AGENT {sess['agent']} session {sess['id']} is not bound to a visible active BB child; last message {idle:.0f} min ago. "
                    f"Facts: {sess.get('binding_fact', 'binding unknown')}; started {age or 0:.0f} min ago; "
                    f"{follow_ups} follow-up message{'s' if follow_ups != 1 else ''} after its brief. "
                    "Ask: Was this helper resumed after it finished? Can the owner see it in BB (check by "
                    "session and thread id, not title)? Default: let it finish, and start any further work "
                    "in a fresh visible BB child with a Delta.",
                    valid=(sessions.get("valid", False) and bb.get("list_valid", False) and
                           bb.get("binding_valid", False)), urgent=True, track=True)

    for child in bb["children"]:
        ghost_key = "ghost-agent:" + str(child.get("id"))
        if child.get("status") != "active":
            trigger(ghost_key, False, "", valid=(sessions.get("valid", False) and
                    bb.get("list_valid", False) and bb.get("binding_valid", False)))
            continue
        ghost_min = setting(env, "WATCH_GHOST_MIN", 15)
        bound = child.get("bound_sessions", [])
        active_bound = [s for s in bound if s.get("time_idle") is None and s.get("idle_outcome") is None]
        working = [s for s in active_bound if
                   (minutes_since(s.get("last_message"), now) is not None and
                    minutes_since(s.get("last_message"), now) < ghost_min)]
        if not bound:
            ghost = True
            evidence_text = "no bound OpenCode session"
            inactive = ghost_min
        elif not active_bound:
            ghost = False
            evidence_text = "bound OpenCode session idle or finished"
            inactive = 0
        elif working:
            ghost = False
            evidence_text = f"{len(working)} bound session(s) with recent activity"
            inactive = 0
        else:
            ghost = True
            ages = [minutes_since(s.get("last_message"), now) for s in bound]
            inactive = max((age if age is not None else 10_000 for age in ages), default=10_000)
            evidence_text = ", ".join(
                f"{s['id']} idle={s.get('time_idle') is not None or s.get('idle_outcome') is not None} "
                f"last={minutes_since(s.get('last_message'), now):.0f}m"
                if s.get("last_message") is not None else f"{s['id']} has no session message"
                for s in bound)
        if ghost:
            trigger(ghost_key, True,
                    f"GHOST BB child {child.get('id')} ({child.get('title', 'untitled')}): active; {evidence_text}.",
                    max(1, int(inactive // 60)),
                    valid=(sessions.get("valid", False) and bb.get("list_valid", False) and
                           bb.get("binding_valid", False)))
        else:
            trigger(ghost_key, False, "", valid=(sessions.get("valid", False) and
                    bb.get("list_valid", False) and bb.get("binding_valid", False)))

    # Keep recent samples so FAILs can be judged at the evidence file's timestamp.
    load_samples = state.get("load_samples", [])
    if not isinstance(load_samples, list):
        load_samples = []
    if host.get("uptime_valid", False) and load is not None:
        load_samples.append({"time": now, "load": load})
    load_samples = [sample for sample in load_samples
                    if isinstance(sample, dict) and isinstance(sample.get("time"), (int, float)) and
                    isinstance(sample.get("load"), (int, float)) and abs(now - sample["time"]) <= 7 * 86400]
    state["load_samples"] = load_samples

    # Only gesture/recording/timing FAILs with a nearby high-load evidence sample qualify.
    if isa_valid:
        fail_first = state.setdefault("fail_first_load", {})
        if not state.get("fail_rows_initialized"):
            for ident, signature, *_ in isa.get("fails", []):
                fail_first[ident + ":" + signature] = {"baseline": True, "first_seen": now}
            state["fail_rows_initialized"] = True
        for ident, signature, _, tool, evidence_mtime in isa.get("fails", []):
            key = ident + ":" + signature
            if key not in fail_first:
                fail_first[key] = {"baseline": False, "first_seen": now}
            first = fail_first[key]
            if first.get("baseline"):
                continue
            nearest = min((sample for sample in load_samples
                           if evidence_mtime is not None and abs(sample["time"] - evidence_mtime) <= 600),
                          key=lambda sample: abs(sample["time"] - evidence_mtime), default=None)
            qualifies = tool in ("REC", "GESTURE", "TIME") and nearest is not None and nearest["load"] > 40
            age = minutes_since(evidence_mtime, now) or 0
            detail = (f"FAIL {ident}: {tool} probe evidence was modified at load {nearest['load']:.1f} "
                      f"(>40), {age:.0f} min ago; recheck under calm load." if qualifies else "")
            trigger("fail-load:" + key, qualifies, detail)

    # Three failed attempts are enough to park a row instead of repeating it.
    if isa_valid:
        checked = {normalize_ident(ident) for ident in isa.get("checked", [])}
        parked = {normalize_ident(ident) for ident in isa.get("parked", [])}
        parked |= {normalize_ident(ident) for ident in isa.get("blocked", [])}
        live_claims = set()
        if sessions.get("valid", False):
            for sess in sessions.get("live", []):
                promise = sess.get("promise") or {}
                if promise.get("valid"):
                    live_claims |= {normalize_ident(ident) for ident in promise.get("rows", set())}
        for ident, verdict in isa.get("latest_verdicts", {}).items():
            # FAIL and BLOCKED both count as tries; restarts are the orchestrator's to count.
            fails = isa.get("fail_counts", {}).get(ident, 0)
            count = max(isa.get("tries", {}).get(ident, fails), fails)
            blocked_tries = count - fails
            retried = ident in live_claims
            open_fail = verdict.get("status") == "FAIL" and ident not in parked
            claim_text = "; a live helper is still on it" if retried and not open_fail else ""
            trigger("repeat-fail:" + ident,
                    count >= 3 and ident not in checked and (open_fail or retried),
                    f"LOOP {ident}: {count} tries without a PASS ({fails} FAIL, {blocked_tries} BLOCKED)"
                    f"{claim_text}. Ask: What did each try teach, and is the product "
                    "or the test setup failing? What is the cheapest different probe? Default: park it with "
                    "its unlock condition and start the next free item.", track=True)

        active_regressions = set(isa.get("regressions", []))
        alerted_regressions = set(state.setdefault("regressions_alerted", []))
        # Only a newly written FAIL line is a regression; a moved or re-ordered old line is not.
        fresh = state.setdefault("regression_fresh", {})
        for ident in list(fresh):
            if ident not in active_regressions:
                fresh.pop(ident, None)
        for ident in sorted(active_regressions):
            line = ident + ":" + isa.get("latest_fail_sigs", {}).get(ident, "")
            if fresh.get(ident, {}).get("line") != line:
                fresh[ident] = {"line": line, "fresh": line not in prior_fail_lines}
            due = trigger("regression:" + ident,
                          ident not in alerted_regressions and fresh[ident]["fresh"],
                          f"REGRESSION {ident}: passed before, now FAIL. Revert the merge that broke it first, fix on the side. "
                          "Ask: Which merge since the PASS touched its files? Is the new FAIL real or a stale "
                          "probe? Default: revert that merge, re-run the proof, then fix on a side branch.",
                          urgent=True, track=True)
            if due:
                alerted_regressions.add(ident)
        state["regressions_alerted"] = sorted(alerted_regressions)

        ledger_signature = hashlib.sha256(json.dumps({
            "criteria": sorted(isa.get("criteria", [])),
            "checked": sorted(isa.get("checked", [])),
            "owner": sorted(isa.get("owner", [])),
            "parked": sorted(isa.get("parked", [])),
            "blocked": sorted(isa.get("blocked", [])),
            "owner_only": sorted(isa.get("owner_only_ids", [])),
            "latest_verdicts": isa.get("latest_verdicts", {}),
            "verdict_count": isa.get("verdict_count", 0),
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        run_card = snapshot.get("run_card", {})
        if (run_card.get("valid", False) and snapshot.get("head_valid", False) and
                isa.get("ledger_mtime") is not None):
            waiting_text = run_card.get("waiting_text")
            waiting_note = state.get("unclaimed_waiting")
            if (not isinstance(waiting_note, dict) or "text" not in waiting_note or
                    "fresh" not in waiting_note or
                    "ledger_signature" not in waiting_note or "head" not in waiting_note):
                fresh = False  # first observation is a baseline, not proof the note is new
            else:
                identity_unchanged = (waiting_note.get("ledger_signature") == ledger_signature and
                                      waiting_note.get("head") == snapshot.get("head"))
                text_changed = waiting_note.get("text") != waiting_text
                fresh = bool(waiting_text) and identity_unchanged and text_changed
                if not text_changed and identity_unchanged:
                    fresh = bool(waiting_text) and bool(waiting_note.get("fresh"))
            state["unclaimed_waiting"] = {"text": waiting_text,
                                           "ledger_signature": ledger_signature,
                                           "head": snapshot.get("head"),
                                           "fresh": fresh}
        session_promises_valid = all(sess.get("promise_read_valid", True)
                                     for sess in sessions.get("live", []))
        unclaimed_valid = (run_status == "running" and run_card.get("valid", False) and
                           sessions.get("valid", False) and session_promises_valid and
                           snapshot.get("head_valid", False) and isa.get("ledger_mtime") is not None)
        waiting_note = state.get("unclaimed_waiting") or {}
        waiting_is_current = (bool(waiting_note.get("text")) and waiting_note.get("fresh", False) and
                              unclaimed_valid and
                              waiting_note.get("text") == run_card.get("waiting_text") and
                              waiting_note.get("ledger_signature") == ledger_signature and
                              waiting_note.get("head") == snapshot.get("head"))
        if unclaimed_valid:
            checked = {normalize_ident(ident) for ident in isa.get("checked", [])}
            parked = {normalize_ident(ident) for ident in isa.get("parked", [])}
            owner = {normalize_ident(ident) for ident in isa.get("owner", [])}
            owner_only = {normalize_ident(ident) for ident in isa.get("owner_only_ids", [])}
            open_items = set(isa.get("criteria", [])) - checked - parked - owner - owner_only
            open_rows = sorted(open_items)
            if state.get("unclaimed_open_set") != open_rows:
                for key in list(conditions):
                    if key.startswith("unclaimed:"):
                        trigger(key, False, "")
                state["unclaimed_open_set"] = open_rows
            claimed = set()
            for sess in sessions.get("live", []):
                promise = sess.get("promise") or {}
                if promise.get("valid"):
                    claimed |= {normalize_ident(ident) for ident in promise.get("rows", set())}
            # Grace window: a helper that just ended is usually followed by the next one.
            ended = [seconds(child.get("time_idle")) for child in sessions.get("children", [])
                     if (child.get("promise") or {}).get("valid") and child.get("time_idle") is not None]
            last_end = max((stamp for stamp in ended if stamp is not None), default=None)
            in_grace = last_end is not None and 0 <= now - last_end < setting(env, "WATCH_UNCLAIMED_GRACE_MIN", 5) * 60
            if open_items and not (open_items & claimed) and not waiting_is_current and not in_grace:
                key = "unclaimed:" + hashlib.sha256("\n".join(open_rows).encode()).hexdigest()[:12]
                trigger(key, True,
                        f"UNCLAIMED: no live PROMISE claims any of {len(open_rows)} open items ({', '.join(open_rows)}); "
                        f"{len(sessions.get('live', []))} agent(s) running. If one is working on an item, correct its promise; "
                        "otherwise start work or write a `waiting: <reason>` line in the run card. "
                        "Ask: Which open item unblocks the most? Is anything waiting only on you? Default: start a "
                        "fresh visible helper on the free item that unblocks most, smallest first.", track=True)
            else:
                for key in list(conditions):
                    if key.startswith("unclaimed:"):
                        trigger(key, False, "")
        elif run_card.get("valid", False) and run_status is not None and run_status != "running":
            for key in list(conditions):
                if key.startswith("unclaimed:"):
                    trigger(key, False, "")
            state["unclaimed_open_set"] = None

    def clock(stamp: float | None) -> str:
        return dt.datetime.fromtimestamp(stamp).astimezone().strftime("%H:%M") if stamp else "unknown"

    open_ids: list[str] = []
    tries_text = "none"
    if isa_valid:
        done_ids = {normalize_ident(i) for i in isa.get("checked", [])}
        set_aside = done_ids | {normalize_ident(i) for i in isa.get("owner", [])} | \
            {normalize_ident(i) for i in isa.get("owner_only_ids", [])}
        open_ids = [ident for ident in isa.get("criteria", []) if ident not in set_aside]
        tried = sorted(((isa.get("tries", {}).get(ident, 0), ident) for ident in open_ids), reverse=True)
        tries_text = ", ".join(f"{ident} ({count} tries)" for count, ident in tried[:3] if count) or "none"

    # Rule 10: the stall ladder. Honest progress = a new PASS/FAIL ledger line, a new tick,
    # a new PASS/FAIL result row with evidence, or a new commit. It runs even while the orchestrator is busy.
    stall = state.setdefault("stall", {})
    if not isinstance(stall, dict):
        stall = state["stall"] = {}
    if isa_valid:
        proof_lines = isa.get("pass_lines", 0) + len(isa.get("fails", []))
        row_keys = set()
        if evidence.get("valid", False):
            for result in evidence.get("results", []):
                for row in result.get("table_rows", []):
                    if row.get("status") in ("PASS", "FAIL") and row.get("evidence") and not row.get("placeholder"):
                        row_keys.add(hashlib.sha256(f"{result['path']}:{row.get('id')}:{row.get('status')}:"
                                                    f"{row.get('signature', '')}".encode()).hexdigest()[:12])
        seen_rows = set(stall.get("rows_seen", []))
        head = snapshot.get("head") if snapshot.get("head_valid") else None
        progressed = ("since" not in stall or proof_lines > stall.get("proof_lines", 0) or
                      isa.get("pass", 0) > stall.get("checked", 0) or bool(row_keys - seen_rows) or
                      (head is not None and stall.get("head") not in (None, head)))
        if progressed or waiting:
            stall.update(since=now, step=0)
            if progressed:
                stall["last_progress"] = now
        stall.update(proof_lines=max(proof_lines, stall.get("proof_lines", 0)),
                     checked=max(isa.get("pass", 0), stall.get("checked", 0)),
                     rows_seen=sorted(seen_rows | row_keys), head=head or stall.get("head"))
        minutes = (now - stall["since"]) / 60
        ask_min = setting(env, "WATCH_STALL_MIN", 10)
        live_count = len(sessions.get("live", [])) if sessions.get("valid", False) else "?"
        step = stall.get("step", 0)
        if not waiting and not isa.get("done") and step < 3:
            facts = (f"no new proof for {minutes:.0f} min (last at {clock(stall.get('last_progress'))}); "
                     f"proven {isa.get('pass', 0)}/{isa.get('total', 0)}; {live_count} helper(s) live; "
                     f"most-tried open items: {tries_text}.")
            if step == 0 and minutes >= ask_min:
                stall.update(step=1, step_at=now, baseline=action_fingerprint())
                record("stall:1", "stall", f"STALL 1/3: {facts} Ask: What exactly blocks the next proof? "
                       "What is the smallest part you can prove in 15 minutes? Default: split the oldest open "
                       "item and give its smallest provable part to a fresh visible helper.", False, True)
            elif step == 1 and minutes >= ask_min + 5:
                stall["step"] = 2
                if not acted_since(stall.get("baseline", {})):
                    record("stall:2", "stall", f"STALL 2/3: {facts} No new helper or ledger change since STALL 1. "
                           "Ask: Does every free item have a live helper? Is a helper stale or waiting on you? "
                           "Default: restart the stale helper fresh with a Delta, or start the next free item.",
                           True, True)
            elif step == 2 and minutes >= ask_min + 10:
                stall["step"] = 3
                record("stall:3", "stall", f"STALL 3/3: {facts} Ask: Which item has used its tries? What exact "
                       "condition would unlock it? Default: park it now (a BLOCKED line with the unlock "
                       "condition), note it in the run card, and start the next free item. No more stall "
                       "questions until new proof.", True, True)
                notes.append(f"Stall: {facts} Watchdog said park and stopped stall questions until new proof.")

    # Free items: needs met (run card Plan map), not claimed by any live PROMISE.
    run_card = snapshot.get("run_card", {})
    free_idle: list[str] = []
    if isa_valid and run_card.get("plan_valid") and sessions.get("valid", False):
        done_ids = {normalize_ident(i) for i in isa.get("checked", [])}
        parked_ids = {normalize_ident(i) for i in isa.get("parked", [])}
        claimed = set()
        for sess in sessions.get("live", []):
            promise = sess.get("promise") or {}
            if promise.get("valid"):
                claimed |= {normalize_ident(i) for i in promise.get("rows", set())}
        needs = run_card.get("needs", {})
        free_idle = sorted(ident for ident in open_ids if ident in needs and ident not in parked_ids and
                           ident not in claimed and needs[ident] <= done_ids)
        if free_idle and sessions.get("live") and not waiting:
            trigger("free:" + hashlib.sha256("\n".join(free_idle).encode()).hexdigest()[:12], True,
                    f"FREE: {len(free_idle)} free item(s) have no helper ({', '.join(free_idle[:10])}); "
                    f"{len(sessions['live'])} helper(s) live. Ask: Which of these unblocks the most? Does any "
                    "share files with a running helper? Default: start a fresh visible helper on the free item "
                    "that unblocks most, smallest first.", track=True)
        else:
            for key in list(conditions):
                if key.startswith("free:"):
                    trigger(key, False, "")

    # The Plan map is living: every open item has a line, needs name real items, and no needs loop.
    # A run card read from disk is checked even with an empty or missing map: then every open item is missing.
    if isa_valid and (run_card.get("plan_valid") or run_card.get("plan_checked")):
        needs = run_card.get("needs", {})
        known = {normalize_ident(i) for i in isa.get("criteria", [])}
        parked_ids = {normalize_ident(i) for i in isa.get("parked", [])}
        missing = sorted(i for i in open_ids if i not in needs and i not in parked_ids)
        unknown = sorted({n for deps in needs.values() for n in deps} - known) if known else []
        loop: list[str] = []
        finished: set[str] = set()
        def walk(node, path):  # depth-first; each node is finished once, so shared needs are not re-walked
            if loop or node in finished:
                return
            if node in path:
                loop.extend(path[path.index(node):] + [node])
                return
            for nxt in sorted(needs.get(node, ())):
                walk(nxt, path + [node])
            finished.add(node)
        for start in sorted(needs):
            walk(start, [])
        problems = ([f"open items with no Plan map line: {', '.join(missing[:10])}"] if missing else []) + \
                   ([f"needs name unknown items: {', '.join(unknown[:10])}"] if unknown else []) + \
                   ([f"needs loop: {' -> '.join(loop)}"] if loop else [])
        key = "plan:" + hashlib.sha256("\n".join(problems).encode()).hexdigest()[:12]
        trigger(key, bool(problems) and not waiting,
                f"PLAN: the run card's Plan map is out of date ({'; '.join(problems)}). Ask: What did the newest "
                "evidence change about what these items need or touch? Which chain is now the slowest? Default: "
                "fix those Plan map lines and re-name the slowest chain before the next pick.", track=True)
        for old in list(conditions):
            if old.startswith("plan:") and old != key:
                trigger(old, False, "")

    # Code changed under a running tester: the candidate it is checking is no longer the candidate.
    candidates = state.setdefault("qa_candidates", {})
    fingerprint = snapshot.get("candidate")
    if sessions.get("valid", False) and fingerprint:
        testers = [sess for sess in sessions.get("live", []) if sess.get("agent") == "qa" or
                   (sess.get("promise") or {}).get("kind") in ("screen", "timed")]
        tester_ids = {sess["id"] for sess in testers}
        for ident in list(candidates):
            if ident not in tester_ids:
                candidates.pop(ident, None)
                conditions.pop("drift:" + ident, None)
        for sess in testers:
            first = candidates.setdefault(sess["id"], fingerprint)
            child_id = sess.get("thread_id") or sess["id"]
            trigger("drift:" + sess["id"], first != fingerprint,
                    f"DRIFT: code changed while {sess.get('agent', 'tester')} {child_id} is testing "
                    f"(candidate {first[:12]} -> {fingerprint[:12]}). Ask: Is the candidate it tests still the "
                    "one you will ship? Who edited code during the test? Default: let it finish, then re-run QA "
                    "on the new candidate; make no product edits while QA runs.", urgent=True, track=True)

    # Rule 13: the orchestrator session silently running as another agent (for example after a plugin restart).
    first_agent, now_agent = sessions.get("orch_agent_first"), sessions.get("orch_agent")
    switched = bool(first_agent and now_agent and first_agent != now_agent)
    detail = (f"AGENT SWITCH: your session started as {first_agent} but its latest turn ran as {now_agent}. "
              f"Ask: Did the owner choose this? Are you still following {first_agent}'s rules? Default: tell the "
              f"owner to re-select {first_agent} for this thread; until then follow {first_agent}'s rules "
              "(delegate, don't edit product code).") if switched else ""
    if trigger("agent-switch", switched, detail, valid=sessions.get("valid", False), urgent=True, track=True):
        notes.append(detail.split(" Ask:", 1)[0])

    # Rule 12: re-anchor after a context compaction.
    compacted = sessions.get("last_compaction") if sessions.get("valid", False) else None
    if sessions.get("valid", False) and "reanchored_at" not in state:
        state["reanchored_at"] = compacted or 0  # baseline, also when none yet: older compactions are not news
    elif compacted is not None:
        if compacted > float(state["reanchored_at"] or 0):
            state["reanchored_at"] = compacted
            live = sessions.get("live", [])
            titles = ", ".join((bb.get("by_id", {}).get(sess.get("thread_id"), {}).get("title") or
                                sess.get("agent", "agent")) for sess in live[:5])
            rules = run_card.get("owner_rules", [])
            lines = [f"REANCHOR after your compaction at {clock(compacted)}. Goal: {run_card.get('goal') or 'see run card'}.",
                     f"Proven {isa.get('pass', 0)}/{isa.get('total', 0)}; open: {', '.join(open_ids[:20]) or 'none'}.",
                     f"Live helpers: {len(live)}" + (f" ({titles})" if titles else "") +
                     f"; most-tried open items: {tries_text}."]
            if rules:
                lines.append("Owner rules, word for word: " + " | ".join(rules))
            lines.append("Ask: What is the goal in one line, and which open item unblocks the most? Which owner "
                         "rule are you closest to breaking? Default: re-read HOW-TO-WORK.md, the run card (Owner "
                         "rules, Proven recipes, Answers) and the brief checklist before the next delegation.")
            for line in lines:
                messages.append(line)
            urgent_keys.append("reanchor")
            if "re-anchor" not in alert_tags:
                alert_tags.append("re-anchor")
            review["alerts"]["re-anchor"] = review["alerts"].get("re-anchor", 0) + 1

    # Climb line for the heartbeat: proven count, recent gain, free items idle.
    if isa_valid:
        history = [entry for entry in state.get("proven_history", [])
                   if isinstance(entry, list) and len(entry) == 2 and now - entry[0] <= 2 * 3600]
        history.append([now, isa.get("pass", 0)])
        state["proven_history"] = history
        past = [count for stamp, count in history if now - stamp >= 30 * 60]
        base_count = past[-1] if past else history[0][1]
        gain = isa.get("pass", 0) - base_count
        free_text = f" · {len(free_idle)} free item{'s' if len(free_idle) != 1 else ''} idle" \
            if run_card.get("plan_valid") else ""
        snapshot["climb"] = (f"proven {isa.get('pass', 0)}/{isa.get('total', 0)} · "
                             f"{gain:+d} in last 30 min{free_text}")

    # Alerts with an id expect a visible action within 10 minutes; otherwise they escalate once.
    answers = run_card.get("answers", {})
    for aid, rec in list(asked.items()):
        if not isinstance(rec, dict) or now - rec.get("at", now) > 24 * 3600:
            asked.pop(aid, None)
            continue
        if rec.get("done") or now - rec.get("at", now) < 600:
            continue
        cleared = conditions.get(rec.get("key", ""), {}).get("streak", 1) == 0
        # Acted = the problem cleared, or an ANSWER line plus a visible action (new helper, ledger change, commit).
        moved = acted_since(rec.get("baseline", {}))
        rec["acted"] = cleared or (aid in answers and moved)
        rec["done"] = True
        if not rec["acted"] and not waiting:
            answer = answers.get(aid)
            record("unanswered:" + aid, "unanswered alert",
                   f"UNANSWERED {aid} ({rec.get('kind', 'alert')}): the problem is still there 10 min after the alert"
                   + ("" if moved else "; no new helper, ledger change or commit since")
                   + (f"; your answer: {answer[:160]}" if answer else "; no ANSWER line in the run card")
                   + ". Ask: What will you do about it in the next 5 minutes? What would make it go away? "
                   "Default: take the alert's default move now and write its ANSWER line.", True, False)

    # OpenCode recovery is intentionally one reload per hour, followed by a user note if still down.
    server_state = state.setdefault("server", {})
    if server.get("valid", False):
        down = not server.get("reachable")
        server_state["down_streak"] = server_state.get("down_streak", 0) + 1 if down else 0
        if not down:
            server_state.pop("reload_pending_at", None)
        elif server_state["down_streak"] >= 2:
            last_reload = server_state.get("last_reload", 0)
            pending = server_state.get("reload_pending_at")
            if not pending and now - last_reload >= 3600:
                server_state["last_reload"] = now
                server_state["reload_pending_at"] = now
                if dry_run:
                    print("DRY-RUN: would run bb plugin reload opencode (server unreachable on two checks).")
                else:
                    out, error = BB.command(["plugin", "reload", "opencode"], 8.0)
                    print("WATCH: ran bb plugin reload opencode" + (f" ({error})" if error else ""))
            elif pending and now > pending:
                detail = f"OpenCode server still unreachable at port {server.get('port')}; check `bb opencode` and restart the plugin."
                if trigger("opencode-down", True, f"OPENCODE server: {detail}"):
                    notes.append(detail)
                    server_state["reload_pending_at"] = None

    # Only booted simulators accrue no-agent time.
    if sessions.get("valid", False) and host.get("sims_valid", False):
        if not sessions["live"] and host["booted_sims"]:
            sim_idle = state.setdefault("sim_idle", {})
            if sim_idle.get("no_agent_since") is None:
                sim_idle["no_agent_since"] = now
            sim_elapsed = (now - sim_idle["no_agent_since"]) / 60
            trigger("sim-without-agent", sim_elapsed >= setting(env, "WATCH_GHOST_MIN", 15),
                    f"SIMULATOR: {len(host['booted_sims'])} booted simulator(s), no live agent for {sim_elapsed:.0f} min.",
                    valid=sessions.get("valid", False) and host.get("sims_valid", False))
        else:
            state.setdefault("sim_idle", {})["no_agent_since"] = None
            trigger("sim-without-agent", False, "")

    # A brief without TALK-BACK leaves a blocked worker silent until it finishes.
    if sessions.get("valid", False):
        for sess in sessions.get("live", []):
            trigger("no-talkback:" + sess["id"], sess.get("talkback") is False,
                    f"BRIEF {sess.get('agent', 'agent')} {sess['id']}: no TALK-BACK block in its first message, so it "
                    "cannot report BUG/BLOCKED/QUESTION mid-run. Steer it the TALK-BACK block from subagent-delegation.")

    # Continue is rate-limited; only latest ledger verdicts count as progress.
    orch_idle = bb.get("orch_status") not in (None, "active")
    queue_empty = bb.get("queue_count") == 0
    last_msg_age = minutes_since(sessions.get("last_orch_message"), now)
    eligible = (not waiting and isa_valid and sessions.get("valid", False) and bb.get("show_valid", False) and
                bb.get("queue_valid", False) and not isa["done"] and orch_idle and queue_empty and not sessions["live"] and
                snapshot.get("head_valid", False) and last_msg_age is not None and
                last_msg_age > setting(env, "WATCH_CONTINUE_MIN", 15))
    cont = state.setdefault("continue", {})
    if eligible and not cont.get("stopped") and now - cont.get("last_at", 0) >= 900:
        signature = {ident: verdict.get("status")
                     for ident, verdict in sorted(isa.get("latest_verdicts", {}).items())}
        old = cont.get("signature")
        cont["last_at"] = now
        if old is not None and old == signature:
            cont["no_progress"] = cont.get("no_progress", 0) + 1
            print(f"WATCH: skipped unchanged continue ({cont['no_progress']}/3 no-progress checks).")
            if cont["no_progress"] >= 3:
                cont["stopped"] = True
                notes.append("No ledger-verdict progress across three continue checks; watchdog stopped prompting.")
                messages.append("🚦 WATCH STALLED: no ledger-verdict progress across three continue checks, so the watchdog "
                                "stopped nudging (machine and agent checks continue). Tell the owner what is blocking "
                                "and what would unlock it, set the run card status to waiting-owner, then wait.")
        else:
            cont["no_progress"] = 0
            cont["signature"] = signature
            facts = (f"orchestrator={bb.get('orch_status')}, last message {last_msg_age:.0f} min ago, "
                     f"queue empty, no live child sessions, HEAD={snapshot.get('head') or 'unknown'}")
            messages.append(f"WATCH CONTINUE: you are idle with ISA work left ({isa['pass']}/{isa['total']} PASS, "
                            f"{len(isa.get('parked', []))} parked). Re-check these facts cheaply before acting: {facts}. "
                            "Then take the next step per the hivecall loop and the run card, or set the run card status to "
                            "waiting-owner and tell the owner why if genuinely blocked.")

    for note in notes:
        append_note(root, note, dry_run)
    if sessions.get("valid", False):
        for sess in sessions.get("live", []):
            key = "promise_agents" if sess.get("promise") else "other_agents"
            if sess["id"] not in review[key]:
                review[key].append(sess["id"])
    if now - review.get("last_at", now) >= 60 * 60 and (
            review["promise_agents"] or review["other_agents"]):
        counts = review.get("alerts", {})
        total = sum(counts.values())
        by_type = ", ".join(f"{kind} {count}" for kind, count in sorted(counts.items())) or "none"
        judged = [rec for rec in asked.values() if isinstance(rec, dict) and rec.get("done") and
                  rec.get("at", 0) >= review.get("last_at", now) - 600]
        acted = sum(1 for rec in judged if rec.get("acted"))
        messages.append(f"WATCH REVIEW: {total} alerts since last review by type ({by_type}); "
                        f"acted on within 10 min {acted}/{len(judged)}; "
                        f"PROMISE agents {len(review['promise_agents'])}, without {len(review['other_agents'])}; "
                        "check alerts matched reality, note false alarms in the run card's lessons section.")
        review.update(last_at=now, last_sent_at=now, alerts={}, promise_agents=[], other_agents=[])
    emit()
    return alert_tags
