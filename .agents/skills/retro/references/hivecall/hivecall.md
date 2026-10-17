# Hivecall retro

Use for an explicitly requested retro of runs that invoked `hivecall`, including
the weekly automation. The parent retro skill owns cause classification,
verdicts, minimal-change ordering, redaction, and the report. This module adds
run selection, the facts to gather, a weekly grade, report tables, and the
proposal-gate → replay-eval → dashboard path used by the weekly loop.

Rule of thumb: scripts count, Clef labels, you judge. Ask only what the logs can
answer. "Can't tell" is a valid answer; report it with a reason, never guess.

## Gather the facts

From the repository root, inspect the last week's archived runs and build/update
the all-time replay dataset. Archived threads are the only runs counted. The
helpers read thread logs; they never change threads.

```
d=.agents/skills/retro/references/hivecall/scripts
t=${TMPDIR:-/tmp}
python3 "$d/find-runs.py" > "$t/hivecall-runs.json"
python3 "$d/digest.py" "$t/hivecall-runs.json" > "$t/hivecall-digest.json"
```

Build/update the all-time dataset using its archived-only default, then scan it:

```sh
python3 "$d/build-dataset.py" --output "$t/hivecall-dataset.jsonl"
python3 "$d/count-moments.py" "$t/hivecall-dataset.jsonl"
python3 "$d/redact.py" --scan "$t/hivecall-dataset.jsonl"
```

Only after the scan reports zero hits, replace the old dataset with this fresh
archived-only output:

```sh
mv "$t/hivecall-dataset.jsonl" .agents/skills/retro/references/hivecall/evals/dataset.jsonl
```

- Only archived threads count. `find-runs.py` uses its default recent window and
  scans archived threads across projects. A thread counts only when its log has a
  completed skill tool call named exactly `hivecall`, or a user turn carrying
  the injected skill body. Titles, mentions, and plain reads of `SKILL.md` do
  not count. It lists each run's direct children. Never include an unarchived
  thread, regardless of its activity or reported status.
- The dataset builder uses archived threads only. It appends to an existing
  dataset, so build to a fresh temporary output and replace the old file as
  shown above; this ensures no old live-run records remain.
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

- `count-moments.py` reports stored moments for behaviors 1–7. The command
  `python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan
  .agents/skills/retro/references/hivecall/evals/dataset.jsonl` must report zero
  hits before any dataset excerpt is sent to a cloud model or included in an
  issue/PR. Never send raw logs; `digest.py` redacts its Clef requests locally.

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

## Weekly change loop

Run this only as part of the weekly automation. When archived traces are
readable, score the current skill for that week using the baseline route in
`replay/README.md`; the runner appends one `kind: baseline` row. If no traces are
readable, report `BLOCKED` and append no baseline row. Clef remains the direct
first-pass client. Tested prompts go to the `plan` subagent
(`anthropic/claude-opus-5-5`, the real orchestrator model); judge prompts go to
the `reviewer` subagent (GPT family). The Python scripts never call either
agent. The runner exports redacted JSONL with readable Markdown twins and prints
both paths in `awaiting answers: <path>` without adding a partial result. Launch
no more than five agent batches at a time (up to 20 prompts per batch). Multi-batch
exports are numbered, and each twin lists shared system/skill text once with
wrapped item prompts. For the
reviewer, include `.agents/skills/retro/references/hivecall/judge-contract.md`
in the brief. The reviewer returns exactly one JSONL line per item and no other
text, in the strict importer format
`{"id":"<exported 64-character id>","answer":"<raw answer text>"}`. For judge
rows, `answer` contains the prompt-specific raw JSON judgment; tested rows
contain plain-text hypothetical next actions. Import into the same cache and
rerun the exact command. Replay export/import commands are documented in
`replay/README.md`; for example:

