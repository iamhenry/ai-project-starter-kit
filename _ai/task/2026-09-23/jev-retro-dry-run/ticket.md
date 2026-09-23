# Jev-assisted retro and baseline dashboard

## Current scope
User authorized a final rerun on **one thread**, `thr_nv6qzvpt85`, then a minimal
dashboard and PR. Work stays in this repository; no global config edits and no
delegation. Earlier no-PR/two-run plans are superseded. The earlier pipeline-policy
PR draft remains historical and is not part of this delivery.

## Consumer outcome
The retro's issue-to-PR module provides a reviewed-preview → OpenRouter Jev →
recorded hints flow. An LLM judge retains judgment. Its offline dashboard shows
saved-case agreement and honest comparison limits, not invented pipeline progress.

## Files
Canonical module: `.agents/skills/retro/issue-to-pr/`.
The old rubric link and command path remain compatibility entry points.
Human version: retro `metadata.version`; exact uncommitted definitions: content hash.
`evals/results.jsonl` preserves history; raw requests/receipts and keys stay ignored.

## Verification contract
- Run Jev through the real OpenRouter endpoint on the authorized thread.
- Use full helper final reports, not just the first or last 900 characters.
- Open the real generated HTML and compare displayed values with results.jsonl.
- Check desktop/mobile presentation and keep local screenshots.
- Add the smallest offline regression only after the browser smoke works.
- No independent approval claim: user explicitly disallowed delegation.

## Results
- [x] Grouped issue-to-PR files without dropping old rubric/command entry points.
- [x] Full-report rerun: 41 answers, $0.000858, 8/9 expected findings matched.
- [x] Handoff negatives: seven before, three now; an unexpected job classification
  remains a reason for LLM review, not another automatic tuning loop.
- [x] Added Cal.com-inspired design contract and offline dashboard.
- [x] Browser smoke: 89%, two rows, $0.001439 total, “Baseline only.”
- [x] 390px/1280px screenshots saved locally; no mobile page overflow.
- [x] Offline regression and `git diff --check` passed.
- PR prepared as a draft for human review; publication URL belongs in the final
  handoff. No merge or installation authorized.

Detailed receipts and limits: `.agents/skills/retro/issue-to-pr/evals/verification.md`.
Old scratch scripts, reports and raw receipts in this task directory are historical,
not the supported entry point and not part of the PR.
