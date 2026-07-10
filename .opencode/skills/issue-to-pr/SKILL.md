---
name: issue-to-pr
description: Orchestrate and judge an issue-to-PR pipeline without editing artifacts directly. Use when the user wants an issue-to-PR workflow, task-to-PR pipeline, or structured path from request to PR readiness. Routes each stage to the owning skill or subagent, checks gate outputs, asks for revisions when the pipeline drifts, and keeps PR as a placeholder.
---

# Issue To PR

## Pipeline Components

| Component                    | Role                                                      | Why                                                                              |
| ---------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `gather-context`             | Owns intake, research, and proposal options.              | Grounds the pipeline before judging or planning.                                 |
| `judge-proposal`             | Independently reviews proposal quality.                   | Catches weak assumptions before plan creation.                                   |
| `create-issue`               | Owns the selected implementation plan.                    | Keeps planning artifacts with the planning workflow.                             |
| `judge-plan`                 | Independently reviews plan readiness.                     | Prevents implementation from starting on a weak plan.                            |
| Implementation orchestration | Delegates implementation work to write-capable subagents. | Keeps this wrapper orchestration-only while moving the plan toward working code. |
| `code-quality-gate`          | Fresh subagent reviews code quality after implementation. | Catches implementation issues before QA proof begins.                            |
| `verification-gate`          | Fresh subagent proves completed work.                     | Keeps QA execution outside this wrapper.                                         |
| `agent-browser`              | Browser proof path used by `verification-gate`.           | Supports web and mobile-web validation without defining it here.                 |
| `xcodebuildmcp-cli`          | Apple-platform proof path used by `verification-gate`.    | Supports iOS and macOS validation without defining it here.                      |
| PR placeholder               | Future owner handles PR handoff.                          | Keeps review and merge policy outside this wrapper.                              |

## Available Capabilities

### Agents

| Name      | Use for                                          | Delegate when                                 | Avoid when                                  |
| --------- | ------------------------------------------------ | --------------------------------------------- | ------------------------------------------- |
| `code`    | Implementation, bug fixes, refactors, tests.     | Approved write or code changes are ready.     | Research, docs-only edits, judging, QA.     |
| `general` | Docs, config, task artifacts, utility workflows. | Non-code edits or orchestration utility work. | App code implementation and gate decisions. |

### Subagents

| Name      | Use for                                     | Delegate when                                        | Avoid when                                   |
| --------- | ------------------------------------------- | ---------------------------------------------------- | -------------------------------------------- |
| `atlas`   | Local codebase research.                    | Architecture, data flow, dependencies, blast radius. | Pure external docs, judging, implementation. |
| `voyager` | External docs, API, and framework research. | Version-specific docs or best practices are needed.  | Repo-local evidence is enough.               |

Note: although `atlas` and `voyager` have write permissions for research artifacts, this pipeline uses them only for research/reporting unless a stage explicitly assigns an artifact write.

### Skills

| Name                | Use for                          | Delegate when                                       | Avoid when                                   |
| ------------------- | -------------------------------- | --------------------------------------------------- | -------------------------------------------- |
| `judge-proposal`    | Proposal selection gate.         | `{ISSUE_DIR}/issue.md` has approaches and research. | Implementation, plan creation, code review.  |
| `judge-plan`        | Plan readiness gate.             | `{ISSUE_DIR}/plan.md` exists.                       | Architecture redesign or implementation.     |
| `code-quality-gate` | Post-implementation code review. | Implementation is done, before verification.        | Fixing code or QA.                           |
| `verification-gate` | Behavior proof.                  | `APPROVE_CODE` is returned.                         | Exploratory QA or missing prerequisites.     |
| `agent-browser`     | Web and mobile-web proof path.   | `verification-gate` needs browser proof.            | Direct orchestrator QA or non-browser proof. |
| `xcodebuildmcp-cli` | iOS and macOS proof path.        | `verification-gate` needs Apple-platform proof.     | Web or non-UI proof.                         |

Orchestrate and judge the pipeline. Do not create, edit, append, or repair task artifacts directly.

This skill connects modular skills, checks whether each stage produced the expected artifact, and routes revisions back to the owning skill or subagent when the pipeline is off track.

---

## Pipeline

`ISSUE_DIR` is created by `gather-context` using `_ai/task/{YYYY-MM-DD}/{slug}`. All pipeline artifacts are relative to `ISSUE_DIR`.

### 1. Gather Context And Intake

