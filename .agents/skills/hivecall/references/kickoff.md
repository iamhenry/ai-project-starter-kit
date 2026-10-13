# Hivecall kickoff: goal contract, run card, checklist

Read this at the start of every hivecall run, and again when resuming one.

## 1. Turn the owner's input into a goal contract

The owner may give a free-form goal, a spec file, or an ISA.html. Draft this contract from it and show it with the plan. Do not start work until the owner approves.

Use exactly this shape:

```
- Current state: <existing user experience and behavior today, with file paths — facts only>
- Ideal state: <desired user experience and visible outcome when done, not the implementation>
- Narrow scope: IN: <files/behaviors covered> · OUT: <named things not touched>
- Verification: <cheapest check that would fail if broken> → evidence: <output/log/screenshot/screen recording>
- E2E smoke: <one real happy-path flow through the actual entry point → expected visible result>
- Definition of done: scope held · implementation proven and working before regression test is written · check passed with evidence · smoke ran end to end
- Exit criteria: <name the observable that makes this task impossible to finish truthfully, then the one-line status you report and stop — do not keep working a path that cannot succeed>

Implementation Workflow Note: Validate and prove functionality or via smoke tests first. Write permanent automated tests only after the implementation is proven to work, using them to lock in behavior and prevent future regressions.
```

How the contract maps to the run:

- **Verification** becomes one checklist item per check (`ISC-n`), each with its evidence. Evidence files go in `.hivecall/verification/`. A fresh `qa` runs the checks, never the builder.
- **Definition of done** is the finish line the watchdog reads: every counted checklist item ticked with a PASS verdict, or parked.
- **Exit criteria** is when the run stops early: set the run card to `waiting-owner`, report the one-line status, and stop. Items also park after the second failure of the same kind.
- **Owner-only items** (physical device, accounts) go under OUT with a note "owner-only". They are not counted toward done.
- Between items, pick the thinnest runnable slice next (see the hivecall loop).
- **No check, no start.** Before any worker launches, every counted item names a check that can actually run on this machine (for example, an app that cannot be built here cannot be checked here). If any item lacks one, mark it owner-only or ask the owner how it will be proven. Do not launch workers until every counted item has a runnable check.

In the same message ask: **"Watchdog on? (yes / no)"**. Approval of the contract plus that answer starts the run.

## 2. Pick the ledger

- An ISA.html with checkbox criteria and a verification section: use it as-is. Set `LEDGER` to its path.
- Anything else (free-form goal, spec.md): copy [checklist-template.html](checklist-template.html) to `.hivecall/checklist.html` and fill it in. It is the owner's one page: progress panel at the top, the approved goal contract, the checklist grouped by feature, owner-only items, and verification lines. It must survive thread changes and compaction.

Rules:
- One `<h3>` per feature, then `<ul class="isc">` with `<li id="ISC-n"><input type="checkbox" disabled> ISC-n: <observable behavior> — check: <exact check></li>`. The checkbox comes right after the `<li id>`.
- Only the orchestrator edits the page. Tick an item by adding `checked` to its checkbox. Append one `<li>ISC-n: PASS|FAIL|BLOCKED - <reason>; evidence <path></li>` per result to `#verification`. Latest line per ID wins. A `BLOCKED` item stays unticked and counts as stuck.
- Update the `progress` row (`done/total`) with each tick. The page warns when it disagrees.
- Owner-only items go in `#owner-only`; they are never counted.
- Never edit the panel's numbers; the page counts them when opened (reload to refresh).

## 3. Write the run card

`.hivecall/run.md` lets a fresh orchestrator resume and tells the watchdog the run's lifecycle state. It holds no progress; the checklist page does.

```markdown
# Hivecall run card
status: running
goal: <one-line outcome>
ledger: .hivecall/checklist.html
verification: .hivecall/verification/
orchestrator: thread thr_..., session ses_...
watchdog: on, automation auto_...
started: <date>

## Lessons
<one line per surprise, failure, or false alarm: what happened → what to do instead>
```

The approved contract lives on the checklist page, not here.

`status` values, written by the orchestrator only:

| status | Meaning | Watchdog |
|---|---|---|
| `running` | Work in progress | All checks, nudges when idle |
| `waiting-owner` | Blocked on the owner | No nudges; machine and agent checks continue |
| `waiting-usage` | Paused by a usage limit | Same as waiting-owner |
| `closed` | Run over: goal met or only parked items remain | Pauses first, deletes its automation on the check after a successful pause |

## 4. Prepare the repo

- Create `.hivecall/verification/`.
- Hide noise from Git: add `.lanes/` and `.hivecall/verification/` to `.git/info/exclude`. Thousands of evidence files slow Git and BB.
- If watchdog is on, follow [../README.md](../README.md#watchdog): name it `🐝 <orchestrator thread title>`, capture its automation id, write `watchdog: on, automation <id>` in the run card, pass `AUTOMATION_ID`, then use shadow mode before live.

## 5. Keep the owner informed

- **Lessons log.** After any surprise, failure, or false alarm, add one line to the run card's Lessons section right away: what happened → what to do instead.
- **Status footer.** End every reply to the owner with a one-to-two-line summary and this one-row table, counted from the checklist page:

| Done | In progress (likely to close) | Not started | Stuck | Owner-only |
|---|---|---|---|---|
| 5/18 (28%) | 4 | 9 | 0 | 0 |

The owner may be away for hours; the footer must make the current state clear at a glance. The watchdog appends the same table to its messages.

## 6. End the run

When every counted item is ticked or parked:

1. Set `status: closed` in the run card.
2. Send the final report: confirmed (with evidence), parked (with unlock), owner-only items, uncertain.
3. The watchdog pauses after `closed`, then deletes its automation on the check after a successful pause. If pause fails, it retries; a complete ledger with a card that is not closed only pauses and sends `WATCH DONE` without deleting the automation.
