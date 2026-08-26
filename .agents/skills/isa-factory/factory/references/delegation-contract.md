# ISA Factory Delegation Contract

Use this as transient context inside the orchestrator's mandatory delegation
prompt. Do not create a second prompt format or status checklist.

```text
AUTHORITY
- The caller explicitly activates Authoritative Artifact Mode for [isa_path].
- The supplied ISA is the only requirements/progress ledger.
- Authority is limited to the assigned slice and local actions; never remote or destructive.

PROBLEM
- [User-observable problem from the exact locked slice]

GOAL
- [One journey and exact leaf outcome this role must advance]

IDEAL STATE
- [Relevant exact ISA contract, probe, and threshold]

CURRENT STATE
- [Evidence-backed code, runtime, Git, JOURNAL, and open-leaf state]

BOUNDARIES
- [Assigned paths/capability only]
- Declared path set and baseline: [complete product/config path set and
  pre-task content identity]
- Protected pre-existing work: [paths, content digests, and staged/ignored
  state that this assignment must leave unchanged]
- Collision surface: [shared paths/modules, mutable runtime/data, execution
  subjects, build outputs, and verification side effects]
- Do not edit the ISA or JOURNAL, claim PASS, or own journey routing.
- [Role-specific exclusions]

EXACT ISA CONTRACT
- ISA: [isa_path]
- Slice: [slice_id]
- Leaves: [IDs, exact wording, exact probes, exact thresholds]
- Route and implementation-required flag: [per leaf]

ASSIGNMENT
- Role: [implementation | review | acceptance | close]
- [One bounded outcome, dependencies, and non-overlap boundary]

REQUIRED EVIDENCE
- [Changed paths/diff, checks, source identity, acceptance identity, and/or
  per-leaf proof required by the owning skill]
- Post-task diff classification: [every changed path declared or undeclared;
  product/config/behavior impact and disposition for each path]
- Unchanged protected work is not contamination. Unexpected mutation or a new
  path that changes candidate behavior blocks freeze. An adjacent path needed
  by the same capability may be added before freeze when ownership remains
  clear and no active lane collides; re-plan only when journey intent,
  capability boundary, or relevant dependency assumptions change.
- Classify tool metadata by effect. Ignore it when it cannot affect the
  candidate or probe; otherwise declare and trace it.

TRUE ESCALATION
- Escalate only contradictory ISA text, unavailable external authority/access,
  unsafe ambiguity, or destructive/remote action. Otherwise return the blocker
  and its unblock condition.

RETURN CONTRACT
- Return only the owning skill's decision/result, exact evidence paths,
  identity fields, blockers, trade-off, collision status, and next action in a
  compact packet for the factory's existing progress card.
```
