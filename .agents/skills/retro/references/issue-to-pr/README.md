# Issue-to-PR retro check

Default, self-contained helper for issue-to-PR runs reviewed by the [retro skill](../../SKILL.md).
Node 22.16+ and BB CLI are needed to collect a thread; an OpenRouter key is
needed to send it. No package installation. Other kinds of retros are unaffected.

The retro agent starts this check without a separate Jev request, but must still
obtain approval of the preview before sending data. If approval is declined, a
prerequisite is unavailable, or the call fails, report `Jev check not run` with
the reason and continue the LLM-led retro. Never claim a successful Jev check or
write a successful result for a skipped or failed call.

1. Put `OPENROUTER_API_KEY=...` in `retro/.env` or this module's `.env` (ignored).
2. From the repository root, generate the preview:
   `node .agents/skills/retro/references/issue-to-pr/scripts/jev-check.mjs THREAD_ID`
3. Review this module's `evals/last-request.json`. Redaction is best-effort,
   not a privacy guarantee. `requests` is exactly what will leave the machine.
4. Authorize transmission with the same command plus `--send`. It sends the saved
   preview, not a newly collected thread. Changed checker files invalidate it.
5. Open this module's `dashboard.html`. Each successful run regenerates it from
   `evals/results.jsonl`; rebuild without an API call using `--dashboard`.

## Owners and meaning
- `issue-to-pr.md`: policy and change boundaries.
- `jev-questions.json`: model questions, thresholds, local routing policy.
- `evals/cases.json`: expected findings, read only after inference for scoring.
- `evals/results.jsonl`: append-only results, probabilities, versions, fingerprints and cost.
- `evals/receipts/`: local, ignored API request/response evidence.
- `design.md`: styling contract; `dashboard.html`: offline dashboard, refreshed in place from the JSONL.

**Code observations are exact only for the records collected. Jev answers are
probabilistic. The LLM judge decides what the evidence means.** No gate or
publication authority comes from a Jev answer. A missing named child does not
prove a gate was skipped; an error does not prove a child is still running.
The judge must inspect ambiguous or material claims, not just positive flags.

The chart measures agreement on one tuning case, not general accuracy or skill
effectiveness. The old baseline lacks input fingerprints and is not comparable
to a new run using fuller evidence. Do not connect those points as an improvement.

Source anchors detect missing phrases only. They do not detect changed meaning.
Review questions whenever the rubric changes. A version number is for humans;
content fingerprints identify the exact uncommitted definitions used in a run.
Historical instruction compliance needs the instructions in force at the time,
not just today's routing policy.

## Compatibility and ignore rules
The older `retro/scripts/jev-check.mjs` and `retro/issue-to-pr/scripts/jev-check.mjs`
commands forward here; they contain no duplicate logic. The older
`retro/references/issue-to-pr.md` link forwards to this module's rubric.
Canonical documentation and outputs live here only. The previous module-local
`.env` is still accepted as a fallback so existing keys do not need moving.

The repository `.gitignore` protects secrets across the entire repository. The
retro `.gitignore` protects generated output and secrets when the skill is copied
elsewhere. Keep both: they have different scopes. The scratch-task ignore file
protects historical experiment output, which is not part of the supported module.
