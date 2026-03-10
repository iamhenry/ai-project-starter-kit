# Worker Skill Template

Use this template when the readiness gate passes.

```md
---
name: [worker-slug]
description: [one-line mission]
version: [current version numnber]
---

# [Worker Name]

## Mission
- North star: [business outcome]
- Operational objective: [what this worker improves directly]
- Stop condition: [goal reached / blocked / explicit limit]

## Operational Score
- Primary score: [metric]
- Direction: [higher/lower is better]
- Review cadence: [hourly/daily/weekly]
- Leading indicators: [fast proxies]

## Verification Surface
- [source of truth 1]
- [source of truth 2]
- [source of truth 3]

## Environment

### Action-to-Tool Map
| Action | Tool / API | Access | Verification source |
| --- | --- | --- | --- |
| [observe / act / verify task] | [specific tool] | [ready/setup-needed/missing] | [where truth comes from] |

### Permissions
- [credential or integration]

### Off-limits
- [things the worker must never touch]

## Work Loop
1. Observe current state
2. Choose highest-leverage next action
3. Act within limits
4. Verify result against the score
5. Record learning and next hypothesis
6. Continue until stop condition or hard stop

## Memory
- Results log: [file/path/system]
- Best-known playbook: [file/path/system]
- Next cycle reads first: [file/path/system]

## Safety
- Hard stops: [unsafe actions]
- Budget limits: [spend/time/rate limits]
- Escalation triggers: [when to stop and flag]

## Closed Loop Test
- [ ] Can observe the relevant world state
- [ ] Can act on the environment
- [ ] Can verify whether the action helped
- [ ] Can record what happened for the next cycle
- [ ] Can continue autonomously without human judgment

## Proof of Loop
- First cycle: [small bounded tracer bullet]
- Expected proof: [what success looks like]
```

Notes:

- Do not ship a worker with `missing` actions in the action-to-tool map.
- If the north star is slow, optimize a faster operational score that advances it.
