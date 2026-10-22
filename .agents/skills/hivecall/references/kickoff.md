# Hivecall kickoff: goal contract, run card, checklist

Read this at the start of every hivecall run, and again when resuming one.

## 1. Turn the owner's input into a goal contract

The owner may give a free-form goal, a spec file, or an ISA.html. For clear input, draft this contract and plan, then wait for owner approval. If the input cannot support a falsifiable check for every Verification line, use [discovery.md](discovery.md) instead; do not wait for owner contract/plan approval, and follow its judge gates.

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
- **Exit criteria** is when the run stops early: set the run card to `waiting-owner`, report the one-line status, and stop. Items also park after three failed attempts with different approaches.
- **Owner-only items** (physical device, accounts) go under OUT with a note "owner-only". They are not counted toward done. Prefer a simulator or scripted check over owner-only whenever one can prove the behavior.
- Between items, pick the cheapest move that can raise the score (see HOW-TO-WORK.md).
- **Every visual intent has a check.** If the spec has mocks, screenshots or a design doc, each screen they show is named by at least one item's check; otherwise add one before work starts.
- **Write the check first.** An item without a check that can run on this machine gets one written before its worker starts. If none is possible, mark it "judged against spec" and cite the spec line, or owner-only. Do not block other items on it. Example: an app that cannot be built here cannot be checked here, so say that in the contract before work starts.

Ask both questions in the same message: **"Watchdog on? (yes / no)"** and **"Open a PR at the end? (yes / no)"**. On the clear-task route, contract approval plus both answers starts the run; on discovery, the two answers authorize the run without owner approval of the contract or plan.

## 2. Pick the ledger

- An ISA.html with checkbox criteria and a verification section: use it as the ledger. On discovery, add the Discovery items under their heading. Set `LEDGER` to its path.
- Anything else (free-form goal, spec.md): copy [checklist-template.html](checklist-template.html) to `.hivecall/checklist.html` and fill it in. It is the owner's one page: progress panel at the top, the approved goal contract, the checklist grouped by feature, owner-only items, and verification lines. It must survive thread changes and compaction.

Rules:
- One `<h3>` per feature, then `<ul class="isc">` with `<li id="ISC-n"><input type="checkbox" disabled> ISC-n: <observable behavior> — check: <exact check></li>`. The checkbox comes right after the `<li id>`.
- Only the orchestrator edits the page. Tick an item by adding `checked` to its checkbox. Append one `<li>ISC-n: PASS|FAIL|BLOCKED - <reason>; commit <sha>; evidence <path></li>` per result at the end of `#verification`; never insert above older lines. The last line per ID wins. A `BLOCKED` item stays unticked and counts as stuck.
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
base: <branch> @ <commit> (preflight: install, typecheck, build passed)
checkpoint: <commit to revert to>
backup models: <agent> -> <provider/model#variant> (required; used on a credit cutoff)

## Overrides (only where this run differs from HOW-TO-WORK.md defaults)
- machine: <e.g. iOS: 1 simulator, 1 native build; web: 1 browser, 1 dev server; keep 5 GB free>
- regression journeys: <3-5 replayable user journeys, each with its command or flow file>

## Plan map
<one line per open item: ISC-n needs: ISC-a, ISC-b · files: src/x.ts, src/y.css>
<slowest chain: ISC-a -> ISC-b -> ISC-n; update both when evidence changes a need or a file>

## Owner rules
<each owner steer, word for word, with its time; the watchdog repeats these after a compaction>

## Owner decisions
<one line each: time, decision, reason; cite in verdict lines>

## Pre-review checklist
<the run's recurring review findings, one line each; builders check these and attach command output before review>

## Proven recipes
<one line per setup a QA pass proved: what it does, the exact steps or command; link it in later briefs>

## Answers
<one line per watchdog alert: ANSWER <alert id>: <action> — <thread id, ledger line, or park line>>

## Lessons
<one line per surprise, failure, or false alarm: what happened → what to do instead>

## Final report
<written when the run closes or waits on the owner: confirmed with evidence, parked with unlock, owner-only, uncertain>
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

- **Preflight (a few minutes, once).** On the starting branch: install dependencies, typecheck, and run one build. Record the commit as `base` in the run card. If it fails, fixing the base becomes the first item; work that does not depend on the broken parts can start meanwhile. Commit a `checkpoint` to revert to.
- Pick 3-5 regression journeys that cover the areas the run will touch; record them under Overrides.
- Create `.hivecall/verification/`.
- Hide noise from Git: add `.lanes/` and `.hivecall/verification/` to `.git/info/exclude`. Thousands of evidence files slow Git and BB.
- Before committing or opening a PR, inspect staged files and tracked evidence (`git diff --cached --name-only`; `git ls-files` for generated screenshots, recordings and logs, including under `_ai/`). Local excludes do not untrack files already committed. Keep run-only evidence local and cite it unless publication was authorized; do not rewrite shared history to remove it without the owner's approval.
- If watchdog is on, follow [../README.md](../README.md#watchdog): name it `🐝 <orchestrator thread title>`, capture its automation id, write `watchdog: on, automation <id>` in the run card, pass `AUTOMATION_ID`, then start it live.

## 5. Keep the owner informed

- **Lessons log.** After any surprise, failure, or false alarm, add one line to the run card's Lessons section right away: what happened → what to do instead.
- **Only real changes.** One line when an item passes, fails or parks. Hard blockers only, as a loud `🚦` line (HOW-TO-WORK.md). Confirm each owner steer in one line once applied.
- **Status footer.** End every reply to the owner with a one-to-two-line summary and this one-row table, counted from the checklist page:

| Done | In progress (likely to close) | Not started | Stuck | Owner-only |
|---|---|---|---|---|
| 5/18 (28%) | 4 | 9 | 0 | 0 |

The owner may be away for hours; the footer must make the current state clear at a glance. The watchdog appends the same table to its messages.

## 6. End the run

When every counted item is ticked or parked:

1. If PR authority was yes, confirm cited verification evidence files exist, then finish with `create-pr` to push the branch and open a PR; never merge. Otherwise, use local commits only and never push.
2. Write `## Final report` in the run card, set `status: closed`, then send the same report: confirmed (with evidence), parked (with unlock), owner-only items, uncertain.
3. The watchdog pauses after `closed`, then deletes its automation on the check after a successful pause. If pause fails, it retries; a complete ledger with a card that is not closed only pauses and sends `WATCH DONE` without deleting the automation.
