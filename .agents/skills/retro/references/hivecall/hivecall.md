# Hivecall retro

Use for an explicitly requested retro of runs that invoked `hivecall`. The parent
retro skill owns the questions, cause classes, verdicts, minimal-change order,
redaction, and report. This module adds the goal, run selection, where to look,
and two report tables.

## Goal

Hivecall plus its watchdog should run autonomously for hours, reliably and
honestly. It has two jobs:

1. **Stay on track.** The watchdog tells the orchestrator whether agents are on
   track, the orchestrator steers, and workers talk back when stuck.
2. **Deliver the goal contract.** Finish every item with proof, or stop cleanly
   on a hard blocker and say exactly what is left.

Judge changes by both jobs and by time: hours lost to stalls, redo rounds, and
the owner having to step in. Exclude owner idle time.

## Finding the runs

- Use the `bb` CLI (`bb thread list`, `bb thread log <id> --json --all`, redirected
  to files). Default window: the past 7 days, all projects, active and archived.
  If that finds fewer than 3 runs, widen to 30 days and say so.
- Count a thread only when its log shows a completed `skill` tool call whose
  argument is exactly `hivecall`. Titles, mentions, and claims don't count.
- A run lasts from the skill load until the run card says `status: closed`; a
  later non-closed status reopens it. Work after close is follow-up.
- Follow each run's child threads, and their children, to see the whole run.
- Record which version of `.agents/skills/hivecall/` each run loaded (match it
  to `git log`), so a later drop can be traced to a change.
- If `bb` fails with a stale `BB_CLI` setting, run it as `env -u BB_CLI bb ...`
  or call the newest `bb` binary in the BB app's versions folder, and note it.

## Where to look

Check the runs against everything the skill tells agents to do. Before reading
runs, list every rule the skill itself states (in SKILL.md, HOW-TO-WORK.md and
the references). For each rule, count how often runs followed it across every
hand-off, tick and message, not a sample. Then read the runs for problems no
rule covers, such as:

- The owner correcting, redirecting, or asking for status.
- Watchdog alerts, read with the orchestrator's next reply: false alarm,
  already handled, acted on, or ignored. A change to an alert must keep the real
  problems it caught while cutting the false ones.
- Stretches with open work and no agent working, and workers that ended stuck
  without talking back.
- Final reports and ledger ticks compared with the proof that exists.
- Rules in SKILL.md or HOW-TO-WORK.md that runs kept breaking: is the rule
  unclear, unenforced, or wrong?
- Places the skill made runs slow or heavy: needless rebuilds, oversized
  tasks, repeated work.

Count and classify from the original records first, then redact what you keep.

## Output shape

Start with a 2–3 sentence problem statement. List the reviewed runs:

| Thread | Name | Project | Skill version | Outcome |
| --- | --- | --- | --- | --- |

Use this table for proposed changes:

| # | File | What to change | What happened in the runs | Why | What to expect |
| --- | --- | --- | --- | --- | --- |
