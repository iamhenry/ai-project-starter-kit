# Hivecall retro

Use for an explicitly requested retro of runs that invoked `hivecall`, including
the weekly automation. The parent retro skill owns cause classification,
verdicts, minimal-change ordering, redaction, and the report. This module adds
run selection, the facts to gather, a weekly grade, and report tables.

Rule of thumb: scripts count, Clef labels, you judge. Ask only what the logs can
answer. "Can't tell" is a valid answer; report it with a reason, never guess.

## Gather the facts

From the repository root:

```
d=.agents/skills/retro/references/hivecall/scripts
t=${TMPDIR:-/tmp}
python3 $d/find-runs.py --days 7 > $t/hivecall-runs.json
python3 $d/digest.py $t/hivecall-runs.json > $t/hivecall-digest.json
```

- `find-runs.py` scans threads archived in the past 7 days, in all projects. A
  thread counts only when its log has a completed skill tool call named exactly
  `hivecall`, or a user turn carrying the injected skill body. Titles, mentions,
  and plain reads of `SKILL.md` do not count. It lists each run's archived direct
  children.
- `digest.py` reads the logs and reports per run: duration (skill invocation to
  the first `WATCH DONE`, else the last orchestrator event, so it can include
  reopened or follow-up work); quiet gaps (30+ minutes with no orchestrator
  event); active time (duration minus quiet gaps with no BB worker running);
  peak concurrent workers; every watchdog alert line; and every child's final
  report. Clef, Cloudflare's decision model on Ollama Cloud, labels each alert
  `real` or `false`, each child `done`, `blocked`, `failed`, or `partial`, and
  each quiet gap `closed` (run already over), `owner` (waiting on the owner), or
  `stalled`. A stall is a gap labeled `stalled` with no BB worker running; it
  also notes whether the watchdog had sent anything yet. Below 0.8 confidence
  the label is `can't tell`; an alert the orchestrator never answered is
  `no follow-up` and is not sent to Clef. Native OpenCode subagents leave no BB
  thread, so a "stall" may hide them: check the log before calling it real. It
  reuses OpenCode's `ollama-cloud` login; no separate key.
- If a script fails, report that part as `not measured` with the error and
  continue with the rest.

Never open, message, or change a thread. `.hivecall/` files do not survive
archive; the logs (`bb thread log <id> --json --all`) are the only evidence.

## Check, do not trust

Clef labels are hints. Per run, spot-check up to 3 alert labels and 3 child
labels (the most recent of each, plus any that drive a proposal; check all when
fewer exist) against the log, and
report how many held up, for example "5 of 6 held". A QA child labeled `failed`
usually means its check failed, not the worker.

Read the orchestrator's final report and last status table yourself. Pick up to 3
ticked items and confirm the log shows their check ran with a result. Report
"3 of 3 ticks had proof in the log", not "all ticks proven".

## Questions to answer

1. What went well, and what went wrong?
2. Did parallel work help or clash? Use peak concurrent workers and any clashes
   you saw.
3. How many watchdog alerts were real, false, or can't tell?
4. How many stalls, how long was the longest, and was the watchdog running?
5. How many spot-checked ticks had proof?
6. Which lessons recur enough to promote into
   `.agents/skills/hivecall/watchdog/lessons.md` or the hivecall skill?

## Outcome and duration

- **Completed:** the run card or final report says closed, and every open item
  is parked with an unlock or is owner-only.
- **Partial:** it stopped with items neither done nor parked.
- **Cancelled:** the owner stopped it. This wins over the other labels.
- **Unknown:** the log does not show which.

Average active time over Completed runs only, and show duration beside it; give
the other outcomes as counts. With no
Completed runs, write "not measured".

## Weekly grade

Score each part from the counts above:

| Part | 2 | 1 | 0 |
| --- | --- | --- | --- |
| Completion | every run Completed | at least half Completed | fewer than half |
| Proof | every spot-checked tick had proof | one did not | two or more did not |
| Watchdog | at most 25% false | at most 50% false | more than 50% false |
| Stalls | none | longest under 2 hours | any 2 hours or longer |

Watchdog share = `false` / (`real` + `false`), across the week; `can't tell` and
`no follow-up` are left out but reported. With fewer than 5 `real` + `false`
alerts, or when your spot-checks reject 2 or more alert labels, the part is
`not measured`. Leave out a part that is `not measured` and say so. Grade on the share of
available points: A 90%+, B 75%+, C 60%+, D 40%+, F below. With no runs, write
"No runs" and no grade.

## Output shape

Inside the parent report, start with the grade, one line of evidence per part,
and a 2-3 sentence problem statement. Answer the six questions under the
parent's headings. Then:

| Thread | Name | Project | Outcome | Duration | Workers | Alerts real / false / can't tell |
| --- | --- | --- | --- | --- | --- | --- |
| `thr_...` | BB thread title | BB project name | Completed / Partial / Cancelled / Unknown | active h:mm (total h:mm) | peak count | n / n / n |

| # | File | What to change | What happened in the runs | Why | What to expect |
| --- | --- | --- | --- | --- | --- |
| 1 | Owning file and section | Smallest change, in plain words | Runs and the friction seen | The gap in instructions or enforcement | The intended effect |

Keep the parent's Diagnosis and Decision sections. A flawed week can still be
`NO_CHANGE` when the cause is `one_off`, `input`, or `environment`.
