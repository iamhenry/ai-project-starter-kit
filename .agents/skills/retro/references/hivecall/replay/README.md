# Hivecall weekly evaluation

This is the single source of exact CLI commands for the weekly automation. Run commands from the repository root. The evaluator reads, but never changes, `evals/dataset.jsonl`; reports go under `replay/reports/`, and each completed run appends one result row to `evals/results.jsonl`.

## Resume, call budgets, and rate limits

Every successful tested-agent output, Clef label, and judge-agent verdict is checkpointed under `.lanes/replay-cache/`. This is untracked local state; do not commit it. The cache key hashes the agent, redacted request, report tag, and run identity (for example `current`, `proposed`, or `replicate-1`). Identical-skill controls therefore get an independent fresh agent answer, while reruns resume per identity. Cache writes are atomic, so an interrupted run does not leave a half-written answer. Use `--cache-dir PATH` to store the cache elsewhere; keep it between attempts if you want to resume. Existing Clef cache entries remain usable; old tested/judge entries keyed to the removed models are ignored.

Only one baseline or eval may run at a time in a repository. A non-blocking process lock at `.lanes/replay-run.lock` makes a concurrent invocation exit `BLOCKED` before it reads the dataset, creates its cache, or calls Clef. Sequential retries are safe; completed result rows are idempotent by run identity.

Both `baseline` and `eval` accept `--max-calls N`, which limits new (uncached) direct Clef calls; cache hits do not count toward the limit. The limit is optional and defaults to no cap. The runner prints an upper-bound estimate by stage and logs `[stage] i/N` progress to stderr and `replay.log` beside the cache. The default cache and log are `.lanes/replay-cache/` and `.lanes/replay-cache/replay.log`.

Clef HTTP 429 and 5xx responses are retried up to five attempts per request. The runner honors `Retry-After` up to the same 10-minute maximum; a longer requested delay stops immediately with `BLOCKED`. Otherwise it uses exponential backoff starting at about 30 seconds, with jitter and a 10-minute cap. If retries or `--max-calls` stop a run, it exits non-zero with `BLOCKED`, preserves completed answers, and does not append a partial row to `evals/results.jsonl`.

## Tested and judge agent handoff

The scripts never call the tested or judge agent. Missing prompts are exported as redacted JSONL plus an agent-readable Markdown twin; the command exits successfully with `awaiting answers: <path>` and writes no partial result. Each batch contains one role (`tested` or `judge`) and at most 20 prompts by default. Change the limit with `--batch-size N`. When a role has more prompts, all are written in order to `<export-path-stem>.b01.jsonl` and matching `.b01.md`, `.b02.jsonl` and `.b02.md`, and so on; every path is printed. A single batch keeps the exact JSONL export path and also writes its `.md` twin. The default export path is under `.lanes/hivecall-handoff/`; pass `--export-prompts PATH` to choose a stable path.

Launch a `plan` subagent for each `tested` batch and a `reviewer` subagent for each `judge` batch. `plan` is the tested role and runs `anthropic/claude-opus-5-5`, matching the real orchestrator model; `reviewer` is the GPT-family judge. Run up to five batch subagents in parallel, then launch the next batches as slots open. Give each subagent its numbered `.md` twin, not the machine JSONL; the Markdown lists each shared system/skill section once, references those sections by number, and wraps prompt lines to 1,200 characters. For `reviewer`, also give the judge contract path below. The plan prompt itself contains the simulation-only boundary. Each agent must return one importer-format answer line per item, preserving its ID, with no other text. Combine the returned answer lines from all batches into one answers JSONL, import it into the same cache, and rerun the exact original command. Repeat until it produces the report and result row:

```text
Judge contract: .agents/skills/retro/references/hivecall/judge-contract.md
Answer line: {"id":"<exported 64-character id>","answer":"<raw answer text>"}
```

For replay judge items, `answer` contains the prompt-specific raw JSON judgment as a string. For tested items, it contains the plain-text hypothetical next action. The importer validates every outer line before changing the cache.

```sh
python3 .agents/skills/retro/references/hivecall/replay/run.py import \
  --answers "$ANSWERS_JSONL" --cache-dir .lanes/replay-cache
```

