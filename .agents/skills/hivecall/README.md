# Hivecall

Hand an agent a goal and let it run to the finish without you babysitting it.

## What it does

An orchestrator agent breaks your goal into a checklist, hands each piece to fresh worker agents, and ticks an item only when an independent tester proves it. A small watchdog script checks the run every 5 minutes. It nudges the orchestrator if it stalls, warns about stuck or hidden agents and machine problems, and switches itself off when the goal is met.

## When to use it

- A goal with many checkable pieces: a feature set, a spec, an ISA.
- You want it done end to end while you're away.

Not for: a quick fix, a one-file change, or research. It costs more than a normal session.

## How a run goes

1. You type `hivecall` and give a goal: a few sentences, a spec file, or an ISA.html.
2. It shows you a goal contract and a plan, and asks "Watchdog on?".
3. You approve. Nothing runs before that.
4. It works through the checklist. Open `.hivecall/checklist.html` in a browser to see progress.
5. It ends in one of three ways:
   - **Done:** every item proven. You get a final report, and the watchdog pauses itself.
   - **Blocked:** it tells you what's in the way and what would unblock it.
   - **Stalled:** the watchdog pings you once and stops nudging.

Every reply ends with a one-row status table, so you can catch up at a glance.

## What's in this folder

| File | What it is |
|---|---|
| `SKILL.md` | The rules the orchestrator follows |
| `references/kickoff.md` | Goal contract, checklist, run card, how to end a run |
| `references/checklist-template.html` | The progress page |
| `watchdog/watch.py` | The watchdog script |
| `watchdog/lessons.md` | Rules learned from past runs |

## Needs

BB with the OpenCode plugin provider (not ACP), the `orchestrator` agent, and `python3`. The watchdog needs nothing else installed.

## Watchdog

A Python 3 script (built-ins only, no AI) that checks the run every 5 minutes: machine health, whether every agent is visible in BB and keeping its promise, whether the orchestrator went idle with work left, and whether the run is finished. It only reports, by queuing one message to the orchestrator's BB thread. Its one action is pausing its own timer when the run is over. Its rules are the INVARIANTS block at the top of `watchdog/watch.py`; change them only with the owner's OK.

Each check takes 1–2 seconds of CPU. A failed read skips that check for the run; it never alarms on missing data. Simulator and recorder checks find nothing on projects that don't use them.

### Inputs

