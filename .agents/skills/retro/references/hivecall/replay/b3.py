#!/usr/bin/env python3
"""Re-anchor behavior-3 replay moments at the orchestrator's pre-gap turn end."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
HIVECALL = ROOT / ".agents/skills/retro/references/hivecall"
DATASET = HIVECALL / "evals/dataset.jsonl"
REDACTOR = HIVECALL / "scripts/redact.py"
GAP_MS = 30 * 60 * 1000


def dataset_builder():
    scripts = HIVECALL / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / "build-dataset.py"
    spec = importlib.util.spec_from_file_location("hivecall_dataset_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_events(run_id):
    result = subprocess.run(
        ["bb", "thread", "log", run_id, "--json", "--all"],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError("could not read an archived hivecall trace")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("archived hivecall trace was not valid JSON") from None


def redact_excerpt(text):
    result = subprocess.run(
        [sys.executable, str(REDACTOR)], input=str(text), capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError("shared redactor failed for a B3 excerpt")
    return result.stdout.removesuffix("\n")


def is_activity(event):
    item = (event.get("data") or {}).get("item") or {}
    return event.get("type") == "client/turn/requested" or (
        event.get("type") == "item/completed"
        and item.get("type") in ("agentMessage", "toolCall", "commandExecution", "delegation")
    )


def active_worker_counts(events):
    builder = dataset_builder()
    active = set()
    unknown = 0
    counts = []
    spawned_commands = set()
    for event in events:
        item = (event.get("data") or {}).get("item") or {}
        item_id = item.get("id")
        if event.get("type") == "item/started" and builder.is_delegation_action(event):
            if item_id:
                active.add(item_id)
                if item.get("type") == "commandExecution":
                    # A spawn command's process can finish while its child remains live.
                    spawned_commands.add(item_id)
            else:
                unknown += 1
        elif event.get("type") in ("item/completed", "item/delegation/completed") and item_id:
            if item_id not in spawned_commands:
                active.discard(item_id)
        counts.append(len(active) + unknown)
    return counts


def reanchor_events(run_id, week, events, invoked_at):
    builder = dataset_builder()
    events = sorted(
        (event for event in events if (event.get("createdAt") or 0) >= invoked_at),
        key=lambda event: (event.get("createdAt") or 0, event.get("seq") or 0),
    )
    counts = active_worker_counts(events)
    activities = [(index, event) for index, event in enumerate(events) if is_activity(event)]
    totals = {"longGaps": 0, "turnEnds": 0, "openWork": 0,
              "zeroWorkerMoments": 0, "liveWorkerMoments": 0}
    moments = []
    for (before_index, before), (after_index, after) in zip(activities, activities[1:]):
        gap_ms = (after.get("createdAt") or 0) - (before.get("createdAt") or 0)
        if gap_ms <= GAP_MS:
            continue
        totals["longGaps"] += 1
        before_item = (before.get("data") or {}).get("item") or {}
        if before.get("type") != "item/completed" or before_item.get("type") != "agentMessage":
            continue
        if not any(event.get("type") == "turn/completed"
                   for event in events[before_index + 1:after_index]):
            continue
        totals["turnEnds"] += 1
        prior = "\n".join(builder.event_text(event)
                           for event in events[max(0, before_index - 90):before_index])
        state = builder.open_state(prior)
        if state != "open":
            continue
        totals["openWork"] += 1
        live_workers = counts[before_index]
        context = redact_excerpt(builder.context(events, before_index))
        action = builder.action(before)
        action["text"] = redact_excerpt(action.get("text", ""))
        if live_workers == 0:
            totals["zeroWorkerMoments"] += 1
            expected = "progress_or_owner_wait"
        else:
            totals["liveWorkerMoments"] += 1
            expected = "wait_for_worker"
        check = {
            "rule": "pre-gap orchestrator turn ended with open work",
            "anchor": "before-final-orchestrator-message",
            "gapMinutes": round(gap_ms / 60000, 2),
            "label": "open",
            "liveWorkerCount": live_workers,
            "expectedNextAction": expected,
        }
        moment = builder.moment(
            run_id, week, 3, before, context, action, check,
            trigger_event_id=after.get("id"),
        )
        moment["replayAnchor"] = "b3_pre_final_message"
        moment["replayControl"] = "zero_worker_progress" if live_workers == 0 else "live_worker_wait"
        moments.append(moment)
    return moments, totals


def reanchor_records(records, excluded_ids=(), event_loader=load_events):
    runs = {}
    for record in records:
        if record.get("recordType") not in ("run", "runUpdate"):
            continue
        run_id = record.get("runId")
        if not run_id or run_id in excluded_ids:
            continue
        run = runs.setdefault(run_id, {"week": record.get("week"), "invokedAt": record.get("invokedAt")})
        run["week"] = record.get("week") or run["week"]
        run["invokedAt"] = record.get("invokedAt") or run["invokedAt"]
    moments, totals = [], {"longGaps": 0, "turnEnds": 0, "openWork": 0,
                           "zeroWorkerMoments": 0, "liveWorkerMoments": 0}
    for run_id, run in runs.items():
        if not isinstance(run.get("invokedAt"), (int, float)):
            raise RuntimeError("dataset record lacks an invocation timestamp")
        rows, counts = reanchor_events(run_id, run["week"], event_loader(run_id), run["invokedAt"])
        moments.extend(rows)
        for key in totals:
            totals[key] += counts[key]
    return moments, totals, len(runs)


def read_records(path):
    records = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            raise ValueError(f"invalid JSONL at line {line_no}") from None
    return records


def audit(args):
    if args.archive_only:
        if args.exclude_run_id:
            raise SystemExit("do not combine --archive-only with --exclude-run-id")
    elif len(args.exclude_run_id) != len(set(args.exclude_run_id)):
        raise SystemExit("do not repeat --exclude-run-id values")
    moments, totals, runs = reanchor_records(read_records(args.dataset), args.exclude_run_id)
    report = HERE / "reports/b3-anchor-audit.md"
    moment_file = HERE / "reports/b3-turn-end-moments.jsonl"
    report.parent.mkdir(parents=True, exist_ok=True)
    moment_file.write_text("".join(json.dumps(moment, ensure_ascii=False) + "\n"
                                     for moment in moments), encoding="utf-8")
    lines = [
        "# Behavior 3 turn-end anchor audit", "",
        "**Status: PRECHECK; local archived-log inspection only, no model calls.**", "",
        f"- Archived run records inspected: {runs}.",
        f"- Long gaps over 30 minutes: {totals['longGaps']}.",
        f"- Orchestrator turn ends before long gaps: {totals['turnEnds']}.",
        f"- Turn ends with open work: {totals['openWork']}.",
        f"- Zero-live-worker moments: {totals['zeroWorkerMoments']}.",
        f"- Live-worker wait moments: {totals['liveWorkerMoments']}.",
        f"- Total retained B3 moments: {len(moments)}; both classes count toward the 10-moment replay floor.",
        f"- Failure-side zero-worker moments: {totals['zeroWorkerMoments']}; live-worker wait moments: {totals['liveWorkerMoments']}.",
        f"- Redacted context/action excerpts: `{moment_file.relative_to(ROOT)}`.",
        "- Replay contexts end before the final orchestrator message; evaluator-only gap and worker counts are not included in model prompts.",
        "- Unresolved delegations, unknown worker starts, and spawn commands count as live.",
        "- Zero-worker moments test whether the next action keeps work moving; live-worker moments test whether it correctly waits.",
        "",
    ]
    if len(moments) < 10:
        lines.insert(-1, f"- B3 replay incomplete: total retained moments have only {len(moments)}; required 10. Do not loosen the anchor.")
    elif totals["zeroWorkerMoments"] < 10:
        count = totals["zeroWorkerMoments"]
        noun = "moment" if count == 1 else "moments"
        verb = "is" if count == 1 else "are"
        lines.insert(-1, f"- B3 replay floor met. Only {count} zero-worker {noun} {verb} failure-side; B3 power is low.")
    lines.insert(-1, "- Extraction is currently local to replay; move it into `scripts/build-dataset.py` after the method is accepted.")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


def self_check():
    builder = dataset_builder()
    ms = 31 * 60 * 1000
    events = [
        {"id": "u", "type": "client/turn/requested", "createdAt": 1,
         "data": {"input": [{"text": "- in progress: open task"}]}},
        {"id": "a", "type": "item/completed", "createdAt": 2,
         "data": {"item": {"id": "a", "type": "agentMessage", "status": "completed", "text": "I will wait."}}},
        {"id": "t", "type": "turn/completed", "createdAt": 3, "data": {}},
        {"id": "u2", "type": "client/turn/requested", "createdAt": ms,
         "data": {"input": [{"text": "continue"}]}},
    ]
    moments, counts = reanchor_events("run", "2026-W42", events, 0)
    assert counts == {"longGaps": 1, "turnEnds": 1, "openWork": 1,
                      "zeroWorkerMoments": 1, "liveWorkerMoments": 0}
    assert len(moments) == 1 and moments[0]["actualNextAction"]["eventId"] == "a"
    assert moments[0]["fixedCheck"]["expectedNextAction"] == "progress_or_owner_wait"
    assert moments[0]["context"].endswith("- in progress: open task")
    assert moments[0]["replayAnchor"] == "b3_pre_final_message"
    with_worker = [events[0],
                   {"id": "w", "type": "item/started", "createdAt": 2,
                    "data": {"item": {"id": "w", "type": "delegation"}}},
                   *events[1:]]
    moments, counts = reanchor_events("run", "2026-W42", with_worker, 0)
    assert len(moments) == 1 and counts["liveWorkerMoments"] == 1
    assert moments[0]["fixedCheck"]["expectedNextAction"] == "wait_for_worker"
    short_gap = [dict(event) for event in events]
    short_gap[-1] = {**short_gap[-1], "createdAt": 30 * 60 * 1000 + 2}
    moments, counts = reanchor_events("run", "2026-W42", short_gap, 0)
    assert not moments and counts["longGaps"] == 0
    safe = redact_excerpt("Fixture Person contact@example.invalid /Users/fixture/project")
    assert "contact@example.invalid" not in safe and "/Users/fixture/project" not in safe
    print("PRECHECK: B3 pre-turn anchor and live-worker filter passed")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-check")
    run = sub.add_parser("audit")
    run.add_argument("--dataset", default=str(DATASET))
    run.add_argument("--exclude-run-id", action="append", default=[])
    run.add_argument("--archive-only", action="store_true")
    args = parser.parse_args()
    if args.command == "self-check":
        self_check()
    else:
        audit(args)


if __name__ == "__main__":
    main()
