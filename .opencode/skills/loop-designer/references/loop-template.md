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
| Action | Tool / API | Access | Checkpoint | Verification source |
| --- | --- | --- | --- | --- |
| [observe / act / verify task] | [specific tool] | [ready/setup-needed/missing] | [autonomous/human-relay/human-approval] | [where truth comes from] |

### Permissions
- [credential or integration]

### Off-limits
- [things the worker must never touch]

### Inputs
[Third-party content, data sources, or assets this worker consumes. For each:]
| Input | Source | Quota / Limit | Legal constraint | If exhausted |
| --- | --- | --- | --- | --- |
| [e.g. hook videos] | [e.g. YouTube scraper] | [e.g. 10/day] | [e.g. grey zone — fair use] | [e.g. pause, find new creator] |

## On Start
[What the worker reads FIRST when starting a new cycle or fresh session.]

1. Read the results log to understand current state
2. Read the best-known playbook for working strategy
3. Check the latest score against the baseline
4. Resume from the last recorded next-hypothesis

## Operating Principles
[Decision-making heuristics that guide the worker. Examples:]

- Change one variable at a time so you can attribute results
- Study what's already working before inventing from scratch
- Explore broadly when score is flat; exploit when score is improving
- [Add domain-specific judgment the worker needs to make good decisions]
- [What this worker should NEVER do — anti-patterns learned from failure]

## Work Loop
[Write domain-specific steps. Do not copy generic observe-act-verify. Example:]

1. Check current metrics against baseline
2. Identify the highest-leverage action based on learnings so far
3. Execute the action using the mapped tools
4. Wait for review cadence, then verify the result
5. Score against baseline; keep the approach or discard
6. Record what worked, what didn't, and why
7. Repeat from step 1 with updated knowledge

[Replace the example above with the actual loop for this worker's domain.]

## When Stuck
[What the worker should try before escalating. Examples:]

- If N consecutive attempts show no improvement, widen the search space
- Revisit assumptions about what the score is actually measuring
- Try a fundamentally different approach rather than incremental tweaks
- Review the experiment log for patterns in what failed

## Memory
- Results log: [file/path/system]
- Best-known playbook: [file/path/system]
- Next cycle reads first: [file/path/system]

Each log entry is one JSON object per line (JSONL). At minimum:

```jsonl
{"id": "cycle-001", "date": "...", "action": "...", "result": "...", "score_delta": 0.0, "status": "keep|discard|fail", "reasoning": "..."}
```

Extend with domain-specific fields as needed (e.g., `module`, `test_time_ms`, `views`, `conversions`).

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
- Bump the version when refining the worker so results can be attributed to the version that produced them.
