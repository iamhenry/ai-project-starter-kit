# Weekly Hivecall retro automation

Draft for `auto_rcepm5xwbyo`: Monday 06:00 America/Los_Angeles; OpenCode
`openai/gpt-6.1-sol`, high reasoning, full permission, fresh worktree from
`main`. This file is a prompt draft; do not change the automation configuration.

## Owner's outcome

Each Monday, audit archived Hivecall traces, write one retro report and at most
one evidence-backed proposal, gate it, and compare a surviving change against
the current skill on held-out traces. Keep all weekly history on the single
`retro/hivecall-history` branch and its one standing draft PR, titled
`Hivecall retro history`. Each Monday, start in a fresh `main` worktree, fetch
the history branch, and create a unique local branch based on the remote history
branch or `origin/main` if it does not exist. When history exists, merge
`origin/main` before analysis; conflicts mean `BLOCKED`, not manual resolution.
Regenerate the dataset, append the week's result rows, write the report, rebuild
the dashboard, then push only to the standing history branch. Replay currently
evaluates only `.agents/skills/hivecall/SKILL.md`; any other owner receives the
verdict “not evaluable yet” and cannot get a proposal PR. If an eligible eval passes, open a
separate PR from `retro/hivecall-<date>` containing only that skill file. Its
body links to the week report on the history branch. The standing PR and its
weekly report are the history record; do not create a separate weekly issue. The
owner reviews and merges; you never merge. Read threads only through the
supplied read-only scripts.

## Never

- Never open, message, stop, or change a BB thread. The trace helpers may read
  logs; do not use any other thread operation.
- Never send raw or unredacted trace text to any cloud model, GitHub issue, or
  PR. Use the local redaction helpers and require a zero-hit scan before sharing
  dataset excerpts or report text. Redacted trace text may go to Clef, the
  separate judge, and the tested model through their direct clients. Never send
  real trace context through OpenCode.
- On the dated proposal branch, the only source file you may edit is exactly
  `.agents/skills/hivecall/SKILL.md`; the replay currently reads only that file.
  Never edit another file in that tree or any other source file. The only other
  tracked changes allowed are this run's
  regenerated dataset, results rows, report, and dashboard on the history
  branch. Do not hand-edit the dataset or edit `scripts/`, `gate/`, `replay/`,
  or the dashboard builder.
- Keep all dataset, results, report, and dashboard changes on
  `retro/hivecall-history`. A dated proposal branch and PR must contain only
  the proposal's one owning source file; never cherry-pick or copy the data
  commit onto it.
- Never open a proposal PR unless the proposal gate returns `PASS` and the replay
  result is a complete `PASS`: every targeted behavior beats its noise band and
  no other trusted behavior regresses. Missing or untrusted scores are not a
  win. The standing history PR is the sole exception.
- Never merge a PR or force-push. Push only `retro/hivecall-history`; on a
  complete eval `PASS`, also push `retro/hivecall-<date>` for its proposal PR.
  Do not push any other branch, create a separate weekly issue, or change
  automation settings.

## Observe

From the fresh `main` worktree, fetch `origin/main` and the standing remote
branch if it exists. Create a uniquely named local history branch from the
remote history branch; on the first Monday, start from `origin/main`:

