# Lean Issue-to-PR Handoffs

## Outcome

Reduce avoidable issue-to-PR handoff time while preserving every existing policy gate and each domain skill's standalone contract.

## Current Gap

`issue-to-pr` names owners and routes revisions, but it does not explicitly require concise path-and-delta handoffs, resuming the original owner for repairs, or mechanical pre/post ownership checks. This leaves room for repeated context, unnecessary rediscovery, and unprovable cross-stage writes.

## Scope

- Tune only `.agents/skills/issue-to-pr/SKILL.md` unless verification exposes a directly related defect.
- Keep stage order, gate independence, retry ceilings, publication authority, and domain skill procedures unchanged.
- Add no cross-skill packet protocol, shared mode, helper artifact, or broad skill-contract rewrite.

## Acceptance

- Initial handoffs pass authoritative artifact paths and only the concise framing needed to locate the next action and stop condition.
- Repair handoffs resume the original owner with the failed criterion, relevant evidence, and delta since its prior attempt.
- The wrapper checks pre/post repository changes against the dispatched owner's allowed write scope and blocks unexplained ownership violations.
- Missing owner-declared prerequisites are classified as `BLOCKED`, not converted into another verdict or repaired by the wrapper.
- Existing fresh judge, code-quality, and verification gates remain intact.
- The final diff is narrow and independently reviewed before publication.

## Verification

The consumer is the next orchestrator loading `issue-to-pr`. Verify that the final skill presents one unambiguous handoff/revision rule, preserves owner-local procedures, and contains no new wrapper-specific artifact or protocol.
