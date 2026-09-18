# Lean Issue-to-PR Handoffs

## Outcome

Reduce avoidable issue-to-PR handoff time while preserving every existing policy gate and enough ticket evidence for a later session to continue without the original media.

## Current Gap

`issue-to-pr` names owners and routes revisions, but it does not explicitly require concise path-and-delta handoffs, resuming the original owner for repairs, or mechanical pre/post ownership checks. It also keeps current stage, candidate, retries, and next action only in conversation context, which compaction can lose. This leaves room for repeated context, unnecessary rediscovery, unprovable cross-stage writes, and unreliable resumption.

## Scope

- Tune `.agents/skills/issue-to-pr/SKILL.md` and `.agents/skills/create-ticket/SKILL.md` only.
- Keep stage order, gate independence, retry ceilings, publication authority, and domain skill procedures unchanged.
- Add no cross-skill packet protocol, shared mode, helper artifact, or broad skill-contract rewrite.
- Reuse this existing `ticket.md`; do not add another state file.

## Acceptance

- Initial handoffs pass authoritative artifact paths and only the concise framing needed to locate the next action and stop condition.
- Repair handoffs resume the original owner with the failed criterion, relevant evidence, and delta since its prior attempt.
- The wrapper checks pre/post repository changes against the dispatched owner's allowed write scope and blocks unexplained ownership violations.
- Missing owner-declared prerequisites are classified as `BLOCKED`, not converted into another verdict or repaired by the wrapper.
- The wrapper alone maintains bounded `Pipeline State` and `Checkpoint Timeline` sections in the existing `ticket.md`, before and after each dispatch.
- Durable state identifies the stage, exact candidate, latest checkpoint and receipt, next owner/action, allowed writes, retries consumed, and blocker or unlock condition.
- Timeline entries stay concise and link to owner evidence instead of copying domain conclusions; owner artifacts remain authoritative and fresh judges do not receive the timeline.
- Existing fresh judge, code-quality, and verification gates remain intact.
- Supplied image or video evidence remains attached or linked and is accompanied by concise, factual context needed by a later worker: relevant visible state, important text or annotations, dimensions or sequence when material, and what it demonstrates.
- Media descriptions omit irrelevant detail, personal data, and speculation, and state when the media could not be inspected.
- The final diff is narrow; the user will review it directly without subagent verification.

## Verification

The consumers are the next orchestrator loading `issue-to-pr` and the later worker reading a ticket created from supplied media. Confirm the final skills preserve unambiguous coordination state and enough factual media context without adding a new state file or general artifact-write permission.

## Pipeline State

- Stage: User review
- Exact candidate: base `4f425cb`; two-skill delivery diff SHA-256 `aed5accc1ca26ca88efaf5be5a7face6b17c0be2e527ef9eb22d3361e780e409`
- Latest checkpoint/receipt: Final Build correction completed; `git diff --check` and Ruby YAML frontmatter validation passed
- Next owner/action: User reviews the updated PR #113 directly
- Allowed writes: None; implementation is complete
- Retries consumed: Code revision 2 of 2; user explicitly authorized one final correction pass
- Blocker/unlock condition: None; user explicitly declined subagent verification and will review the PR directly

## Checkpoint Timeline

- Code quality attempt 1 — candidate `4f425cb` + delivery diff `ba91327f` — `REVISE_CODE` — failed criteria: deterministic ticket-to-`ISSUE_DIR` entry, durable chat-only verdict fields, candidate/baseline ordering, and conflict reconciliation — next: original Build owner repairs only those items.
- Build repair 1 — candidate `4f425cb` + delivery diff `e4a81a2d` — `COMPLETED` — corrected the four failed criteria in `.agents/skills/issue-to-pr/SKILL.md`; `git diff --check` passed — next: fresh code-quality re-review.
- Code quality attempt 2 — candidate `4f425cb` + delivery diff `e4a81a2d` — `REVISE_ARTIFACT`, `REVISE_CODE` 82/100 — `.agents/skills/issue-to-pr/SKILL.md:144` requires result fields some owners do not return and may lose exact repair instructions; line 146 does not explicitly name `issue-to-pr` as reconciliation actor — next: `EXHAUSTED` under the two-verdict ceiling.
- User decision — explicitly authorized one final correction pass limited to the two attempt-2 findings; acceptance gates remain required.
- User scope update — keep both related skill changes in PR #113; add the minimal durable media-description rule to `create-ticket`; do not use a verification subagent because the user will review directly.
- Final Build correction — candidate `4f425cb` + delivery diff `aed5accc` — `COMPLETED` — corrected owner-native timeline outcomes, named `issue-to-pr` as reconciliation actor, and added factual media descriptions to `create-ticket`; `git diff --check` and YAML frontmatter validation passed — next: commit, push, and direct user review.