```sh
RUN_DATE=$(date +%F)
RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')
HISTORY_BRANCH="retro/hivecall-history"
DATE_BRANCH="retro/hivecall-$RUN_DATE"
HISTORY_LOCAL="retro/hivecall-history-$RUN_DATE-$RUN_ID"
PROPOSAL_LOCAL="retro/hivecall-proposal-$RUN_DATE-$RUN_ID"
git fetch origin refs/heads/main:refs/remotes/origin/main || { echo BLOCKED; exit 1; }
REMOTE_HISTORY=$(git ls-remote --heads origin "refs/heads/$HISTORY_BRANCH") || { echo BLOCKED; exit 1; }
if [ -n "$REMOTE_HISTORY" ]; then
  git fetch origin "refs/heads/$HISTORY_BRANCH:refs/remotes/origin/$HISTORY_BRANCH" || { echo BLOCKED; exit 1; }
  BASE_REF="origin/$HISTORY_BRANCH"
else
  BASE_REF="origin/main"
fi
REPORT=".agents/skills/retro/references/hivecall/replay/reports/weekly-$RUN_DATE.md"
DATASET=".agents/skills/retro/references/hivecall/evals/dataset.jsonl"
RESULTS=".agents/skills/retro/references/hivecall/evals/results.jsonl"
DASHBOARD=".agents/skills/retro/references/hivecall/dashboard/dashboard.html"
BASELINE_REPORT=".agents/skills/retro/references/hivecall/replay/reports/baseline.md"
REPORT_TAG="weekly-$RUN_DATE"
REPLAY_REPORT=".agents/skills/retro/references/hivecall/replay/reports/eval-$REPORT_TAG.md"
TMPDIR=${TMPDIR:-/tmp}
HISTORY_BODY="$TMPDIR/hivecall-history-body.md"
PROPOSAL_BODY="$TMPDIR/hivecall-proposal-body.md"
git status --short
git switch -c "$HISTORY_LOCAL" "$BASE_REF"
if [ -n "$REMOTE_HISTORY" ]; then
  git merge --no-edit origin/main || { echo BLOCKED; exit 1; }
fi
MAIN_SHA=$(git rev-parse origin/main)
```

The unique local name avoids collisions with branches checked out in other
linked worktrees. When history exists, merge `origin/main` immediately after
checkout and before inspecting traces or running tools. If that merge conflicts,
stop and report `BLOCKED`; do not resolve it. If the worktree is not clean or
branch creation fails, stop and report `BLOCKED`; do not reset, reuse, or
overwrite another branch. Set `MAIN_SHA` only after that merge, so scripts,
current-skill inputs, and proposal baselines reflect the merged main content.

Run the trace, digest, dataset, count, and privacy checks from the repository
root exactly as shown in `.agents/skills/retro/references/hivecall/hivecall.md`.
Only archived threads count; use the scripts' default run selection. Build to a
fresh temporary output, count and scan it, then replace the existing dataset
only when the scan has zero hits. This clean rebuild excludes both live runs
and any older unarchived rows. Commit the regenerated dataset on the history
branch with this week's results, report, and dashboard. If the redaction scan
has any hits, do not send excerpts to a model or PR; report `BLOCKED` with
counts only.

If no traces can be read, record `BLOCKED` and append no baseline row. Otherwise,
score the current skill for this week's archived dataset before judging a
proposal. Check `evals/results.jsonl` first so a retry does not append a second
baseline for this Monday. Run the baseline command exactly as documented in
`.agents/skills/retro/references/hivecall/replay/README.md`; do not invent or
reuse flags. Record its baseline report at `$BASELINE_REPORT` and its completed
baseline row in `$RESULTS`.

The runner appends the baseline row on success. If the route fails or exits
incomplete, report `BLOCKED` and ensure no baseline row from that attempt
remains. Skip the proposal gate and replay for this week; continue with the
report and history-only update. Never substitute a rule-only PRECHECK row or
invent scores. Redacted
trace context is authorized for Clef, the judge, and tested model through the
direct clients; never send it through OpenCode.

Invoke the `retro` skill and follow its workflow and report template. Read the
thread facts through the scripts, spot-check Clef labels against their source
logs, and make the final judgment yourself. Report script failures as `not
measured`; do not guess. If there are no runs, write that finding and do not
invent a proposal.

Write exactly one report to `$REPORT`.
It must distinguish observations from judgment and retain the grade, outcome
labels, proof spot-check, proposal (or why there is none), and archived-only
selection status. Sanitize it before using it in a remote request.

## Orient

If the report has no supported proposal, choose `NO_CHANGE`. If missing evidence
prevents a diagnosis, choose `BLOCKED`. In either case, do not append an eval
row. Keep any baseline row and continue to the weekly history commit/push.

