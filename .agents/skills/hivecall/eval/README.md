# Hivecall eval

This tells you whether a change to the hivecall skill made runs better, worse, or no different.

## What an eval is, in one minute

An eval is a test for an AI workflow. A normal test checks code. This one checks how the agents behaved in a real run.

It doesn't start any agents itself. It reads the record of runs you already did: every message, tool call, and helper agent. Then it asks the same questions of each run, like "did every hand-off include the talk-back block?" or "was every PASS tick backed by a tester?" Each answer becomes a percentage. The average of those percentages is the run's score.

Grade the runs before a skill edit, freeze them as the **baseline**, edit the skill, then do a few new runs. If the new runs score higher on the same questions, the edit helped. If they score lower, it hurt.

## How it works

```
your hivecall runs (OpenCode + BB records, read-only)
        │
        ▼
  eval.py finds every run where the hivecall skill was loaded
        │
        ▼
  scripted checks: counted by code, the same answer every time
  judged checks: Clef (a small AI model) answers yes/no questions
        │
        ▼
  results + dashboard, saved privately in ~/.evals/hivecall/
```

- **A run** starts when the hivecall skill loads. It ends when the run card says `status: closed`. Anything after that is follow-up and isn't graded.
- **Scripted checks** are most of the score. They count things in the record, so they never change their answer.
- **Judged checks** need reading between the lines, like "was this watchdog alert a false alarm?" Clef answers those. A judge counts only after it agrees with at least 20 hand-checked answers at least 80% of the time. Until then the dashboard shows it as "not trusted" and leaves it out of the score.

## How to run it

You need Python 3. Nothing to install. Run these from this folder.

**First time, or after you change this eval:**

```bash
python3 eval.py --regrade            # grade every hivecall run again
python3 eval.py --judge-preview      # build the questions for Clef, with secrets removed; look before sending
python3 eval.py --judge-send         # ask Clef (only new or changed questions)
python3 eval.py --dashboard          # rebuild the dashboard
python3 eval.py --freeze-baseline    # save today's results as the baseline (once)
```

**After a skill edit and a new hivecall run:**

```bash
python3 eval.py                      # grade only the new runs
python3 eval.py --judge-preview && python3 eval.py --judge-send
python3 eval.py --dashboard
```

Other commands: `--list` shows every run it found. `--run <id>` grades one run.

## What to expect

- Grading takes a few minutes, mostly to read the records. Clef takes about a second per question; a full first send is around 7 minutes.
- Open `~/.evals/hivecall/dashboard.html` in a browser. You'll see:
  - a bar chart of the score per run, with the baseline as a dashed line;
  - a table of the 9 scored behaviors, one column per run (green = 100%, red = less, grey = didn't apply);
  - a context table with numbers that help explain a score but aren't part of it, like hours and skill size.
- If the baseline was graded by an older version of this eval, the dashboard says so and doesn't compare. Regrade, then freeze again.
- "n/a" means the behavior didn't come up in that run. For example, no worker got stuck. It's left out of the score, not counted as zero.

## What it measures

| # | Job | Behavior | Counted as |
|---|---|---|---|
| 1 | Stay on track | Briefs with a talk-back block | briefs containing TALK-BACK / briefs |
| 2 | Stay on track | Briefs with a valid PROMISE line | briefs the watchdog's own PROMISE parser accepts / briefs |
| 3 | Stay on track | Agents visible as BB threads | visible agents / agents |
| 4 | Stay on track | Stuck workers who spoke up | workers whose final result starts with BLOCKED and who sent BUG/BLOCKED/QUESTION/STOP first / those workers |
| 5 | Stay on track | Watchdog alerts that were real | 1 − share of alert lines the judge calls false alarms (judge) |
| 6 | Deliver honestly | PASS ticks backed by a tester | PASS ticks with an earlier tester (`qa`) PASS for that item plus evidence / PASS ticks |
| 7 | Deliver honestly | Ledger items proven at close | items whose last tick is a backed PASS / items |
| 8 | Deliver honestly | Orchestrator turns with no code edit or screenshot read | clean turns / turns (pushes shown; push permission not checked) |
| 9 | Deliver honestly | Run card closed | 100% or 0% |

**Context, not in the score:** 10 hours (run, working, stalled, waiting on you, waiting on usage limits, per proven item) · 11 useful watchdog alerts: a real problem the orchestrator then acted on (judge) · 12 `subagent-delegation` loaded before the first hand-off · 13 worker messages using talk-back words, sent to the right parent · 14 skill size in words · 15 your corrections per run hour (judge) · 16 final reports that overclaim (judge).

**Reading alerts both ways:** a watchdog change is better only if false alarms (5) go down while useful alerts (11) stay, and stalled hours (10) and your corrections (15) don't go up. Deleting an alert lowers false alarms but also drops useful ones and lets stalls go unflagged.

## Keeping it honest as the skill changes

An eval goes stale when the skill changes how runs are written and the eval keeps looking for the old words. Three habits stop that.

1. **Change the eval in the same edit as the skill.** If an edit renames something this eval reads, like the TALK-BACK block, the PROMISE line, the ledger tick format, the run card status words, or a watchdog alert name, update `eval.py` too. It's like fixing a unit test after changing the code. "Check details" below lists what each check reads.
2. **Read the first new run next to its dashboard column.** After the first run on an edited skill, spend about 10 minutes reading that run, then compare with the dashboard. If a check says n/a or 100% when the run clearly did something else, the eval is stale. Fix it before trusting the score.
3. **Compare only runs graded by the same eval version.** The dashboard does this for you. When you change a check or a judge question, bump `EVAL_VERSION` in `eval.py`, regrade, and freeze a new baseline. The raw records are kept, so old runs can always be regraded.

## Private data

Traces, results, and the filled-in dashboard stay in `~/.evals/hivecall/` (or `HIVECALL_EVAL_DIR`). Never copy them into this repo. The committed `dashboard.html` has no data. It loads `dashboard-data.js`, a git-ignored link to the private file. Clef questions pass through a secret filter first, and `--judge-preview` lets you inspect them before anything is sent.

## Check details

- OpenCode subagents and BB threads are joined into one tree of agents. Only agents created and messages sent inside the run count.
- The run window comes from `status:` writes to `.hivecall/run.md`, including shell edits. A later non-closed status reopens the run. Follow-up hours are capped at 24.
- Ledger ticks are read from file writes and from shell commands that write the ledger. A tester's proof can be its final result or result rows it wrote before the tick.
- Shell commands count as code edits only when a code file is the write target.
- Watchdog alerts are recognized by their names (OFF TRACK, HOST, GHOST, LEDGER, …), with or without a leading 🚦. Worker result posts (`RESULT …`, `Acknowledged`) don't count as your messages.
- The final report is the `## Final report` section of the run card if there is one. Otherwise it's the orchestrator's last message after the close and before your next message.
- Labels for the judges come from the traces. For watchdog alerts, the orchestrator's own reply usually says whether the alert was false or real. A flagged leftover process that a working agent still uses is a false alarm; one left behind by a finished agent is real.
- Every Clef answer is tied to a hash of its exact question and input. If either changes, only that answer is asked again.
- The Ollama key is read into memory only, never printed or written.
- Hours come from message times, with a five-minute gap rule for "working".
