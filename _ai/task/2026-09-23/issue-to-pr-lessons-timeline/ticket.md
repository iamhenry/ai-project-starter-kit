# Issue-to-PR lessons timeline

## Outcome

The main issue-to-PR agent keeps a lean, chronological `lessons.md` inside the current run's `ISSUE_DIR` for its mistakes, missing context or tools, and environment learnings. No separate files for those categories.

## Scope

- Change only `.agents/skills/issue-to-pr/SKILL.md` for the workflow.
- Keep checkpoint verdicts and resume state in `ticket.md`; lessons are advisory, not another gate or state source.
- Preserve the existing pipeline stages, gates, and dispatch rules.
- Do not implement unrelated suggestions from the referenced thread or change publication authority.

## Verification

The next pipeline agent can create or resume `{ISSUE_DIR}/lessons.md`, append useful bumps without logging routine stages, and continue the existing gate and ownership rules. Review the final skill text and diff; this instruction-only change needs no live app run.
