---
name: issue-to-pr
description: Orchestrate and judge an issue-to-PR planning pipeline without editing artifacts directly. Use when the user wants an issue-to-PR workflow, task-to-PR pipeline, or structured path from request to implementation readiness. Routes each stage to the owning skill, checks gate outputs, asks for revisions when the pipeline drifts, and keeps implementation, verification, and PR as placeholders.
---

# Issue To PR

## Pipeline Components

| Component | Role | Why |
| --- | --- | --- |
| `gather-context` | Owns intake, research, and proposal options. | Grounds the pipeline before judging or planning. |
| `judge-proposal` | Independently reviews proposal quality. | Catches weak assumptions before plan creation. |
| `create-issue` | Owns the selected implementation plan. | Keeps planning artifacts with the planning workflow. |
| `judge-plan` | Independently reviews plan readiness. | Prevents implementation from starting on a weak plan. |
| Implementation placeholder | Future owner consumes `plan.md`. | Keeps execution details out of this wrapper. |
| `verification-gate` | Fresh subagent proves completed work. | Keeps QA execution outside this wrapper. |
| `agent-browser` | Browser proof path used by `verification-gate`. | Supports web and mobile-web validation without defining it here. |
| `xcodebuildmcp-cli` | Apple-platform proof path used by `verification-gate`. | Supports iOS and macOS validation without defining it here. |
| PR placeholder | Future owner handles PR handoff. | Keeps review and merge policy outside this wrapper. |

Orchestrate and judge the pipeline. Do not create, edit, append, or repair task artifacts directly.

This skill connects modular skills, checks whether each stage produced the expected artifact, and routes revisions back to the owning skill or subagent when the pipeline is off track.

---

## Pipeline

### 1. Gather Context And Intake

- Run `gather-context` with the raw user issue/request.
- `gather-context` owns issue intake, task folder creation, and `issue.md` creation/update.
- Write supporting research under `_ai/task/{YYYY-MM-DD-slug}/research/*.md`.
- Append or update the approach options in `issue.md`.
- Gate: `issue.md`, all required `research/*.md`, and `Approaches` in `issue.md` exist.
- If the gate fails, route revision back to `gather-context`; do not patch artifacts here.

### 2. Proposal Judge Checkpoint

- Delegate review to a fresh subagent using `judge-proposal`.
- The subagent must receive only the task artifacts it needs, not accumulated conversation context.
- The review must be clean, independent, and adversarial enough to catch weak assumptions before planning.
- Gate: `issue.md` contains `Judge Decision` with `Status: SELECTED` or `Status: ASK_USER`.
- If `ASK_USER`, stop and ask the one focused question from `judge-proposal`.

### 3. Create Issue Plan

- Run the `create-issue` workflow after the proposal is selected.
- Write `_ai/task/{YYYY-MM-DD-slug}/plan.md` in the same task directory.
- The plan should be based on `issue.md`, accepted approach details, and `research/*.md`.
- Gate: `plan.md` exists in the same task directory.
- If missing, route revision back to `create-issue`; do not create `plan.md` here.

### 4. Plan Judge Checkpoint

- Delegate review to a fresh subagent using `judge-plan`.
- The subagent must receive only `issue.md`, `plan.md`, and relevant `research/*.md` artifacts.
- The review must be independent from the proposal judge and main-agent working context.
- Gate: `plan.md` contains `Plan Judge` with `APPROVE_PLAN`, `REVISE_PLAN`, or `ASK_USER`.
- Continue only on `APPROVE_PLAN`; route `REVISE_PLAN` to `create-issue` and stop on `ASK_USER`.

### 5. Implementation Placeholder

- Placeholder only.
- Future work should define how implementation agents consume `plan.md`, update task state, and avoid coupling this wrapper to execution details.

### 6. Verification Gate

- After implementation is complete, delegate verification to a fresh subagent using `verification-gate`.
- The subagent must receive `plan.md`, the implementation summary, changed files, and any relevant test/build output.
- `verification-gate` reads `plan.md` and routes proof by platform: `web`/`mobile-web` through `agent-browser`, `ios`/`macos` through `xcodebuildmcp-cli`, and `non-ui` through a direct proof path.
- Gate: `verification-gate` returns `PASS`, `FAIL`, or `BLOCKED` with evidence.
- Continue only on `PASS`; route `FAIL` or `BLOCKED` to the implementation owner or user as appropriate.
- Do not run QA directly or define browser, iOS, macOS, or non-UI verification steps in this wrapper.

### 7. PR Placeholder

- Placeholder only.
- Future work should define PR creation, review, and handoff workflow.
- Do not define PR review policy or merge-readiness logic in this wrapper.

---

## Artifact Contract

Allowed task artifacts:

- `_ai/task/{YYYY-MM-DD-slug}/issue.md`
- `_ai/task/{YYYY-MM-DD-slug}/plan.md`
- `_ai/task/{YYYY-MM-DD-slug}/research/*.md`

Do not create helper docs, reference files, sidecar state, ADR files, or wrapper-specific metadata unless this contract is intentionally revised later.

---

## Ownership Boundaries

| Artifact or decision | Owner |
| --- | --- |
| `issue.md` intake, scenarios, approaches | `gather-context` |
| `research/*.md` evidence reports | `gather-context` research agents |
| `Judge Decision` in `issue.md` | `judge-proposal` fresh subagent |
| `plan.md` | `create-issue` workflow |
| `Plan Judge` in `plan.md` | `judge-plan` fresh subagent |
| Verification proof | `verification-gate` fresh subagent |
| Pipeline order, gates, revision routing | `issue-to-pr` |

When an artifact is missing or malformed, ask the owner to revise it. Do not fix it inside this wrapper.

---

## Delegation Rule

Judge and verification checkpoints are always delegated to fresh subagents:

- Use `judge-proposal` for the proposal checkpoint.
- Use `judge-plan` for the plan checkpoint.
- Use `verification-gate` after implementation is complete.
- Do not reuse main-agent context for judge decisions or verification proof.
- Pass artifact paths and concise task framing only.
- Treat judge and verification feedback as gates before continuing to the next phase.

---

## Revision Routing

- Missing `issue.md`, missing research files, or missing approaches: rerun or revise `gather-context`.
- `judge-proposal` returns `ASK_USER`: stop and ask its one focused question.
- Missing `plan.md`: rerun or revise `create-issue`.
- `judge-plan` returns `REVISE_PLAN`: route notes back to `create-issue` and request a revised `plan.md`.
- `judge-plan` returns `ASK_USER`: stop and ask its one focused question.
- `verification-gate` returns `FAIL` or `BLOCKED`: route evidence to the implementation owner or user; do not patch or verify directly here.
- Any unexpected state: stop with the artifact path, expected state, actual state, and owning stage.

---

## Constraints

- Keep this skill lean: orchestration only.
- Do not create, edit, append, or repair `issue.md`, `plan.md`, or `research/*.md` directly.
- Do not duplicate decision logic from `gather-context`, `create-issue`, judge skills, implementation skills, verification skills, or PR workflows.
- Do not define implementation execution details.
- Do not run QA directly or define web, mobile-web, iOS, macOS, or non-UI verification flows beyond `verification-gate` delegation.
- Do not define PR creation or review details beyond placeholders.
- Prefer artifact handoff over hidden state.
- Prefer modular delegation over bloating this wrapper.

## Known Gap

`create-issue` must write `plan.md` into the same `_ai/task/{YYYY-MM-DD-slug}/` directory as `issue.md`. If it creates a new task directory, stop and route that as a `create-issue` workflow revision.
