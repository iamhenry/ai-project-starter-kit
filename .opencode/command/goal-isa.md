---
description: Execute an end-to-end product workflow from an authoritative ISA.md
agent: orchestrator
subtask: false
---

# Goal ISA

## Input contract

`$ARGUMENTS` must contain one ISA path or `@file` reference.

If `$ARGUMENTS` is empty, do NOT proceed. Ask the user for it:

> Please provide the path to the authoritative ISA.md file.
> Usage: `/goal-isa @_ai/docs/ISA.md` or `/goal-isa path/to/ISA.md`

Otherwise, treat the first supplied input as the source of truth: `<ISA_PATH>`.

Treat `<ISA_PATH>` as the source of truth.

Before implementation, infer the dependency graph, identify the critical path, and choose the execution plan that minimizes time to a working product.

Optimize for these objectives, in priority order:
1. Complete real end-to-end user journeys as thin vertical slices that a user can actually execute.
2. Minimize total completion time by maximizing useful concurrency through independent, low-collision execution lanes.
3. Delegate work in tight, manageable units. Each delegated task must have a bounded scope (a single verifiable user-facing slice or concrete capability) to prevent context drift and ensure high execution quality.
4. Minimize rework by introducing shared abstractions only when they are justified by multiple completed or imminent user journeys.
5. Keep the application integrated, runnable, and shippable after every completed milestone.
6. Verify outcomes through real end-to-end execution rather than implementation artifacts. Passing tests, compiled code, mock integrations, or completed components are evidence—not success. Success is a user successfully completing the intended journey.

Continuously re-evaluate the dependency graph, critical path, and execution lanes as new information emerges. Prefer adapting the plan over following an initially chosen architecture or implementation order.

---

If `JOURNAL.md` does not exist, create it.

Review relevant entries in `JOURNAL.md`. Give higher weight to more recent entries and to anything still clearly applicable to the current work.

Use judgment to ignore or treat as low-confidence information that appears outdated, resolved, superseded, or no longer relevant.

While working, if you hit any small friction—missed tool call, confusing setup, flaky command, stale cache, misleading error, non-obvious gotcha—immediately append a short entry:

```
### Papercut - [YYYY-MM-DD HH:MM]
what you were doing → what got in the way (optional cause/fix guess)

After finishing the task, append a concise summary:

## Task: [task name] - [YYYY-MM-DD HH:MM]
- Summary: [what you did]
- Key decisions: [list]
- New insights or blockers: [list]
- Connection to prior work: [brief note]
```

Keep every entry tight. If you notice something in the journal that is clearly no longer true, mark it [OUTDATED] or [RESOLVED].
