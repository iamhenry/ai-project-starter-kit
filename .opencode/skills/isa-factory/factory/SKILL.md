---
name: isa-factory
description: Orchestrate Plan, Implement, Review, Accept, Close, and Repeat for one supplied authoritative ISA without creating duplicate planning or progress artifacts.
---

# ISA Factory

This is an orchestration-only wrapper. The supplied ISA is the sole
requirements, progress, and completion ledger. It activates Authoritative
Artifact Mode for this invocation and grants local implementation, commit, and
ledger authority within that ISA only. It never pushes, performs remote Git
actions, or performs destructive actions.

## Pipeline Components

| Component | Role |
| --- | --- |
| `isa-plan` | Selects one thin vertical slice and returns a transient locked packet. |
| `code` / `general` | Fresh bounded implementation agents for code or non-code capability work. |
| `code-quality-gate` | Fresh code review for slices that change files; invoked with explicit `mode: isa`. |
| `verification-gate` | Fresh runtime/product acceptance; invoked with explicit `mode: isa`. |
| `isa-close` | Validates PASS packets, commits the exact candidate, then updates ISA provenance/progress in a separate local commit. |
| `agent-browser` / `xcodebuildmcp-cli` | Capability routes selected by `verification-gate`; not run or defined here. |

## Available Capabilities

### Agents

| Agent | Use |
| --- | --- |
| `code` | Application implementation, tests, and code changes. |
| `general` | Docs, non-code artifacts, and other bounded utility changes. |

Use one fresh modifying agent by default. Do not fan out automatically; sequence
overlapping work.

### Subagents and Skills

`atlas` may be used by the owning phase for local research, and `voyager` only
for necessary external documentation. The factory delegates to `isa-plan`,
`code-quality-gate`, `verification-gate`, and `isa-close`; their references own
the detailed phase contracts. Fresh contexts are mandatory for Plan, Review,
Accept, and each correction.

## Input Contract

- Exactly one readable ISA path is required, supplied by the command; resolve
  `@file` before use. Never infer or substitute `_ai/docs/ISA.md`.
- Pass the resolved `isa_path` unchanged to every phase.
- The ISA must provide its own identity, open leaf criteria, exact probes and
  thresholds, evidence rules, and current progress. An ISA contradiction is a
  hard interrupt; do not repair it here.
- No `issue.md`, `plan.md`, research report, dashboard, sidecar status, or
  product-ISA implementation is an input or output.

## Pipeline

Repeat this ordered pipeline from the latest authoritative ISA state:

### 1. Plan

Invoke `isa-plan` with `isa_path`. Require a transient `LOCKED ISA SLICE`
packet. It must select one journey and 1-5 open leaves, preserve their exact
text/probes/thresholds, identify dependencies and routes, and state whether
implementation is required. A blocked packet routes to its declared blocker;
do not invent a preflight/probe phase or persist the packet.

### 1a. Prepare Execution Lane

Before Implement, the factory prepares only the environment capabilities
declared by the locked slice. Reuse a healthy existing lane when possible;
otherwise start the required runtime, service, simulator, database, or local
dependency using repository instructions, then run one minimal baseline smoke
check.

Separate the iterate lane from the close artifact. If the change lives only
in a layer a live-reload or incremental runtime can project (interpreted UI,
styles, scripts), prepare or reuse that lane and do not rebuild the shipped
binary to implement. Rebuild the native or packaged artifact when the change
cannot appear without it. Accept still uses the ISA-named shipped identity;
this lane is not proof.

This preparation proves only that implementation can execute; it does not run
ISA acceptance probes or prepare outcomes that depend on the new code. Keep the
result transient and hand the selected runtime, target, process, and subject
handles to downstream agents.

Implementation agents do not troubleshoot environment setup. If preparation
fails, allow one bounded recovery attempt owned by the factory. Then route a
separate environment blocker or choose another slice; do not delegate product
implementation into a broken lane.

### 2. Implement

