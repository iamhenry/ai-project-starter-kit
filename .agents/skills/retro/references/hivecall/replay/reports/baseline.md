# Hivecall current-skill baseline

- Sample: up to 30 per behavior; seed 20261016.
- Raw dataset moments: 1152; replayable moments: 1149.
- Baseline labels: Clef model `clef`; selective adjudication judge `ollama-cloud/kimi-k3`.
- For any later tested replay, use the `plan` subagent (`anthropic/claude-opus-5-5`); it was not invoked in this baseline labeling.
- Evidence links use run/thread ID and event ID in `baseline-labels.json`.
- ISC-5 behavior 3 trace-baseline moments may use `fixedCheck.gapMinutes` (at least 30) to identify observed quiet gaps; this evaluator-only field is not sent to the tested model.
- ISC-6 behavior 3 replay uses a separate turn-end anchor: context before the final orchestrator message, open work, and a later gap over 30 minutes. Both zero-worker progress moments and live-worker wait moments count toward the 10-moment floor. Only zero-worker moments are failure-side; a small count means low B3 power.
- Tier 1 owner wording is not distinguishable in this dataset (speaker attribution was discarded); only explicit tier 2 rules are counted as ground truth.
- Unknown answers are excluded from the score denominator and counted separately; missing evidence never counts as PASS.
- Each completed baseline uses a fixed-seed calibration partition disjoint from scored moments; the table reports calibration / scored / replayable / raw counts.
- Behavior 5 scores alert handling only (not missed-stall recall); behavior 6 scores bounded briefs only (not final reports); both are partial and not-trusted.

| Behavior | Score | Calibration / scored / replayable / raw | Pass / fail / unknown | Trust |
|---|---:|---:|---:|---|
| 1. Every checklist item is finished or explicitly parked with a reason. | 70% | 3 / 27 / 163 / 163 | 19 / 8 / 0 | ok |
| 2. Never tick an item without item-specific, independent proof. | 100% | 3 / 27 / 126 / 126 | 27 / 0 / 0 | ok |
| 3. Do not leave work open and go quiet; keep making useful progress. | 0% | 2 / 10 / 12 / 12 | 0 / 10 / 0 | ok |
| 4. Run independent work in parallel without overlapping ownership or files. | 0% | 3 / 27 / 343 / 343 | 0 / 27 / 0 | ok |
| 5. Treat watchdog alerts accurately: act on real problems, ignore false alarms, and do not miss stalls. | 92% | 3 / 27 / 162 / 162 | 22 / 2 / 3 | not-trusted |
| 6. Give workers bounded briefs and leave clean, useful reports. | 0% | 3 / 27 / 343 / 343 | 0 / 27 / 0 | not-trusted |
| 7. Use reasonable time and cost (measured at run level, not by replay). | not measured | 0 / 0 / 0 / 3 | 0 / 0 / 0 | not-measured |

## Behavior 7 run-level facts

```json
{
  "runsWithDuration": 3,
  "medianDurationMinutes": 2171,
  "runsWithTokens": 3,
  "medianTokens": 14618174,
  "costUsd": null,
  "costNote": "provider logs do not include USD cost"
}
```

## Clef/judge calibration

TPR (pass sensitivity) and TNR (fail specificity) compare each model with tier 1/2 labels. The dataset does not retain speaker attribution, so tier 1 is unavailable; tier 2 is the deterministic rule subset.

```json
{
  "clef": {
    "tier1": {
      "n": 0,
      "TPR": null,
      "TNR": null
    },
    "tier2": {
      "n": 72,
      "TPR": 0.938,
      "TNR": 0.95
    }
  },
  "judge": {
    "tier1": {
      "n": 0,
      "TPR": null,
      "TNR": null
    },
    "tier2": {
      "n": 27,
      "TPR": 0.375,
      "TNR": 0.455
    }
  }
}
```

See `baseline-labels.json` for moment-level Clef, rule, judge and tier-2 labels. `borderline-moments.json` contains up to 10 disagreements for the orchestrator to present to the owner.

## Clef calibration examples

Each Clef question uses up to three real trace examples with explicit PASS/FAIL labels; examples are in `baseline-examples.json`.

## Incomplete gate

- No behavior 1–3 count is below 10.
