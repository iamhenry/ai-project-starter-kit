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

Maximize useful concurrency with fresh agents whose assignments are bounded to
one verifiable vertical slice or concrete capability. Fan out when collision
risk is low; sequence shared paths, mutable state, subjects, outputs, or
authority-sensitive writes rather than maximizing agent count for its own sake.

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

When more independent work is startable, fill a concurrent wave with additional
fresh Plan invocations. Pass active leaf, path, dependency, runtime/data,
subject, output, and verification-side-effect reservations as transient
coordination context so no leaf or mutable surface gets two owners. Stop adding
lanes when collision or integration cost would outweigh useful concurrency.

### 1a. Prepare Execution Lane

Before Implement, prepare only the capabilities declared by each locked slice.
Prefer the least costly healthy, traceable environment that can run the work.
Reuse it when the change remains within its refresh boundary: the changes it
can load without reprovisioning while still being attributable to the
candidate. Rebuild or reprovision only when the change crosses that boundary,
the exact probe requires a stronger artifact class, or environment health or
candidate attribution cannot be established.

Separate iteration convenience from acceptance strength. The exact ISA
criterion and probe choose the evidence class; a fresh agent or generic phase
name does not imply a fresh build. Work from the authoritative project tree or
a proven-complete content-addressed materialization, never an ad hoc filtered
mirror whose required inputs may be absent.

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
`general` agent using the delegation contract. Run low-collision assignments
concurrently and sequence a shared enabling capability before its dependents.
Introduce shared structure only when at least two selected or imminent journeys
need it; otherwise prefer the local change.
The factory owns the journey;
the agent owns only the assigned capability and evidence preparation. Do not
delegate implementation for `implementation_required: no`; preserve existing
behavior and proceed to gates. Agents may not edit the ISA, `JOURNAL.md`, or
close/credit leaves.

### 3. Review

If every selected capability has `implementation_required: no`, skip Implement
and Review. Freeze the immutable current committed source identity with an
empty declared path set and route directly to Accept using the explicit
no-implementation route. If any capability changes files, classify the diff
against its declared paths and content-aware baseline. Unchanged protected
work is allowed; unexpected mutation or behavior-affecting undeclared content
blocks freeze. See `references/delegation-contract.md`.

Freeze a source identity for each lane and delegate fresh `code-quality-gate`
reviews concurrently with explicit `mode: isa`, the exact `isa_path`, immutable
locked slice, implementation summary, changed files/diff, checks, and source
identity. Build/runtime identity is not required for Review. On
`APPROVE_CODE`, integrate approved lanes into one immutable content-identified
candidate. If integration changes reviewed content or a relevant dependency
assumption, rerun Review only for affected lanes. On `REVISE_CODE`, allow one
correction by a fresh implementation agent, freeze a new source identity, and
rerun review. On `ASK_USER`, interrupt only under the Human Interrupt rules.

### 4. Accept

Delegate a fresh `verification-gate` with explicit `mode: isa`, the same
immutable slice, reviewed source identity, extended integrated/build/runtime
identity, either the matching `APPROVE_CODE` result for an implementation slice
or the explicit no-implementation route, and all required prerequisites.
Produce each required artifact once per integrated candidate and verify
independent journeys concurrently when subjects and mutable state cannot
interfere. One real end-to-end execution is the default; add up to two more
perspectives only when each addresses a distinct named risk. The verifier owns
runtime/product truth and returns an overall verdict plus a
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

Serialize integrated candidate and authoritative ledger writes. A parked or
non-PASS probe cannot close. Close valid siblings only when removing or
correcting another lane does not change their accepted integrated candidate;
otherwise rerun only materially affected evidence.

A completed wave leaves one integrated runnable candidate. A lane with parked
proof remains open and is not presented as a completed milestone.

### 6. Repeat

A blocked leaf is not a blocked factory. After Close or a park, reread the
supplied ISA. Re-check each parked leaf's unlock condition against current
ISA, JOURNAL, and runtime evidence; unpark and plan any leaf whose condition
is now met. Then select the next open leaf this lane can run without
irreversibly altering state a still-parked leaf's unlock depends on. Stop
when every remaining open leaf is closed or parked.

An environment, tooling, or external-availability miss parks the dependent
acceptance probe, not reviewed implementation. Keep that work intact and
continue non-overlapping lanes. Re-plan only when journey intent, selected
leaves, capability boundaries, or relevant dependency assumptions change;
unrelated commits, protected work, or a renewed runtime handle are not enough.

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
immutable, grow candidate identity only through its canonical source and
acceptance stages, and forward complete per-leaf packets without credit or
mutation. Canonical detail lives in
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

After each completed delegated task, Close, park, or hard blocker, emit one
compact chat progress card from the ISA's authoritative counts. Batch agents
that finish together into one card. Never write it as a file or count activity,
tests, commits, or agent claims as closed.

```md
Closed N/T · remaining R · next: [one startable leaf or slice]

| Lane | State/outcome | Criteria | Evidence/trade-off | Collision/next |
| --- | --- | --- | --- | --- |
| [A: short job] | [active/completed/blocked] | [ISC ids] | [proof or blocker; choice made] | [none or exact edge; next] |
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
- Implementation failure: allow one correction with a fresh bounded agent;
  narrow or re-plan only when the slice boundary or relevant assumptions changed.
- `REVISE_CODE`: one fresh implementation correction, new candidate identity, then rerun Review. A second review failure requires narrower re-plan.
- `ASK_USER`: interrupt only for a true human interrupt; otherwise return the concrete missing prerequisite to its owner.
- `FAIL`: route failing leaf evidence to the implementation owner; correct the
  same slice when its contract still holds, and re-plan only when its boundary
  or relevant assumptions changed. Do not close.
- `BLOCKED`: park the probe with its exact unblock condition, preserve reviewed
  implementation, and continue independent work. Do not close.
- Identity `VOID/BLOCKED`: invalidate only the affected evidence/candidate,
  restore traceability, and rerun the affected gate; re-plan only when the slice
  contract or relevant assumptions changed.
- Close mismatch or missing authority: no ledger mutation; stop with exact path and reason.

When acceptance blockers repeat as the same class, close any valid PASS
leaves first, park that leaf, and re-plan toward other open startable work.
Do not repeat implementation and acceptance churn on the same class.

## Human Interrupts

Use `references/human-interrupts.md`; interrupt only at its true authority,
contradiction, safety, or destructive/remote-action boundary. Do not guess,
fabricate evidence, or widen scope.

## Constraints And Completion

- No preflight/probe phase, baseline/report artifact, indiscriminate agent
  fanout, or mandatory proof-count policy.
- No duplicate ledger, issue, plan, dashboard, or product-ISA implementation.
- No remote, push, destructive, reset, amend, force, branch-delete, or unrelated Git action.
- Use as many bounded low-collision lanes as are useful; keep fresh agents per
  phase and correction, and serialize true contention.
- `done` means the current slice was validly closed by `isa-close`, or the whole supplied ISA is already complete. Otherwise return the concrete blocked/re-plan state.

## Output Check

Return the compact phase outcome and exact evidence paths/identities. Preserve
the invoked skill's verdict vocabulary. Do not present a summary as progress or
claim a leaf closed before `isa-close` returns success.