For each capability in the packet, delegate one fresh bounded `code` or
`general` agent using the delegation contract. The factory owns the journey;
the agent owns only the assigned capability and evidence preparation. Do not
delegate implementation for `implementation_required: no`; preserve existing
behavior and proceed to gates. Agents may not edit the ISA, `JOURNAL.md`, or
close/credit leaves.

### 3. Review

If every selected capability has `implementation_required: no`, skip Implement
and Review. Freeze the immutable current committed candidate identity with an
empty declared path set and route directly to Accept using the explicit
no-implementation route. If any capability changes files, first classify the
post-implementation diff against the complete declared path set and baseline.
Any undeclared changed path blocks candidate freeze until reverted or explicitly
re-planned; see
`references/delegation-contract.md`. Then delegate a fresh
`code-quality-gate` with explicit `mode: isa`, the exact `isa_path`, immutable
locked slice, implementation summary, changed files/diff, checks, and frozen
candidate identity. On `APPROVE_CODE`, continue. On `REVISE_CODE`, allow one
correction by a fresh implementation agent, freeze a new identity, and rerun
review. On `ASK_USER`, interrupt only under the Human Interrupt rules.

### 4. Accept

Delegate a fresh `verification-gate` with explicit `mode: isa`, the same
immutable slice and complete candidate identity, either the matching
`APPROVE_CODE` result for an implementation slice or the explicit
no-implementation route, and all required runtime/build prerequisites. The
verifier owns runtime/product truth and returns an overall verdict plus a
complete in-context packet record for every leaf; each record carries every
Close-required field unchanged, including the complete candidate identity. The
factory only checks the contract, forwards the complete packet set unchanged,
and routes the result. No acceptance packet may credit or mutate the ISA.

### 5. Close

Invoke `isa-close` only after its eligibility contract is satisfied: one
independent `PASS` packet per target leaf, matched frozen candidate/build
identity, supplied `isa_path`, and explicit local commit authority. Forward the
complete packet set unchanged. `isa-close` alone owns candidate reuse/commit,
ledger credit, and the separate product/ledger commit; it must not push or use
destructive Git actions. See `isa-factory/close/references/verdict-contract.md`,
`isa-factory/factory/references/candidate-identity.md`, and
`isa-factory/close/references/ledger-update.md`.

### 6. Repeat

A blocked leaf is not a blocked factory. After Close or a park, reread the
supplied ISA. Re-check each parked leaf's unlock condition against current
ISA, JOURNAL, and runtime evidence; unpark and plan any leaf whose condition
is now met. Then select the next open leaf this lane can run without
irreversibly altering state a still-parked leaf's unlock depends on. Stop
when every remaining open leaf is closed or parked.

A same-class miss is the same leaf failing for the same reason class (for
example: required world-state missing or not ready, probe window missed,
environment unreadiness after a mutation, or a state the current system
cannot produce). A new input, URL, record, or retry of that class is not a
new class. On a second same-class miss: close any sibling PASS, park that
leaf with an exact unlock condition, and immediately plan different
startable work. Do not loop the same failed delegation.

## Canonical Phase Contracts

The factory owns phase order, ownership, routing, revision, and completion; it
does not restate phase schemas or mechanics. Keep the Plan packet transient and
immutable, carry candidate identity unchanged, and forward complete per-leaf
packets without credit or mutation. Canonical detail lives in
`isa-factory/plan/references/slice-contract.md`,
`isa-factory/factory/references/candidate-identity.md`,
`isa-factory/close/references/verdict-contract.md`,
`isa-factory/close/references/provenance.md`, and
`isa-factory/close/references/ledger-update.md`.

## Resume And Progress

Resume by rereading the supplied ISA, not chat history or agent summaries.
Transient slice, candidate, review, and acceptance packets are discarded after
the phase unless handed to the next phase. Progress means only the supplied
ISA's checkbox/progress movement performed by `isa-close`; activity, tests,
commits, and agent claims are not progress. Never create duplicate status.

