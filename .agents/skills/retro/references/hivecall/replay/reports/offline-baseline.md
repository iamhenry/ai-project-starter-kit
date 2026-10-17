# Hivecall offline rule-only baseline

**Status: PRECHECK only; this is not the Clef-labeled ISC-5 baseline.**

- Sample: up to 30 per behavior; seed 20261016.
- Cloud calls: none. No dataset context or action text was sent outside this machine.
- Source mode: archive-only dataset contract; 3 archived run records remain.
- For any later replay, use the `plan` subagent (`anthropic/claude-opus-5-5`); it was not invoked for this report.
- B4/B6 completions excluded: 0; source event type is present and 0 events were untyped or not pending starts.
- B3 baseline eligibility uses evaluator-only `fixedCheck.gapMinutes` (at least 30); that metadata is not sent to a tested model.
- Scores are rule-only lower bounds: rule-undecidable actions count as failures. Numeric scores are `not-trusted` because Clef/judge review was not run.
- Behaviors 4 and 6 are intentionally unscored in this local rule-only lower-bound report; use the Clef baseline for them.
- B3 local replay-anchor audit: 11 qualifying moments from 3 archived runs; 14 long gaps, 12 turn ends, 11 with open work; zero-worker count 1, live-worker count 10; by week: {"2026-W41": 6, "2026-W42": 5}.
- B3 replay count floor met: 11 total moments. Only 1 zero-worker moment is failure-side; B3 power is low.
- The archive-only source has 12 stored B3 trace gaps across 3 runs; two live runs are excluded by owner direction.
- This aggregate report omits trace/event IDs and action text; redacted excerpts are stored separately in the B3 audit artifact.
- The source dataset does not preserve owner speaker attribution, so tier-1 labels remain unavailable.

| Behavior | Rule-only lower bound | Sample / baseline / raw | Pass / fail / unknown | Trust |
|---|---:|---:|---:|---|
| 1. Every checklist item is finished or explicitly parked with a reason. | 73% | 30 / 163 / 163 | 22 / 8 / 0 | not-trusted |
| 2. Never tick an item without item-specific, independent proof. | 100% | 30 / 126 / 126 | 30 / 0 / 0 | not-trusted |
| 3. Do not leave work open and go quiet; keep making useful progress. | 0% | 12 / 12 / 12 | 0 / 12 / 0 | not-trusted |
| 4. Run independent work in parallel without overlapping ownership or files. | not measured | 0 / 0 / 343 | 0 / 0 / 343 | not-measured |
| 5. Treat watchdog alerts accurately: act on real problems, ignore false alarms, and do not miss stalls. | 0% | 30 / 162 / 162 | 0 / 30 / 26 | not-trusted |
| 6. Give workers bounded briefs and leave clean, useful reports. | not measured | 0 / 0 / 343 | 0 / 0 / 343 | not-measured |
| 7. Use reasonable time and cost (measured at run level, not by replay). | not measured | 0 / 0 / 3 | 0 / 0 / 0 | not-measured |

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

## ISC-5 baseline count gate

- Behaviors 1–3 each have at least 10 trace-baseline moments. B3 turn-end count floor is 11 total (10 required). Only 1 zero-worker moment is failure-side; power is low.
