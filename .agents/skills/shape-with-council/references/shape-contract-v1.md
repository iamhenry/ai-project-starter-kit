# Shape Contract v1

Build this structure internally, then render it with the headings below. Every field is required. Use `None` or an empty list when a field does not apply.

```yaml
shape_contract:
  version: 1
  task:
    title: string
    original_request: string
  routing:
    depth_requested: low | medium | high | inferred
    depth_used: low | medium | high
    depth_reason: string
    research_level: local | targeted_external | broad_external
    research_reason: string
    council_mode: low | medium
    panel_models: [provider/model]
    judge_model: provider/model
    critic_model: provider/model | None
  problem:
    current: string
    ideal: string
    in_scope: [string]
    out_of_scope: [string]
  project_context:
    isa_path: string | None
    ethos_status: loaded | missing_proceeding | missing_blocked
    vision_status: loaded | missing_proceeding | missing_blocked
    local_evidence:
      - citation: path:line
        supports: string
    external_evidence:
      - citation: URL
        version_or_commit: string
        retrieved: YYYY-MM-DD
        supports: string
    evidence_conflicts: [string]
  clarification:
    questions:
      - question: string
        answer: string
    assumptions: [string]
    unresolved_blockers: [string]
  decision:
    recommendation: string
    confidence: string
    strongest_points: [string]
    disagreements: [string]
    flaws_and_risks: [string]
    minimal_correction: string
    change_my_mind_evidence: string
    critic_objection: string | None
    critic_correction: string | None
  behavior:
    outcomes: [string]
    states: [string]
    interactions: [string]
    transitions:
      - from: string
        action: string
        to: string
    failures:
      - condition: string
        user_observable_result: string
        recovery: string
    accessibility: [string]
    edge_cases: [string]
  solution_shape:
    existing_or_new_surface: existing | new | mixed
    selected_shape: string
    smallest_reversible_change: string
    reuse: [string]
    affected_surfaces: [string]
    dependencies: [string]
    dependents: [string]
    blast_radius: [string]
    rollback: string
    deferred_work: [string]
  acceptance_criteria:
    - id: AC-1
      claim: string
      probe: string
      expected: string
      falsifier: string
  anti_criteria:
    - id: ANTI-1
      claim: string
      probe: string
      falsifier: string
  isa_update:
    operation: create | patch | none
    target: string | None
    affected_sections: [string]
    reused_claim_ids: [string]
    new_claim_ids: [string]
    proposed_claims:
      - id: string
        text: string
        probe: string
    decision_entry: string
  readiness:
    status: needs_input | ready_for_review | approved
    blockers: [string]
    next_step: string
```

## Task

Include title and the original request verbatim.

## Routing

Show deliberation depth and research level separately, with reasons and actual model IDs. `high` always records Council mode `medium` plus a critic model.

## Problem

Use neutral Current, Ideal, In scope, and Out of scope statements.

## Project context and evidence

List each local and external citation beside the exact claim it supports. Do not list sources that did not affect the contract.

## Clarification

Record questions, answers, disclosed assumptions, and unresolved blockers.

## Decision

Preserve the judge's recommendation, strongest evidence, disagreements, risks, minimal correction, and change-my-mind evidence. For high depth, include the critic's strongest objection and the revision it caused.

## Behavior

Describe user outcomes, visible states, interactions, transitions, failures and recovery, accessibility, and edge cases. Avoid implementation detail unless it changes observable behavior.

## Solution shape

Name what is reused, what changes, dependencies in both directions, blast radius, rollback, and deferred work. Prefer the smallest reversible shape that satisfies every criterion.

## Acceptance criteria and anti-criteria

Every criterion is binary and has one concrete probe, expected result, and falsifier. Anti-criteria protect adjacent behavior and explicit non-goals.

## ISA update

Describe the exact patch without applying it. Reuse stable claim IDs where semantics match; allocate new IDs only after inspecting the canonical ISA.

## Readiness

Use `needs_input` when a material uncertainty remains, `ready_for_review` before human approval, and `approved` only after the user explicitly approves the rendered contract.
