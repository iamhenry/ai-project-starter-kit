# Hivecall current-skill baseline

- Sample: up to 30 per behavior; seed 20261016.
- Raw dataset moments: 1152; replayable moments: 1149.
- Baseline labels: Clef model `clef`; selective adjudication uses the `reviewer` OpenCode agent (GPT family).
- Replay tested model: the `plan` OpenCode agent (`anthropic/claude-opus-5-5`); not invoked in baseline labeling.
- Evidence links use run/thread ID and event ID in `baseline-labels.json`.
- ISC-5 behavior 3 trace-baseline moments may use `fixedCheck.gapMinutes` (at least 30) to identify observed quiet gaps; this evaluator-only field is not sent to the tested model.
- ISC-6 behavior 3 replay uses a separate turn-end anchor: context before the final orchestrator message, open work, and a later gap over 30 minutes. Both zero-worker progress moments and live-worker wait moments count toward the 10-moment floor. Only zero-worker moments are failure-side; a small count means low B3 power.
- Tier 1 owner wording is not distinguishable in this dataset (speaker attribution was discarded); only explicit tier 2 rules are counted as ground truth.
- Unknown answers are excluded from the score denominator and counted separately; missing evidence never counts as PASS.
- Behavior 7 scores runs PASS when active minutes per distinct finished ledger item (behavior 1 `tick`/`pass` evidence) are at most 45; digest `activeMinutes` is preferred, then `durationMinutes`; zero finished items FAIL and unknown item counts are excluded.
- Each completed baseline uses a fixed-seed calibration partition disjoint from scored moments; the table reports calibration / scored / replayable / raw counts.
- Behavior 5 scores alert handling only (not missed-stall recall); behavior 6 scores bounded briefs only (not final reports); both are partial and not-trusted.

| Behavior | Score | Calibration / scored / replayable / raw | Pass / fail / unknown | Trust |
|---|---:|---:|---:|---|
| 1. Every checklist item is finished or explicitly parked with a reason. | 70% | 3 / 27 / 163 / 163 | 19 / 8 / 0 | ok |
| 2. Never tick an item without item-specific, independent proof. | 100% | 3 / 27 / 126 / 126 | 27 / 0 / 0 | ok |
| 3. Do not leave work open and go quiet; keep making useful progress. | 0% | 2 / 10 / 12 / 12 | 0 / 10 / 0 | ok |
| 4. Run independent work in parallel without overlapping ownership or files. | 0% | 3 / 27 / 343 / 343 | 0 / 27 / 0 | ok |
| 5. Treat watchdog alerts accurately: act on real problems, ignore false alarms, and do not miss stalls. | 96% | 3 / 27 / 162 / 162 | 23 / 1 / 3 | not-trusted |
| 6. Give workers bounded briefs and leave clean, useful reports. | 0% | 3 / 27 / 343 / 343 | 0 / 27 / 0 | not-trusted |
| 7. Use reasonable time and cost (measured at run level, not by replay). | 50% | 0 / 3 / 3 / 3 | 1 / 1 / 1 | not-trusted |

## Behavior 7 run-level facts

```json
{
  "runs": 3,
  "runsWithDuration": 3,
  "medianDurationMinutes": 2171,
  "runsWithActiveMinutes": 3,
  "runsWithDigestActiveMinutes": 0,
  "medianActiveMinutes": 2171,
  "runsWithTokens": 3,
  "medianTokens": 14618174,
  "costUsd": null,
  "costNote": "provider logs do not include USD cost",
  "behavior7": {
    "rule": "PASS when active minutes per finished checklist item are at most 45; zero finished items FAIL.",
    "activeMinutesSource": "digest activeMinutes when present; otherwise durationMinutes",
    "finishedItemsSource": "distinct itemIds from behavior 1 ledger-edit moments labeled tick or pass",
    "score": 50,
    "trust": "not-trusted",
    "scoredRuns": 3,
    "replayableRuns": 3,
    "knownRuns": 2,
    "PASS": 1,
    "FAIL": 1,
    "UNKNOWN": 1,
    "evidence": [
      {
        "runId": "thr_55cgwjcgzk",
        "activeMinutes": 2171,
        "activeMinutesSource": "durationMinutes (digest active time unavailable)",
        "finishedItems": 96,
        "minutesPerItem": 22.61,
        "label": "PASS"
      },
      {
        "runId": "thr_4af5cb8u34",
        "activeMinutes": 1132,
        "activeMinutesSource": "durationMinutes (digest active time unavailable)",
        "finishedItems": null,
        "minutesPerItem": null,
        "label": "UNKNOWN",
        "reason": "finished item count unavailable from ledger-edit evidence"
      },
      {
        "runId": "thr_c64uzdrhjc",
        "activeMinutes": 2811,
        "activeMinutesSource": "durationMinutes (digest active time unavailable)",
        "finishedItems": 6,
        "minutesPerItem": 468.5,
        "label": "FAIL"
      }
    ]
  }
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
      "TPR": 0.062,
      "TNR": 0.909
    }
  }
}
```

See `baseline-labels.json` for moment-level Clef, rule, judge and tier-2 labels. `borderline-moments.json` contains up to 10 disagreements for the orchestrator to present to the owner.

## Clef calibration examples

Each Clef question uses up to three real trace examples with explicit PASS/FAIL labels; examples are in `baseline-examples.json`.

## Incomplete gate

- No behavior 1–3 count is below 10.
