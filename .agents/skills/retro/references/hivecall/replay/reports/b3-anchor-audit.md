# Behavior 3 turn-end anchor audit

**Status: PRECHECK; local archived-log inspection only, no model calls.**

- Archived run records inspected: 3.
- Long gaps over 30 minutes: 14.
- Orchestrator turn ends before long gaps: 12.
- Turn ends with open work: 11.
- Zero-live-worker moments: 1.
- Live-worker wait moments: 10.
- Total retained B3 moments: 11; both classes count toward the 10-moment replay floor.
- Failure-side zero-worker moments: 1; live-worker wait moments: 10.
- Redacted context/action excerpts: `.agents/skills/retro/references/hivecall/replay/reports/b3-turn-end-moments.jsonl`.
- Replay contexts end before the final orchestrator message; evaluator-only gap and worker counts are not included in model prompts.
- Unresolved delegations, unknown worker starts, and spawn commands count as live.
- Zero-worker moments test whether the next action keeps work moving; live-worker moments test whether it correctly waits.
- B3 replay floor met. Only 1 zero-worker moment is failure-side; B3 power is low.
- Extraction is currently local to replay; move it into `scripts/build-dataset.py` after the method is accepted.