```sh
HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py baseline \
  --cache-dir .lanes/replay-cache --batch-size 20 \
  --export-prompts .lanes/hivecall-handoff/baseline.jsonl
python3 .agents/skills/retro/references/hivecall/replay/run.py import \
  --answers .lanes/hivecall-handoff/answers.jsonl --cache-dir .lanes/replay-cache
```

The tested and judge model families differ.
If the baseline route fails or is incomplete, report `BLOCKED` and leave no
baseline row; never substitute a rule-only PRECHECK row.

Then finish the retro report and make at most one evidence-backed proposal for
its owning file. No proposal means `NO_CHANGE`; missing evidence that prevents
diagnosis means `BLOCKED`. Those outcomes add no eval row.

The replay currently reads only `SKILL.md` from each supplied skill directory
(`replay/run.py:875-882,994-997`), so only the exact owner
`.agents/skills/hivecall/SKILL.md` is evaluable. For any other owner, still run
the proposal gate and write the proposal plus its gate verdict in the weekly
report as `not evaluable yet`. Do not run replay, open a proposal PR, or append
an eval row—even for gate `REJECT`; the weekly baseline, if any, is the only
results row.

1. Read `gate/rubric.md`, write the exact proposed change and its evidence as
   the gate's JSON input, then run the proposal gate from the repository root:

   ```sh
    python3 .agents/skills/retro/references/hivecall/gate/run-gate.py \
     --proposal .hivecall/verification/proposal.json \
     --output .hivecall/verification/gate-result.json \
     --cache-dir .lanes/gate-cache \
     --export-prompts .lanes/hivecall-handoff/gate-reviewer.jsonl --batch-size 20
    ```

     When the gate prints `awaiting answers: <path>`, launch a `reviewer`
     subagent with the judge-contract path and batch path; return exactly one
     importer-format JSONL row per item and no other text. Then run
    `gate/run-gate.py import --answers <answers.jsonl> --cache-dir .lanes/gate-cache`
    and rerun the exact gate command. It emits a second reviewer batch only if
    the first answer is malformed; after two invalid answers the verdict is
    `ERROR`, never `PASS`.

   Gate `PASS` means only “worth evaluating” for the exact
   `.agents/skills/hivecall/SKILL.md` owner. On gate `REJECT` for that eligible
   owner, append one
   `kind: eval`, `verdict: rejected` row with null scores, `not-measured` trust,
   and `gate` in its `tested` text (the schema has no separate note field); do
   not run replay. A gate `ERROR` is `BLOCKED`, not a rejection and not an eval
   row. Do not apply a rejected proposal.
  2. For a gate `PASS` on the exact eligible skill file, run the replay eval per
    `.agents/skills/retro/references/hivecall/replay/README.md`, including its
    export → dedicated-agent → import → rerun loop. The replay
   compares the current and proposed skill on held-out trace moments, includes
   scorecards, changed moments, judge/Clef disagreements, and the held-out
   note, and appends its result to
   `.agents/skills/retro/references/hivecall/evals/results.jsonl`. Do not treat
   missing or untrusted scores as a win. A replay `REJECT` row has measured
   scores; a replay `PASS` is `shipped` only after its separate proposal PR is
   open. Never label a non-eval outcome as `rejected`.
3. Rebuild the offline dashboard every Monday after processing result rows,
   even when this run appends no row:

   ```sh
   node .agents/skills/retro/references/hivecall/dashboard/build.mjs
   ```

   The dashboard reads
   `.agents/skills/retro/references/hivecall/evals/results.jsonl` and writes
    `.agents/skills/retro/references/hivecall/dashboard/dashboard.html`. The
    weekly automation maintains one standing history branch and draft PR,
    updating it every Monday. It opens an additional change PR only for a
    gate-approved replay `PASS` on `.agents/skills/hivecall/SKILL.md`; that PR
    contains only this file. Dataset, results, report, and dashboard stay on the
    history branch. Never merge a PR or force-push. `NO_CHANGE` and `BLOCKED` add
    no eval row; if there are no readable traces, they add no baseline row.
