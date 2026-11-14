#!/usr/bin/env python3
# PURPOSE — keep a hivecall run healthy and moving: watch machine health,
# check that every agent is on track with what it promised, and keep the run
# going until the ledger (checklist.md or ISA.html) is complete, only genuine
# hard blockers remain, or the run card says the run is closed.
#
# INVARIANTS — what this script is and is not. Change these only with the user's OK.
# Mirrored in ../VISION.md §2.2 for human reading; update both in the same commit.
#
# 1. Watch, never act on the run. It never stops agents, fixes code, records
#    results or edits the ISA. It pauses its own automation when done and
#    deletes it on the check after the run card closes.
#    (Other exception: at most one OpenCode reload per hour when the server is down.)
# 2. No AI, cheap, every 5 minutes. A plain script that finishes in seconds
#    and adds no load of its own.
# 3. Quiet unless it matters. One status line per run. A message only for a
#    real problem, seen on two runs in a row, sent once per problem. Each
#    run-moving alert is a fact, two questions and a default move, with an
#    alert id the orchestrator answers in the run card. Urgent alerts
#    interrupt the turn (at most once per 10 minutes); the rest are queued.
# 4. Judge agents only against their own promise. "Off track" means no real
#    progress on the work the agent's brief promised, past its pace.
#    Never guess from activity, tone or file names.
# 5. Real progress means proof. Testers: a new PASS/FAIL with evidence.
#    Builders: a growing build log or edits in their own lane. Placeholders
#    and "waiting" don't count.
# 6. Fewer false alarms beats more checks. When an alarm is wrong, remove or
#    loosen the check. Never add a special case.
# 7. Never alarm on missing data. If a read fails (BB, OpenCode, files), skip
#    that check for this run.
# 8. Every agent must be visible in BB. An agent running but not shown is
#    always reported.
# 9. Protect the machine. Report high load, low disk, huge files and orphaned
#    recorders or log processes.
# 10. Keep the run climbing, without spinning. Progress means honest proof: a
#     new PASS/FAIL ledger verdict, a new PASS/FAIL result row with evidence,
#     or a new commit. Revise verdicts, BLOCKED and waiting don't count. With
#     no progress it asks at 10 minutes, asks again at 15 if nothing was done,
#     and says park at 20, even while the orchestrator is busy. Then it stops
#     nudging until progress and leaves the user a note. An idle orchestrator
#     with work left is nudged; 3 idle checks with no change stop that too.
# 11. Stop when done. When the ledger is complete or only parked items remain,
#     pause its own automation; when the run card says closed, pause first and
#     delete the automation on the check after a successful pause.
#     While the run card says waiting, never nudge; keep the other checks.
# 12. Re-anchor after compaction. When the orchestrator compacts its context,
#     send one short message: goal, done and open items, live helpers, stuck
#     items, the owner's rules word for word, and where to re-read the rest.
# 13. Keep the orchestrator itself. When its session's latest turn runs as a
#     different agent than the one it started as, alert it and leave the user
#     a note. Only the user can switch it back.