| Variable | Required | Value |
|---|---|---|
| `REPO` | yes | Absolute repo path (the orchestrator's worktree) |
| `ORCH_THREAD` | yes | Orchestrator BB thread id (`bb thread show --self --json`, or `bb thread search`) |
| `ORCH_SESSION` | yes | Orchestrator OpenCode session id: `REPO=... python3 watch.py --find-session` |
| `VERIFY_DIR` | yes | Folder where testers write result files, e.g. `$REPO/.hivecall/verification` |
| `LEDGER` | yes* | `.hivecall/checklist.html` or an ISA.html (*defaults to `_ai/docs/ISA.html`) |
| `RUN_CARD` | no | Defaults to `$REPO/.hivecall/run.md` |
| `PROJECT_ID` | yes for self-pause | BB project id; the watchdog finds its automation by name `hivecall watchdog <ORCH_THREAD>` |
| `AUTOMATION_ID` | no | Use instead of the name lookup |
| `STATE_FILE` | no | Defaults to `$REPO/.lanes/watch-state.json` |
| `WATCH_SHADOW` | no | `1` = log would-be messages to `.lanes/watch-shadow.log` instead of sending |

Optional limits: `WATCH_LOAD_LIMIT` (150), `WATCH_DISK_FREE_GB` (10), `WATCH_LARGE_FILE_MB` (100), `WATCH_LARGE_FILE_MIN` (15), `WATCH_AGENT_STUCK_MIN` (10), `WATCH_AGENT_MAX_HOURS` (3), `WATCH_GHOST_MIN` (15), `WATCH_ORPHAN_MIN` (15), `WATCH_CONTINUE_MIN` (15).

### Inspect

```sh
W="<path to this skill>/watchdog/watch.py"
export REPO="$(pwd)" LEDGER="$REPO/.hivecall/checklist.html" VERIFY_DIR="$REPO/.hivecall/verification"
export ORCH_THREAD='thr_...' ORCH_SESSION="$(python3 "$W" --find-session | head -1 | cut -f1)"
python3 "$W" --once-report   # read-only summary
python3 "$W" --dry-run       # prints messages instead of sending
```

### Turn it on

1. Copy `watch.py` into the repo at `.hivecall/watch.py` so the automation reads a file that does not move.
2. Create the automation (paused), in shadow mode:

```sh
LAUNCHER=$'import os, runpy, sys\np = os.path.join(os.environ["REPO"], ".hivecall/watch.py")\nsys.argv = [p] + sys.argv[1:]\nrunpy.run_path(p, run_name="__main__")'
ENV_JSON="$(python3 -c 'import json,os; keys=("ORCH_THREAD","ORCH_SESSION","REPO","LEDGER","VERIFY_DIR","PROJECT_ID","WATCH_SHADOW"); print(json.dumps({k:os.environ[k] for k in keys if os.environ.get(k)}))')"
bb automation create --project "$PROJECT_ID" --name "hivecall watchdog $ORCH_THREAD" \
  --cron '*/5 * * * *' --timezone "$(readlink /etc/localtime | sed 's#.*/zoneinfo/##')" \
  --script "$LAUNCHER" --interpreter python3 --working-directory "$REPO" --disabled --env-json "$ENV_JSON"
```

3. `bb automation resume <id>` with `WATCH_SHADOW=1`. After one or two checks, read `.lanes/watch-shadow.log` and the run history (`bb automation runs <id>`). The heartbeat line looks like `load 5 · disk 80 GB · 2 agents visible · 1/4 · OK`.
4. Go live: `bb automation update <id> --env-json "<same JSON without WATCH_SHADOW>" --interpreter python3 --working-directory "$REPO" --script "$LAUNCHER"`. `update` drops fields you don't pass, so always re-pass all of them.

Pause: `bb automation pause <id>`. Remove: `bb automation delete <id>`.

### How it ends

- Run card `status: closed` → pauses its automation on the next check, sends nothing.
- Ledger complete or parked-only while the card is not closed → one `WATCH DONE` message, then pauses.
- If it is still firing after done (pause failed), it retries the pause on every run.
- `status: waiting-owner` / `waiting-usage` → no nudges; other checks continue.
- Three nudges with no ledger verdict change → one `🚦 WATCH STALLED` message, then no more nudges until the card goes from waiting back to running.
- It never restarts a dead orchestrator. The only repair is at most one `bb plugin reload opencode` per hour when the OpenCode server is unreachable.

### Agent promises

Put one machine-readable line in each child's first message so the watchdog can judge it against its own promise:

`PROMISE: kind=<screen|timed|build|code|helper> rows=<IDs/ranges or -> result=<bare filename in VERIFY_DIR or -> lane=<path or ->` (optional `pace=<minutes>`)

| Kind | Use for | Progress window | Signal |
|---|---|---:|---|
| screen | Tester checking UI rows | 10 min | Real PASS/FAIL answer in its result file |
| timed | Tester that must wait (timers, reminders) | 15 min | Answer; `PENDING-WAIT ISC-n until HH:MM` pauses that row |
| build | Long native builds | 10 min | Newest `.build/*.log` in its lane grows |
| code | Builder | 20 min | Any file in its lane changes |
| helper | Reviewer or other answer-producing agent | 20 min | PASS/FAIL answer with evidence |

Result rows: `| ISC-n | PASS|FAIL|BLOCKED | observed | evidence file |`. A row counts only if it is PASS/FAIL, not a placeholder, and cites evidence. Testers write result files as they go, not at the end. Sessions without a valid promise still get the basic stuck/visible/ghost checks. A brief with no `TALK-BACK:` line (from `subagent-delegation`) raises one BRIEF alert for that agent.

Every message the watchdog sends ends with the one-row status table (Done · In progress · Not started · Stuck · Owner-only). In progress = rows promised by live agents that are not yet done.

### Offline checks

`python3 watch.py --simulate <scenario>` runs deterministic built-in scenarios with no BB/OpenCode calls. Scenarios: stuck-agent, ghost-agent, ghost-agent-no-message, invisible-agent, high-load, disk-big-file, orphan-recorder, fail-under-load, unrecorded-pass, unrecorded-pass-reload, superseded-pass, server-down, combined-alerts, shadow-mode, continue, anti-spin, done, read-failure, working-old-bb, resumed-idle-agent, off-track, on-track-timed, on-track-code, fast-jules, new-testers-old-results, no-promise, review, lane-drift, alert-once. `REPO` must point at any temp folder.

### Rolling out a changed watchdog

Shadow mode, then replay a real stuck run (must alarm) and real false alarms (must stay silent), then a live drill. When an alarm is wrong, loosen or remove the check; never add a special case.