For one proposal, identify its single owning file and exact patch. The replay
reads only `SKILL.md` from each supplied skill directory (`replay/run.py:875-882,
994-997`), so the only currently evaluable owner is exactly
`.agents/skills/hivecall/SKILL.md`. For any other owner, still run the proposal
gate and record both the proposal and its gate verdict in the weekly report as
`not evaluable yet`; do not run replay, append an eval row, or open a proposal
PR. The weekly baseline, if any, is the only result row for that case. Continue
with the history-only update. For the eligible `SKILL.md` owner, read
`gate/rubric.md`; create a JSON input with target behaviors, owning file, exact
proposed edit, falsifiable verification, source/moment/concrete trace evidence,
and cause class. Run the gate using a local temporary proposal and verdict path:

```sh
OWNING_FILE="<the proposal's one owning file>"
python3 .agents/skills/retro/references/hivecall/gate/run-gate.py \
  --proposal "$TMPDIR/hivecall-proposal.json" \
  --output "$TMPDIR/hivecall-gate-result.json"
```

For the eligible `SKILL.md` owner, gate `PASS` only authorizes replay. On
`REJECT`, leave the file unchanged and append exactly one eval row with
`verdict: "rejected"`, null scores, `not-measured` trust, null deltas for every
target, and `tested` containing the literal note `gate` plus a short proposal
description. The results schema has no separate note field. Use the proposal's
target behavior numbers, link the weekly report, and record the current skill
revision. Do not append a gate-rejection row for any other owning file. From the
repository root, append the eligible gate-rejection row through the replay
helper:

```sh
REPORT="$REPORT" PROPOSAL_SUMMARY="<short description>" TARGETS_JSON='[1, 2]' python3 - <<'PY'
import json, os, sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / ".agents/skills/retro/references/hivecall/replay"))
import run
targets = json.loads(os.environ["TARGETS_JSON"])
run.append_result(
    "eval", f"gate REJECT: {os.environ['PROPOSAL_SUMMARY']}", "rejected",
    targets, {}, {}, {str(target): None for target in targets},
    (root / os.environ["REPORT"]).resolve(), run.skill_revision(run.CURRENT_SKILL),
)
PY
```

Do not call this row a replay result. On `ERROR` or missing verdict, choose
`BLOCKED` and append no eval row. In every non-PASS case, leave the owning file
unchanged and continue with the weekly history commit/push only.

## Decide

Only after gate `PASS` for the exact owner `.agents/skills/hivecall/SKILL.md`,
preserve separate whole-skill inputs outside the repo's
`.agents/` tree. Archive the entire current skill directory from captured main,
copy it to a separate proposed directory, and apply the exact gate-approved
patch only to the matching file in the proposed copy:

```sh
REPLAY_TMP=$(mktemp -d)
ARCHIVE_DIR="$REPLAY_TMP/from-main"
CURRENT_SKILL_DIR="$REPLAY_TMP/current"
PROPOSED_SKILL_DIR="$REPLAY_TMP/proposed"
mkdir -p "$ARCHIVE_DIR"
git archive --format=tar "$MAIN_SHA" .agents/skills/hivecall | tar -xf - -C "$ARCHIVE_DIR"
mv "$ARCHIVE_DIR/.agents/skills/hivecall" "$CURRENT_SKILL_DIR"
cp -R "$CURRENT_SKILL_DIR" "$PROPOSED_SKILL_DIR"
OWNING_RELATIVE="${OWNING_FILE#.agents/skills/hivecall/}"
PROPOSED_SKILL_FILE="$PROPOSED_SKILL_DIR/$OWNING_RELATIVE"
test -f "$CURRENT_SKILL_DIR/SKILL.md"
test -f "$PROPOSED_SKILL_DIR/SKILL.md"
```

Apply only the proposed source edit at `$PROPOSED_SKILL_FILE`. Choose `BUILD_WEEK`
and `TARGETS` from the trace weeks and the proposal's behavior numbers, following
the held-out rules in `replay/README.md`. Use the README's models, sample size,
and seed; the documented eval report tag below writes
`replay/reports/eval-$REPORT_TAG.md`:

```sh
BUILD_WEEK="<selected build week>"
TARGETS="<comma-separated target behavior numbers>"
HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py eval \
  --current "$CURRENT_SKILL_DIR" --proposed "$PROPOSED_SKILL_DIR" \
  --build-week "$BUILD_WEEK" --targets "$TARGETS" \
  --report-tag "$REPORT_TAG" \
  --model deepseek-v4-pro --judge-model kimi-k3 \
  --per-behavior 30 --seed 20261016
```

