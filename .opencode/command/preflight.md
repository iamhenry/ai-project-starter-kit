---
name: preflight
description: Draft gherkin scenarios + pseudocode plan before implementing
---

Before writing any code, produce a preflight plan for the current task.

## Rules
- DO NOT edit any files yet. This is planning only.
- When implementation begins: touch only what is scope.

## Step 1 — Gherkin Scenarios
Write as many scenarios as the task requires. Each gets exactly 1–2 acceptance criteria.

```
Scenario: [name]
  Given [context]
  When [action]
  Then [outcome]
AC:
- [criterion]
- [criterion 2 if needed]
```

## Step 2 — Pseudocode Plan
Plain-english steps only. No real code syntax.
Flag unknowns as [ASSUMPTION: ...].
