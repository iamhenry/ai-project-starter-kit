from __future__ import annotations

import datetime as dt
import hashlib
import io
import os
import re
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

from hivewatch.collect import summary_line
from hivewatch.evaluate import evaluate
from hivewatch.ledger import parse_isa, parse_result_text
from hivewatch.probes import load_lane_facts
from hivewatch.promise import normalize_ident, parse_promise, promise_metrics
from hivewatch.shell import state_read, state_write


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