Do not compare one file to itself or substitute another model route or weaken
the replay rule. A complete replay `PASS` requires every targeted
behavior to improve beyond the measured noise band and every other trusted
behavior to be no worse. Otherwise the result is `REJECT`; incomplete coverage
is not a pass.

The replay runner writes the report to `$REPLAY_REPORT` and appends the eval row
to `$RESULTS`. Confirm that exactly one eval row was added; do not hand-append a
duplicate. A complete replay
`REJECT` is `verdict: "rejected"` with its measured scores. A complete replay
`PASS` may be treated as `shipped` only after its separate proposal PR is open.
If replay fails or is incomplete, report `BLOCKED`, ensure no eval row from that
failed attempt remains, and do not open a proposal PR. Set `EVAL_VERDICT` to
`PASS`, `REJECT`, or `BLOCKED` from this result; use `NO_CHANGE` when no
proposal was supported.

On a complete replay `PASS`, keep the runner's exact appended row out of the
history branch until the proposal PR opens. Save that last row, then restore the
previous results file; do not hand-author a replacement:

```sh
tail -n 1 "$RESULTS" > "$TMPDIR/hivecall-pass-result.jsonl"
sed '$d' "$RESULTS" > "$TMPDIR/hivecall-results-before-pass.jsonl"
mv "$TMPDIR/hivecall-results-before-pass.jsonl" "$RESULTS"
```

Record the scorecard, every flipped moment, judge/Clef disagreements, and the
held-out-week note in the report.

## Act

Every Monday, rebuild the dashboard after processing this week's dataset and
result rows, even if no row was appended:

```sh
node .agents/skills/retro/references/hivecall/dashboard/build.mjs
```

Write a short weekly history-PR body to `$HISTORY_BODY` with
the grade, outcome, proposal or why there was none, baseline/eval row status,
report path, and dashboard update. On replay `PASS`, state that the eval row is
held pending the proposal PR; add the PR URL and shipped-row status after it
opens. The history worktree's source files remain unchanged; stage only the
history data/report/dashboard paths below:

Before any remote PR update/create, scan every existing report/body and, on
`PASS`, the proposed source file. Prepare both PR body files first when replay
passes. If any scan finds hits, do not send or push that text; sanitize it and
scan again, or report `BLOCKED` with counts only:

```sh
python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$REPORT"
python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$HISTORY_BODY"
for payload in "$BASELINE_REPORT" "$REPLAY_REPORT"; do
  if [ -f "$payload" ]; then
    python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$payload"
  fi
done
if [ "${EVAL_VERDICT:-}" = "PASS" ]; then
  python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$PROPOSED_SKILL_FILE"
  python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$PROPOSAL_BODY"
fi
```

```sh
git diff --check
git status --short
HISTORY_CHANGED=0
for artifact in "$DATASET" "$RESULTS" "$REPORT" "$DASHBOARD" "$BASELINE_REPORT" "$REPLAY_REPORT"; do
  if [ -f "$artifact" ]; then git add -- "$artifact"; fi
done
if ! git diff --cached --quiet; then
  git commit -m "Record Hivecall retro for $RUN_DATE"
  HISTORY_CHANGED=1
fi
```

### Push and update the standing history PR every Monday

Push only this standing history branch; never force-push. If its fast-forward
push is rejected, fetch and merge the remote once, then report `BLOCKED` without
retrying the push. The report and data must be available on this branch before
making any proposal PR:

```sh
if [ "$HISTORY_CHANGED" = 1 ]; then
  if ! git push origin HEAD:"$HISTORY_BRANCH"; then
    git fetch origin "$HISTORY_BRANCH" || { echo BLOCKED; exit 1; }
    git merge --no-edit "origin/$HISTORY_BRANCH" || { echo BLOCKED; exit 1; }
    echo BLOCKED
    exit 1
  fi
elif [ "$BASE_REF" = "origin/main" ]; then
  echo BLOCKED
  exit 1
fi
gh pr list -R iamhenry/ai-project-starter-kit --state all \
  --head "$HISTORY_BRANCH" --json number,title,isDraft,url
```

