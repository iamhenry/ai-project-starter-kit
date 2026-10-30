# Hivecall kickoff: goal contract, run card, checklist

Read this at the start of every hivecall run, and again when resuming one.

## 1. Turn the owner's input into a goal contract

The owner may give a free-form goal, a spec file, or an ISA.html. For clear input, draft this contract and plan, then wait for owner approval. Choose per item: when it cannot support a falsifiable Verification check, use [discovery.md](discovery.md); clear and find-out items can share a run. Do not wait for owner contract/plan approval for discovery; judge a plan only when needed. Planless discovery still needs a fresh qa `REPRODUCED` for a reproduction/cause or fresh reviewer `SELECTED` on a cited non-bug finding (judge-proposal even for one option); cited research alone never ticks.

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

- **Verification** becomes one checklist item per check (`ISC-n`), each with its evidence. Evidence files go in `.hivecall/verification/`. For build items a fresh `qa` runs the checks, never the builder; discovery items use the fresh scoped verdict and receipt in [discovery.md](discovery.md).
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

### Parking an item

A BLOCKED receipt alone does not park an open criterion. Keep its original text/check and leave its checkbox unticked; add `data-status="parked"` to the **input inside that criterion**, not the run card or a separate note. Append the reason and exact unlock under `#verification`. For example:

```html
<!-- In #criteria; keep the original item's text and check. -->
<li id="ISC-23"><input type="checkbox" disabled data-status="parked"> ISC-23: original behavior — check: original check</li>
<!-- Append under #verification; use the actual reason, unlock and evidence. -->
<li>ISC-23: BLOCKED - parked; reason: required permission unavailable; unlock: permission granted and delivery proven; evidence .hivecall/verification/blocked-23.md</li>
```

### Vetted additions and replacements

A helper proposes an addition with positive evidence (failed check, spec line, or reproduction result), not opinion or a negative finding. The primary orchestrator approves, never the proposer; even an orchestrator-originated change needs helper-produced evidence. Trace each addition to a line of the approved goal contract or spec; otherwise put it on a later list in the run card or `WISHLIST.md`, not the ledger. Judge convergence before approval: additions based only on earlier additions, additions outpacing proven tasks, or repeated changes to one area are warning signs. If not converging, park or ask one 🚦 question and continue other work; there is no fixed growth limit.

Append this exact record under `#verification` for each approved new item (replace placeholders; use `new` for no replacement):

```html
<li>ISC-24: ADDED by orchestrator; replaces ISC-23; evidence .hivecall/verification/repro.md; goal spec.md:12; converging: fixes the reported defect</li>
```

To replace ISC-23, retain its text and check, leave it unchecked, mark its input `data-status="parked"` (Markdown: `parked` on the criterion), and append `<li>ISC-23: BLOCKED - superseded by ISC-24; reason: corrected cause; evidence .hivecall/verification/repro.md</li>`. Append ISC-24 separately; no existing item is edited except its parking marker. The new item needs its own falsifiable check and real-entry-point E2E smoke before build.

For Markdown ledgers, put `parked` on the unchecked criterion line and any BLOCKED result row for that item, with reason/unlock. Parking never makes an item PASS or hides other open items. Keep the card `running` until close (or use `waiting-owner`/`waiting-usage` when paused); do not set the whole run to `parked` to hide work.

Save all ticks, receipts and parking markers in a **separate completed tool call before** writing `## Final report` or `status: closed`. The close gate checks the ledger as it exists before the call runs: updating the ledger and closing in one script is refused while that pre-call ledger is still open or unearned. Read the named open/unearned ids in the error, fix their ledger state, then retry the close separately. This does not weaken the approval/receipt check or turn a parked item into a proven one.

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
```

A fresh card has no `## Final report` heading. While the run waits on the owner, write the report so far under `## Progress report`. Add `## Final report`, with its content, only when every counted item is ticked or parked: confirmed with evidence, parked with unlock, owner-only, uncertain. The plugin blocks that heading, and setting `status: closed`, while counted items are open or ticked without approval and receipt.

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
2. After the ledger's ticks/receipts/parking markers are saved in a completed tool call, use a separate call to write `## Final report` in the run card and set `status: closed`. Then send the same report: confirmed (with evidence), parked (with unlock), owner-only items, uncertain.
3. The watchdog pauses after `closed`, then deletes its automation on the check after a successful pause. If pause fails, it retries; a complete ledger with a card that is not closed only pauses and sends `WATCH DONE` without deleting the automation.
