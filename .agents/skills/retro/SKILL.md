---
name: retro
description: "Use only when the user explicitly asks for a retro or retrospective, or explicitly invokes or names `retro`, to learn from a completed or failed run. Never invoke automatically after work, failures, reviews, or other agent activity."
version: 1.0.4
---

# Retro

Use this skill only after the user explicitly requests it. It reviews one completed
or failed run involving a skill, command, prompt, agent, or workflow.

Identify the skill or workflow being reviewed. If a matching
`references/<skill-name>/README.md` exists, read it and follow its specific
guidance alongside the workflow below. Otherwise use this skill on its own.
Keep target-specific rules, tools and data inside that reference directory.
Helper outputs are evidence, not verdicts; inspect the underlying sources when
claims are uncertain or consequential. Disclose missing checks rather than
inventing results. The retro judge retains the final judgment.

## Guardrails

- Treat the target artifact as the source of truth. Do not create a universal
  ledger, shared protocol, or self-modifying feedback system.
- Read by default. A proposal remains read-only until the user explicitly
  authorizes editing.
- Never approve your own proposed change. Name the target owner and leave the
  normal review path intact.
- Redact secrets, credentials, and personal information from evidence and
  reports. Never reproduce them.
- If evidence is missing, the request is unsupported, or the change belongs to
  another owner or layer, say so instead of guessing or editing.

## Workflow

1. Identify the target, its intended outcome, the observed outcome, and the
   evidence for each. Separate facts from interpretation.
2. Compare expected with observed. Record both the useful behavior and the
   failure or friction, including when no failure occurred.
3. Classify the main cause as one or more of: `artifact_gap`,
   `execution_drift`, `input`, `environment`, `wrong_owner`, `one_off`, or
   `bloat`. Explain why the evidence supports the classification.
4. Run a counterfactual check: would the same change help another realistic
   case, or does it only fit this input, run, tool, or environment? Reject
   one-off fixes and changes unsupported by evidence.
5. Choose the smallest useful response, in this order: delete bloat, clarify
   an ambiguous instruction, move content to the correct artifact or owner,
   then add a rule only when the pattern is repeatable and the target owns it.
6. When proposing changes, summarize them in a prioritized file-by-file change
   map. Rank by impact and recurrence, keep each row to the smallest owning
   change, and describe the intended improvement rather than promising an
   unverified result.
7. Return exactly one verdict: `NO_CHANGE`, `PROPOSE_CHANGE`, or `BLOCKED`.
   Use `NO_CHANGE` when evidence does not support changing the reviewed
   artifact, including execution-only, one-off, or wrong-layer findings; still
   report useful observations and route to the owner when relevant. Use
   `PROPOSE_CHANGE` when evidence supports a generalizable improvement owned
   by the reviewed target. Use `BLOCKED` only when missing evidence or context
   prevents a diagnosis.

## Required report

After analysis, return this reusable final-response template:

```md
# Retro: <target>

## What Went Right

<What met the intent, reduced risk, or produced useful evidence. Write
"None observed" when applicable.>

## What Went Wrong

<State the gap between intent and observation. Write "None observed" when
applicable. Do not invent a failure.>

## What Could Be Improved

<List evidence-backed improvements only. Distinguish a proposed target change
from a change that cannot be made.>

<When proposing changes, include this table. Otherwise write "No change
proposed.">

| Priority | File | Before | After | Intended improvement |
| --- | --- | --- | --- | --- |
| <rank> | <owning artifact path> | <current behavior> | <smallest proposed change> | <expected benefit> |

## Diagnosis

- Target and artifact type: <skill, command, prompt, agent, or workflow>
- Expected: <intended outcome>
- Observed: <actual outcome>
- Evidence: <facts supporting the diagnosis>
- Cause class: <artifact_gap, execution_drift, input, environment, wrong_owner, one_off, or bloat>
- Counterfactual/generalization check: <would this help another realistic case?>

## Decision

- Verdict: `NO_CHANGE`, `PROPOSE_CHANGE`, or `BLOCKED`
- Rationale: <why this verdict applies>
- Target owner and artifact: <owner and reviewed artifact>
- Proposed change, if any: <smallest supported change>
- Approval status: read-only unless the user explicitly authorized an edit.
```