After Close, a parked leaf, a completed subagent wave, or a hard blocker, emit
one compact chat progress card from the ISA's authoritative counts. Never write
it as a file. Never count activity, tests, commits, or agent claims as closed.

```md
Closed N/T · remaining R · next: [one startable leaf or slice]

| Lane | Criteria | Files | Agent |
| --- | --- | --- | --- |
| [A: short job] | [ISC ids] | [paths or —] | [owner or —] |
```

Show at most the current/next lanes. Mark parked leaves in Lane, not as closed.
Critical path: one line under the table.

## Artifact Contract

Allowed durable writes are the application files explicitly assigned by a
slice, plus the supplied ISA and `JOURNAL.md` during `isa-close`. The factory
creates no planning, report, progress, dashboard, status, or packet artifacts.
`isa-plan` packets and review/accept results remain transient unless the
invoked skill's contract requires a retained evidence path.

## Ownership Boundaries

| Decision or artifact | Owner |
| --- | --- |
| Slice choice, exact leaf contract, route | `isa-plan` |
| Assigned capability and implementation files | Fresh implementation agent |
| Code-quality decision | Fresh `code-quality-gate` |
| Runtime/product verdict and evidence | Fresh `verification-gate` |
| Candidate commit, ISA provenance/progress, JOURNAL entry | `isa-close` only |
| Journey, sequencing, gates, routing, resume | `isa-factory` |

The factory does not implement, review, verify, close, edit the ISA, or repair
phase-owned artifacts directly.

## Delegation Rules

Every modifying, review, acceptance, and close delegation must use the
orchestrator's mandatory task prompt template plus the transient
`references/delegation-contract.md`. Include only the current slice and the
minimum paths/evidence needed. Preserve Authority, Problem, Goal, Ideal State,
Current State, Boundaries, exact ISA Contract, role-specific Assignment,
Required Evidence, true Escalation, and the compact Return Contract. Do not add
duplicate status checkboxes. Capability belongs to the agent; journey and
phase routing remain with the factory.

## Revision Routing

- `isa-plan` blocked: route the concrete dependency, contract gap, or external authority need; interrupt only when permitted.
- Implementation failure: allow one correction with a fresh bounded agent; then narrow and re-plan.
- `REVISE_CODE`: one fresh implementation correction, new candidate identity, then rerun Review. A second review failure requires narrower re-plan.
- `ASK_USER`: interrupt only for a true human interrupt; otherwise return the concrete missing prerequisite to its owner.
- `FAIL`: route failing leaf evidence to the implementation owner, then narrow and re-plan; do not close.
- `BLOCKED` or identity `VOID/BLOCKED`: route the exact unblock condition or invalidate and re-plan; do not close.
- Close mismatch or missing authority: no ledger mutation; stop with exact path and reason.

When acceptance blockers repeat as the same class, close any valid PASS
leaves first, park that leaf, and re-plan toward other open startable work.
Do not repeat implementation and acceptance churn on the same class.

## Human Interrupts

Use `references/human-interrupts.md`; interrupt only at its true authority,
contradiction, safety, or destructive/remote-action boundary. Do not guess,
fabricate evidence, or widen scope.

## Constraints And Completion

- No preflight/probe phase, baseline/report artifact, automatic multi-agent fanout, or mandatory three-simulator policy.
- No duplicate ledger, issue, plan, dashboard, or product-ISA implementation.
- No remote, push, destructive, reset, amend, force, branch-delete, or unrelated Git action.
- One modifying agent by default; fresh agents per phase and correction.
- `done` means the current slice was validly closed by `isa-close`, or the whole supplied ISA is already complete. Otherwise return the concrete blocked/re-plan state.

## Output Check

Return the compact phase outcome and exact evidence paths/identities. Preserve
the invoked skill's verdict vocabulary. Do not present a summary as progress or
claim a leaf closed before `isa-close` returns success.
