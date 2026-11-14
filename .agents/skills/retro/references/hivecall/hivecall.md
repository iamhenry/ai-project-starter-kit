# Hivecall retro

Use for an explicitly requested retro of runs that invoked `hivecall`. The weekly
retro runs as the BB workflow `.bb/workflows/hivecall-retro.js`; it reads this
file. The parent retro skill owns cause classes, redaction and minimal-change
order. This file owns the expected behavior: one fixed set of stages every run
is judged on, so every report covers the same ground.

## Goal

Hivecall should take a goal to a result the owner accepts, without the owner
babysitting, honestly, and without wasted work. A retro answers two questions
with evidence: which stages behaved as expected in each run, and what is
systemically going well or wrong across runs and weeks.

## Where the evidence is

- A run is an archived BB thread whose log has a completed `skill` tool call
  named exactly `hivecall` and writes a run card. Only archived threads count:
  an active one may still be working. Its thread log and OpenCode session stay
  readable after the thread and its worktree are archived. Follow its child
  threads (`bb thread list --parent-thread <id>`) too.
- Saved run folder, when the plugin version had it:
  `~/.hivecall/runs/<repo>/<started>-<thread>/` holds the run's `events.jsonl`, `run.md` (run card with owner rules, lessons and final report)
  and ledger, copied by the plugin every 10 minutes while the run is live and
  once on close; a run that never closed is judged as it stands. `source.txt` names the
  worktree; read its `.hivecall/verification/` and `git log` if it still exists.
- `events.jsonl`: one row per helper launch (`helper-created`: agent, brief role,
  items, commits), guardrail (`blocked`, `allowed`, `warning` with `rule`),
  verdict (`review-result`: approved, failed, passed), tick (`allowed` with
  `action: tick`) and `agent-mismatch`.
- Orchestrator thread: the `orchestrator:` line of the run card. Save
  `bb thread log <thread> --json --all > <tmp file>`; it holds the owner's
  messages, watchdog alerts and replies. Briefs given to native helpers are in
  `opencode session export <session id> > <tmp file>` (session id from the run
  card or the log's `providerThreadId`). Always redirect to a file. If `bb` fails
  on a stale `BB_CLI`, run `env -u BB_CLI bb ...`.
- A run lasts from the skill load until `status: closed`. Owner messages after
  close are the owner's verdict on the result; read them.

## Stages

Each stage gets PASS, FAIL or UNKNOWN with one evidence line (file plus line,
event time, or log sequence). PASS needs evidence too. UNKNOWN names the command
or file that was tried. A stage that did not occur in the run (for example no
review was needed) is PASS with that reason.

### Setup

- **kickoff**: The goal contract states the outcome for its full reach (for
  example "any article", not only the samples), what must keep working, an
  expected result taken from the original source, and exit criteria that cannot
  keep the defect. FAIL when the owner later had to add one of these, or a gap
  in the contract let the run pass without the goal.
- **plan**: Items are thin steps toward the goal and the plan map stays current.
  FAIL when an item was mostly tooling for its own sake, or the plan kept
  pointing at work the evidence had ruled out.

### Work

- **handoff**: Each brief has one checkable result, the delta since the last
  attempt and the correct edit scope, and goes to the right agent: build work to
  build (or the run's named implementation agent), review to `reviewer`, QA to
  `qa`, research to a research agent. FAIL on any `agent-mismatch` or
  `right-agent` block for review or QA, a brief that made a helper redo valid
  work, or an edit outside the stated scope.
- **build**: Behavior is made to work and proven before tests are written; no
  unrelated changes. FAIL when tests came before proof or the owner corrected
  scope.
- **review**: Review is sized to risk: behavior-changing code is reviewed,
  renames, tests and docs on proven work are not. FAIL on review rounds spent on
  low-risk commits or more than two revise rounds on one slice.

### Proof

- **proof**: Every tick rests on an independent QA result on a named commit,
  checked against a reference that does not come from the code under change.
  FAIL when a check compared the output with itself, a tick was later
  contradicted, or a mismatch was accepted as a tradeoff without the owner.
- **stuck**: When an item kept failing, the run changed angle, split it or parked
  it with an unlock, and never widened scope or lowered the bar. FAIL on repeated
  attempts with the same approach, or `replan` pauses that changed nothing.
- **keep-working**: What worked before still works: the contract's keep-working
  steps ran on the candidate. FAIL when the owner found a regression or the
  steps never ran.

### Oversight

- **watchdog**: Alerts were real and acted on. FAIL when most alerts were false,
  or a real alert was ignored.
- **owner-channel**: The owner stayed hands-off and was told about blockers
  clearly. FAIL on owner corrections or status questions mid-run that the
  harness should have prevented.
- **close**: The final report compares the result with the goal, says plainly
  when the goal is unmet, and its claims match the receipts. FAIL when the owner
  said after close that it was not solved, or the report read as success while a
  parked item blocked the goal.

## Privacy

Judge from the original records, then redact what goes into the report: no
secrets or tokens, personal names, owner quotes, emails, IPs, private or tailnet
hosts, local paths, thread/project/session ids, or commit ids. Paraphrase owner
messages. Before posting, scan the complete report with the repository's secret
and private-data rules. Any match blocks the post; show only the rule name and
line number. Redact identifying values, not behavior. Keep scratch files in a
temp folder.

## Proposed fixes

At most three, each pointing at a FAIL that repeats across runs or weeks, as the
smallest change to `.opencode/plugins/hivecall/` (prefer a guardrail in code for
a repeated failure, a line of wording for a one-off). If a fix renames an alert,
a ledger or verification line format, the TALK-BACK or PROMISE words or a run
card status word, mark it `EVAL IMPACT`. The retro proposes only; it never edits,
commits or starts a hivecall run.
