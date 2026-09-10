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

Orchestrate and judge the pipeline. Do not create, edit, append, or repair task artifacts directly.

This skill connects modular skills, checks whether each stage produced the expected artifact, and routes revisions back to the owning skill or subagent when the pipeline is off track.

Use this composition for authorized delivery; focused research, planning, review, or verification calls remain valid and stop at their requested endpoint. Supply scope, authority, and optionally S/M/L/XL with a risk/uncertainty rationale. Each owner calibrates its own inputs, execution, effort, independence, evidence, recovery, and completion; size is not a stage-skip rule. A tiny delivery still passes applicable intake, selection, plan, implementation, fresh quality, and fresh acceptance responsibilities, which may share one fresh session only under the SMALL combined-gate rule. Do not reproduce owners' operating procedures here or grant publication beyond user authority.

---

## Pipeline

`ISSUE_DIR` is created by `gather-context` using `_ai/task/{YYYY-MM-DD}/{slug}`. All pipeline artifacts are relative to `ISSUE_DIR`.

Use existing `issue.md`, `plan.md`, and stage reports rather than restarting intake. Explicit user changes take precedence: route reconciliation to the artifact owner and request the owners' assessment of affected evidence and required rechecks. Preserve sound unrelated evidence; coupled, uncertain, or consequential changes may justify broader fresh assurance, not an automatic whole-pipeline restart. Before dispatch, check the owner's declared inputs; repair pipeline-owned gaps through their owners, not by asking the user to author documents. Ask only for missing intent or permission. Allow one narrow repair per underlying prerequisite or receipt gap, within existing stricter limits; if it remains unresolved, stop with the owner and unlock condition. Renaming a gap or redispatching never resets a budget.

### 1. Gather Context And Intake

- Run `gather-context` with the raw user issue/request in **intake-only** mode. Before research, require `{ISSUE_DIR}/issue.md` with the task classification and a sufficiently clear reported behavior or requested outcome; unresolved intake questions return to their owner under Revision Routing.
- For `bug` tasks, invoke `reproduce-bug` at this boundary, before research, proposal selection, or planning. Continue only on `REPRODUCED` with evidence matching the reported entry point; a mocked or different-path reproduction does not satisfy this gate. On `NOT_REPRODUCED` or `BLOCKED`, stop and report its structured result and next action. Safe, bounded prerequisite investigation may resolve a blocker, but does not authorize production edits or bypass reproduction. Reuse valid existing faithful evidence through the reproduction owner rather than requiring another run.
- For non-bug tasks, skip reproduction. Resume `gather-context` at Phase 1 in the same `ISSUE_DIR`, passing the reproduction result and evidence paths for bugs so research and proposals are grounded in observations. Reproduction establishes the symptom, not the cause; research investigates the cause, and the causal gate before implementation still applies.
- Let `gather-context` choose investigation depth and applicable evidence locations under its own contract; do not prescribe a research fan-out or option count.
- Gate: its declared intake, evidence, and supported approaches are present in the existing `ISSUE_DIR`.
- If the gate fails, route revision back to `gather-context`; do not patch artifacts here.

### 2. Proposal Judge Checkpoint

- Delegate review to a fresh subagent using `judge-proposal`.
- The subagent must receive only the task artifacts it needs, not accumulated conversation context.
- Pass selection authority explicitly; the proposal owner must not infer permission to choose for the user.
- Gate: `{ISSUE_DIR}/issue.md` contains `Judge Decision` with `Status: SELECTED` or `Status: ASK_USER`.
- If `ASK_USER`, use Revision Routing to distinguish an owned artifact gap from a user decision.

### 3. Create Issue Plan

