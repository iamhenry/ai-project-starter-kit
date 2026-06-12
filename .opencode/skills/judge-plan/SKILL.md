---
name: judge-plan
description: Lean standalone gate for reviewing create-issue plan artifacts before implementation. Use after `{ISSUE_DIR}/plan.md` exists to check format, proposal fidelity, actionability, and ETHOS alignment without doing architecture review or implementation.
---

# Judge Plan

Use this skill after `create-issue` writes a local plan artifact and before any implementation starts.

Keep the scope narrow:

- Check whether agents can safely execute the plan.
- Confirm the plan follows the selected proposal from `issue.md`, using research as supporting evidence if needed.
- Catch malformed markdown, missing required structure, vague tasks, and obvious ETHOS drift.
- Write the decision back into `plan.md`.

Do not use this skill for broad architecture review, redesign, implementation, code edits, commits, or separate review files.

## Inputs

Read only these artifacts when available:

- `{ISSUE_DIR}/issue.md`
- `{ISSUE_DIR}/plan.md`
- `{ISSUE_DIR}/research/*.md`
- `_ai/docs/ETHOS.md`
- `.opencode/command/workflow/01-plan/02-create-issue.md` as the structural reference

If the task directory or `plan.md` is missing, return `ASK_USER` with the missing artifact.

## Artifact Contract

The plan must be a create-issue style artifact for `{ISSUE_DIR}/plan.md` and include enough structure for a follow-on implementation agent to execute without guessing.

`ISSUE_DIR` is the artifact directory created by `gather-context` for the current pipeline run.

Required major sections:

- Acceptance Criteria with measurable checkbox criteria
- User Story and Gherkin BDD Scenarios in valid markdown fences
- Scope and Boundaries
- Codebase Orientation, Dependencies, Data Flow, and relevant model or architecture notes
- Deliverables and Error Handling
- Implementation Checklist with phased, atomic checklist tasks and concrete file paths or locations
- Verification Gate Plan with `Verification Mode`, `Objective`, `Primary Flow`, `Regression Check`, `Evidence Plan`, `Pass Criteria`, and `Blocked Conditions`

## Review Steps

1. Locate the chosen proposal in `issue.md`, especially `## Judge Decision` and/or `## Approaches`; use `research/*.md` only as supporting evidence.
2. Check `plan.md` against the create-issue structure, especially acceptance criteria, Gherkin scenarios, implementation checklist, and verification gate plan.
3. Check proposal fidelity: the plan must implement the selected proposal and not silently switch approach.
4. Check actionability: tasks must be concrete enough for a junior implementation agent, with files, actions, and verification.
5. Check markdown parse safety: headings, lists, tables, and fenced code blocks must be well-formed enough that agents will not misread the plan.
6. Check ETHOS lightly: prefer tracer-bullet scope, reuse, user trust, safe failure, and minimal friction. Do not re-litigate architecture unless the plan contradicts these principles in a blocking way.

## Scorecard

Score out of 100:

- Scoring anchors: full credit means the plan clearly satisfies the item with artifact evidence; half credit means partial satisfaction or thin evidence; zero means missing, contradicted, or unverifiable.
- Create-issue structure: 40
  - 10 required major sections exist.
  - 10 acceptance criteria and Gherkin are measurable, testable, and markdown-valid.
  - 10 implementation checklist uses action prefixes, files or locations, and phased tasks.
  - 10 verification gate includes `Verification Mode`, `Objective`, `Primary Flow`, `Regression Check`, `Evidence Plan`, `Pass Criteria`, and `Blocked Conditions`.
- Proposal fidelity: 35
  - 15 plan implements the selected approach.
  - 10 plan does not drift into unselected scope.
  - 5 plan preserves stated out-of-scope boundaries.
  - 5 plan uses research constraints and repo style evidence.
- Actionability: 20
  - 8 tasks identify files or locations.
  - 6 tasks are atomic enough for implementation agents.
  - 4 verification steps are concrete.
  - 2 risks or blockers are clear.
- Style alignment: 5
  - 5 follows create-issue formatting and repo planning style.

## Hard Fail Rules

Return `REVISE_PLAN` regardless of score if any are true:

- A major required section is missing.
- The plan contradicts or drops the chosen proposal.
- Implementation tasks are too vague to execute safely.
- Markdown structure is broken enough that agents may misread it, including malformed fences around Gherkin or code examples.

Return `APPROVE_PLAN` when no hard fail applies and the score is 85 or higher.

Return `REVISE_PLAN` when a hard fail applies, or when artifacts are sufficient to revise but the score is below 85.

Return `ASK_USER` when required artifacts are missing, product intent is ambiguous, the selected proposal is ambiguous, or the judge cannot distinguish between valid competing approaches from the existing artifacts.

## Writeback Rule

Append or update one concise `## Plan Judge` section at the end of `plan.md`. Do not create a separate review file.

If a `## Plan Judge` section already exists, replace that section only. Preserve the rest of `plan.md` exactly.

Use this structure:

```md
## Plan Judge

- Decision: `APPROVE_PLAN|REVISE_PLAN|ASK_USER`
- Score: [0-100]
- Chosen proposal: [one sentence]
- Checked: [issue.md, plan.md, research files, ETHOS, create-issue reference as applicable]

### Notes

- [approve note or required revision]
- [approve note or required revision]

### Required Changes

- [Only for REVISE_PLAN or ASK_USER; otherwise `None`]
```

## Output

After writing `plan.md`, return this exact structure in chat:

```md
## Plan Judge Result

- Decision: `APPROVE_PLAN|REVISE_PLAN|ASK_USER`
- Score: [0-100]
- Plan: `{ISSUE_DIR}/plan.md`
- Writeback: `## Plan Judge` appended or updated

### Key Findings

- [highest-signal finding]
- [highest-signal finding]

### Next Action

- [implement / revise plan / ask user to choose proposal or provide artifact]
```

## Constraints

- Do not edit application code.
- Do not implement the plan.
- Do not broaden into architecture review or redesign.
- Do not create helper files, references, or separate review artifacts.
- Do not commit changes.
- Keep review notes concise and tied to the artifacts.
