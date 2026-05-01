---
name: system-shaper
description: Shape a messy workflow or system into one simple reliable flow. Use when the user wants to design a process, reduce brittleness, define owners, choose one source of truth, or turn an idea into a minimal operating model.
---

# System Shaper

Use this skill to turn a vague or brittle workflow into a clear, reliable shape.

## Goal

Produce one simple flow with:
- a clear outcome
- named owners
- one source of truth
- explicit pass/fail rules
- a fail path
- clear separation between judging and acting
- a minimal build order

## How To Work

Ask only the smallest set of questions needed.

1. What outcome are we trying to cause?
2. What triggers the flow?
3. What are the exact steps in the one true flow?
4. Who owns each step?
5. Where does the real rule, verdict, and current state live?
6. Who judges pass/fail, and who changes status or state?
7. What makes the flow pass, fail, or retry?
8. What old path, duplicate state, or ambiguity should be removed?
9. What is out of scope?

If the user is vague, push for one concrete example.
If the design has multiple sources of truth, duplicated decision-makers, mixed judging/acting, or unclear ownership, call that out and simplify it.

## Output

Return this template every time:

```md
## Goal

## Why

## Inputs / Trigger

## One True Flow
1. ...
2. ...
3. ...

## Outputs / End State

## Owners

## Source of Truth

## Judge vs Act

## Pass / Fail Criteria

## Failure / Retry Path

## Side Jobs Kept Out of Core Path

## Out of Scope

## Risks

## Decision

## What To Deprecate

## Docs / Human Path To Update

## Minimal Build Order
1. ...
2. ...
3. ...
```

## Heuristics

- Prefer one flow over many branches.
- Prefer one owner per step.
- Prefer one place where rules live, one place where decisions happen, and one place where state changes.
- Separate judgment from movement.
- Prefer explicit failure handling over silent fallback.
- Keep notifications, cleanup, logging, indexing, and retries out of pass/fail logic.
- Deprecate old paths when a new path becomes canonical.
- Update docs and operator instructions when the path changes.
- Keep it practical; avoid abstract framework talk.
