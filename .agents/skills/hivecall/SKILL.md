---
name: hivecall
description: Autonomous multi-agent run that works through a large ledger of tasks until each is done or parked. Expensive. The user must explicitly invoke it by typing hivecall, /hivecall or @hivecall. Agents must never load or start it on their own, from inference, or from words like swarm, parallel or many tasks. Run by the orchestrator only.
---

# Hivecall

Work through a ledger of many tasks autonomously: thin end-to-end slices, parallel lanes, evidence-based ticks, and a plan that adapts. Run by the `orchestrator` agent. Subagents never run this skill.

## Start conditions

Start only when all are true:

- The user explicitly invoked hivecall in this conversation.
- A ledger is supplied: one file of open items. Each item has an ID, an exact check, and a done state.
- The user approved the run. This approval replaces the orchestrator's IMPLEMENTATION GATE for this run only.

If any is missing, say which and stop.

## Ledger rules

- The ledger is the only progress record. Create no other status file.
- Only the orchestrator ticks items, and only on independent proof: a fresh `qa` result that ran the item's exact check on the exact candidate. A builder's own claim, passing tests, a compile, a mock, or a summary is not proof. A builder marking its own work verified is self-verification, not proof.
- Never edit an item's text, check or threshold. Update the progress count with each tick.
- Keep the plan (dependencies, critical path, lanes) in chat. Do not write it to the ledger.

## Loop

Repeat until every item is done or parked:

1. **Pick** the thinnest slice a user could run end to end: 1-5 related items. Run lanes in parallel only when they touch different files and state.
2. **Delegate** each slice as one bounded task. `build` or `general` implements. Add `reviewer` and `qa` as risk warrants, always in fresh agents, never the builder. Every brief says: do not spawn further subagents unless allowed.
3. **Tick** items proven by independent evidence. Commit the accepted work locally. Never push.
4. **Re-check** (below).

## Re-check after every result

Ask three things: did this unblock or break another item, did the critical path move, can a new lane start?

- No to all: continue silently.
- Yes to any: update the plan in chat, send one line ("re-planned: X because Y"), and continue.

Re-plan on new evidence, not on activity.

## Park, don't loop

- A failure gets one correction using a different approach.
- A second failure of the same kind: park the item with its exact unlock condition and move to other work.
- Owner-only items (physical device, human access) are parked from the start.
- Parked items do not stop the run.

## Stop and ask only for

Missing authority or access, a contradictory ledger, or a destructive or remote action. Never push. Never fabricate evidence.

## Progress card

After each tick, park or blocker, one line:

`Closed N/T · parked P · next: <item>`

## Good

- The app is runnable after every tick.
- Done means a run proved it.
- Plan changes come from evidence.
- The run scales: under 5 items, keep the plan in your head; past that, the ledger is the plan.

## Anti-patterns

- Foundation or shared abstraction before two real journeys need it.
- Ticking from a builder's self-report or green tests.
- Repeating a failed approach.
- Parallel tasks that share files or depend on each other.
- Delegating a task that spans several slices.
- Re-planning on every tool call.
- Asking for approval between slices once the run is approved.
- Fanning out a skill's own subagents inside every lane. Size expensive skills first.