- Invoke the tracked `create-issue` owner at `.agents/commands/workflow/01-plan/02-create-issue.md` after selection, passing the existing `ISSUE_DIR` and approved artifacts. It owns plan structure and proportional detail.
- Gate: its declared output `{ISSUE_DIR}/plan.md` exists.
- If the plan artifact appears elsewhere or `{ISSUE_DIR}/plan.md` is missing, stop and route as a `create-issue` output mismatch; do not create `{ISSUE_DIR}/plan.md` here.

### 4. Plan Judge Checkpoint

- Delegate review to a fresh subagent using `judge-plan`.
- The subagent must receive only `{ISSUE_DIR}/issue.md`, `{ISSUE_DIR}/plan.md`, and relevant `{ISSUE_DIR}/research/*.md` artifacts.
- The review must be independent from the proposal judge and main-agent working context.
- Gate: `{ISSUE_DIR}/plan.md` contains `Plan Judge` with `APPROVE_PLAN`, `REVISE_PLAN`, or `ASK_USER`.
- Continue only on `APPROVE_PLAN`; route `REVISE_PLAN` to `create-issue` and handle `ASK_USER` through Revision Routing.

### 5. Implementation Orchestration

- For `bug` tasks, require the earlier `REPRODUCED` result and an evidence-backed causal explanation that distinguishes the proposed cause from competing explanations before dispatching implementation — suspicion about code alone is not enough. Pass the reproduction result and evidence paths to implementation subagent(s); do not rerun reproduction merely because the plan is approved, duplicate its SOP, or write reproduction details into `plan.md`. If the reported entry point or relevant conditions changed, route affected evidence back to the reproduction owner before proceeding.
- When the causal explanation is not obvious from the reproduction result, route one bounded diagnostic step before implementation: one hypothesis, one smallest discriminating probe that is safe to run without production edits, its observation, then the next action (proceed, or one focused question to the owner). "Obvious" means existing reproduction observations already discriminate the proposed cause from competing explanations; if they do not, run the diagnostic step. Diagnostic probes may be delegated as read/safe work even though causal evidence is still required before any production edit.
- If the reproduction observations do not discriminate the cause and a probe needs more visibility, the implementation owner may add minimal temporary instrumentation, but only inside a safe, authorized, disposable diagnostic context (branch, sandbox, or explicitly approved run): prefer existing logs first; instrument only at the uncertain boundary, recording the relevant inputs, the decision it enables, its output, and a correlation marker only when needed; count injected inputs, retries, external calls, and side effects as real cost and weigh them before adding it; never log secrets, personal data, or full prompt bodies. This never authorizes an evidence-backed production fix before the causal gate above; instrumentation for diagnosis must be removed or handed to implementation with a removal requirement.
- Do not implement directly from this wrapper.
- Always delegate write operations to implementation subagents.
- Delegate relevant read or research operations when needed.
- If `{ISSUE_DIR}/plan.md` has a clear, safe delegation structure, follow it.
- If `{ISSUE_DIR}/plan.md` lacks safe delegation structure, create an ad hoc delegation todo list in memory/context only and delegate safely.
- Do not save a new plan to disk or revise `{ISSUE_DIR}/plan.md` just to add delegation structure.
- Avoid overlapping file edits; when overlap exists, sequence agents instead of parallelizing them.
- Collect the implementation summary, changed files, commands run, known risks, and raw Mechanical command output from implementation subagents.
- For bug tasks, also pass the reproduction result and evidence paths (including the reproduction smoke steps) to verification so it can reuse the same faithful smoke for the before/after proof.

### 6. Code Quality Gate

- After implementation is complete, delegate review to a fresh subagent using `code-quality-gate`.
- Pass the inputs declared by `code-quality-gate`, including exact candidate identity and available receipts.
- Gate: `code-quality-gate` returns `APPROVE_CODE`, `REVISE_CODE`, or `ASK_USER` with concise evidence.
- Continue to verification only on `APPROVE_CODE`.
- On `REVISE_CODE`, route the gate's classified findings and requested rechecks to their owners. Enforce its declared verdict ceiling across dispatches, separate from verification failures.
- If `ASK_USER`, repair a pipeline-owned missing input under the prerequisite rule above; otherwise stop and ask the focused question.
- Do not review or patch code directly from this wrapper.

