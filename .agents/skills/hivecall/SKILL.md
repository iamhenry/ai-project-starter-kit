---
name: hivecall
version: 1.1.0
description: Autonomous multi-agent run that works through a large ledger of tasks until each is done or parked. Expensive. The user must explicitly invoke it by typing hivecall, /hivecall or @hivecall. Agents must never load or start it on their own, from inference, or from words like swarm, parallel or many tasks. Run by the orchestrator only.
---

# Hivecall

Work through a ledger of many tasks autonomously: thin end-to-end slices, parallel lanes, evidence-based ticks, and a plan that adapts. Run by the `orchestrator` agent. Subagents never run this skill.

## Start conditions

Start only when all are true:

- The user explicitly invoked hivecall in this conversation.
- A goal or task description is supplied: free-form text, a spec file, or an ISA.html ledger. Raw bug reports use discovery.
- On a clear-task route, the owner approved the goal contract and answered both kickoff questions; on discovery, the owner's answers authorize the run and judges approve/revise the plan. This replaces the orchestrator's IMPLEMENTATION GATE for this run only. (See Kickoff.)

If the goal is missing, ask for it and stop.

## Kickoff

Read [HOW-TO-WORK.md](HOW-TO-WORK.md) first: the owner's constants for every run. Read [watchdog/lessons.md](watchdog/lessons.md) before the first delegation, not only when resuming. After any context compaction or compression, and on a watchdog `REANCHOR` message, re-read HOW-TO-WORK.md and the run card (Owner rules, Proven recipes, Answers) before the next delegation. Then follow [references/kickoff.md](references/kickoff.md):

