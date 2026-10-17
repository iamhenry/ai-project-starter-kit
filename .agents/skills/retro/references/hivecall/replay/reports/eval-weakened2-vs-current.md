# Hivecall held-out replay

**Verdict: REJECT (control only)**

- Run tag: `weakened2-vs-current`.
- Tested agent: `plan` (`anthropic/claude-opus-5-5`); judge agent: `reviewer` (GPT family). The families differ.
- Held-out rule: weeks before `2026-W42`; eligible moments: 120.
- Behavior filter: 2.
- Sample: up to 30 per selected replayable behavior; seed 20261016.
- Clef/judge few-shot examples use only the build-week partition (weeks ≥ `2026-W42`); none available for behaviors: none.
- UNKNOWN answers are excluded from score denominators and reported separately; missing or unparseable answers never count as PASS.
- B3 sample classes: not evaluated (filtered).
- Only redacted moment context and skill text went to the tested model; no agent/repository instructions or tools.

| Behavior | Current | Changed | Unknown current/changed | Delta (points) | Noise band (95% paired bootstrap) | Trust |
|---|---:|---:|---:|---:|---:|---|
| 1. Every checklist item is finished or explicitly parked with a reason. | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |
| 2. Never tick an item without item-specific, independent proof. | 100% | 93% | 0/0 | -6.67 | [0.0, 0.0] | ok |
| 3. Do not leave work open and go quiet; keep making useful progress. | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |
| 4. Run independent work in parallel without overlapping ownership or files. | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |
| 5. Treat watchdog alerts accurately: act on real problems, ignore false alarms, and do not miss stalls. | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |
| 6. Give workers bounded briefs and leave clean, useful reports. | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |
| 7. Use reasonable time and cost (measured at run level, not by replay). | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) | not evaluated (filtered) |

## Controls

- Weakened proof rule: behavior 2 score 97%; current score 100%; positive control PASS.
- Repeated-current noise control: within measured noise.
- Candidate skill is identical to current: no.

## Held-out by week

| Week | Behavior | Current | Changed | Unknown current/changed | n |
|---|---:|---:|---:|---:|---:|
| 2026-W41 | 2 | 100% | 93% | 0/0 | 30 |

## Judge/rule disagreements

5 disagreement records; see `eval-moments.json`.

## Flipped moments

2 moments changed pass/fail; see `eval-moments.json` for run/thread and event IDs.

## PR rule

- Reject: filtered behavior set is control only; excluded behaviors cannot be checked for regressions.
- Reject: target behavior 2 did not beat the noise band.

Detailed evidence: `.agents/skills/retro/references/hivecall/replay/reports/eval-weakened2-vs-current-moments.json`.