The importer keeps existing cached answers. Empty or invalid agent answers follow the existing `UNKNOWN` path; no run appends a result until every required agent answer is available. Clef remains the direct, cheap first pass and still requires `HIVECALL_ALLOW_DATASET_CLOUD=1`. The reviewer (GPT family) and tested `plan` agent (Claude family) are intentionally different families.

## Precheck

```sh
python3 .agents/skills/retro/references/hivecall/replay/run.py self-check
```

This checks local parsing and scoring rules. It makes no model calls.

## Current-skill baseline (ISC-5)

```sh
HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py baseline \
  --per-behavior 30 --seed 20261016 --batch-size 20 \
  --export-prompts .lanes/hivecall-handoff/baseline.jsonl
```

The current dataset contains archived runs only, so `--exclude-run-id` defaults to none and is omitted. It may be repeated to exclude a specific run when needed. The baseline samples up to 30 moments per behavior with a fixed seed, then reserves a small fixed-seed calibration partition disjoint from the scored moments; the report lists both partition sizes. Rules decide wherever possible; Clef labels the remaining actions. The `reviewer` agent handles low-confidence labels, rule/Clef disagreements, and a seeded 10% sample. Unknown answers are counted separately and excluded from score denominators; missing evidence never counts as PASS. The baseline records Clef/judge calibration against tier-2 rules; speaker attribution was discarded, so tier-1 owner labels cannot be verified automatically. Up to 10 borderline moments are saved for the owner. Incomplete baselines and offline rule-only prechecks do not append rows to `evals/results.jsonl`.

Behaviors 5 and 6 are partial and `not-trusted`: the trace schema lacks missed-stall and clean-worker-report observations. Behavior 7 scores each run PASS when active minutes (or duration when active time is unavailable) per distinct finished checklist item are at most 45; zero finished items FAIL, and missing item evidence is UNKNOWN. Time and tokens are run-level, and provider logs do not supply USD cost.

## Held-out replay (ISC-6)

Set these values before running. Both skill directories must contain a `SKILL.md` file and live outside `.agents/`; OpenCode recursively discovers `SKILL.md` files under `.agents/skills/`.

```sh
REPLAY_TMP="$(mktemp -d)"
CURRENT_SKILL_DIR="$REPLAY_TMP/current"
PROPOSED_SKILL_DIR="$REPLAY_TMP/proposed"
mkdir -p "$CURRENT_SKILL_DIR" "$PROPOSED_SKILL_DIR"
cp -R .agents/skills/hivecall/. "$CURRENT_SKILL_DIR/"
cp -R /path/to/proposed-skill/. "$PROPOSED_SKILL_DIR/"
BUILD_WEEK=2026-W43
TARGETS=2,3
REPORT_TAG=weekly-change
```

Keep the inputs in this temporary directory for the replay; remove it afterward with `rm -rf "$REPLAY_TMP"`. Never create candidate copies with `SKILL.md` under `.agents/skills/`.

```sh
HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py eval \
  --current "$CURRENT_SKILL_DIR" --proposed "$PROPOSED_SKILL_DIR" \
  --build-week "$BUILD_WEEK" --targets "$TARGETS" \
  --report-tag "$REPORT_TAG" \
  --per-behavior 30 --seed 20261016 --batch-size 20 \
  --export-prompts .lanes/hivecall-handoff/eval.jsonl
```

`--targets` is required and is a comma-separated list of behavior numbers from 1–7. It defines which behaviors need at least 10 moments both overall and in held-out weeks and which behaviors the change must improve; all available behaviors are still compared to check for regressions. `--exclude-run-id RUN_ID` may be repeated but defaults to none. `--report-tag` preserves separate reports/results for separate runs. Only moments from weeks before `--build-week` are eligible. The tested model is the `plan` OpenCode agent (`anthropic/claude-opus-5-5`); the judge is the `reviewer` OpenCode agent (GPT family). The families differ. Only Clef uses the direct HTTPS client. If a target misses either 10-moment floor, replay omits that target from scoring, evaluates the other requested behaviors, and writes a `REJECT (target not evaluable)` report when any requested behavior remains evaluable; otherwise it keeps the incomplete exit. Baseline behavior 7 scores each run PASS when digest-style active minutes (or duration when active time is unavailable) per distinct finished item from behavior 1 ledger-edit evidence are at most 45; zero finished items FAIL, unknown item counts are excluded, and fewer than five runs are not-trusted.

