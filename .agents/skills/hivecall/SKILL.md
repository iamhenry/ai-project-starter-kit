---
name: hivecall
description: Autonomous multi-agent run that works through a large ledger of tasks until each is done or parked. Expensive. The user must explicitly invoke it by typing hivecall, /hivecall or @hivecall. Agents must never load or start it on their own, from inference, or from words like swarm, parallel or many tasks. Run by the orchestrator only.
---

# Hivecall

Work through a ledger of many tasks autonomously: thin end-to-end slices, parallel lanes, evidence-based ticks, and a plan that adapts. Run by the `orchestrator` agent. Subagents never run this skill.

## Start conditions

Start only when all are true:

- The user explicitly invoked hivecall in this conversation.
- A goal is supplied: free-form text, a spec file, or an ISA.html ledger.
- The user approved the goal contract and answered "watchdog on?" (see Kickoff). This approval replaces the orchestrator's IMPLEMENTATION GATE for this run only.

If the goal is missing, ask for it and stop.

## Kickoff

Follow [references/kickoff.md](references/kickoff.md):

1. Draft the goal contract and plan from the user's input. Filter owner-only items out of the counted list.
2. Show both. Ask "Watchdog on? (yes / no)". Wait for approval.
3. Use the supplied ISA.html as the ledger, or create `.hivecall/checklist.html` from the template, with the approved contract on it.
4. Write the run card `.hivecall/run.md` with `status: running`.
5. If watchdog is on, set it up per [README.md](README.md#watchdog): name it `🐝 <orchestrator thread title>`, capture the automation id, write `watchdog: on, automation <id>` in the run card, pass `AUTOMATION_ID`, then use shadow first and live second.

When resuming in a fresh thread, read the run card and ledger first, then [watchdog/lessons.md](watchdog/lessons.md).

## Ledger rules

- The ledger is the only progress record. The run card holds lifecycle status only (running, waiting-owner, waiting-usage, closed). Create no other status file.
- Only the orchestrator ticks items, and only on independent proof: a fresh `qa` result that ran the item's exact check on the exact candidate. A builder's own claim, passing tests, a compile, a mock, or a summary is not proof. A builder marking its own work verified is self-verification, not proof.
- Never edit an item's text, check or threshold. Update the progress count with each tick.
- Keep the plan (dependencies, critical path, lanes) in chat. Do not write it to the ledger.

## Loop

Repeat until every item is done or parked:

1. **Pick** the thinnest slice a user could run end to end: 1-5 related items. Run lanes in parallel only when they touch different files and state.
2. **Delegate** each slice as one bounded task. Load the `subagent-delegation` skill before the first delegation and follow it for every brief. Every brief carries its TALK-BACK block (one channel, filled with your real id) so workers can send BUG / BLOCKED / QUESTION mid-run. `build` or `general` implements. Add `reviewer` (`code-quality-gate`) and `qa` (`verification-gate`) as risk warrants, always in fresh agents, never the builder. Every brief says: do not spawn further subagents unless allowed. With the watchdog on, every brief also carries a `PROMISE:` line and a result filename (see README.md, Watchdog).
3. **Tick** items proven by independent evidence. Commit the accepted work locally. Never push.
4. **Log lessons.** After any surprise, failure, or false alarm, add one line to the run card's Lessons section.
5. **Re-check** (below).

## Re-check after every result

Ask three things: did this unblock or break another item, did the critical path move, can a new lane start?

- No to all: continue silently.
- Yes to any: update the plan in chat, send one line ("re-planned: X because Y"), and continue.

Re-plan on new evidence, not on activity.

## Park, don't loop

- A failure gets one correction using a different approach. If its cause is unclear, the correction brief names `bugging-out` and carries the failed evidence; the builder picks the next playbook, not a repeat.
- A second failure of the same kind: park the item with its exact unlock condition and move to other work.
- Owner-only items (physical device, human access) are parked from the start.
- Parked items do not stop the run.

## Stop and ask only for

Missing authority or access, a contradictory ledger, or a destructive or remote action. Never push. Never fabricate evidence. While waiting on the user, set the run card to `waiting-owner`; after a usage limit, `waiting-usage`. Set it back to `running` when work resumes.

## End

When every counted item is ticked or parked: set the run card to `status: closed`, then send the final report (confirmed with evidence, parked with unlock, owner-only items, uncertain). The watchdog pauses after closure and deletes its automation on the check after a successful pause; it retries a failed pause. Ledger completion before the card is closed only pauses the watchdog and sends `WATCH DONE`. A `WATCH DONE` or `🚦 WATCH STALLED` message means: report to the user and stop; do not start new work.

## Workflow skills

`subagent-delegation` (briefs), `verification-gate` with `qa` (independent proof), `code-quality-gate` with `reviewer` (as risk warrants), `reproduce-bug` (bugs), `bugging-out` (unclear cause or a failed fix), `gather-context` with `atlas` / `voyager` (research), `git-commits` (local commits only). Platform skills as the project needs them, e.g. `xcodebuildmcp-cli` and `argent` for iOS, `agent-browser` for web.

## Status footer

End every reply to the user with a one-to-two-line summary and the one-row status table from [references/kickoff.md](references/kickoff.md) section 5 (Done · In progress · Not started · Stuck · Owner-only). The user may be away for hours; the footer must show the current state at a glance.

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
