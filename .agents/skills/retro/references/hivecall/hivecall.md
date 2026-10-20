# Hivecall retro

Use for an explicitly requested retro of runs that invoked `hivecall`. The parent
retro skill owns the questions, cause classes, verdicts, minimal-change order,
redaction, and report. This module adds the goal, run selection, where to look,
what good looks like, how to apply authorized edits, and two report tables. It is
self-contained: a scheduled trigger only needs to invoke it and state authority.

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
- Hand-offs to OpenCode helper agents are not in BB logs. Read them from the
  orchestrator's OpenCode session: `opencode session export <session id> > file`
  (the session id is the `providerThreadId` in the BB log). Always redirect to a
  file; piped output is truncated. Do not use `--sanitize`; it blanks the text.
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

## Privacy

Count and classify from the original records first, then redact. Before any run
text goes into scratch notes, helper prompts, the report, or a commit, remove
secrets and tokens, emails, personal paths (`/Users/<name>` -> `/Users/[user]`),
IPs, and personal names. Paraphrase the owner; never quote verbatim. Redact only
identifying or secret values, never the behavior (what happened, when, counts,
alert names, statuses), so redaction cannot skew findings. Keep scratch files in
a temp folder outside the repo and delete them at the end. Commits contain no run
excerpts, thread or session IDs, or personal data.

## What good and bad look like

Good:
- Every rule the skill states is listed with followed / total per run, counted
  across all hand-offs, ticks and messages. Subagents may split the counting.
- Each change points at a count or a concrete event and names the rule or
  friction it fixes.
- A safeguard that caught real problems is kept; a noisy one is made more
  accurate.
- Every claim has evidence. What couldn't be checked says "unknown" and why.
- Small, simple edits. The skill grows only with a stated reason.

Bad:
- Reading a few runs as stories, or sampling.
- Skipping a count because logs are large, or calling a plain yes/no text check
  "subjective".
- Deleting an alert or rule because it was sometimes wrong.
- Calling something a restored regression without the commit where it was lost.
- Claiming nothing useful was removed without counting.
- Proposing changes the skill already has.

## Applying changes

Only when the request authorizes edits:
- Edit only `.agents/skills/hivecall/`. Do not read or modify its `eval/` folder.
- Keep the existing structure. Report words in SKILL.md, HOW-TO-WORK.md and
  references/*.md before and after; justify each increase in one line.
- If `watchdog/watch.py` changes, run every `--simulate` scenario, each with its
  own temporary `REPO` folder; all must pass.
- Bump the patch version in SKILL.md, commit locally on the current branch, and
  never push, open a PR, or merge. Do not start a hivecall run.

## Output shape

Start with a 2–3 sentence problem statement. List the reviewed runs:

| Thread | Name | Project | Skill version | Outcome |
| --- | --- | --- | --- | --- |

Use this table for proposed changes:

| # | File | What to change | What happened in the runs | Why | What to expect |
| --- | --- | --- | --- | --- | --- |

Then the rule counts (rule, followed / total per run, or unknown and why). If
edits were applied: commit, branch, skill size before/after, simulation result,
what should improve and what could get worse, and run hiccups (anything in this
profile, the retro skill or the tools that slowed the run or was unclear).
