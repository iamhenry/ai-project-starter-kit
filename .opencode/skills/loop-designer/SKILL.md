---
name: loop-designer
description: Design a closed autonomous loop for a measurable goal. Use when the user wants to create an agentic loop, digital worker, autonomous operator, long-running agent, or SKILL.md that can observe act verify record and continue with minimal human intervention.
version: 1.5
---

# Loop Designer

Turn a goal into a closed-loop `SKILL.md` for an autonomous worker.

Keep it simple. Use heuristics, not rigid frameworks.

## Purpose

This skill takes a fuzzy goal and produces a deployable worker `SKILL.md`. You describe the business outcome. The loop-designer interviews you, checks readiness, maps tools, and produces a self-contained worker that can observe, act, verify, record, and continue — with or without human checkpoints depending on what the domain requires.

It doesn't run the loop. It designs the worker that runs it.

Think of it as designing an arena: you define the playing field (environment), the rules (constraints and checkpoints), the score (operational metric), and the win condition (stopping threshold). The worker is the player — the loop-designer builds the arena it plays in.

## Core principles

- Make the goal measurable
- Pick the fastest trustworthy feedback
- Map every required action to a specific tool
- Persist learnings between cycles
- Be opinionated about process, neutral on tactics
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
- convert a job description into an autonomous worker
- figure out what a role involves before designing a worker

Examples:

- "Design an ASO worker to grow iOS revenue to $10k MRR"
- "Create an autonomous content worker that grows downloads"
- "Turn this ops process into a closed loop"
- "Here's a job description — turn it into a digital worker"
- "I need someone to handle Twitter marketing — what does that role look like?"

## Outputs

Produce one of two outcomes:

1. `READY` -> write the worker `SKILL.md`
2. `NOT READY` -> list the exact blockers; do not write the worker skill yet

## Workflow

### 0) Role discovery

Every worker starts here. The user provides a job description, a job link, or a vague idea of the role they want to automate. The agent extracts a structured role brief before moving to mission intake.

If the user hasn't provided a job description or a clear goal, ask:

> Do you have a job description for this role (a link or paste), or would you like me to research similar roles to build a starting point?

**Research**

Regardless of input quality:

1. Search for 4-5 real job descriptions that match the user's description
2. Synthesize the common responsibilities across them
3. Surface responsibilities the user may not have considered
4. Research the domain's baseline strategy and common heuristics — the worker needs informed starting assumptions, not blank-slate guessing

**Extract**

From the user's input and the research, extract:

1. **Responsibilities** — list each distinct responsibility
2. **Metrics / KPIs** — explicit or implied success measures
3. **Tools / platforms** — mentioned or implied by the responsibilities
4. **Constraints** — brand guidelines, compliance, budget, team dependencies
5. **Autonomy classification** — for each responsibility, classify:
   - `automatable` — can be done by an agent end-to-end
   - `human-relay` — human performs a mechanical step (no judgment)
   - `human-judgment` — requires human decision-making

**Present**

Present the extracted role as a table:

| Responsibility | Autonomy | Implied metric | Implied tool |
| --- | --- | --- | --- |
| e.g. Create short-form video content | automatable | views, engagement rate | AI video gen, scheduling API |
| e.g. Respond to community comments | human-judgment | response time, sentiment | platform native |
| e.g. Publish content to platform | human-relay | posting cadence | scheduling tool |

**Clarify and narrow**

Before trimming, ask targeted questions to resolve any ambiguity — unclear responsibilities, missing context (target audience, scale, platform, success criteria), or contradictions between the user's input and what the research surfaced.

After presenting, tell the user:

- Which responsibilities can likely close the loop (automatable + human-relay)
- Which ones can't (human-judgment) and why
- Ask the user to trim: "Which of these do you want the worker to handle?"

The trimmed role brief becomes the starting input for Step 1.

### 1) Mission intake

Use the trimmed role brief from Step 0 as the starting point — the responsibilities, metrics, and tools inform the mission, score, and environment below.

Restate the mission in one sentence:

