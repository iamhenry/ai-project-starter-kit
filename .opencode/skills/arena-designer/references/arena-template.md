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
| What to check | How to check | Good looks like | Cadence |
| --- | --- | --- | --- |
| [metric or state] | [API call / file read / command] | [threshold or direction] | [how often] |

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
[Write domain-specific steps. Do not copy generic observe-act-verify. Example for a content growth worker:]

1. Research trending content in the niche (formats, hooks, topics)
2. Create one piece of content based on highest-signal pattern
3. Publish through the configured channel
4. Wait for review cadence, then check engagement metrics
5. Score against baseline; keep the approach or discard
6. Record what worked, what didn't, and why
7. Repeat from step 1 with updated knowledge

[Replace the example above with the actual loop for this worker's domain.]

## Operating Principles
[Decision-making heuristics that guide the worker. Examples:]

- Change one variable at a time so you can attribute results
- Study what's already working before inventing from scratch
- Explore broadly when score is flat; exploit when score is improving
- [Add domain-specific judgment the worker needs to make good decisions]

## Memory
- Results log: [file/path/system]
- Best-known playbook: [file/path/system]
- Next cycle reads first: [file/path/system]

Each log entry should capture: `date | action taken | result | score delta | kept or discarded | reasoning`

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

## When Stuck
[What the worker should try before escalating. Examples:]

- If N consecutive attempts show no improvement, widen the search space
- Revisit assumptions about what the score is actually measuring
- Try a fundamentally different approach rather than incremental tweaks
- Review the experiment log for patterns in what failed

## Proof of Loop
- First cycle: [small bounded tracer bullet]
- Expected proof: [what success looks like]
```

Notes:

- Do not ship a worker with `missing` actions in the action-to-tool map.
- If the north star is slow, optimize a faster operational score that advances it.