If exactly one open PR exists, set `HISTORY_PR_NUMBER` to its number, confirm its
title is `Hivecall retro history` and it is a draft, then update its body. If no
PR for the branch exists at all, create the standing draft PR and then query
again to set `HISTORY_PR_NUMBER`. If an earlier PR is closed, there is more than
one PR, or an existing PR is not a draft, report `BLOCKED`; do not create a
duplicate:

```sh
gh pr edit "$HISTORY_PR_NUMBER" -R iamhenry/ai-project-starter-kit \
  --title "Hivecall retro history" --body-file "$HISTORY_BODY"
```

On the first run only, create the standing draft PR instead:

```sh
gh pr create -R iamhenry/ai-project-starter-kit --base main \
  --head "$HISTORY_BRANCH" --draft --title "Hivecall retro history" \
  --body-file "$HISTORY_BODY"
```

### Complete replay `PASS` only

Create the separate dated proposal branch from the captured `main` revision and
copy in the exact evaluated proposed file. The weekly report is already available on
`retro/hivecall-history`; do not copy or cherry-pick data, results, report, or
dashboard files to the dated branch. Its only changed file is the proposal's
owning source file:

```sh
git switch -c "$PROPOSAL_LOCAL" "$MAIN_SHA"
cp "$PROPOSED_SKILL_FILE" "$OWNING_FILE"
git diff --check
git add -- "$OWNING_FILE"
test "$(git diff --cached --name-only)" = "$OWNING_FILE"
git commit -m "Improve Hivecall workflow from weekly retro"
if ! git push origin HEAD:"$DATE_BRANCH"; then
  echo BLOCKED
  exit 1
fi
PR_TITLE="[Hivecall retro] $(date '+%-m/%-d/%y'): <short change>"
gh pr create -R iamhenry/ai-project-starter-kit --base main --head "$DATE_BRANCH" \
  --title "$PR_TITLE" --body-file "$PROPOSAL_BODY"
```

The proposal PR body must contain the gate verdict, scorecard, flipped moments,
judge/Clef disagreements, held-out note, a link to the week report at
`https://github.com/iamhenry/ai-project-starter-kit/blob/retro/hivecall-history/$REPORT`,
and a clear statement that the owner reviews and merges. Use scanned, redacted
content only. Verify the PR diff contains only `$OWNING_FILE`. Do not merge it.
After it opens, return to the history branch and append the exact saved result
row; rebuild the dashboard and push the updated history branch. If the proposal
branch push or PR creation fails, report `BLOCKED` and do not append the saved
row as `shipped`. Then add the
proposal PR URL and shipped-row status to the standing history-PR body, rescan
that body, and edit the standing PR:

```sh
git switch "$HISTORY_LOCAL"
cat "$TMPDIR/hivecall-pass-result.jsonl" >> "$RESULTS"
node .agents/skills/retro/references/hivecall/dashboard/build.mjs
for artifact in "$RESULTS" "$DASHBOARD"; do
  if [ -f "$artifact" ]; then git add -- "$artifact"; fi
done
if git diff --cached --quiet; then
  echo BLOCKED
  exit 1
fi
git commit -m "Record shipped Hivecall proposal for $RUN_DATE"
if ! git push origin HEAD:"$HISTORY_BRANCH"; then
  git fetch origin "$HISTORY_BRANCH" || { echo BLOCKED; exit 1; }
  git merge --no-edit "origin/$HISTORY_BRANCH" || { echo BLOCKED; exit 1; }
  echo BLOCKED
  exit 1
fi
python3 .agents/skills/retro/references/hivecall/scripts/redact.py --scan "$HISTORY_BODY"
gh pr edit "$HISTORY_PR_NUMBER" -R iamhenry/ai-project-starter-kit \
  --title "Hivecall retro history" --body-file "$HISTORY_BODY"
```

If replay is `REJECT`, `NO_CHANGE`, or `BLOCKED`, do not create or push a dated
branch or add an eval row beyond the applicable gate/replay rejection.

Return the report path, verdict, gate/replay outcome, dashboard/result status,
history commit and PR, and dated PR URL when applicable. Do not claim a win when
the replay was incomplete or untrusted.
