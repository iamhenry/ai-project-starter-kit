# Correct Retro Workflow Skills

Type: Task

## Outcome

Apply the approved universal retro and workflow instruction updates to the
repository-owned skills, and restore the mistakenly edited global copies.

## Scope

- `.agents/skills/retro/SKILL.md`
- `.agents/skills/issue-to-pr/SKILL.md`
- `.agents/skills/reproduce-bug/SKILL.md`
- `.agents/skills/verification-gate/SKILL.md`
- Restore only the matching accidental edits under `~/.config/opencode/skills/`.
- Do not modify any `qa` agent file.

## Acceptance

- Retro proposals use a conditional prioritized File/Before/After/Improvement table.
- Issue-to-PR delegates reproduction and verification to exact `qa`, and quality review to exact `reviewer`.
- Changed user or consumer behavior is observed through the actual path before regression tests are added.
- Reproduction and verification report model-backed product operations without choosing or downgrading models.
- GitHub issue references delegate ticket materialization to `create-ticket`.
- Wording is general and contains no audited-session-specific rules.
- Global skill files are restored to their prior contents.

## Mechanical

- `git diff --check`
- Assert the repository files contain the requested contracts.
- Assert the global files no longer contain the accidental additions.
- Assert global and repository QA agent files remain Luna/xhigh where configured.

## Assurance

Run one fresh combined low-risk QA pass only. Do not run separate review and verification gates.