1. If the input cannot yet support a falsifiable check for every Verification line (e.g., an ambiguous goal or raw bug report), follow [references/discovery.md](references/discovery.md) first; otherwise draft the goal contract and plan as today.
2. On a clear-task route, show both and ask "Watchdog on? (yes / no)" and "Open a PR at the end? (yes / no)"; wait for contract approval. On discovery, those answers authorize the run; judges approve or revise the plan.
3. Use the supplied ISA.html as the ledger, or create `.hivecall/checklist.html` from the template, with the approved contract or the Discovery items on it.
4. Write the run card `.hivecall/run.md` with `status: running`, including the Plan map: one line per open item with what it needs and the files it touches. Name its slowest chain of needs. Size every task to fit in 15 minutes. A task is one outcome, one set of files, one proof check; a slice can hold several tasks.
5. If watchdog is on, set it up per [README.md](README.md#watchdog): name it `🐝 <orchestrator thread title>`, capture the automation id, write `watchdog: on, automation <id>` in the run card, pass `AUTOMATION_ID`, then start it live.

When resuming in a fresh thread, read HOW-TO-WORK.md, the run card and ledger first, then [watchdog/lessons.md](watchdog/lessons.md). Verify a handoff against git and the ledger before trusting it.

## Ledger rules

- The ledger is the only progress record. The run card holds lifecycle status only (running, waiting-owner, waiting-usage, closed). Create no other status file.
- Only the orchestrator ticks items, and only on independent proof: a fresh `qa` result that ran the item's exact check on the exact candidate. A builder's own claim, passing tests, a compile, a mock, or a summary is not proof. A builder marking its own work verified is self-verification, not proof.
- Never edit an item's text, check or threshold. Update the progress count with each tick.
- Append implementation items only when ticking the plan-approved discovery item, in that same edit; never edit existing items.
- Keep the plan (critical path, lanes) in chat; only the Plan map lines go in the run card. Do not write the plan to the ledger.
- The Plan map is living: when evidence changes what an item needs or touches (a hidden dependency, a split, a new item), update its line in the same turn and re-name the slowest chain.

## Loop

Repeat until every item is done or parked:

1. **Pick** the steepest step: the cheapest move that can raise the score (HOW-TO-WORK.md), and among free items (needs met, no file overlap with work in flight) the one that unblocks the most others, smallest first. Fix a passed item that broke before new work. Slice 1-5 related items a user could run end to end. Run lanes in parallel only when they touch different files and state. No helper cap: every free item gets a helper; only browser or device QA is limited by the machine.
2. **Delegate** each task to its own helper; a slice only groups tasks for its end-to-end proof. Load the `subagent-delegation` skill before the first delegation and follow it for every brief. Every helper is a fresh visible BB child thread; never resume or queue work to a finished helper. To continue its work, start a fresh child with a Delta (done, remaining, continue in). Every brief carries its TALK-BACK block through `bb thread tell` to your thread, so workers' BUG / BLOCKED / QUESTION lines appear in the timeline; quote them to the owner word for word. `build` or `general` implements. Require `code-quality-gate` with a fresh `reviewer` for source-code (including test-only) and behavior-changing config before QA ticks; it is optional for non-executable docs/config. The builder runs the run card's pre-review checklist and attaches command output first. After a `REVISE_CODE` fix, send a delta review (the fix diff plus the earlier findings only). After a second `REVISE_CODE` on the same slice, split it or change the angle; never send a third fix. Once the reviewer approves, commit the candidate locally; QA tests that commit and its PASS line names the commit id, so every proven item is a checkpoint to return to. Use a fresh `qa` for `verification-gate`. Every brief says: do not spawn further subagents unless allowed. With the watchdog on, every brief also carries a `PROMISE:` line and a result filename (see README.md, Watchdog).
   Before sending a brief, check its final text: the TALK-BACK block is present, and, when the watchdog is on, `watchdog/watch.py`'s `parse_promise` returns `valid: true` for its `PROMISE:` line. Use only the five kinds in README.md (`screen`, `timed`, `build`, `code`, `helper`); a reviewer or researcher is a `helper`, not `review` or `verdict`. Fix a missing or invalid line before launching the agent.
3. **Answer watchdog alerts.** For each alert with an id, write one line under the run card's Answers within 10 minutes: `ANSWER <id>: <action> — <thread id, ledger line, or park line>`. The action must be something the watchdog can see; "noted" is not an action. On a stale-helper alert, decide: restart it fresh with a Delta, let it run (say why), or ask it to land its smallest provable part now. Don't split a running helper; split only when planning.
4. **Tick** items proven by independent evidence on the committed candidate. Never push without the kickoff's explicit PR authority. For a worktree lane, merge it first (below). Stop the helper's BB thread once its result is in.
5. **Guard old passes.** After each merge, rerun the run's regression journeys. If a passed item breaks, revert that merge first and fix on the side (HOW-TO-WORK.md).
6. **Log lessons.** After any surprise, failure, or false alarm, add one line to the run card's Lessons section.
7. **Re-check** (below).

## Worktree lanes (optional)

Use when parallel lanes would otherwise share a checkout. One lane = one visible BB child thread with its own worktree, branched from the orchestrator's branch: `bb thread spawn --parent-self --project <id> --new-environment worktree --visibility visible`.

- Group work so no two live lanes touch the same files. Lanes share the run's machine limits (HOW-TO-WORK.md defaults or run card overrides); when a lane needs a test device, it takes a free one within that limit.
- Lanes never edit the ledger. They write evidence and result rows to the orchestrator's `VERIFY_DIR`; only the orchestrator ticks.
- Limit live lanes to what disk allows (a worktree with dependencies and builds can need several GB).
- **Merge after QA passes:** the lane's candidate was committed before QA (its PASS line names that commit); then in the orchestrator's checkout `git merge --no-ff <lane-branch>`; rebuild and rerun the ledger's regression smoke checks on the merged build; tick; remove the worktree (`git worktree remove`) and stop the lane thread. A merge conflict or smoke failure reopens the item; never tick from the lane's build alone.

## Re-check after every result

Ask three things: did this unblock or break another item, did the critical path move, can a new lane start?

- No to all: continue silently.
- Yes to any: update the plan in chat, send one line ("re-planned: X because Y"), and continue.

Re-plan on new evidence, not on activity.

## Park, don't loop

- A FAIL, a BLOCKED, and a restarted helper each count as an attempt. Up to three attempts, each meaningfully different from the last, for example a new hypothesis or method, then a stronger model or research. Use judgment on what counts as different; never rerun the same idea. Debug in tight, time-boxed log loops (HOW-TO-WORK.md, Defaults). If the cause is unclear, the correction brief names `bugging-out` and carries the failed evidence; the builder picks the next playbook, not a repeat.
- Attempt 2 must use a new angle and check the run card's Proven recipes first. A BLOCKED report names the cheapest other probe it tried.
- After the third failure, park the item with its exact unlock condition and move to other work. When a QA pass finds a working setup (a fixture, a way to open a screen), add it to Proven recipes and link it in later briefs.
- Owner-only items (physical device, human access) are parked from the start. In an unattended run, a question for the owner is written in the run card and its item parked; the run continues.
- Parked items do not stop the run.

## Stop and ask only for

The hard blockers in HOW-TO-WORK.md, sent as one `🚦` line: missing authority or access, a contradictory ledger, a destructive or remote action, disk full after allowed cleanup, or model credits out with no backup. Everything else is decided from the specs and recorded. Never push without the kickoff's explicit PR authority. Never fabricate evidence. While waiting on the user, write `## Final report` so far into the run card and set it to `waiting-owner`; after a usage limit, `waiting-usage`. Set it back to `running` when work resumes.

## End

When every counted item is ticked or parked: if PR authority was yes, confirm cited verification evidence files exist, then finish with `create-pr` (push the branch and open a PR; never merge); otherwise use local commits only. Then write `## Final report` into the run card, set it to `status: closed`, and send the final report (confirmed with evidence, parked with unlock, owner-only items, uncertain). The watchdog pauses after closure and deletes its automation on the check after a successful pause; it retries a failed pause. Ledger completion before the card is closed only pauses the watchdog and sends `WATCH DONE`. On `WATCH DONE`, complete only an already-authorized `create-pr` closeout; otherwise report and stop. On `🚦 WATCH STALLED`, report and stop without new work.

## Workflow skills

`subagent-delegation` (briefs), `create-ticket` (raw intake), `reproduce-bug` via `qa`, `gather-context` (local code and official-doc research), `bugging-out` (unclear cause), `judge-proposal` and `judge-plan` via fresh `reviewer`, `.agents/commands/workflow/01-plan/02-create-issue.md`, `code-quality-gate` with `reviewer` (every source change), `verification-gate` with `qa`, `create-pr` (only with kickoff authority), and `git-commits` (local commits without PR authority). Platform skills as the project needs them, e.g. `xcodebuildmcp-cli` and `argent` for iOS, `agent-browser` for web.

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
- Delegating a task that spans several slices, or one that won't fit in 15 minutes.
- Resuming a finished helper instead of starting a fresh visible one with a Delta.
- Logging an alert as "expected" without an action the watchdog can see.
- Re-planning on every tool call.
- Asking for approval between slices once the run is approved.
- Fanning out a skill's own subagents inside every lane. Size expensive skills first.
