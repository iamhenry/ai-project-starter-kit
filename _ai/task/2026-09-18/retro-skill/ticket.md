# Create Universal Retro Skill

Type: Feature

## Outcome

Create a lean `retro` skill that the user explicitly invokes to learn from a completed or failed run across any skill, command, prompt, agent, or workflow.

## Acceptance

- `.agents/skills/retro/SKILL.md` is fewer than 150 lines total.
- The skill triggers only when the user explicitly requests a retro or names `retro`; agents do not invoke it automatically.
- Every result includes what went right, what went wrong, and what could be improved.
- The required final response is shown as one reusable fenced Markdown template.
- It compares intended and observed behavior, classifies the cause, and returns `NO_CHANGE`, `PROPOSE_CHANGE`, or `BLOCKED`.
- It prefers deletion or clarification over adding rules and rejects one-off, wrong-layer, or unsupported changes.
- It works across skills, commands, prompts, agents, and workflows without adding a shared protocol or ledger.
- It is read-only by default; edits require explicit user authority and remain subject to the target artifact's normal review path.
- Scope is limited to the new skill and this task ticket.

## Mechanical

- `git diff --check`
- `test "$(wc -l < .agents/skills/retro/SKILL.md)" -lt 150`
- Parse and inspect YAML frontmatter.

## Review

Run one fresh quality gate only. Do not add a separate verification gate or broad eval campaign.

## Quality Gate Result

- The single fresh gate returned `REVISE_CODE` at 82/100 for overlapping verdicts, an undefined `NO_CHANGE` rule, and missing evidence-redaction guidance.
- The skill now defines non-overlapping verdicts, keeps edit authority separate from diagnosis, and redacts sensitive evidence.
- No second gate was run, as requested. Final mechanical checks passed at 81 lines.
