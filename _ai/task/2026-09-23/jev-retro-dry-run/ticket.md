# Jev-assisted retro and baseline dashboard

## Final consolidation (supersedes compatibility decisions below)
User approved removing all old issue-to-PR entry points. The generic SKILL.md
loads a matching `references/<skill-name>/README.md` without target-specific
rules. All issue-to-PR rules, scripts, data, ignore rules and the local key live
inside `references/issue-to-pr/`. Old command paths are intentionally retired.
No more verification runs or API calls; update the same PR.

## Follow-up: canonical layout and verbatim design
Move the module to `retro/references/issue-to-pr/`, flatten its rubric/questions,
and replace the summarized design with the user's exact supplied Markdown.
The user subsequently requested removing the test, a top-level version field,
and one `dashboard.html` file instead of a template/output pair. No further tests
or verification runs; only regenerate the dashboard's data after the rename.
Keep small old-path entry points where needed rather than duplicate implementations.
Keep root and skill ignore rules: repository-wide secrets versus portable skill
outputs/keys. Verify new and old CLI paths, local rendering, links, and exact design
text without another API call; update the existing PR. No delegation/global edits.

## Follow-up: default behavior and cleanup
User requested Jev by default for issue-to-PR retros and an update to PR #122.
Version 1.0.2 routes those retros to the existing helper, retains preview approval,
and makes unavailable/declined/failed checks explicit before LLM-only continuation.
Other retros are unaffected. No new API call is needed for this instruction change.
Remove requested PNGs and environment template; keep the scratch ignore file to
protect historical raw output. The old script is superseded by the committed module;
old reports remain local historical evidence, not fresh findings to publish.

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
Canonical module: `.agents/skills/retro/references/issue-to-pr/`.
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
- [x] 390px/1280px screenshots inspected; no mobile page overflow. Screenshots
  subsequently removed at the user's request.
- [x] Offline regression and `git diff --check` passed.
- PR prepared as a draft for human review; publication URL belongs in the final
  handoff. No merge or installation authorized.

Detailed receipts and limits: `.agents/skills/retro/references/issue-to-pr/evals/verification.md`.
Old scratch scripts, reports and raw receipts in this task directory are historical,
not the supported entry point and not part of the PR.
