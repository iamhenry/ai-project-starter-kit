# Blind QA script: Pro To-Do benchmark

For the parent only. **Never copy this file into the run's repo**; the run gets `TASK.md` and `design.md` only.

Same method as run 10 (`~/swarm-test/run10/evidence/SCORE.md`), so the scores compare.

## Setup
- Freeze first: record the app folder's file hashes and HEAD. Re-check after QA; a changed hash voids the QA.
- 3 testers in parallel, each a fresh visible `qa` running `verification-gate` sized small: tester A features 1–10, B 11–20, C 21–29.
- Each tester uses its own isolated `agent-browser` session on `file://<run repo>/index.html`, clears that page's localStorage and IndexedDB once at the start, and works only through the UI. Read-only inspection is allowed only to confirm a visible style, a chart's pixels, or a drag target.
- Blind: testers read `TASK.md` and `design.md` only. They do not open the ledger, the run card, evidence, or earlier runs. Reading app source to find an entry point is allowed only after the UI shows none, and that is itself a discoverability finding.
- One real try per feature. No retries to make a feature pass.
- Testers write only inside their own QA folder; they never modify the app.

## Verdicts
| Verdict | Meaning | Points |
|---|---|---|
| WORKS | Every part of the feature as written in `TASK.md` behaved correctly | 1 |
| PARTLY | Some parts worked; name the part that didn't | 0.5 |
| BROKEN | The main action failed | 0 |
| CAN'T TEST | The tool can't drive it (for example the OS notification prompt); not counted | — |

Each row: `| # | Feature | Verdict | What I did → what I saw |`, plus a screenshot path for anything not WORKS.

## Scores
- **Working score** = points / testable features. #22 attachments and #23 reminders are excluded, as in run 10 (27 features).
- **Claims confirmed** = features the run's ledger marks PASS that QA scores WORKS / 27.
- Also list every claim contradiction: ledger PASS, QA saw a concrete wrong result (firm) or could not confirm (soft).

## Feature parts to check (the "and also" parts drifted most in run 10)
| # | Must see |
|---:|---|
| 1 | Enter and the Add button both add; blank input ignored |
| 2 | Checkbox toggles; done shows crossed out |
| 3 | Delete moves the item to Trash |
| 4 | Double-click edits; Enter saves; **Escape cancels**; empty text deletes |
| 5 | Drag reorders; **order kept after reload** |
| 6 | All / Active / Done / **Due today** each show the right items |
| 7 | "N items left" is right; Clear done removes done items |
| 8 | A new task survives an **immediate** reload |
| 9 | Arrows move, Space toggles, Delete removes, focus ring visible |
| 10 | One level of sub-tasks; parent done only when all children are done |
| 11 | Export valid JSON; import it back; invalid file shows a **visible** message and changes nothing |
| 12 | Native date picker sets the date; overdue marked in grayscale |
| 13 | Month and week views; drag between days changes the date; **week resize changes duration** |
| 14 | Create, **rename**, delete lists; move a task; each list has a grayscale shade |
| 15 | Daily recurrence creates the next one on the **right date**; weekly, monthly, custom exist |
| 16 | Cmd/Ctrl+Z and Cmd/Ctrl+Shift+Z undo and redo a calendar move |
| 17 | A change in one tab appears live in another |
| 18 | Add a tag, click it to filter, rename it everywhere (also in search) |
| 19 | P1–P3, sorting changes the order, shown in calendar and board |
| 20 | Search finds text in lists, tags and notes and highlights matches |
| 21 | Notes render bold, links and **checklists** |
| 22 | (not scored) image drop attaches and previews after reload |
| 23 | (not scored) notification fires when permission is granted |
| 24 | Timer start and stop; totals per task and per list |
| 25 | Cmd/Ctrl+K opens the palette; typing an action name runs it |
| 26 | Board columns; drag between them; list view agrees |
| 27 | Stats page draws completions per day on a `<canvas>` |
| 28 | List / Board / Calendar / Stats; **current view kept after reload** |
| 29 | Trash restores an item; Empty removes it for good |

## Pass bar (from the frozen decisions)
App: working score ≥ 80% and claims confirmed ≥ 70% (run 10: swarm 80% / 59%, solo 83% / 70%, 90 min). The behavior half of the bar is read from the eval (context rows 11–15 and the hidden-helper check).