### 7. Verification Gate

- After `code-quality-gate` returns `APPROVE_CODE`, delegate verification to a fresh subagent using `verification-gate`.
- Pass the inputs declared by `verification-gate`, including the current candidate and bug reproduction evidence where applicable. It owns the shortest credible proof route and prerequisite recovery.
- Gate: `verification-gate` returns `PASS`, `FAIL`, or `BLOCKED` with evidence on disk at `{ISSUE_DIR}/verification/result.md`.
- Before treating the work as PR-ready, confirm the cited evidence is accessible (embedded or linked, paths resolve) and each artifact is labeled before/after where the claim depends on a state change, with stated limits. Evidence that does not open or does not support the claim is not PR-ready.
- After it returns, run only a file-existence check: `test -f` on `{ISSUE_DIR}/verification/result.md` and every cited evidence path. Missing file = `FAIL`. This is not QA.
- Continue only on `PASS` when every `test -f` succeeds. A `PASS` paragraph with missing files is `FAIL`.
- On `FAIL` or `BLOCKED`, route the verification owner's classified outcome and requested rechecks; enforce its declared ceiling across dispatches. Source corrections require fresh code-quality approval before acceptance. Do not redispatch against an unchanged blocker or add unrelated edits for a proof gap.
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
- `{ISSUE_DIR}/verification/` (`result.md`, `screenshots/`, `videos/`) owned by `verification-gate`

Do not create helper docs, reference files, sidecar state, ADR files, or wrapper-specific metadata. The wrapper must not write `{ISSUE_DIR}/verification/`; it only checks cited paths exist.

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
| `{ISSUE_DIR}/verification/`                          | `verification-gate` fresh subagent |
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

Before any correction, compare the failed criterion with prior findings: what changed, and why would this repair resolve the underlying failure? A rejection is not automatic permission for more code. Reconsider recurring failures before the cap; if no supported repair remains, stop with the evidence and decision needed. Never use exhaustion to waive safety or independent acceptance.

- Missing `gather-context`-declared intake, cited evidence, or approaches: route repair to `gather-context`; compact inline research is not a missing report.
- `judge-proposal` returns `ASK_USER`: route pipeline-owned gaps to `gather-context` within the prerequisite bound; ask the user only for the remaining decision.
- Missing `{ISSUE_DIR}/plan.md`: rerun or revise `create-issue`.
- `judge-plan` returns `REVISE_PLAN`: route notes back to `create-issue` and request a revised `{ISSUE_DIR}/plan.md`.
- `judge-plan` returns `ASK_USER`: route pipeline-owned gaps to their artifact owners within the prerequisite bound; ask the user only for the remaining decision.
- `code-quality-gate` returns `REVISE_CODE` or `ASK_USER`: use step 6's classified routing and unchanged verdict ceiling.
- `verification-gate` returns `FAIL` or `BLOCKED`: use step 7's classified routing and unchanged verdict ceiling. A blocked gate does not restart itself; its owner may repair the prerequisite within the existing bound before a new dispatch.
- `verification-gate` returns `PASS` but `test -f` fails on `result.md` or a cited path: treat as `FAIL`.
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
- Do not run QA directly or define web, mobile-web, iOS, macOS, or non-UI verification flows beyond `verification-gate` delegation. The wrapper may run `test -f` on cited verification paths only.
- Do not define PR creation or review details beyond placeholders.
- Prefer artifact handoff over hidden state.
- Prefer modular delegation over bloating this wrapper.

## Output Check

The wrapper checks `create-issue` output against `{ISSUE_DIR}`. If `create-issue` writes the plan artifact anywhere other than `{ISSUE_DIR}/plan.md`, stop and route that as a `create-issue` output mismatch.