"""Cheap watchdog for a long-running BB/ISA task."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import socket
import sqlite3
import stat as stat_module
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hivewatch.shell import (
    BB,
    BBAdapter,
    append_note,
    command,
    dispatch,
    flatten_dicts,
    load_bb,
    minutes_since,
    parse_elapsed,
    parse_load,
    seconds,
    setting,
    state_read,
    state_write,
)
from hivewatch.promise import (
    BB_WORKTREES,
    OFF_TRACK_IDLE_MIN,
    PROMISE_DEFAULTS,
    bind_promise_paths,
    declared_path,
    lane_roots,
    normalize_ident,
    off_track_idle_age,
    parse_promise,
    parse_promise_rows,
    promise_metrics,
    result_session_finished,
    result_verdict_key,
)
from hivewatch.ledger import (
    EVIDENCE_REFERENCE,
    ISA_VERDICT,
    PLACEHOLDER,
    VERDICT,
    clear_done_state,
    delete_automation,
    extract_html_ledger,
    extract_markdown_ledger,
    finish_closed_run,
    load_results,
    parse_isa,
    parse_result_text,
    pause_automation,
    read_run_card,
    read_run_status,
    walk_files,
)

from hivewatch.probes import (
    bb_child_sessions,
    load_host_facts,
    load_lane_facts,
    load_server,
    load_sessions,
)


def collect(env: dict[str, str], now: float | None = None) -> dict:
    now = now or time.time()
    root = env.get("REPO", "")
    isa = parse_isa(env.get("LEDGER") or env.get("ISA") or os.path.join(root, "_ai/docs/ISA.html"), root)
    run_card = read_run_card(env.get("RUN_CARD") or os.path.join(root, ".hivecall", "run.md"))
    run_status = run_card["status"]
    host = load_host_facts(root, now, env)
    sessions = load_sessions(env.get("ORCH_SESSION", ""), now, root, env.get("VERIFY_DIR", ""),
                             bb_child_sessions(env.get("ORCH_THREAD", "")))
    bb = BB.load(env.get("ORCH_THREAD", ""), sessions["children"], sessions["live"])
    server = load_server()
    promised_paths = {session["promise"].get("result_path") for session in sessions["children"]
                      if session.get("promise") and session["promise"].get("result_path")}
    evidence = load_results(env.get("VERIFY_DIR", ""), isa, now, promised_paths)
    lanes = load_lane_facts(sessions["live"])
    head, head_error = command(["git", "-C", root, "rev-parse", "HEAD"], 2.0)
    # Candidate = HEAD plus uncommitted product edits (run files excluded), for the DRIFT check.
    diff, diff_error = command(["git", "-C", root, "diff", "HEAD", "--", ".", ":(exclude).hivecall",
                                ":(exclude).lanes", ":(exclude)_ai"], 3.0)
    # New, untracked source files change the candidate too; screenshots and logs a tester writes do not.
    others, others_error = command(["git", "-C", root, "ls-files", "--others", "--exclude-standard", "--", ".",
                                    ":(exclude).hivecall", ":(exclude).lanes", ":(exclude)_ai"], 3.0)
    untracked = []
    for name in sorted(others.splitlines()) if not others_error else []:
        if re.search(r"\.(html?|css|scss|m?js|jsx|tsx?|py|swift|kt|go|rs|json)$", name):
            try:
                st = os.stat(os.path.join(root, name))
                untracked.append(f"{name}:{st.st_size}:{st.st_mtime_ns}")
            except OSError:
                pass
    candidate = (hashlib.sha256((f"{head}\n{diff}\n" + "\n".join(untracked)).encode()).hexdigest()
                 if head and not head_error and not diff_error else None)
    return {"now": now, "host": host, "server": server, "sessions": sessions, "bb": bb,
            "isa": isa, "run_status": run_status, "run_card": run_card, "evidence": evidence,
            "lanes": lanes, "head": head, "candidate": candidate,
            "head_valid": bool(head and not head_error),
            "head_error": head_error}


def report(snapshot: dict) -> str:
    host, server, sessions, bb, isa, evidence = (snapshot[k] for k in
        ("host", "server", "sessions", "bb", "isa", "evidence"))
    newest = evidence["newest"]
    newest_text = (f"{Path(newest['path']).name} ({minutes_since(newest['mtime'], snapshot['now']):.0f} min ago)"
                   if newest else "none") if evidence.get("valid", False) else "unknown"
    port = server["port"] if server["port"] else "unknown"
    live_count = len(sessions["live"]) if sessions.get("valid", False) else "unknown"
    visible_count = (sum(1 for t in bb["children"] if t.get("status") == "active" and t.get("visible"))
                     if bb.get("list_valid", False) else "unknown")
    status = ("complete/parked-only" if isa["done"] else "work remains") if not isa.get("error") else "unknown"
    isa_progress = (f"{isa['pass']}/{isa['total']} checked, {isa['pass_lines']} PASS lines; "
                    f"frontmatter {isa.get('frontmatter') or 'unknown'}; owner {isa['owner_done']}/{len(isa['owner'])}; "
                    f"blocked {len(isa['blocked'])}; parked {len(isa.get('parked', []))}"
                    if not isa.get("error") else "unknown")
    lines = [
        "WATCH REPORT",
        f"Load (1m): {host['load'] if host.get('uptime_valid') else 'unknown'}; disk free: {host['free_gb']:.1f} GB" if host.get("df_valid") else f"Load (1m): {host['load'] if host.get('uptime_valid') else 'unknown'}; disk free: unknown",
        f"Booted simulators: {len(host['booted_sims']) if host.get('sims_valid') else 'unknown'}; watched processes: {len(host['processes']) if host.get('processes_valid') else 'unknown'}",
        f"OpenCode: attached={server['attached'] if server.get('valid') else 'unknown'} port={port} TCP={('reachable' if server['reachable'] else 'unreachable') if server.get('valid') else 'unknown'}",
        f"Live child sessions: {live_count}; BB-visible active children: {visible_count}; orchestrator={bb['orch_status'] if bb.get('show_valid') else 'unknown'}; queue={bb['queue_count'] if bb.get('queue_valid') else 'unknown'}",
        f"ISA: {isa_progress}; {status}",
        f"Newest evidence: {newest_text}; recent result files: {len(evidence['results']) if evidence.get('valid') else 'unknown'}",
    ]
    errors = [e for e in (isa.get("error"), host.get("uptime_error"), host.get("df_error"),
                           host.get("sims_error"), host.get("ps_error"), host.get("recent_big_error"),
                           server.get("error"), sessions.get("error"), evidence.get("error"),
                           *bb.get("errors", [])) if e]
    if errors:
        lines.append("Read warnings: " + "; ".join(errors))
    return "\n".join(lines)


def summary_line(snapshot: dict, alert_tags: list[str]) -> str:
    host = snapshot.get("host", {})
    sessions = snapshot.get("sessions", {})
    bb = snapshot.get("bb", {})
    isa = snapshot.get("isa", {})
    load = host.get("load") if host.get("uptime_valid") else None
    free = host.get("free_gb") if host.get("df_valid") else None
    visible = (sum(1 for child in bb.get("children", [])
                   if child.get("status") == "active" and child.get("visible"))
               if bb.get("list_valid") else None)
    live = len(sessions.get("live", [])) if sessions.get("valid") else None
    if visible is None and live is None:
        agents = "? agents visible"
    elif visible is not None and visible == live:
        agents = f"{visible} agents visible"
    else:
        agents = f"{visible if visible is not None else '?'}/{live if live is not None else '?'} agents visible"
    ledger = (f"{isa['pass']}/{isa['total']}" if not isa.get("error") and
              isa.get("pass") is not None and isa.get("total") is not None else "?/?")
    status = "OK" if not alert_tags else f"ALERT: {alert_tags[0]}" + (
        f" +{len(alert_tags) - 1}" if len(alert_tags) > 1 else "")
    climb = f" · {snapshot['climb']}" if snapshot.get("climb") else ""
    return (f"load {load:.0f}" if load is not None else "load ?") + " · " + \
        (f"disk {free:.0f} GB" if free is not None else "disk ? GB") + \
        f" · {agents} · {ledger} · {status}{climb}"


def status_table(snapshot: dict) -> list[str]:
    """One-row owner status table appended to every watchdog message (lines, not one string)."""
    isa = snapshot.get("isa", {})
    if isa.get("error") or not isa.get("total"):
        return []
    checked = {normalize_ident(i) for i in isa.get("checked", [])}
    parked = {normalize_ident(i) for i in isa.get("parked", [])} - checked
    owner = {normalize_ident(i) for i in isa.get("owner", [])} - checked
    promised = set()
    for sess in snapshot.get("sessions", {}).get("live", []):
        promise = sess.get("promise") or {}
        promised |= {normalize_ident(i) for i in promise.get("rows", set())}
    in_progress = promised - checked - parked - owner
    total = isa["total"]
    not_started = max(total - len(checked) - len(parked) - len(owner) - len(in_progress), 0)
    owner_cell = f"{len(owner)}" + (f" (+{isa.get('owner_only', 0)} not counted)" if isa.get("owner_only") else "")
    return ["| Done | In progress | Not started | Stuck | Owner-only |",
            "|---|---|---|---|---|",
            f"| {len(checked)}/{total} ({round(len(checked) * 100 / total)}%) | {len(in_progress)} | "
            f"{not_started} | {len(parked)} | {owner_cell} |"]


def evaluate(snapshot: dict, state: dict, env: dict[str, str], dry_run: bool) -> list[str]:
    now = snapshot["now"]
    host, server, sessions, bb, isa, evidence = (snapshot[k] for k in
        ("host", "server", "sessions", "bb", "isa", "evidence"))
    root = env.get("REPO", "")
    thread_id = env.get("ORCH_THREAD", "")
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


def synthetic(name: str, now: float) -> dict:
    old = now - 25 * 60
    isa = {"pass": 0, "total": 2, "pass_lines": 0, "owner": [], "owner_done": 0, "blocked": [],
           "parked": [], "checked": [], "fails": [], "done": False, "error": "",
           "latest_verdicts": {}, "fail_counts": {}, "criteria": ["ISC-001", "ISC-002"],
           "regressions": [], "owner_only_ids": [], "ledger_mtime": now - 100,
           "verdict_count": 0}
    host = {"load": 5.0, "uptime_valid": True, "free_gb": 80.0, "df_valid": True,
            "processes": [], "processes_valid": True, "recent_big": [], "recent_big_valid": True,
            "booted_sims": [], "sims_valid": True, "files": []}
    server = {"reachable": True, "valid": True, "attached": True, "port": 49374}
    sessions = {"live": [], "children": [], "last_orch_message": now, "error": "", "valid": True}
    bb = {"children": [], "orch_status": "active", "queue_count": 1, "binding": {}, "errors": [],
          "list_valid": True, "show_valid": True, "queue_valid": True, "binding_valid": True}
    evidence = {"files": [], "newest": {"path": "/fixture/evidence.txt", "name": "evidence.txt", "mtime": now},
                "results": [], "valid": True}
    if name == "stuck-agent":
        evidence["newest"]["mtime"] = old
        evidence["files"].append({"path": "/fixture/worker-result.md", "name": "worker-result.md", "mtime": old, "size": 100})
        evidence["results"].append({"path": "/fixture/INT8-A-result.md", "name": "INT8-A-result.md",
                                    "mtime": old, "rows": [], "table_rows": [],
                                    "verdict_count": 0, "pending_wait": None, "builder": False})
    elif name == "unrecorded-pass":
        row = {"id": "ISC-123", "status": "PASS", "text": "observed expected result; evidence result.png",
               "placeholder": False, "evidence": True}
        evidence["results"].append({"path": "/fixture/worker-result.md", "name": "worker-result.md",
                                    "mtime": old, "rows": [("ISC-123", "PASS")], "table_rows": [row],
                                    "verdict_count": 1, "pending_wait": None, "builder": False})
        evidence["newest"]["mtime"] = now
    elif name == "superseded-pass":
        result_mtime = now - 60 * 60
        evidence["results"].append({"path": "/fixture/ISC-013.1-result.md", "name": "ISC-013.1-result.md",
                                    "mtime": result_mtime, "rows": [("ISC-013.1", "PASS")],
                                    "table_rows": [{"id": "ISC-013.1", "status": "PASS",
                                                    "text": "old pass; evidence old.png"}],
                                    "verdict_count": 1, "pending_wait": None, "builder": False})
        isa["latest_verdicts"] = {"ISC-013.1": {"status": "FAIL", "reason": "newer smoke failed"}}
        isa["ledger_mtime"] = now - 30 * 60
    elif name in ("orphan-recorder", "orphan-recorder-active"):
        host["processes"] = [{"pid": 123, "ppid": 1, "age": 1200,
                              "command": "recordVideo /fixture/out.mp4", "orphan": True}]
        if name == "orphan-recorder-active":
            host["processes"].extend([
                {"pid": 124, "ppid": 1, "age": 1200,
                 "command": "xcrun simctl spawn booted launchd", "orphan": True},
                {"pid": 125, "ppid": 1, "age": 1200,
                 "command": "log stream --style compact", "orphan": True},
            ])
            promise = parse_promise("PROMISE: kind=screen rows=001 result=Jules-result.md lane=- pace=10")
            promise["result_path"] = "/fixture/Jules-result.md"
            sess = {"id": "ses-jules", "agent": "qa", "created": now - 5 * 60,
                    "last_message": now, "last_assistant": now, "time_idle": None,
                    "idle_outcome": None, "thread_id": "thr-jules", "visible": True,
                    "promise": promise, "promise_read_valid": True, "steers": []}
            sessions.update(live=[sess], children=[sess])
            bb["by_id"] = {"thr-jules": {"id": "thr-jules", "title": "Jules"}}
    elif name == "unclaimed":
        isa.update(total=5, criteria=[f"ISC-{i:03d}" for i in range(1, 6)],
                   owner=["ISC-004"], owner_only_ids=["ISC-005"], parked=["ISC-003"],
                   latest_verdicts={"ISC-003": {"status": "BLOCKED"}})
        promise = {"valid": True, "kind": "helper", "rows": set(), "result_path": "/fixture/helper.md",
                   "pace": 20}
        sess = {"id": "ses-claimer", "agent": "helper", "created": now, "last_message": now,
                "last_assistant": now, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-claimer", "visible": True, "promise": promise,
                "promise_read_valid": True, "steers": []}
        sessions.update(live=[sess], children=[sess])
        bb["by_id"] = {"thr-claimer": {"id": "thr-claimer", "title": "claimer"}}
    elif name == "leftover-session":
        promise = {"valid": True, "kind": "helper", "rows": {"ISC-001"},
                   "result_path": "/fixture/stale-result.md", "pace": 20}
        sess = {"id": "ses-leftover", "agent": "builder", "created": now - 601 * 60,
                "last_message": now - 601 * 60, "last_assistant": now - 601 * 60, "time_idle": None,
                "idle_outcome": None, "thread_id": "thr-ended", "visible": False,
                "promise": promise, "promise_read_valid": True, "talkback": False, "steers": []}
        sessions.update(live=[sess], children=[sess])
        bb["children"] = [{"id": "thr-ended", "status": "failed", "title": "ended helper",
                            "bound_sessions": [sess], "sessions": [sess]}]
        bb["by_id"] = {"thr-ended": bb["children"][0]}
    elif name == "idle-helper":
        sess = {"id": "ses-idle", "agent": "helper", "created": old,
                "last_message": old, "last_assistant": old, "time_idle": now - 60,
                "idle_outcome": "completed", "thread_id": "thr-idle", "visible": True,
                "promise": {"valid": True, "kind": "helper", "rows": {"ISC-001"},
                            "result_path": "/fixture/idle.md", "pace": 20}}
        bb["children"] = [{"id": "thr-idle", "status": "active", "title": "finished helper",
                            "bound_sessions": [sess], "sessions": []}]
        bb["by_id"] = {"thr-idle": bb["children"][0]}
        sessions["children"] = [sess]
    elif name == "ghost-agent":
        bb["children"] = [{"id": "thr-fixture", "title": "worker", "status": "active", "visible": True,
                            "last_activity": old, "sessions": []}]
    elif name == "ghost-agent-no-message":
        sess = {"id": "ses-fixture", "agent": "builder", "created": old,
                "last_message": None, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": True}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "worker", "status": "active",
                            "visible": True, "last_activity": old, "bound_sessions": [sess],
                            "sessions": [sess]}]
    elif name == "invisible-agent":
        sess = {"id": "ses-fixture", "agent": "builder", "created": old, "last_message": now,
                "time_idle": None, "idle_outcome": None, "thread_id": None, "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
    elif name == "high-load":
        host["load"] = 160.0
    elif name == "disk-big-file":
        host["free_gb"] = 4.0
        host["recent_big"] = [{"path": "/fixture/recording.mp4", "name": "recording.mp4", "size": 220*1024*1024, "created": now-60}]
    elif name == "fail-under-load":
        host["load"] = 41.0
        isa["fails"] = [("ISC-123", "sig123", "ISC-123: FAIL - fixture", "REC", now)]
    elif name == "server-down":
        server.update(reachable=False, port=49374)
    elif name in ("continue", "anti-spin"):
        bb.update(orch_status="idle", queue_count=0)
        sessions["last_orch_message"] = now - 20*60
    elif name == "working-old-bb":
        sess = {"id": "ses-working", "agent": "builder", "created": old,
                "last_message": now - 2 * 60, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": True}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "working child", "status": "active",
                            "visible": True, "last_activity": old, "bound_sessions": [sess],
                            "sessions": [sess]}]
    elif name == "resumed-idle-agent":
        sess = {"id": "ses-resumed", "agent": "builder", "created": old,
                "last_message": now, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "resumed worker", "status": "idle",
                            "visible": False, "updatedAt": now}]
    elif name == "read-failure":
        host.update(load=200.0, uptime_valid=False, uptime_error="fixture timeout",
                    free_gb=1.0, df_valid=False, df_error="fixture timeout",
                    booted_sims=["Fixture (Booted)"])
        sess = {"id": "ses-fixture", "agent": "builder", "created": old, "last_message": now,
                "time_idle": None, "idle_outcome": None, "thread_id": None, "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        sessions.update(valid=False, last_orch_message=now - 20 * 60, error="fixture SQLite timeout")
        server.update(valid=False, reachable=False, error="fixture timeout")
        bb.update(queue_count=None, list_valid=False, show_valid=False, queue_valid=False,
                  binding_valid=False, errors=["fixture read timeout"],
                  children=[{"id": "thr-fixture", "status": "active", "bound_sessions": [], "sessions": []}])
        isa.update(done=False, error="fixture ISA read failure")
        evidence.update(valid=False, error="fixture verification scan failure",
                        newest={"path": "/fixture/wait.md", "name": "wait.md", "mtime": old},
                        files=[{"path": "/fixture/build.log", "name": "build.log", "mtime": old,
                                "size": 100}],
                        results=[{"path": "/fixture/worker-result.md", "name": "worker-result.md",
                                  "mtime": old, "rows": [("ISC-123", "PASS")], "verdict_count": 1,
                                  "pending_wait": None, "builder": False}])
    elif name == "done":
        isa.update({"pass": 1, "total": 1, "pass_lines": 1, "pass_ids": ["ISC-001"],
                    "checked": ["ISC-001"], "done": True})
    return {"now": now, "host": host, "server": server, "sessions": sessions, "bb": bb,
            "isa": isa, "evidence": evidence,
            "run_status": "running" if name in ("done", "not-closed", "unclaimed", "reopen") else None,
            "run_card": {"valid": True, "status": None, "waiting_text": None},
            "head": "fixture-head", "head_valid": True}


def simulate(name: str, state_path: str, env: dict[str, str]) -> None:
    base = 1_800_000_000.0
    state = state_read(state_path)
    if name in ("orphan-recorder", "orphan-recorder-active"):
        state = {}
        if name == "orphan-recorder":
            state["orphan_idle"] = {"no_agent_since": base - 15 * 60}
    if name in ("closed-delete", "done", "not-closed"):
        sim_env = dict(env, AUTOMATION_ID="auto-fixture", PROJECT_ID="project-fixture")
        state = {}
        output = io.StringIO()
        if name == "closed-delete":
            first = synthetic(name, base)
            first["run_status"] = "closed"
            with redirect_stdout(output):
                evaluate(first, state, sim_env, True)
            if "DRY-RUN: would run bb automation delete" in output.getvalue():
                raise AssertionError("closed run deleted its automation on the first check")
            if "DRY-RUN: would run bb automation pause auto-fixture" not in output.getvalue():
                raise AssertionError(f"first closed check did not pause the automation: {output.getvalue()}")
            # Dry-run cannot persist a real pause, so model the completed first check here.
            state["closed_pause_recorded"] = True
            state["closed_automation_id"] = "auto-fixture"
            second = synthetic(name, base + 300)
            second["run_status"] = "closed"
            with redirect_stdout(output):
                evaluate(second, state, sim_env, True)
            if "DRY-RUN: would run bb automation delete auto-fixture --project project-fixture --yes" not in output.getvalue():
                raise AssertionError(f"next closed check did not delete the explicit automation id: {output.getvalue()}")
            no_id_env = {"REPO": env.get("REPO", ""), "ORCH_THREAD": "fixture-thread"}
            no_id_state = {}
            no_id_output = io.StringIO()
            for i in range(2):
                no_id_snapshot = synthetic(name, base + i * 300)
                no_id_snapshot["run_status"] = "closed"
                with redirect_stdout(no_id_output):
                    evaluate(no_id_snapshot, no_id_state, no_id_env, True)
            if "bb automation delete" in no_id_output.getvalue():
                raise AssertionError("closed run deleted without a saved or explicit automation id")
            print("SIM closed-delete: first closed check paused; next check would delete auto-fixture by explicit id; missing id did not delete.")
            print(summary_line(second, []))
            return
        if name == "not-closed":
            for status in ("running", "waiting-owner", "waiting-usage"):
                snap = synthetic(name, base)
                snap["run_status"] = status
                with redirect_stdout(output):
                    evaluate(snap, state, sim_env, True)
            if "bb automation delete" in output.getvalue():
                raise AssertionError(f"non-closed status deleted the automation: {output.getvalue()}")
            print("SIM not-closed: running, waiting-owner, and waiting-usage did not delete the automation.")
            print(summary_line(snap, []))
            return
        for i in range(2):
            snap = synthetic(name, base + i * 900)
            snap["run_status"] = "running"
            with redirect_stdout(output):
                evaluate(snap, state, sim_env, True)
        if "bb automation delete" in output.getvalue():
            raise AssertionError(f"ledger completion without closed status deleted the automation: {output.getvalue()}")
        print("SIM done: complete ledger paused the automation; no delete while run card was not closed.")
        print(summary_line(snap, []))
        return
    if name == "alert-once":
        state = {}
        sim_env = dict(env, WATCH_AGENT_MAX_HOURS="100")
        session = {"id": "ses-fixture", "agent": "builder", "created": base,
                   "last_message": base - 15 * 60, "time_idle": None, "idle_outcome": None,
                   "thread_id": "thr-fixture", "visible": True}
        output = io.StringIO()

        def run(now: float, last_message: float) -> list[str]:
            session["last_message"] = last_message
            snap = synthetic(name, now)
            snap["sessions"].update(live=[session], children=[session])
            with redirect_stdout(output):
                found = evaluate(snap, state, sim_env, True)
            return found

        persistent_alerts = 0
        for i in range(39):
            tags = run(base + i * 5 * 60, base - 15 * 60)
            persistent_alerts += tags.count("stuck agent")
        if persistent_alerts != 1:
            raise AssertionError(f"persistent condition alerted {persistent_alerts} times over 3+ hours")

        clear_at = base + 195 * 60
        tags = run(clear_at, clear_at)
        record = state["conditions"]["stuck-agent:ses-fixture"]
        if "stuck agent" in tags or record.get("streak") != 0 or record.get("last_alert") != 0:
            raise AssertionError(f"valid inactive read did not clear the alert occurrence: {record}")
        if "stuck agent" in run(clear_at + 5 * 60, clear_at):
            raise AssertionError("reactivated condition alerted before its second active check")
        tags = run(clear_at + 10 * 60, clear_at)
        if "stuck agent" in tags:
            raise AssertionError("reactivated condition alerted on its first active check")
        tags = run(clear_at + 15 * 60, clear_at)
        if "stuck agent" not in tags:
            raise AssertionError("reactivated condition did not alert on its second active check")
        tags = run(clear_at + 20 * 60, clear_at)
        if "stuck agent" in tags:
            raise AssertionError("reactivated persistent condition alerted more than once")
        print("SIM alert-once: one stuck-agent alert across 3+ hours; clear reset it; recurrence alerted once after two checks.")
        snap = synthetic(name, clear_at + 20 * 60)
        snap["sessions"].update(live=[session], children=[session])
        print(summary_line(snap, tags))
        return
    if name == "anti-spin":
        state = {}
        output = io.StringIO()
        unchanged_ledger = {"ISC-001": {"status": "PASS"}}
        for i in range(4):
            now = base + i * 900
            snap = synthetic(name, now)
            snap["head"] = f"fixture-commit-{i}"
            snap["isa"]["latest_verdicts"] = unchanged_ledger
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
            cont = state.get("continue", {})
            if cont.get("no_progress") != i:
                raise AssertionError(f"git commit counted as ledger progress on check {i + 1}: {cont}")
            if cont.get("stopped", False) != (i == 3):
                raise AssertionError(f"anti-spin stop mismatch on check {i + 1}: {cont}")

        cases = (
            ("PASS", {}, {"ISC-001": {"status": "PASS"}}),
            ("FAIL", {"ISC-001": "PASS"},
             {"ISC-001": {"status": "PASS"}, "ISC-002": {"status": "FAIL"}}),
            ("BLOCKED", {"ISC-001": "PASS", "ISC-002": "FAIL"},
             {"ISC-001": {"status": "PASS"}, "ISC-002": {"status": "FAIL"},
              "ISC-003": {"status": "BLOCKED"}}),
        )
        for i, (status, previous, current) in enumerate(cases, start=1):
            progress_state = {"continue": {"last_at": base + 3 * 900,
                                            "signature": previous, "no_progress": 2}}
            now = base + (3 + i) * 900
            snap = synthetic(name, now)
            snap["head"] = "fixture-commit"
            snap["isa"]["latest_verdicts"] = current
            alerts = evaluate(snap, progress_state, env, True)
            cont = progress_state["continue"]
            if cont.get("no_progress") != 0 or cont.get("stopped"):
                raise AssertionError(f"new {status} verdict did not reset the continue streak: {cont}")

        print("SIM anti-spin: 3 unchanged-ledger checks stopped prompting despite new commits; new PASS/FAIL/BLOCKED verdicts reset the streak.")
        print(summary_line(snap, alerts))
        return
    if name == "combined-alerts":
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic("high-load", base + i * 60)
            snap["host"].update(load=160.0, free_gb=4.0)
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
        text = output.getvalue()
        host_lines = [line for line in text.splitlines() if re.match(r"(?:🚦 )?HOST ", line)]
        if text.count("DRY-RUN: would queue to") != 1 or len(host_lines) != 2:
            raise AssertionError(f"alerts were not one combined, one-line-per-alert message: {text!r}")
        print(text, end="")
        print("SIM combined-alerts: two alerts would be sent in one combined message.")
        print(summary_line(snap, alerts))
        return
    if name == "lane-drift":
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builder_lane = root / "_ai" / "tools" / "watch"
            own_file = builder_lane / "watch.py"
            source = root / "src" / "tester-output.png"
            other_lane = root / ".lanes" / "other-live"
            other_source = other_lane / "src" / "other.ts"
            own_file.parent.mkdir(parents=True)
            source.parent.mkdir(parents=True)
            other_source.parent.mkdir(parents=True)
            started = time.time()
            own_file.write_text("initial lane file", encoding="utf-8")
            os.utime(own_file, (started - 600, started - 600))
            source.write_bytes(b"tester output")
            other_source.write_text("another live lane", encoding="utf-8")
            builder = {"id": "ses-builder", "created": started,
                       "promise": {"valid": True, "kind": "code",
                                    "lane_path": str(builder_lane)}}
            now = time.time()
            facts = load_lane_facts([builder])[builder["id"]]
            if not facts["valid"] or facts["latest_mtime"] != os.stat(own_file).st_mtime:
                raise AssertionError(f"out-of-lane files affected the promise lane signal: {facts}")
            own_file.write_text("changed inside promise lane", encoding="utf-8")
            detected = load_lane_facts([builder])[builder["id"]]
            if detected["latest_mtime"] != os.stat(own_file).st_mtime:
                raise AssertionError(f"change inside promise lane was missed: {detected}")
        print("SIM lane-drift: tester output elsewhere is ignored; own-lane change is the code signal.")
        return
    if name in ("on-track-code", "fast-jules", "new-testers-old-results", "superseded-pass"):
        state = {}
        alerts = []
        for i in range(2):
            now = base + i * 300
            snap = synthetic(name, now)
            if name == "on-track-code":
                sessions = []
                lanes = {}
                for agent in ("Sam", "Kai"):
                    ident = "ses-" + agent.lower()
                    promise = {"valid": True, "kind": "code", "rows": set(), "pace": 20,
                               "lane_path": f"/fixture/{agent}"}
                    sessions.append({"id": ident, "agent": "code", "created": base - 60 * 60,
                                     "last_message": now, "time_idle": None, "idle_outcome": None,
                                     "thread_id": "thr-" + agent.lower(), "visible": True,
                                     "promise": promise, "steers": []})
                    lanes[ident] = {"valid": True, "latest_mtime": base - 10 * 60,
                                    "build_mtime": None}
                    snap["bb"].setdefault("by_id", {})["thr-" + agent.lower()] = {
                        "title": agent}
                snap["sessions"].update(live=sessions, children=sessions)
                snap["lanes"] = lanes
                snap["evidence"]["results"] = [{"path": "/fixture/tester-changing-result.md",
                    "name": "tester-changing-result.md", "mtime": now, "rows": [],
                    "table_rows": [], "verdict_count": 0, "builder": False}]
            elif name == "fast-jules":
                rows = "\n".join(f"| ISC-{i:03d} | PASS | checked result; evidence ISC-{i:03d}.png |"
                                  for i in range(1, 11))
                mtime = now - 5 * 60
                parsed = parse_result_text(rows, mtime)
                promise = {"valid": True, "kind": "screen",
                           "rows": {f"ISC-{i:03d}" for i in range(1, 11)},
                           "pace": 10, "result_path": "/fixture/Jules-result.md"}
                sess = {"id": "ses-jules", "agent": "qa", "created": base - 60 * 60,
                        "last_message": now, "time_idle": None, "idle_outcome": None,
                        "thread_id": "thr-jules", "visible": True, "promise": promise,
                        "promise_read_valid": True, "steers": [now - 30 * 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-jules": {"title": "Jules"}}
                snap["evidence"]["results"] = [{"path": promise["result_path"],
                    "name": "Jules-result.md", "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "new-testers-old-results":
                sessions = []
                for n, agent in enumerate(("Sam", "Kai")):
                    promise = {"valid": True, "kind": "screen", "rows": {f"ISC-{n + 1:03d}"},
                               "pace": 10, "result_path": f"/fixture/{agent}-new-result.md"}
                    sessions.append({"id": f"ses-{agent.lower()}", "agent": "qa",
                                     "created": base - 5 * 60, "last_message": now,
                                     "time_idle": None, "idle_outcome": None,
                                     "thread_id": f"thr-{agent.lower()}", "visible": True,
                                     "promise": promise, "promise_read_valid": True, "steers": []})
                snap["sessions"].update(live=sessions, children=sessions)
                snap["bb"]["by_id"] = {f"thr-{agent.lower()}": {"title": agent}
                                        for agent in ("Sam", "Kai")}
                snap["evidence"]["results"] = [{"path": f"/fixture/INT{i}-A-result.md",
                    "name": f"INT{i}-A-result.md", "mtime": base - 45 * 60,
                    "rows": [], "table_rows": [], "verdict_count": 0,
                    "pending_wait": None, "builder": False}
                    for i in (8, 9, 10, 11, 12, 13, 14, 15)]
            print(f"SIM {name} run {i + 1}:")
            alerts = evaluate(snap, state, env, True)
            if "off track" in alerts or "stuck agent" in alerts:
                raise AssertionError(f"false no-progress alert: {alerts}")
        if name == "on-track-code":
            print("SIM on-track-code: Sam and Kai stayed silent within pace; unrelated tester output did not count.")
        elif name == "fast-jules":
            metrics = promise_metrics(snap["sessions"]["live"][0], snap, state)
            if metrics["answers"] != 10 or metrics["unanswered"] != 1 or metrics["breached"]:
                raise AssertionError(f"fast Jules context mismatch: {metrics}")
            print("SIM fast-jules: 10 recent answers and one unanswered steer did not raise off-track.")
        elif name == "new-testers-old-results":
            if any(key.startswith(("off-track:", "stuck-agent:")) and
                   (record.get("streak", 0) > 0 or record.get("last_alert", 0))
                   for key, record in state.get("conditions", {}).items()):
                raise AssertionError("old result files were attributed to new live testers")
            print("SIM new-testers-old-results: two new testers without result files plus eight old files stayed silent.")
        else:
            if "unrecorded PASS" in alerts:
                raise AssertionError("superseded ISC-013.1 PASS was reported as unrecorded")
            print("SIM superseded-pass: old ISC-013.1 PASS stayed silent after the ledger's newer FAIL.")
        print(summary_line(snap, alerts))
        return
    if name == "unrecorded-pass-reload":
        state = {}
        result = {"path": "/fixture/ISC-139-result.md", "name": "ISC-139-result.md",
                  "mtime": base - 25 * 60, "rows": [("ISC-139", "PASS")],
                  "table_rows": [{"id": "ISC-139", "status": "PASS", "text": "observed; evidence 139.png"}],
                  "verdict_count": 1, "builder": False}
        legacy = {"path": "/fixture/ISC-140-result.md", "name": "ISC-140-result.md",
                  "mtime": base - 25 * 60, "rows": [("ISC-140", "PASS")],
                  "table_rows": [{"id": "ISC-140", "status": "PASS", "text": "observed; evidence 140.png"}],
                  "verdict_count": 1, "builder": False}
        state["conditions"] = {"unrecorded-pass:/fixture/ISC-140-result.md:ISC-140":
                                {"streak": 2, "last_alert": base - 3600, "severity": 1}}
        for i in range(2):
            snap = synthetic(name, base + i * 300)
            snap["evidence"]["results"] = [result, legacy]
            alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
        if "unrecorded PASS" not in alerts:
            raise AssertionError(f"ISC-139 unrecorded PASS did not alert once: {alerts}")
        state = state_read(state_path)
        snap = synthetic(name, base + 10 * 60)
        snap["evidence"]["results"] = [result, legacy]
        alerts = evaluate(snap, state, env, True)
        if "unrecorded PASS" in alerts:
            raise AssertionError(f"unrecorded PASS repeated after reload: {alerts}")
        if not state.get("unrecorded_passes"):
            raise AssertionError("stable unrecorded-PASS dedupe was not persisted")
        print("SIM unrecorded-pass-reload: ISC-139 alerted once; reload stayed silent; old key migrated.")
        print(summary_line(snap, alerts))
        return
    if name in ("off-track", "on-track-timed", "no-promise", "review"):
        state = {}
        steps = 2
        for i in range(steps):
            now = (base + (59 if i == 0 else 60) * 60 if name == "review"
                   else base + i * 60)
            snap = synthetic(name, now)
            if name == "off-track":
                fixture = Path("/fixture/tester-result.md")
                text = ("| ISC | Verdict | Observed | Evidence |\n| --- | --- | --- | --- |\n"
                        "| ISC-064 | PASS | swipe opened the thread | `ISC-064-swipe.png` |\n"
                        "| ISC-067 | FAIL | flick opened nothing | `ISC-067-flick.json` |\n"
                        "| ISC-068 | BLOCKED | not probed after ISC-067 FAIL | `ISC-067-note.txt` |\n")
                mtime = base - 110 * 60
                parsed = parse_result_text(text, mtime)
                pass_rows = [row["id"] for row in parsed["table_rows"] if row["status"] == "PASS"]
                snap["isa"]["latest_verdicts"] = {ident: {"status": "PASS"} for ident in pass_rows}
                snap["isa"]["ledger_mtime"] = now
                promised = sorted({row["id"] for row in parsed["table_rows"]})
                promise = parse_promise(
                    f"PROMISE: kind=screen rows={','.join(promised)} "
                    "result=tester-result.md lane=-"
                )
                promise["result_path"] = str(fixture)
                sess = {"id": "ses-fixture", "agent": "tester", "created": base - 120 * 60,
                        "last_message": base - 30 * 60, "last_assistant": base - 30 * 60, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-fixture", "visible": True,
                        "promise": promise, "promise_read_valid": True,
                        "steers": [base - 90 * 60, base - 60 * 60, base - 30 * 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-fixture": {"id": "thr-fixture", "title": "sample tester"}}
                snap["evidence"]["results"] = [{"path": str(fixture),
                    "name": fixture.name, "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "on-track-timed":
                deadline = (dt.datetime.fromtimestamp(base).astimezone() + dt.timedelta(minutes=30)).strftime("%H:%M")
                mtime = base - 5 * 60
                parsed = parse_result_text(
                    f"| ISC-001 | PASS | observed expected result; evidence timed-result.json |\n"
                    f"PENDING-WAIT ISC-001 until {deadline}\n", mtime)
                promise = parse_promise(
                    "PROMISE: kind=timed rows=001 result=timed-result.md lane=-"
                )
                promise["result_path"] = "/fixture/timed-result.md"
                sess = {"id": "ses-timed", "agent": "tester", "created": base - 10 * 60,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-timed", "visible": True,
                        "promise": promise, "promise_read_valid": True, "steers": [base - 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-timed": {"id": "thr-timed", "title": "timed tester"}}
                snap["evidence"]["results"] = [{"path": "/fixture/timed-result.md",
                    "name": "timed-result.md", "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "no-promise":
                sess = {"id": "ses-no-promise", "agent": "helper", "created": base - 2 * 3600,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-no-promise", "visible": True,
                        "promise": None}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["evidence"]["results"] = [{"path": "/fixture/old-result.md",
                    "name": "old-result.md", "mtime": base - 2 * 3600, "rows": [],
                    "table_rows": [], "verdict_count": 0, "pending_wait": None,
                    "waits": {}, "builder": False}]
            else:
                sess = {"id": "ses-review", "agent": "helper", "created": base - 5 * 60,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-review", "visible": True,
                        "promise": None}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-review": {"id": "thr-review", "title": "review helper"}}
                state.setdefault("review", {"last_at": base, "alerts": {"off track": 2},
                                              "promise_agents": [], "other_agents": []})
            print(f"SIM {name} run {i+1}:")
            alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
            if name == "review" and i == 0 and state.get("review", {}).get("last_sent_at") is not None:
                raise AssertionError("review message sent before 60 minutes")
        if name == "off-track":
            if state.get("conditions", {}).get("off-track:ses-fixture", {}).get("last_alert") != base + 60:
                raise AssertionError("off-track promise did not alert after two checks")
            print("SIM off-track: an old result plus 30 minutes without session activity raised an alert.")
        elif name == "on-track-timed":
            if state.get("conditions", {}).get("off-track:ses-timed", {}).get("streak", 0) != 0:
                raise AssertionError("PENDING-WAIT did not pause the timed promise clock")
            print("SIM on-track-timed: PENDING-WAIT paused the clock; no off-track alert.")
        elif name == "no-promise":
            if any(key.startswith("off-track:") for key in state.get("conditions", {})):
                raise AssertionError("a session without PROMISE received an on-track check")
            print("SIM no-promise: no on-track alert for an unpromised session.")
        else:
            if state.get("review", {}).get("last_sent_at") != base + 60 * 60:
                raise AssertionError("review message did not send exactly once")
            print("SIM review: silent at 59 minutes; one queued review message at 60 minutes.")
        print(summary_line(snap, alerts))
        return
    if name == "fail-under-load":
        cases = (("SIM", 41.0, False), ("REC", 41.0, True), ("REC", 5.0, False))
        last_snapshot = None
        alerts = []
        for tool, load, expected in cases:
            case_state = {"fail_rows_initialized": True}
            for i in range(2):
                now = base + i * 60
                snap = synthetic(name, now)
                snap["host"]["load"] = load
                snap["isa"]["fails"] = [("ISC-123", "sig123", "ISC-123: FAIL - fixture", tool, base)]
                alerts = evaluate(snap, case_state, env, True)
                last_snapshot = snap
            observed = "FAIL under load" in alerts
            if observed != expected:
                raise AssertionError(f"{tool} at load {load} alert mismatch: {alerts}")
            print(f"SIM fail-under-load: {tool} at evidence load {load:.0f} "
                  f"{'alerted' if observed else 'did not alert'} as expected.")
        print(summary_line(last_snapshot, alerts))
        return
    if name == "disk-big-file":
        state = {}
        output = io.StringIO()
        disk_env = dict(env, WATCH_DISK_FREE_GB="10")
        for i, free in enumerate((8.0, 8.0, 4.0, 4.0)):
            snap = synthetic(name, base + i * 60)
            snap["host"]["free_gb"] = free
            with redirect_stdout(output):
                alerts = evaluate(snap, state, disk_env, True)
        disk_lines = [line for line in output.getvalue().splitlines() if "HOST disk:" in line]
        if len(disk_lines) != 2 or "🚦 HOST disk:" in disk_lines[0] or "🚦 HOST disk:" not in disk_lines[1]:
            raise AssertionError(f"disk escalation did not emit normal 8 GB then 🚦 4 GB alerts: {disk_lines}")
        calm_state = {}
        calm_output = io.StringIO()
        for i in range(2):
            calm = synthetic(name, base + 300 + i * 60)
            calm["host"]["free_gb"] = 6.0
            with redirect_stdout(calm_output):
                evaluate(calm, calm_state, disk_env, True)
        calm_line = next((line for line in calm_output.getvalue().splitlines() if "HOST disk:" in line), "")
        if not calm_line or "🚦" in calm_line:
            raise AssertionError(f"6 GB disk alert changed unexpectedly: {calm_line!r}")
        floor_state = {}
        floor_output = io.StringIO()
        for i in range(2):
            floor = synthetic(name, base + 600 + i * 60)
            floor["host"]["free_gb"] = 4.0
            with redirect_stdout(floor_output):
                floor_tags = evaluate(floor, floor_state, dict(env, WATCH_DISK_FREE_GB="3"), True)
            if ("low disk" in floor_tags) != (i == 1):
                raise AssertionError(f"4 GB disk floor did not alert after two checks: {floor_tags}")
        floor_lines = [line for line in floor_output.getvalue().splitlines() if "HOST disk:" in line]
        if len(floor_lines) != 1 or "🚦 HOST disk:" not in floor_lines[0] or "<5 GB" not in floor_lines[0]:
            raise AssertionError(f"4 GB free with WATCH_DISK_FREE_GB=3 did not raise the independent floor alert: {floor_lines}")
        print("SIM disk-big-file: normal 8 GB warning escalated at 4 GB; the <5 GB 🚦 floor also fired with WATCH_DISK_FREE_GB=3; 6 GB stayed unmarked.")
        print(summary_line(snap, alerts))
        return
    if name == "sim-idle-timer":
        state = {}
        checks = ((0, False), (14 * 60, False), (20 * 60, True), (35 * 60, True),
                  (36 * 60, False), (37 * 60, True), (52 * 60, True), (53 * 60, True))
        for i, (elapsed, booted) in enumerate(checks):
            snap = synthetic(name, base + elapsed)
            snap["host"]["booted_sims"] = ["Fixture (Booted)"] if booted else []
            tags = evaluate(snap, state, env, True)
            since = state.get("sim_idle", {}).get("no_agent_since")
            expected_since = base + (20 * 60 if i in (2, 3) else 37 * 60 if i >= 5 else 0) if booted else None
            if since != expected_since:
                raise AssertionError(f"simulator idle timer mismatch at check {i + 1}: {since} != {expected_since}")
            expected_alert = i == len(checks) - 1
            if ("idle simulator" in tags) != expected_alert:
                raise AssertionError(f"simulator idle alert mismatch at check {i + 1}: {tags}")
        print("SIM sim-idle-timer: no simulators accrued no-agent time; booting started a fresh timer; alert needed two checks.")
        print(summary_line(snap, tags))
        return
    if name == "repeat-fail":
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ISA.html"
            rows = "".join(f'<li id="ISC-{i:03d}"><input type="checkbox">{i}</li>'
                           for i in range(1, 5))
            ledger.write_text('<ul>' + rows + '</ul>'
                              '<table id="owner-verification-table"><tr><td>Owner</td><td><a href="#ISC-004">4</a></td></tr></table>'
                              '<section id="verification"><ul>'
                              '<li>ISC-001: FAIL - first</li><li>ISC-001: FAIL - second</li>'
                              '<li>ISC-001: PASS - recovered</li><li>ISC-001: FAIL - one after pass</li>'
                              '<li>ISC-002: FAIL - one</li><li>ISC-002: FAIL - two</li><li>ISC-002: FAIL - three</li>'
                              '<li>ISC-003: FAIL - one</li><li>ISC-003: FAIL - two</li><li>ISC-003: FAIL - three</li>'
                              '<li>ISC-003: BLOCKED - parked</li>'
                              '<li>ISC-004: FAIL - one</li><li>ISC-004: FAIL - two</li><li>ISC-004: FAIL - three</li>'
                              '</ul></section>', encoding="utf-8")
            isa = parse_isa(str(ledger), directory)
        if isa.get("fail_counts", {}).get("ISC-001") != 1:
            raise AssertionError(f"PASS did not reset repeat-fail count: {isa.get('fail_counts')}")
        if "ISC-003" not in isa.get("blocked", []) or "ISC-004" not in isa.get("parked", []):
            raise AssertionError(f"BLOCKED and owner-parked fixtures were not parsed: {isa}")
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            snap["isa"] = isa
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            if ("repeat failure" in tags) != (i == 1):
                raise AssertionError(f"repeat-fail did not honor two-check alerting: {tags}")
        loop_lines = [line for line in output.getvalue().splitlines() if line.startswith("LOOP ISC-")]
        if len(loop_lines) != 1 or not loop_lines[0].startswith("LOOP ISC-002:"):
            raise AssertionError(f"only the eligible 3-FAIL row should raise LOOP: {loop_lines}")
        print("SIM repeat-fail: 2 FAILs, post-PASS FAIL, BLOCKED and owner-parked rows stayed quiet; eligible 3 FAILs alerted.")
        print(summary_line(snap, tags))
        return
    if name == "unclaimed":
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
            if i == 0 and "unclaimed work" in alerts:
                raise AssertionError("unclaimed set alerted on its first check")
            if i == 1 and "unclaimed work" not in alerts:
                raise AssertionError("unclaimed set did not alert on its second check")
        text = output.getvalue()
        if "UNCLAIMED: no live PROMISE claims any of 2 open items (ISC-001, ISC-002); 1 agent(s) running." not in text:
            raise AssertionError(f"unclaimed alert did not list all open rows: {text}")
        open_key = "unclaimed:" + hashlib.sha256(b"ISC-001\nISC-002").hexdigest()[:12]
        if state.get("conditions", {}).get(open_key, {}).get("last_alert") != base + 60:
            raise AssertionError("unclaimed set was not deduplicated by its sorted row set")

        quiet_state = {}
        for i in range(2):
            quiet = synthetic(name, base + i * 60)
            quiet["sessions"]["live"][0]["promise"]["rows"].add("ISC-001")
            quiet_tags = evaluate(quiet, quiet_state, env, True)
            if "unclaimed work" in quiet_tags:
                raise AssertionError(f"one claimed open row did not suppress the alert: {quiet_tags}")

        waiting_state = {}
        for i in range(2):
            existing = synthetic(name, base + i * 60)
            existing["run_card"].update(waiting_text="owner review")
            tags = evaluate(existing, waiting_state, env, True)
            note = waiting_state.get("unclaimed_waiting", {})
            if ("unclaimed work" in tags) != (i == 1) or note.get("fresh"):
                raise AssertionError("an existing waiting line on fresh state silenced UNCLAIMED")

        changed_note = synthetic(name, base + 120)
        changed_note["run_card"].update(waiting_text="waiting for the owner")
        if "unclaimed work" in evaluate(changed_note, waiting_state, env, True):
            raise AssertionError("a newly written waiting line with an unchanged identity did not silence UNCLAIMED")
        if not waiting_state["unclaimed_waiting"].get("fresh"):
            raise AssertionError("observed waiting-line text change was not marked fresh")
        stable_note = synthetic(name, base + 180)
        stable_note["run_card"].update(waiting_text="waiting for the owner")
        if "unclaimed work" in evaluate(stable_note, waiting_state, env, True):
            raise AssertionError("a fresh waiting line did not remain quiet while its identity stayed stable")
        state_write(state_path, waiting_state)
        waiting_state = state_read(state_path)  # watchdog restart preserves the old note identity
        for i in range(2):
            stale_note = synthetic(name, base + 240 + i * 60)
            stale_note["run_card"].update(waiting_text="waiting for the owner")
            stale_note["isa"].update(verdict_count=1,
                                      latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
            stale_note["head"] = "fixture-head-after-another-change"
            tags = evaluate(stale_note, waiting_state, env, True)
            if i == 0 and "unclaimed work" in tags:
                raise AssertionError("old waiting line alerted before its second check after a HEAD change")
            if i == 1 and "unclaimed work" not in tags:
                raise AssertionError("old waiting line stayed quiet after ledger/HEAD identity changed")
        fresh_waiting_state = waiting_state
        for i in range(2):
            fresh = synthetic(name, base + 360 + i * 60)
            fresh["run_card"].update(waiting_text="new owner review")
            fresh["isa"].update(verdict_count=1,
                                latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
            fresh["head"] = "fixture-head-after-another-change"
            tags = evaluate(fresh, fresh_waiting_state, env, True)
            if "unclaimed work" in tags:
                raise AssertionError("new waiting text did not silence UNCLAIMED for the unchanged identity")

        simultaneous_state = {}
        first = synthetic(name, base)
        evaluate(first, simultaneous_state, env, True)
        same_check_change = synthetic(name, base + 60)
        same_check_change["run_card"].update(waiting_text="new note")
        same_check_change["head"] = "fixture-head-changed-with-note"
        same_check_change["isa"].update(verdict_count=1,
                                         latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
        if "unclaimed work" not in evaluate(same_check_change, simultaneous_state, env, True):
            raise AssertionError("waiting text changed with HEAD/ledger and incorrectly silenced UNCLAIMED")

        cycling_state = {}
        for i, rows in enumerate(("ISC-001", "ISC-002", "ISC-001", "ISC-001")):
            cycling = synthetic(name, base + i * 60)
            cycling["isa"].update(criteria=[rows], total=1, parked=[], owner=[], owner_only_ids=[], checked=[])
            cycling["sessions"]["live"][0]["promise"]["rows"].clear()
            tags = evaluate(cycling, cycling_state, env, True)
            if i < 3 and "unclaimed work" in tags:
                raise AssertionError(f"open-set transition reused an earlier streak on step {i + 1}")
            if i == 3 and "unclaimed work" not in tags:
                raise AssertionError("stable open set did not alert on its second consecutive check")
        missing_state = {}
        for i in range(2):
            missing = synthetic(name, base + i * 60)
            missing["sessions"]["valid"] = False
            if "unclaimed work" in evaluate(missing, missing_state, env, True):
                raise AssertionError("unreadable sessions raised an unclaimed alert")
        missing_head_state = {}
        for i in range(2):
            missing_head = synthetic(name, base + i * 60)
            missing_head["run_card"].update(waiting_text="owner review")
            if not i:
                missing_head.update(head=None, head_valid=False)
            if "unclaimed work" in evaluate(missing_head, missing_head_state, env, True):
                raise AssertionError("an unreadable HEAD raised an unclaimed alert")
        if "unclaimed_waiting" not in missing_head_state:
            raise AssertionError("waiting note was not recorded when HEAD identity became readable")
        print("SIM unclaimed: fresh-start notes stayed untrusted; rewritten notes silenced only across unchanged ledger/HEAD identity, while identity changes re-armed alerts.")
        print(summary_line(snap, alerts))
        return
    if name == "regression":
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ISA.html"
            head = ('<ul><li id="ISC-001"><input type="checkbox" checked>Row</li></ul>'
                    '<section id="verification"><ul>')
            state = {}
            output = io.StringIO()
            sequence = []
            for verdict in ("PASS", "FAIL", "PASS", "FAIL"):
                sequence.append(verdict)
                lines = ''.join(f'<li>ISC-001: {value} - step {i}</li>'
                                for i, value in enumerate(sequence, 1))
                ledger.write_text(head + lines + '</ul></section>', encoding="utf-8")
                parsed = parse_isa(str(ledger), directory)
                if parsed.get("verdict_count") != len(sequence):
                    raise AssertionError(f"verdict history count was not parsed: {parsed}")
                if verdict == "FAIL" and parsed.get("done"):
                    raise AssertionError("latest FAIL on a checked criterion was treated as ledger completion")
                checks = 2 if verdict == "FAIL" else 1
                for check in range(checks):
                    snap = synthetic(name, base + len(sequence) * 60 + check)
                    snap["isa"] = parsed
                    snap["run_status"] = "running"
                    with redirect_stdout(output):
                        tags = evaluate(snap, state, env, True)
                    expected_alert = verdict == "FAIL" and check == 1
                    if ("regression" in tags) != expected_alert:
                        raise AssertionError(f"regression episode alert mismatch for {sequence}: {tags}")
            ledger.write_text(
                '<ul><li id="ISC-002"><input type="checkbox">Owner row</li></ul>'
                '<table id="owner-verification-table"><tr><td>Owner</td>'
                '<td><a href="#ISC-002">2</a></td></tr></table>'
                '<section id="verification"><ul><li>ISC-002: FAIL - owner parked</li></ul></section>',
                encoding="utf-8")
            owner_parked = parse_isa(str(ledger), directory)
            if not owner_parked.get("done"):
                raise AssertionError(f"unchecked owner-parked FAIL blocked completion: {owner_parked}")
            ledger.write_text(
                '<ul><li id="ISC-003"><input type="checkbox">Owner-only row</li></ul>'
                '<ul id="owner-only"><li>ISC-003: owner-only</li></ul>'
                '<section id="verification"><ul><li>ISC-003: FAIL - owner-only</li></ul></section>',
                encoding="utf-8")
            owner_only = parse_isa(str(ledger), directory)
            if not owner_only.get("done"):
                raise AssertionError(f"unchecked owner-only FAIL blocked completion: {owner_only}")
        text = output.getvalue()
        regression_lines = [line for line in text.splitlines() if line.startswith("REGRESSION ISC-001:")]
        if len(regression_lines) != 2 or any("Revert the merge that broke it first" not in line
                                              for line in regression_lines):
            raise AssertionError(f"PASS→FAIL→PASS→FAIL did not re-alert with revert-first guidance: {text}")
        print("SIM regression: checked-row FAIL stayed open; unchecked owner-parked/owner-only FAILs did not block completion; PASS re-armed regression alerts.")
        print(summary_line(snap, tags))
        return
    if name == "stall":
        state = {}
        output = io.StringIO()
        seen = {}
        for minute in (0, 5, 10, 15, 20, 25, 30):
            snap = synthetic(name, base + minute * 60)
            snap["run_status"] = "running"
            snap["isa"].update(pass_lines=1, verdict_count=1, tries={"ISC-002": 2})
            with redirect_stdout(output):
                seen[minute] = evaluate(snap, state, env, True)
        text = output.getvalue()
        for step, minute in ((1, 10), (2, 15), (3, 20)):
            if f"STALL {step}/3:" not in text or "stall" not in seen[minute]:
                raise AssertionError(f"stall step {step} did not fire at {minute} min: {seen[minute]}")
        if any("stall" in seen[m] for m in (0, 5, 25, 30)):
            raise AssertionError(f"stall fired outside its 10/15/20 ladder: {seen}")
        if "most-tried open items: ISC-002 (2 tries)" not in text:
            raise AssertionError("stall question did not name the most-tried open item")
        if not re.search(r"UNANSWERED W\d+ \(stall\)", text):
            raise AssertionError("an unacted STALL 1 did not escalate after 10 minutes")
        if "(--mode auto, interrupts now)" not in text:
            raise AssertionError("urgent stall steps did not interrupt")
        if "Answer each alert id under the run card's Answers" not in text:
            raise AssertionError("alert ids were sent without the ANSWER instruction")
        progressed = synthetic(name, base + 35 * 60)
        progressed["run_status"] = "running"
        progressed["isa"].update(pass_lines=2, verdict_count=2)
        evaluate(progressed, state, env, True)
        if state["stall"].get("step") != 0:
            raise AssertionError("a new PASS line did not reset the stall ladder")
        busy_state = {}
        for minute in (0, 10):
            busy = synthetic(name, base + minute * 60)
            busy["run_status"] = "running"
            busy["bb"]["orch_status"] = "active"
            tags = evaluate(busy, busy_state, env, True)
        if "stall" not in tags:
            raise AssertionError("stall ladder skipped a busy orchestrator")
        print("SIM stall: asked at 10, re-asked at 15, said park at 20, stayed quiet after; progress reset it; unacted alert escalated.")
        print(summary_line(progressed, []))
        return
    if name == "agent-switch":
        state = {}
        output = io.StringIO()
        fired = []
        for minute, agent in ((0, "orchestrator"), (5, "build"), (10, "build"), (15, "build")):
            snap = synthetic(name, base + minute * 60)
            snap["sessions"]["orch_agent_first"] = "orchestrator"
            snap["sessions"]["orch_agent"] = agent
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            fired.append("agent switched" in tags)
        if fired != [False, False, True, False]:
            raise AssertionError(f"agent switch should alert once, on the second check: {fired}")
        text = output.getvalue()
        for needle in ("AGENT SWITCH: your session started as orchestrator", "would append user note"):
            if needle not in text:
                raise AssertionError(f"agent-switch output missing {needle!r}: {text}")
        print("SIM agent-switch: a session that started as orchestrator and now runs as build alerted once and left a note.")
        return

    if name == "reanchor":
        state = {}
        output = io.StringIO()
        card = {"valid": True, "status": "running", "waiting_text": None, "goal": "ship the to-do app",
                "owner_rules": ["19:11 keep tasks atomic", "22:03 hill climb fast and honest"],
                "answers": {}, "needs": {}, "plan_valid": False}
        for minute, compacted in ((0, base - 600), (5, base - 600), (10, base + 8 * 60), (15, base + 8 * 60)):
            snap = synthetic(name, base + minute * 60)
            snap["run_card"] = card
            snap["sessions"]["last_compaction"] = compacted
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            if ("re-anchor" in tags) != (minute == 10):
                raise AssertionError(f"re-anchor fired at the wrong check ({minute} min): {tags}")
        text = output.getvalue()
        for needle in ("REANCHOR after your compaction", "Goal: ship the to-do app",
                       "Owner rules, word for word: 19:11 keep tasks atomic | 22:03 hill climb fast and honest",
                       "re-read HOW-TO-WORK.md"):
            if needle not in text:
                raise AssertionError(f"re-anchor message missing {needle!r}: {text}")
        fresh = {}
        for minute, compacted in ((0, None), (5, base + 3 * 60)):
            snap = synthetic(name, base + minute * 60)
            snap["run_card"] = card
            snap["sessions"]["last_compaction"] = compacted
            with redirect_stdout(io.StringIO()):
                tags = evaluate(snap, fresh, env, True)
        if "re-anchor" not in tags:
            raise AssertionError("the first compaction of a run that started with none did not re-anchor")
        print("SIM reanchor: an old compaction was a baseline; a new one sent goal, open items and owner rules once.")
        return
    if name == "plan-map":
        state = {}
        output = io.StringIO()
        card = {"valid": True, "status": "running", "waiting_text": None, "goal": "ship it", "owner_rules": [],
                "answers": {}, "needs": {}, "plan_valid": True}
        tags_seen = []
        for minute in (0, 5, 10):
            snap = synthetic(name, base + minute * 60)
            snap["run_status"] = "running"
            open_ids = [i for i in snap["isa"].get("criteria", [])
                        if i not in {normalize_ident(c) for c in snap["isa"].get("checked", [])}]
            if len(open_ids) < 2:
                raise AssertionError(f"plan-map sim needs two open items: {open_ids}")
            first, second = open_ids[0], open_ids[1]
            card["needs"] = ({first: {second}, second: {first}} if minute < 10 else
                             {i: set() for i in open_ids})
            snap["run_card"] = card
            with redirect_stdout(output):
                tags_seen.append(evaluate(snap, state, env, True))
        text = output.getvalue()
        if "plan map out of date" not in tags_seen[1] or "needs loop:" not in text:
            raise AssertionError(f"a needs loop did not raise PLAN on the second check: {tags_seen} {text}")
        if "plan map out of date" in tags_seen[0] or "plan map out of date" in tags_seen[2]:
            raise AssertionError(f"PLAN fired on the first check or after the map was fixed: {tags_seen}")
        print("SIM plan-map: a needs loop raised PLAN once on the second check; a fixed map stayed quiet.")
        return
    if name == "regression-order":
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ISA.html"
            head = ('<ul><li id="ISC-001"><input type="checkbox" checked>Row</li></ul>'
                    '<section id="verification"><ul>')
            state = {}
            tags_seen = []
            for lines in ('<li>ISC-001: FAIL - old probe</li>',
                          '<li>ISC-001: PASS - fixed</li><li>ISC-001: FAIL - old probe</li>',
                          '<li>ISC-001: PASS - fixed</li><li>ISC-001: FAIL - old probe</li>'):
                ledger.write_text(head + lines + '</ul></section>', encoding="utf-8")
                snap = synthetic(name, base + len(tags_seen) * 300)
                snap["isa"] = parse_isa(str(ledger), directory)
                snap["run_status"] = "running"
                with redirect_stdout(io.StringIO()):
                    tags_seen.append(evaluate(snap, state, env, True))
            if any("regression" in tags for tags in tags_seen):
                raise AssertionError(f"a PASS inserted above an old FAIL line raised REGRESSION: {tags_seen}")
        print("SIM regression-order: an old FAIL line left below a new PASS stayed quiet.")
        return
    if name == "leftover-session":
        state = {}
        output = io.StringIO()
        statuses = ("failed", "active", "failed", "failed", "failed", "active", "failed", "failed")
        expected_alerts = {3, 7}
        for i, status in enumerate(statuses):
            snap = synthetic(name, base + i * 60)
            snap["bb"]["by_id"]["thr-ended"]["status"] = status
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            if ("leftover session" in tags) != (i in expected_alerts):
                raise AssertionError(f"leftover failed/healthy sequence mis-alerted at {status} step {i + 1}: {tags}")
            if i == 0:
                suppressed = ("OFF TRACK", "AGENT builder (ses-leftover)", "AGENT builder session ses-leftover",
                              "BRIEF builder ses-leftover", "GHOST BB child thr-ended")
                if any(marker in output.getvalue() for marker in suppressed):
                    raise AssertionError(f"stale session raised additional alerts before recovery: {output.getvalue()}")
            if status == "active":
                rec = state.get("conditions", {}).get("leftover-session:ses-leftover", {})
                if rec.get("streak") != 0 or rec.get("last_alert"):
                    raise AssertionError(f"healthy session did not clear its LEFTOVER episode: {rec}")
        text = output.getvalue()
        leftover_lines = [line for line in text.splitlines() if line.startswith("LEFTOVER session ses-leftover")]
        if len(leftover_lines) != 2 or any("interrupt it before relaunching" not in line for line in leftover_lines):
            raise AssertionError(f"two separate stale-session episodes should each produce one LEFTOVER line: {leftover_lines}")
        if f"would queue to {env['ORCH_THREAD']}:" not in output.getvalue():
            raise AssertionError("leftover alert was not addressed to the orchestrator thread")

        stale_state = {"orphan_idle": {"no_agent_since": base - 16 * 60}}
        stale_tags = []
        for i in range(2):
            stale = synthetic(name, base + i * 60)
            stale["run_status"] = "running"
            stale["isa"].update(total=1, criteria=["ISC-001"], checked=[], owner=[], parked=[],
                                owner_only_ids=[], latest_verdicts={})
            stale["host"]["processes"] = [{"pid": 321, "ppid": 1, "age": 1200,
                                           "command": "recordVideo /fixture/orphan.mp4", "orphan": True}]
            stale["sessions"]["live"][0]["promise"]["rows"] = {"ISC-001"}
            stale["run_card"]["status"] = "running"
            stale_tags = evaluate(stale, stale_state, env, True)
            if stale["sessions"]["live"]:
                raise AssertionError("ended BB session remained an effective live claim")
        if not {"unclaimed work", "orphan process", "leftover session"}.issubset(stale_tags):
            raise AssertionError(f"ended helper suppressed unclaimed/orphan checks: {stale_tags}")
        print("SIM leftover-session: healthy checks reset LEFTOVER; failed/failed alerted once, and a recovered session re-armed it.")
        print(summary_line(snap, tags))
        return
    if name == "idle-helper":
        state = {"conditions": {"off-track:ses-idle": {"streak": 1, "last_alert": 0, "severity": 0}}}
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            tags = evaluate(snap, state, env, True)
            if "off track" in tags or "ghost agent" in tags:
                raise AssertionError(f"finished helper was treated as active: {tags}")
        if state["conditions"]["off-track:ses-idle"].get("streak") != 0:
            raise AssertionError("idle helper did not clear its off-track streak")
        print("SIM idle-helper: finished OpenCode helper cleared off-track and BB ghost alerts.")
        print(summary_line(snap, tags))
        return
    if name == "reopen":
        state = {"done": True, "pause_result": "paused old run", "closed_pause_recorded": True,
                 "closed_automation_id": "auto-old", "delete_result": "deleted old", "automation_deleted": True}
        output = io.StringIO()
        snap = synthetic(name, base)
        with redirect_stdout(output):
            tags = evaluate(snap, state, dict(env, AUTOMATION_ID="auto-fixture", PROJECT_ID="fixture"), True)
        stale = {"done", "pause_result", "closed_pause_recorded", "closed_automation_id",
                 "delete_result", "automation_deleted"} & state.keys()
        if stale or "would run bb automation pause" in output.getvalue() or state.get("done"):
            raise AssertionError(f"reopened running run retained stale pause state: {stale}, {output.getvalue()}")
        print("SIM reopen: running card plus incomplete ledger cleared stale done/pause state without pausing.")
        print(summary_line(snap, tags))
        return
    steps = 2
    if name == "server-down":
        steps = 4
    elif name == "anti-spin":
        steps = 4
    elif name == "done":
        steps = 2
    elif name == "read-failure":
        steps = 2
        conditions = state.setdefault("conditions", {})
        for key in ("high-load", "low-disk", "invisible-agent:ses-fixture", "ghost-agent:thr-fixture",
                    "stuck-builder-log:/fixture/build.log", "stuck-agent:/fixture/worker-result.md",
                    "unrecorded-pass:/fixture/worker-result.md:ISC-123"):
            conditions[key] = {"streak": 1, "last_alert": 0, "severity": 0}
        state["server"] = {"down_streak": 1, "last_reload": 0}
    elif name == "working-old-bb":
        steps = 2
    elif name == "resumed-idle-agent":
        steps = 2
        state.setdefault("conditions", {})["invisible-agent:ses-resumed"] = {
            "streak": 0, "last_alert": 0, "severity": 0}
    for i in range(steps):
        now = base + i * 900
        snap = synthetic(name, now)
        alerts = []
        if name == "anti-spin" and i > 0:
            snap["now"] = now
        print(f"SIM {name} run {i+1}:")
        if state.get("done"):
            print("WATCH: done=true; future run exits without another message.")
            continue
        if name == "server-down":
            # Simulated server stays down; the real reload command is never invoked.
            pass
        alerts = evaluate(snap, state, env, True)
        if name == "read-failure":
            conditions = state.get("conditions", {})
            keys = ("high-load", "low-disk", "invisible-agent:ses-fixture", "ghost-agent:thr-fixture",
                    "stuck-builder-log:/fixture/build.log", "stuck-agent:/fixture/worker-result.md",
                    "unrecorded-pass:/fixture/worker-result.md:ISC-123")
            if any(conditions.get(key, {}).get("streak") != 1 for key in keys):
                raise AssertionError("a failed read changed an affected alert streak")
            if state.get("server", {}).get("down_streak") != 1:
                raise AssertionError("an OpenCode read failure advanced its recovery streak")
            print("SIM read-failure: no alert; affected host/BB/session streaks remain 1/2.")
        if name == "working-old-bb":
            streak = state.get("conditions", {}).get("ghost-agent:thr-fixture", {}).get("streak", 0)
            if streak != 0:
                raise AssertionError(f"working bound session was treated as ghost: streak={streak}")
            print("SIM working-old-bb: no ghost alert; bound session message is recent.")
        if name == "resumed-idle-agent":
            rec = state.get("conditions", {}).get("invisible-agent:ses-resumed", {})
            expected_streak = i + 1
            expected_alert = now if i == 1 else 0
            if rec.get("streak") != expected_streak or rec.get("last_alert") != expected_alert:
                raise AssertionError(f"resumed idle thread alert mismatch: {rec}")
            if i == 1:
                print("SIM resumed-idle-agent: invisible-agent alert fires on the second run.")
        if name == "ghost-agent-no-message" and i == 1:
            streak = state.get("conditions", {}).get("ghost-agent:thr-fixture", {}).get("streak", 0)
            if streak != 2 or "ghost agent" not in alerts:
                raise AssertionError(f"missing-message bound session did not raise the ghost alert: {alerts}")
            print("SIM ghost-agent-no-message: bound session without a message raised the ghost alert.")
        if name == "orphan-recorder" and i == 1:
            if "orphan process" not in alerts:
                raise AssertionError(f"orphan process did not alert after two no-agent checks: {alerts}")
            print("SIM orphan-recorder: orphan process alerted after two checks with no agent for 15 minutes.")
        if name == "orphan-recorder-active" and i == 1:
            records = [state.get("conditions", {}).get(f"orphan-process:{pid}", {}) for pid in (123, 124, 125)]
            if "orphan process" in alerts or any(record.get("streak") != 0 for record in records):
                raise AssertionError(f"active tester's recorder/simctl/log process raised an alert: {alerts}, {records}")
            print("SIM orphan-recorder-active: active tester's orphan recorder stayed quiet.")
        state_write(state_path, state)
    if name == "anti-spin" and state.get("continue", {}).get("stopped"):
        print("SIM: anti-spin stopped after three unchanged checks.")
    if name == "stuck-agent" and any(key.startswith("stuck-agent:") for key in state.get("conditions", {})):
        raise AssertionError("an old result file without a live session raised a stuck-agent alert")
    if name == "stuck-agent":
        print("SIM stuck-agent: finished-agent result file raised no no-progress alert.")
    print(summary_line(snap, alerts))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print queued messages instead of sending them")
    parser.add_argument("--once-report", action="store_true", help="print one read-only health summary")
    parser.add_argument("--find-session", action="store_true",
                        help="print the newest top-level OpenCode session for REPO (the orchestrator's ORCH_SESSION)")
    parser.add_argument("--simulate", choices=("stuck-agent", "ghost-agent", "ghost-agent-no-message", "invisible-agent", "high-load",
        "disk-big-file", "orphan-recorder", "orphan-recorder-active", "fail-under-load", "unrecorded-pass", "unrecorded-pass-reload",
        "superseded-pass", "server-down", "combined-alerts", "continue",
        "anti-spin", "done", "closed-delete", "not-closed", "read-failure", "working-old-bb", "resumed-idle-agent",
        "off-track", "on-track-timed", "on-track-code", "fast-jules", "new-testers-old-results",
        "no-promise", "review", "lane-drift", "alert-once", "repeat-fail", "unclaimed", "stall", "reanchor", "agent-switch", "plan-map", "regression-order", "sim-idle-timer",
        "regression", "leftover-session", "idle-helper", "reopen"),
        help="run a deterministic offline scenario; always dry-run")
    args = parser.parse_args()
    env = dict(os.environ)
    root = env.get("REPO", "")
    if not root:
        print("REPO is required", file=sys.stderr)
        return 2
    state_path = env.get("STATE_FILE") or os.path.join(root, ".lanes", "watch-state.json")
    if args.simulate:
        env.setdefault("ORCH_THREAD", "fixture-thread")
        simulate(args.simulate, state_path, env)
        return 0
    if args.once_report:
        print(report(collect(env)))
        return 0
    if args.find_session:
        db = os.path.expanduser("~/.local/share/opencode/opencode.db")
        try:
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3) as conn:
                rows = conn.execute(
                    "select id, agent, title from session_v2 where parent_id is null and directory = ? "
                    "order by time_updated desc limit 5", (os.path.realpath(root),)).fetchall()
        except sqlite3.Error as exc:
            print(f"OpenCode database read failed: {exc}", file=sys.stderr)
            return 1
        for row in rows:
            print("\t".join(str(value) for value in row))
        return 0 if rows else 1
    if not env.get("ORCH_THREAD") or not env.get("ORCH_SESSION") or not env.get("VERIFY_DIR"):
        print("ORCH_THREAD, ORCH_SESSION, and VERIFY_DIR are required", file=sys.stderr)
        return 2
    state = state_read(state_path)
    if state.get("done"):
        run_status = read_run_status(env.get("RUN_CARD") or os.path.join(root, ".hivecall", "run.md"))
        if run_status == "running":
            isa = parse_isa(env.get("LEDGER") or env.get("ISA") or os.path.join(root, "_ai/docs/ISA.html"), root)
            if not isa.get("error") and not isa.get("done"):
                clear_done_state(state)
        if state.get("done") and run_status == "closed":
            finish_closed_run(state, env, args.dry_run)
        elif state.get("done"):
            # Ledger-only completion retries pause until the run card is closed.
            state.pop("closed_pause_recorded", None)
            state.pop("closed_automation_id", None)
            state.pop("delete_result", None)
            state["pause_result"] = pause_automation(env, args.dry_run)
        if state.get("done"):
            state_write(state_path, state)
            print(f"WATCH: run already done; {state.get('delete_result') or state.get('pause_result', 'automation lifecycle complete')}.")
            print(summary_line({}, []))
            return 0
    snapshot = collect(env)
    alerts = evaluate(snapshot, state, env, args.dry_run)
    state_write(state_path, state)
    print(summary_line(snapshot, alerts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
