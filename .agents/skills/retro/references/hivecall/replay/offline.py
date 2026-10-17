#!/usr/bin/env python3
"""Offline, rule-only baseline for archived traces; never makes requests."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as replay  # noqa: E402
import b3 as b3_replay  # noqa: E402


def forbid_network(*_args, **_kwargs):
    raise RuntimeError("offline runner forbids network requests")


urllib.request.urlopen = forbid_network


def source_event_type(moment):
    action = moment.get("actualNextAction") or {}
    return (moment.get("sourceEventType") or moment.get("source_event_type")
            or moment.get("eventType") or moment.get("event_type")
            or action.get("sourceEventType") or action.get("eventType")
            or action.get("event_type"))


def filter_reviewed_runs(records, excluded_ids):
    kept_records = [r for r in records if r.get("runId") not in excluded_ids]
    raw_moments = replay.all_moments(kept_records)
    raw_counts = {b: sum(m.get("behavior") == b for m in raw_moments) for b in range(1, 8)}
    kept, filtered = [], {"liveRunMoments": 0, "completionMoments": 0, "untypedDelegationMoments": 0}
    excluded_runs = {r.get("runId") for r in records if r.get("runId") in excluded_ids}
    filtered["liveRunMoments"] = sum(
        len(r.get("moments", [])) for r in records if r.get("runId") in excluded_runs)
    for moment in raw_moments:
        if moment.get("behavior") in (4, 6):
            event_type = source_event_type(moment)
            action = moment.get("actualNextAction") or {}
            if (event_type and "completed" in event_type) or action.get("status") in ("completed", "done"):
                filtered["completionMoments"] += 1
                continue
            if event_type != "item/started" or action.get("status") != "pending":
                filtered["untypedDelegationMoments"] += 1
                continue
        kept.append(moment)
    return kept_records, kept, filtered, len(excluded_runs), raw_counts


def offline_labels(moment, behavior):
    rule = replay.rule_label(moment, behavior)
    return rule if rule in ("PASS", "FAIL") else "FAIL"


def eligible_baseline_moments(moments):
    return [m for m in moments
            if m.get("behavior") not in (4, 6) and replay.baseline_moment(m)]


def run(args):
    if args.archive_only:
        if args.exclude_run_id:
            raise SystemExit("do not combine --archive-only with --exclude-run-id")
    else:
        replay.validate_excluded_runs(args.exclude_run_id)
    records = replay.read_records(args.dataset)
    filtered_records, moments, filtered, excluded_run_count, raw_counts = filter_reviewed_runs(
        records, set(args.exclude_run_id))
    try:
        b3_moments, b3_totals, inspected_runs = b3_replay.reanchor_records(
            filtered_records, args.exclude_run_id)
        b3_by_week = {week: sum(m.get("week") == week for m in b3_moments)
                      for week in sorted({m.get("week") for m in b3_moments})}
    except (OSError, RuntimeError, ValueError) as exc:
        b3_moments, b3_totals, inspected_runs, b3_by_week = [], None, 0, {}
        b3_error = str(exc)
    else:
        b3_error = None
    b3_failure_count = b3_totals["zeroWorkerMoments"] if b3_totals is not None else 0
    b3_failure_verb = "is" if b3_failure_count == 1 else "are"
    b3_failure_noun = "moment" if b3_failure_count == 1 else "moments"
    baseline_moments = eligible_baseline_moments(moments)
    sampled, totals = replay.select_sample(baseline_moments, args.per_behavior, args.seed)
    all_counts = {b: sum(m.get("behavior") == b for m in moments) for b in range(1, 8)}
    scorecard = {}
    for behavior in range(1, 8):
        bucket = [m for m in sampled if m.get("behavior") == behavior]
        if behavior in (4, 6):
            scorecard[str(behavior)] = {"score": None, "trust": "not-measured", "moments": 0,
                                        "pass": 0, "fail": 0, "unknown": raw_counts[behavior]}
            continue
        if behavior == 7 or not bucket:
            scorecard[str(behavior)] = {"score": None, "trust": "not-measured", "moments": 0,
                                        "pass": 0, "fail": 0, "unknown": 0}
            continue
        labels = [offline_labels(m, behavior) for m in bucket]
        passed = labels.count("PASS")
        failed = len(labels) - passed
        scorecard[str(behavior)] = {"score": round(100 * passed / len(labels)),
                                    "trust": "not-trusted", "moments": len(labels),
                                    "pass": passed, "fail": failed,
                                    "unknown": sum(replay.rule_label(m, behavior) is None for m in bucket)}

    incomplete = [f"baseline incomplete: behavior {b} has only {totals[b]} replayable moments"
                  for b in (1, 2, 3) if totals[b] < 10]
    report = HERE / "reports/offline-baseline.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Hivecall offline rule-only baseline", "",
             "**Status: PRECHECK only; this is not the Clef-labeled ISC-5 baseline.**", "",
             f"- Sample: up to {args.per_behavior} per behavior; seed {args.seed}.",
             "- Cloud calls: none. No dataset context or action text was sent outside this machine.",
              (f"- Source mode: archive-only dataset contract; {len(filtered_records)} archived run records remain."
               if args.archive_only else
               f"- Named live-run exclusions: {excluded_run_count} of {len(args.exclude_run_id)} were present in the current source file; {filtered['liveRunMoments']} moments removed; {len(filtered_records)} run records remain."),
               "- Planned tested agent for any later replay: OpenCode `plan` (`anthropic/claude-opus-5-5`); the `reviewer` judge is GPT-family.",
              f"- B4/B6 completions excluded: {filtered['completionMoments']}; source event type is present and {filtered['untypedDelegationMoments']} events were untyped or not pending starts.",
              "- B3 baseline eligibility uses evaluator-only `fixedCheck.gapMinutes` (at least 30); that metadata is not sent to a tested model.",
              "- Scores are rule-only lower bounds: rule-undecidable actions count as failures. Numeric scores are `not-trusted` because Clef/judge review was not run.",
               "- Behaviors 4 and 6 are intentionally unscored in this local rule-only lower-bound report; use the Clef baseline for them.",
                (f"- B3 local replay-anchor audit: {len(b3_moments)} qualifying moments from {inspected_runs} archived runs; "
                 f"{b3_totals['longGaps']} long gaps, {b3_totals['turnEnds']} turn ends, "
                  f"{b3_totals['openWork']} with open work; zero-worker count {b3_totals['zeroWorkerMoments']}, "
                  f"live-worker count {b3_totals['liveWorkerMoments']}; "
                 f"by week: {json.dumps(b3_by_week, sort_keys=True)}."
                 if b3_totals is not None else f"- B3 local replay-anchor audit unavailable: {b3_error}."),
               (f"- B3 replay incomplete: total turn-end moments are {len(b3_moments)}; required 10."
                 if b3_totals is not None and len(b3_moments) < 10 else
                  (f"- B3 replay count floor met: {len(b3_moments)} total moments. Only {b3_failure_count} zero-worker {b3_failure_noun} {b3_failure_verb} failure-side; B3 power is low."
                  if b3_totals is not None and b3_totals["zeroWorkerMoments"] < 10 else "")),
              f"- The archive-only source has {raw_counts[3]} stored B3 trace gaps across {len(filtered_records)} runs; two live runs are excluded by owner direction.",
              "- This aggregate report omits trace/event IDs and action text; redacted excerpts are stored separately in the B3 audit artifact.",
             "- The source dataset does not preserve owner speaker attribution, so tier-1 labels remain unavailable.",
              "", "| Behavior | Rule-only lower bound | Sample / baseline / raw | Pass / fail / unknown | Trust |",
             "|---|---:|---:|---:|---|"]
    for behavior in range(1, 8):
        entry = scorecard[str(behavior)]
        score = "not measured" if entry["score"] is None else f"{entry['score']}%"
        lines.append(f"| {behavior}. {replay.BEHAVIORS[behavior]} | {score} | {entry['moments']} / {totals[behavior]} / {raw_counts[behavior]} | {entry['pass']} / {entry['fail']} / {entry['unknown']} | {entry['trust']} |")
    lines += ["", "## Behavior 7 run-level facts", "", "```json",
              json.dumps(replay.behavior7_summary(filtered_records), indent=2), "```", "",
              "## ISC-5 baseline count gate", ""]
    lines += [f"- {reason}" for reason in incomplete] if incomplete else [
        (f"- Behaviors 1–3 each have at least 10 trace-baseline moments. B3 turn-end count floor is {len(b3_moments)} total (10 required). Only {b3_failure_count} zero-worker {b3_failure_noun} {b3_failure_verb} failure-side; power is low."
         if b3_totals is not None and len(b3_moments) >= 10 else
         "- Behaviors 1–3 each have at least 10 trace-baseline moments; this does not clear the separate B3 replay gate.")]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


def self_check():
    records = [{"recordType": "run", "runId": "keep", "week": "2026-W42", "moments": [
        {"eventId": "start", "behavior": 4, "actualNextAction": {"eventType": "item/started", "status": "pending"}},
        {"eventId": "done", "behavior": 6, "actualNextAction": {"eventType": "item/completed"}},
        {"eventId": "unknown", "behavior": 4, "actualNextAction": {"kind": "delegation"}},
    ]}, {"recordType": "run", "runId": "skip", "moments": [{"behavior": 1}]}]
    _, moments, filtered, count, _ = filter_reviewed_runs(records, {"skip"})
    assert count == 1 and len(moments) == 1
    assert filtered["completionMoments"] == 1 and filtered["untypedDelegationMoments"] == 1
    eligible = eligible_baseline_moments(moments + [{"behavior": 1},
        {"behavior": 4, "actualNextAction": {"eventType": "item/started", "status": "pending"}},
        {"behavior": 6, "actualNextAction": {"eventType": "item/started", "status": "pending"}},
    ])
    assert len(eligible) == 1 and eligible[0]["behavior"] == 1
    try:
        urllib.request.urlopen("http://127.0.0.1/")
    except RuntimeError as exc:
        assert "forbids network" in str(exc)
    else:
        raise AssertionError("offline self-check unexpectedly allowed a network request")
    print("PRECHECK: offline filters and network block passed")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-check")
    baseline = sub.add_parser("baseline")
    baseline.add_argument("--dataset", default=str(replay.DATASET))
    baseline.add_argument("--skill", default=str(replay.CURRENT_SKILL))
    baseline.add_argument("--exclude-run-id", action="append", default=[])
    baseline.add_argument("--archive-only", action="store_true",
                          help="trust the dataset builder contract that only archived runs are included")
    baseline.add_argument("--per-behavior", type=int, default=30)
    baseline.add_argument("--seed", type=int, default=20261016)
    args = parser.parse_args()
    if args.command == "self-check":
        self_check()
    else:
        run(args)


if __name__ == "__main__":
    main()