- Run `gather-context` with the raw user issue/request.
- If manually orchestrating `gather-context`, preserve its exact research topology: 4 `atlas` agents plus 1 `voyager` agent.
- `general` may scaffold or synthesize artifacts only; it must not replace the specialized `gather-context` research agents.
- `gather-context` owns issue intake, task folder creation, and `{ISSUE_DIR}/issue.md` creation/update.
- Write supporting research under `{ISSUE_DIR}/research/*.md`.
- Append or update the approach options in `{ISSUE_DIR}/issue.md`.
- Gate: `{ISSUE_DIR}/issue.md`, all required `{ISSUE_DIR}/research/*.md`, and `Approaches` in `{ISSUE_DIR}/issue.md` exist.
- If the gate fails, route revision back to `gather-context`; do not patch artifacts here.

### 2. Proposal Judge Checkpoint

- Delegate review to a fresh subagent using `judge-proposal`.
- The subagent must receive only the task artifacts it needs, not accumulated conversation context.
- The review must be clean, independent, and adversarial enough to catch weak assumptions before planning.
- Gate: `{ISSUE_DIR}/issue.md` contains `Judge Decision` with `Status: SELECTED` or `Status: ASK_USER`.
- If `ASK_USER`, stop and ask the one focused question from `judge-proposal`.

### 3. Create Issue Plan

- Before running `create-issue`, verify `{ISSUE_DIR}` exists.
- Run the `create-issue` workflow after the proposal is selected.
- Instruct `create-issue` or the executing agent to write `{ISSUE_DIR}/plan.md`.
- The plan should be based on `{ISSUE_DIR}/issue.md`, accepted approach details, and `{ISSUE_DIR}/research/*.md`.
- After `create-issue`, verify `{ISSUE_DIR}/plan.md` exists.
- If the plan artifact appears elsewhere or `{ISSUE_DIR}/plan.md` is missing, stop and route as a `create-issue` output mismatch; do not create `{ISSUE_DIR}/plan.md` here.

### 4. Plan Judge Checkpoint

- Delegate review to a fresh subagent using `judge-plan`.
- The subagent must receive only `{ISSUE_DIR}/issue.md`, `{ISSUE_DIR}/plan.md`, and relevant `{ISSUE_DIR}/research/*.md` artifacts.
- The review must be independent from the proposal judge and main-agent working context.
- Gate: `{ISSUE_DIR}/plan.md` contains `Plan Judge` with `APPROVE_PLAN`, `REVISE_PLAN`, or `ASK_USER`.
- Continue only on `APPROVE_PLAN`; route `REVISE_PLAN` to `create-issue` and stop on `ASK_USER`.

### 5. Implementation Orchestration

- Do not implement directly from this wrapper.
- Always delegate write operations to implementation subagents.
- Delegate relevant read or research operations when needed.
- If `{ISSUE_DIR}/plan.md` has a clear, safe delegation structure, follow it.
- If `{ISSUE_DIR}/plan.md` lacks safe delegation structure, create an ad hoc delegation todo list in memory/context only and delegate safely.
- Do not save a new plan to disk or revise `{ISSUE_DIR}/plan.md` just to add delegation structure.
- Avoid overlapping file edits; when overlap exists, sequence agents instead of parallelizing them.
- Collect the implementation summary, changed files, commands run, and known risks from implementation subagents.

### 6. Code Quality Gate

- After implementation is complete, delegate review to a fresh subagent using `code-quality-gate`.
- The subagent must receive `{ISSUE_DIR}/plan.md`, implementation summary, changed files, commands run, and known risks.
- Gate: `code-quality-gate` returns `APPROVE_CODE`, `REVISE_CODE`, or `ASK_USER` with concise evidence.
- Continue to verification only on `APPROVE_CODE`.
- If `REVISE_CODE`, route notes back to implementation subagent(s), revise implementation, then rerun `code-quality-gate`.
- If `ASK_USER`, stop and ask the focused question.
- Do not review or patch code directly from this wrapper.

### 7. Verification Gate

- After `code-quality-gate` returns `APPROVE_CODE`, delegate verification to a fresh subagent using `verification-gate`.
- The subagent must receive `{ISSUE_DIR}/plan.md`, the implementation summary, changed files, and any relevant test/build output.
- `verification-gate` reads `{ISSUE_DIR}/plan.md` and routes proof by platform: `web`/`mobile-web` through `agent-browser`, `ios`/`macos` through `xcodebuildmcp-cli`, and `non-ui` through a direct proof path.
- Gate: `verification-gate` returns `PASS`, `FAIL`, or `BLOCKED` with evidence.
- Continue only on `PASS`; route `FAIL` or `BLOCKED` to the implementation owner or user as appropriate.
- Do not run QA directly or define browser, iOS, macOS, or non-UI verification steps in this wrapper.

