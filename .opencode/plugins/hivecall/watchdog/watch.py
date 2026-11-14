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
from hivewatch.collect import collect, report, status_table, summary_line
from hivewatch.evaluate import evaluate


from hivewatch.sim.simulate import simulate, synthetic


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