B3 replay anchors immediately before the final orchestrator message with open items and a later gap over 30 minutes. With no live worker, the next action must keep work moving (launch/continue a worker or set a legitimate owner-wait). With a live worker, waiting is correct. Both classes count toward the 10-moment floor; report the zero-worker failure-side count separately, because few such moments mean low B3 power. B4/B6 use only typed pending delegation starts, never completions or untyped events. Behavior 7 is not replayed.

The positive control removes the independent-proof rule; the identical-skill control estimates noise. Few-shot examples come only from the build-week partition, never held-out weeks or the evaluated moment; behaviors without build-week examples use none and are named in the report. Each answer receives one explicit Clef pass/fail label. The judge sees blinded A/B labels only for low-confidence labels, rule disagreements, and a seeded 10% sample. UNKNOWN answers are counted, reported, and excluded from score denominators. The report includes per-behavior scores, per-week results, disagreements, flips, controls, and the PR-rule verdict. A change must improve each targeted behavior beyond the identical-control noise band and be no worse on every other trusted behavior. Missing or untrusted scores mean REJECT, not PASS.

### B2 control inputs

The fixed control copies are stored outside OpenCode's skill discovery tree at `.lanes/replay-controls/{current,weakened,identical}`; their hashes and provenance are in `controls/manifest.json`. They were built from the skill at HEAD. The weakened copy removes both the Ledger proof-rule bullet and its matching Tick step wording; the identical copy is byte-for-byte equal to current. Keep current/proposed skill copies outside `.agents/` too: OpenCode recursively discovers `SKILL.md` files there. For the positive control, use the latest invocation week in the dataset as `BUILD_WEEK`; this dataset's latest week is `2026-W42`, so `2026-W41` is held out.

```sh
CURRENT_SKILL_DIR=.lanes/replay-controls/current
WEAKENED_SKILL_DIR=.lanes/replay-controls/weakened
IDENTICAL_SKILL_DIR=.lanes/replay-controls/identical
BUILD_WEEK=2026-W42
TARGETS=2

  HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py eval \
  --current "$CURRENT_SKILL_DIR" --proposed "$WEAKENED_SKILL_DIR" \
  --build-week "$BUILD_WEEK" --targets "$TARGETS" \
  --behaviors 2 \
  --report-tag weakened-vs-current --per-behavior 30 --seed 20261016 \
  --batch-size 20 --export-prompts .lanes/hivecall-handoff/weakened.jsonl

  HIVECALL_ALLOW_DATASET_CLOUD=1 python3 .agents/skills/retro/references/hivecall/replay/run.py eval \
  --current "$CURRENT_SKILL_DIR" --proposed "$IDENTICAL_SKILL_DIR" \
  --build-week "$BUILD_WEEK" --targets "$TARGETS" \
  --behaviors 2 \
  --report-tag identical-vs-current --per-behavior 30 --seed 20261016 \
  --batch-size 20 --export-prompts .lanes/hivecall-handoff/identical.jsonl
```

`--behaviors` accepts a comma-separated behavior list and defaults to all behaviors. These B2 controls use `--behaviors 2` to sample and score only proof behavior; their reports and dashboard rows are tagged **control only**, and cannot produce a PR-eligible PASS because excluded behaviors are not checked for regressions.

## Local-only diagnostics

```sh
python3 .agents/skills/retro/references/hivecall/replay/offline.py baseline
python3 .agents/skills/retro/references/hivecall/replay/b3.py audit
```

These commands make no model calls. B3 excerpts are read from archived thread logs and pass through `scripts/redact.py` before storage. Unresolved delegations, unknown worker starts, and spawn commands count as live. This extraction currently lives under `replay/`; move it into `scripts/build-dataset.py` after the method is accepted.

## Cloud and data safety

`HIVECALL_ALLOW_DATASET_CLOUD=1` is required for each baseline or replay command that sends redacted excerpts to Clef. The tested and judge prompts are handed to the dedicated OpenCode agents through the local files described above; no script sends those prompts through an HTTP chat API. Every prompt passes through `scripts/redact.py`; the dataset remains read-only and raw trace logs are never sent. Do not use `opencode run` for trace evaluation: provider requests can include unrelated agent instructions and home/project paths.
