# Issue-to-PR retro check

Optional, self-contained helper for the [retro skill](../SKILL.md).
Node 22.16+ and BB CLI are needed to collect a thread; an OpenRouter key is
needed to send it. No package installation. Normal retros still work without it.

1. Put `OPENROUTER_API_KEY=...` in `retro/.env` or `issue-to-pr/.env` (ignored).
2. From the repository root, generate the preview:
   `node .agents/skills/retro/issue-to-pr/scripts/jev-check.mjs THREAD_ID`
3. Review `issue-to-pr/evals/last-request.json`. Redaction is best-effort,
   not a privacy guarantee. `requests` is exactly what will leave the machine.
4. Authorize transmission with the same command plus `--send`. It sends the saved
   preview, not a newly collected thread. Changed checker files invalidate it.
5. Open `issue-to-pr/dashboard.html`. Each successful run regenerates it from
   `evals/results.jsonl`; rebuild without an API call using `--dashboard`.

## Owners and meaning
- `references/issue-to-pr.md`: policy and change boundaries.
- `references/jev-questions.json`: model questions, thresholds, local routing policy.
- `evals/cases.json`: expected findings, read only after inference for scoring.
- `evals/results.jsonl`: append-only results, probabilities, versions, fingerprints and cost.
- `evals/receipts/`: local, ignored API request/response evidence.
- `design.md`: styling contract; `dashboard.template.html`: offline UI source.

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

Offline regression check (no API key or BB needed):
`node --test .agents/skills/retro/issue-to-pr/scripts/dashboard.test.mjs`