- business outcome
- operational objective
- stopping condition: a target threshold, a cycle budget, or human-interrupt-only (with justification for why that's safe)
- autonomy mode: `human-reviewed` (human checks reports each cadence), `semi-autonomous` (human handles specific checkpoints), or `fully-autonomous` (no human in the loop — requires stricter safety)

Separate the **north star** from the **operational score**.

After defining the operational score, ask: if the worker optimized ONLY this score, could it produce something you'd reject? If yes, add a constraint or secondary metric. Catch gaming risks at score definition, not after the worker is built.

Ask these anchor questions to ground the mission:

1. What can you measure today? (reveals available verification surface)
2. What tools and accounts do you already have? (reveals environment)
3. What's the fastest thing you could change and see a result? (reveals the tightest loop)

Example:

- North star: `$10k/month iOS revenue`
- Operational score: `weekly organic installs` — chosen because it moves faster than monthly revenue and the worker can influence it directly through content and metadata changes. Revenue is the north star but too slow for cycle-level feedback.
- Stopping condition: `installs plateau for 4 consecutive weeks` or `revenue hits $10k/month`
- Autonomy mode: `semi-autonomous` — human reviews daily analytics report and manually publishes content (platform bot detection)

### 2) Strict readiness gate

Check these five gates:

1. **Score** - Is there a measurable, verifiable score?
2. **Speed** - Is there a bounded review cadence for learning?
3. **Environment** - Is the action space clear and toolable?
4. **Failure cost** - Can bad iterations be contained? For slow-cadence loops (days/weeks per cycle), reverting wastes the entire cycle — prefer learning from failure and moving forward. For fast loops (minutes/hours), reverting is cheap.
5. **Traces** - Can the worker leave a structured experiment log and durable learnings? The log must use a structured, machine-readable format (JSONL recommended). Each entry must include at minimum: identifier, date, action, result, score delta, status (keep/discard/fail), and reasoning. The worker must read this log at cycle start.

Example — Failure cost gate:

- PASS: Worker posts a TikTok slideshow. Bad post gets 0 views, no harm — contained.
- FAIL: Worker sends marketing emails. Bad email burns the subscriber list — irreversible without a human-approval checkpoint.

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

Document tools and their capabilities — do not install, configure, or verify access in this step. The user sets up the environment separately before running the worker.

Build an action-to-tool map. Every action must have:

- a specific tool or API
- access status: `ready` | `setup-needed` | `missing`
- checkpoint: `autonomous` | `human-relay` | `human-approval`
- a verification source

For each action, ask: can the worker do this safely and autonomously, or does a human need to be in the path?

- `autonomous` — worker does it alone, no human needed
- `human-relay` — human performs a mechanical step that requires no judgment (e.g., tapping "publish" to avoid bot detection). Does not break closure.
- `human-approval` — human makes a judgment call before the action proceeds (e.g., approving spend, reviewing content for brand safety). Requires a review cadence.

The checkpoint column feeds the autonomy mode from step 1. Many `human-relay` or `human-approval` actions = the worker is human-in-the-loop, and the design should acknowledge that rather than pretending full autonomy.

Example:

| Action | Tool | Status | Checkpoint | Verification |
| --- | --- | --- | --- | --- |
| Read analytics | Postiz API | ready | autonomous | daily metrics pull |
| Generate slideshow | node-canvas + AI | ready | autonomous | image renders correctly |
| Publish to TikTok | Postiz scheduler | ready | human-relay | human adds trending sound, taps publish |
| Send email blast | Mailchimp API | setup-needed | human-approval | human reviews copy before send |

If any required action is `missing`, the loop is `NOT READY`.

### 4) System sanity check

Before writing the worker, answer these five questions about the loop as a system:

1. **Throughput** — How many cycles per period? (e.g., 7 cycles/week)
2. **Latency** — How long is one cycle? (e.g., ~15 min observe + act + verify)
3. **Reliability** — What's the expected failure rate? (e.g., 1 in 10 cycles fails due to API timeout)
4. **Cost** — What does one cycle cost? (e.g., ~$0.02 in API calls + ~$0.05 in LLM tokens)
5. **Recovery** — What's the restart cost after a mid-cycle failure? (e.g., re-pull metrics, no lost work)

If any answer reveals the loop is impractical (too slow for the goal's timeline, too expensive per cycle, too fragile to run unattended), redesign before proceeding.

### 5) Define the worker

Write the worker around these sections:

- Mission
- Operational Score
- Verification Surface
- Environment
- Work Loop
- Memory (with directory layout and file ownership)
- Safety
- Closed Loop Test

The worker must be self-contained. All files live within the skill directory: `SKILL.md` and `soul.md` (human-owned instructions), `references/` (schemas, format examples — human-owned), and `data/` (runtime artifacts — agent writes here). Define file ownership in the Memory section: which files the human owns (never modified by the agent), which the agent owns (results, playbook), and which are shared (config). Format examples and data schemas belong in `references/` as separate files — the SKILL.md should point to them (e.g., "See `references/results.jsonl`"), never inline JSON/JSONL blocks.

**Contracts vs tactics:** Be explicit about contracts — what tools to use, what formats to produce, how to score, when to stop, what's off-limits. Be open about tactics — what to try, what order to explore, what creative choices to make. Litmus test: if a step specifies *which tool to call* or *what format to produce*, it's a contract — keep it. If it specifies *what the agent should decide*, it's over-specified — remove it and let the agent discover it through iteration. Express thresholds as heuristics with examples, not hard-coded numbers — if a threshold might change with context, write it as a guideline (e.g., "high difficulty, such as >50") rather than a fixed rule.

When the score has components, define diagnostic combinations that tell the worker WHERE things are going wrong, not just that they're going wrong.

See `references/example-worker.md` for the ideal shape of a finished worker skill — use it to calibrate structure, specificity, self-healing patterns, and learning mechanics.

Include a **stall rule** in the Work Loop: define what "stuck" looks like (score flat or degrading for N consecutive cycles) and what the worker does about it (pause, widen search, escalate to human). N should be proportional to the feedback cadence. For fully-autonomous workers, this is mandatory. For human-reviewed workers, the review cadence serves as implicit escalation.

Include a **simplicity criterion** in the Operating Principles: when improvement is marginal, prefer the simpler approach. Removing something and maintaining score is a win. This prevents complexity accumulation over long-running loops.

Include a **resilience principle** in the Operating Principles: define what happens when tools fail, data is partial, or APIs are unavailable. A partial cycle is better than no cycle.

If the worker produces content, communicates with humans, or makes judgment calls that reflect a brand or perspective, also generate a `soul.md` using `references/soul-template.md`. If the worker is purely mechanical (data pipelines, code optimization, monitoring), skip the soul.

After drafting, compare the worker's capabilities against the job descriptions from Step 0. Surface any gaps to the user before finalizing.

### 6) Proof of loop

The first cycle must be **observation-only** — measure the current state before changing anything. This establishes the baseline all future cycles are scored against.

The second cycle makes the first bounded change.

Example — wrong (conflates baseline with action):

- observe metrics and make one change
- verify if it helped

Example — right (separates baseline from first action):

- **Cycle 0:** pull current installs, CTR, conversion rate. Record as baseline. Change nothing.
- **Cycle 1:** make one bounded change (e.g., update one keyword). Verify the delta against baseline. Record result.

### 7) Refine mode

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
- When the work loop has distinct stages with different tools, note per-stage failure handling — a failure at one stage should not force a restart from the beginning
- When tools have per-use costs, define the budget per cycle and per period — not just total budget
- When verification sources have different speeds, act on the fastest reliable signal and adjust strategy on the slower ones
- Identify platform-specific constraints that affect how the worker can act — some actions may need workarounds or checkpoint steps
- If the worker consumes third-party content, data, or assets, treat them as constrained inputs: check availability, quota, legal/ethical limits, and what happens when they run out
- If a platform can silently penalize the worker (shadow ban, suppressed reach, rate throttle), define a detection signal — e.g. if score drops >X% for Y consecutive cycles, suspect platform penalty, pause, and escalate
- When the worker produces outputs in batches, score at the batch level after sufficient time for signal to stabilize — not per individual output
- The more autonomous the worker, the stricter the safety requirements. A human-reviewed worker can rely on regular reports for course correction. A fully-autonomous worker needs explicit stall thresholds, stopping conditions, and escalation rules baked into the skill.
- Treat cadence as a learnable parameter. The worker should shorten cycles when signal arrives early and lengthen them when signal is noisy or still settling.
- Early cycles need wide exploration; later cycles need focused pruning. Cycle 1 should look nothing like cycle 10. Design the work loop to behave differently when it has no history vs 50 cycles of data.

Example — diagnostic combinations for a content-to-installs loop:

| Views | Conversions | Diagnosis | Action |
| --- | --- | --- | --- |
| High | High | Working — scale it | Double down, create variations |
| High | Low | Reach is good, CTA is weak | Fix call-to-action or landing page |
| Low | High | Content converts but isn't seen | Fix hooks, titles, distribution |
| Low | Low | Fundamentally off | Full reset — rethink angle or audience |

This kind of matrix tells the worker WHERE things are going wrong, not just that they're going wrong.

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