### 8. PR Placeholder

- Placeholder only.
- Future work should define PR creation, review, and handoff workflow.
- Do not define PR review policy or merge-readiness logic in this wrapper.

---

## Artifact Contract

Allowed task artifacts:

- `{ISSUE_DIR}/issue.md`
- `{ISSUE_DIR}/plan.md`
- `{ISSUE_DIR}/research/*.md`

Do not create helper docs, reference files, sidecar state, ADR files, or wrapper-specific metadata unless this contract is intentionally revised later.

---

## Ownership Boundaries

| Artifact or decision                                 | Owner                              |
| ---------------------------------------------------- | ---------------------------------- |
| `{ISSUE_DIR}/issue.md` intake, scenarios, approaches | `gather-context`                   |
| `{ISSUE_DIR}/research/*.md` evidence reports         | `gather-context` research agents   |
| `Judge Decision` in `{ISSUE_DIR}/issue.md`           | `judge-proposal` fresh subagent    |
| `{ISSUE_DIR}/plan.md`                                | `create-issue` workflow            |
| `Plan Judge` in `{ISSUE_DIR}/plan.md`                | `judge-plan` fresh subagent        |
| Implementation code changes                          | Implementation subagents           |
| Code quality decision                                | `code-quality-gate` fresh subagent |
| Verification proof                                   | `verification-gate` fresh subagent |
| Pipeline order, gates, revision routing              | `issue-to-pr`                      |

When an artifact is missing or malformed, ask the owner to revise it. Do not fix it inside this wrapper.

---

## Delegation Rule

Judge, implementation, code quality, and verification work is delegated:

- Use `judge-proposal` for the proposal checkpoint.
- Use `judge-plan` for the plan checkpoint.
- Use implementation subagents for all write operations.
- Use `code-quality-gate` after implementation is complete.
- Use `verification-gate` after `APPROVE_CODE`.
- Do not reuse main-agent context for judge decisions, code quality decisions, or verification proof.
- Pass artifact paths and concise task framing only.
- Treat judge, code quality, and verification feedback as gates before continuing to the next phase.

---

## Revision Routing

- Missing `{ISSUE_DIR}/issue.md`, missing `{ISSUE_DIR}/research/*.md` files, or missing approaches: rerun or revise `gather-context`.
- `judge-proposal` returns `ASK_USER`: stop and ask its one focused question.
- Missing `{ISSUE_DIR}/plan.md`: rerun or revise `create-issue`.
- `judge-plan` returns `REVISE_PLAN`: route notes back to `create-issue` and request a revised `{ISSUE_DIR}/plan.md`.
- `judge-plan` returns `ASK_USER`: stop and ask its one focused question.
- `code-quality-gate` returns `REVISE_CODE`: route notes back to implementation subagent(s), revise implementation, and rerun `code-quality-gate`.
- `code-quality-gate` returns `ASK_USER`: stop and ask its focused question.
- `verification-gate` returns `FAIL` or `BLOCKED`: route evidence to the implementation owner or user; do not patch or verify directly here.
- Any unexpected state: stop with the artifact path, expected state, actual state, and owning stage.

---

## Constraints

- Keep this skill lean: orchestration only.
- Do not create, edit, append, or repair `{ISSUE_DIR}/issue.md`, `{ISSUE_DIR}/plan.md`, or `{ISSUE_DIR}/research/*.md` directly.
- Do not write implementation code directly; delegate write operations to implementation subagents.
- Do not create files or saved plans for ad hoc delegation; keep ad hoc delegation in memory/context only.
- Do not duplicate decision logic from `gather-context`, `create-issue`, judge skills, implementation skills, verification skills, or PR workflows.
- Do not define detailed implementation execution prompts.
- Do not perform code quality review directly or skip `code-quality-gate` before verification.
- Do not run QA directly or define web, mobile-web, iOS, macOS, or non-UI verification flows beyond `verification-gate` delegation.
- Do not define PR creation or review details beyond placeholders.
- Prefer artifact handoff over hidden state.
- Prefer modular delegation over bloating this wrapper.

## Output Check

The wrapper checks `create-issue` output against `{ISSUE_DIR}`. If `create-issue` writes the plan artifact anywhere other than `{ISSUE_DIR}/plan.md`, stop and route that as a `create-issue` output mismatch.
