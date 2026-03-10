---
name: loop-designer
description: Design a closed autonomous loop for a measurable goal. Use when the user wants to create an agentic loop, digital worker, autonomous operator, long-running agent, or SKILL.md that can observe act verify record and continue with minimal human intervention.
version: 1.1
---

# Loop Designer

Turn a goal into a closed-loop `SKILL.md` for an autonomous worker.

Keep it simple. Use heuristics, not rigid frameworks.

## Core principles

- Make the goal measurable
- Pick the fastest trustworthy feedback
- Map every required action to a specific tool
- Persist learnings between cycles
- Do not emit the worker skill until the loop is closed

## Closed Loop Test

The loop is only valid if the agent can:

1. **Observe** the relevant world state
2. **Act** on the environment
3. **Verify** whether the action helped
4. **Record** what happened for the next cycle
5. **Continue** autonomously without waiting on human judgment

Treat this as the acceptance criteria for the loop.

If any item fails, the result is `NOT READY`.

---

## When to use

Use this skill when the user wants to:

- create an autonomous agent or digital worker
- design an agentic loop around a business goal
- turn a fuzzy goal into a measurable worker mission
- create or refine a worker `SKILL.md`

Examples:

- "Design an ASO worker to grow iOS revenue to $10k MRR"
- "Create an autonomous content worker that grows downloads"
- "Turn this ops process into a closed loop"

## Outputs

Produce one of two outcomes:

1. `READY` -> write the worker `SKILL.md`
2. `NOT READY` -> list the exact blockers; do not write the worker skill yet

## Workflow

### 1) Mission intake

Restate the mission in one sentence:

- business outcome
- operational objective
- stopping condition

Separate the **north star** from the **operational score**.

Ask these anchor questions to ground the mission:

1. What can you measure today? (reveals available verification surface)
2. What tools and accounts do you already have? (reveals environment)
3. What's the fastest thing you could change and see a result? (reveals the tightest loop)

Example:

- North star: `$10k/month iOS revenue`
- Operational score: `weekly organic installs` or `content->store CTR`

### 2) Strict readiness gate

Check these five gates:

1. **Score** - Is there a measurable, verifiable score?
2. **Speed** - Is there a bounded review cadence for learning?
3. **Environment** - Is the action space clear and toolable?
4. **Failure cost** - Can bad iterations be contained or reverted?
5. **Traces** - Can the worker leave durable artifacts and learnings?

Rules:

- `READY` only if all five pass
- `NOT READY` if any gate is unresolved
- Resolve ambiguity before proceeding
- If the goal is too broad, derive a smaller operational objective that best advances the mission
- A goal is too broad if it requires more than one distinct observe-act-verify loop. Narrow to the single loop with the most signal or that unblocks other loops.

Do not use `needs work`. Use only `READY` or `NOT READY`.

### 3) Tool discovery and closure check

For each required action, discover the tool path using:

- the current environment and installed tools
- project skills and local integrations
- web research for suitable APIs, products, CLIs, MCPs, or services
- optional marketplaces or registries as examples, never as hard dependencies

Build an action-to-tool map. Every action must have:

- a specific tool or API
- access status: `ready` | `setup-needed` | `missing`
- a verification source

If any required action is `missing`, the loop is `NOT READY`.

### 4) Define the worker

Write the worker around these sections:

- Mission
- Operational Score
- Verification Surface
- Environment
- Work Loop
- Memory
- Safety
- Closed Loop Test

Keep the worker focused on heuristics and operating principles.
Do not over-specify tactics that the worker should discover through iteration.
When the score has components, define diagnostic combinations that tell the worker WHERE things are going wrong, not just that they're going wrong.

If the worker produces content, communicates with humans, or makes judgment calls that reflect a brand or perspective, also generate a `soul.md` using `references/soul-template.md`. If the worker is purely mechanical (data pipelines, code optimization, monitoring), skip the soul.

### 5) Proof of loop

Define one short first cycle that proves the loop works.

Example:

- observe baseline metrics
- make one bounded change
- verify the delta
- record the result

### 6) Refine mode

When refining an existing worker:

1. Read the current worker `SKILL.md`
2. Read the results or learnings file(s)
3. Check whether the worker is still closed
4. Tighten the score, tools, verification, or safety limits
5. Update the worker skill

Use `references/refine-checklist.md` when results are noisy or delayed.

---

## Output format

When `READY`, write a worker `SKILL.md` using `references/loop-template.md`.

When `NOT READY`, return:

```md
Status: NOT READY

Blockers:
- [missing score / missing tool / missing verification / unsafe failure mode / no durable traces]

Fastest path to ready:
1. ...
2. ...
3. ...
```

## Important heuristics

- Favor shorter feedback loops over perfect end metrics
- Use leading indicators when lagging business metrics are slow
- Long-running loops are fine; require a review cadence, not a 5-minute cycle
- Every irreversible or high-risk action needs a hard stop
- Ask: if the worker optimized ONLY this score, could it produce something you'd reject? If yes, add a constraint or secondary metric
- When the work loop has distinct stages with different tools, note per-stage failure handling — a failure at one stage should not force a restart from the beginning
- When tools have per-use costs, define the budget per cycle and per period — not just total budget
- When verification sources have different speeds, act on the fastest reliable signal and adjust strategy on the slower ones
- A human touchpoint that requires no judgment (e.g., tapping "post" to avoid bot detection) does not break closure — note it in the Work Loop as a manual relay step
- Identify platform-specific constraints that affect how the worker can act — some actions may need workarounds or manual relay steps
- If the worker consumes third-party content, data, or assets, treat them as constrained inputs: check availability, quota, legal/ethical limits, and what happens when they run out
- If a platform can silently penalize the worker (shadow ban, suppressed reach, rate throttle), define a detection signal — e.g. if score drops >X% for Y consecutive cycles, suspect platform penalty, pause, and escalate
- When the worker produces outputs in batches, score at the batch level after sufficient time for signal to stabilize — not per individual output

## Brief example

Mission: increase iOS revenue to `$10k/month` using ASO and social content.

Good loop shape:

- North star: monthly revenue
- Operational score: weekly installs, content CTR, app-store conversion
- Observe: Stripe, App Store analytics, social analytics, web research
- Act: create and post content, update metadata, test landing pages
- Verify: analytics APIs and attribution reports
- Record: experiment log and best-playbook file

If the worker cannot publish content or read analytics yet, it is `NOT READY`.
