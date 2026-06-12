---
name: code-quality-gate
description: Fresh-subagent code quality review gate after implementation and before verification. Use when code changes are complete and the orchestrator needs APPROVE_CODE, REVISE_CODE, or ASK_USER based on plan fidelity, simplicity, tests, repo style, security, and maintainability. Does not implement or write files.
---

# Code Quality Gate

Use this skill after implementation and before `verification-gate` or other interactive/platform verification.

Run it as a fresh subagent review gate. It reviews the implemented code, returns a decision, and never edits files.

## Inputs

Read the minimum available context:

- Required: `{ISSUE_DIR}/plan.md`
- Required: changed files and/or git diff
- Optional but useful: `{ISSUE_DIR}/issue.md`
- Optional but useful: implementation summary from the implementation agent
- Optional but useful: test, build, lint, and typecheck output
- Optional but useful: `_ai/prompts/quality/code-review.md` as the review standard
- Optional but useful: `_ai/prompts/quality/code-guidelines.md` as the quality standard

If `plan.md` or the changed code/diff is missing, return `ASK_USER` with the missing input.

## Artifact Contract

- `ISSUE_DIR` is the artifact directory created by `gather-context` for the current pipeline run.
- Required: `plan.md`, plus changed files and/or git diff.
- Optional but useful: `issue.md`, implementation summary, test/build/lint/typecheck output, and quality docs.
- If expected command output is missing and needed to judge safely, return `ASK_USER` with the missing command output.
- If command output is missing because it is not applicable, do not penalize it.

## Review Process

1. Reconstruct the intended scope from `plan.md`; use `issue.md` only to resolve ambiguity.
2. Review the diff and directly affected code first.
3. Trigger wider dependency review only when the change touches shared modules, public interfaces, global state, async side effects, security-sensitive paths, or common components.
4. Compare implementation against the referenced quality docs without copying them into the report.
5. Heavily weight simplicity: prefer the smallest code that satisfies `plan.md`; penalize speculative abstractions, extra surfaces, duplicate state, and unplanned features.
6. Check provided test, build, lint, and typecheck output. Do not invent results that were not provided or run.
7. Return a concise structured decision to the orchestrator.

## Weighted Rubric

Score out of 100:

| Category | Weight | Subcriteria |
| --- | ---: | --- |
| Correctness against `plan.md` | 30 | Implements required behavior; respects scope/out-of-scope; has no obvious regressions against plan acceptance criteria. |
| Simplicity / KISS / YAGNI | 25 | Uses the smallest solution that satisfies the plan; avoids speculative abstractions/features; avoids duplicate state or sources of truth. |
| Tests / build / typecheck | 15 | Relevant checks pass when provided; coverage matches changed risk; missing expected output is handled explicitly. |
| Architecture / repo style | 15 | Follows existing patterns; respects boundaries/interfaces; avoids unnecessary dependencies. |
| Security / error handling | 10 | Has no privacy/security regression; handles failure paths safely. |
| Readability / maintainability | 5 | Names and structure are understandable; code is easy to review/change. |

Scoring anchors:

- Full credit: clear artifact or code evidence supports the item.
- Half credit: partially satisfied, thinly evidenced, or has non-blocking gaps.
- Zero credit: missing, contradicted, unverifiable, or unsafe.

## Hard Fails

Return `REVISE_CODE` regardless of score if any are true:

- Relevant test, build, lint, or typecheck output fails.
- High severity bug with direct code evidence.
- Security or privacy issue.
- Implementation contradicts `plan.md`.
- Unplanned scope drift.
- Overengineered solution where a simpler approach satisfies `plan.md`.

Return `ASK_USER` instead when the blocker is missing context, ambiguous product intent, unclear plan scope, conflicting artifacts, or unavailable verification output needed to decide safely.

## Decision Rules

- `APPROVE_CODE`: no hard fail, score is 85 or higher, and remaining issues are low-risk or clearly optional.
- `REVISE_CODE`: hard fail applies, or score is below 85 with actionable implementation changes.
- `ASK_USER`: required inputs are missing, product behavior is ambiguous, or deciding would require guessing beyond the artifacts.

If `REVISE_CODE`, the orchestrator routes notes back to implementation subagent(s), then reruns this gate on the revised diff.

## Output Format

Return exactly this structure:

```md
## Code Quality Gate Result

- Decision: `APPROVE_CODE|REVISE_CODE|ASK_USER`
- Score: [0-100 or `N/A`]
- Reviewed: [plan.md, issue.md, diff/changed files, implementation summary, command outputs, quality docs]

### Findings

- [severity] [file:line or artifact] [specific issue or approval reason]
- [severity] [file:line or artifact] [specific issue or approval reason]

### Required Changes

- [Only for REVISE_CODE or ASK_USER; otherwise `None`]

### Next Action

- [run verification-gate / revise implementation / ask user]
```

## Constraints

- Do not edit files.
- Do not implement fixes.
- Do not create review artifacts or helper files.
- Do not run broad QA; use `verification-gate` after approval.
- Do not duplicate the full quality docs; reference `_ai/prompts/quality/code-review.md` and `_ai/prompts/quality/code-guidelines.md`.
- Do not commit changes.
- Keep findings concise and evidence-based. Speculative risks must be marked low confidence or omitted.
