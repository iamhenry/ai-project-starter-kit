# Local verification — 2026-09-23

Historical record: the user subsequently requested removal of the test file and
renaming the dashboard source to `dashboard.html`. Checks below describe the
earlier candidate, not a fresh verification of that cleanup.

## Actual run
- Thread: `thr_nv6qzvpt85`, no second thread, no delegation.
- OpenRouter returned 41 answers from `typesafe/jev-1.13-20260917`.
- Cost: **$0.000858**; expected-finding agreement **8/9**.
- Full helper final reports replaced 900-character prefixes. Explicit negative
  handoff answers changed from seven to three. This is not proof that every new
  classification is correct: thresholds and model uncertainty still matter.
- The orchestrator-doing-domain-work answer remains unsure (0.59).
- One unexpected classification: helper 9's capability research was called a plan
  judgment. Its title/assignment describes research; the LLM judge should reject
  that routing flag rather than treating Jev as authority.
- No new rule or PR about judge routing was applied to the issue-to-PR pipeline.

## Dashboard smoke
- Opened the generated `dashboard.html` directly through `file://` in Chromium.
- Visible: 89%, two historical rows, $0.001439 cumulative recorded cost, and
  **Baseline only** (no misleading connected trend).
- Checked desktop at 1280px and mobile at 390px. Mobile page width stayed 390px;
  the history table scrolls within its own container. Adjusted SVG labels to stay
  readable at mobile width, then captured fresh screenshots.
- Desktop/mobile screenshots were inspected locally, then removed at the user's
  cleanup request. They are no longer retained receipts; the generated HTML and
  saved result rows remain available for a fresh visual check.
- Accessibility scan: zero automatic violations; manual contrast review requested
  for five SVG text nodes. These use #666 text on white.
- Offline regression: `node --test .agents/skills/retro/references/issue-to-pr/scripts/dashboard.test.mjs`
  passes, covering empty data, history preservation, transcript exclusion and safe embedding.
- `git diff --check` passes.
- After the metadata corrections, an attempted send of the older preview was
  refused before any API call, proving that the exact-preview guard is active.

## Limits and provenance
- Self-review and local consumer smoke only; no independent agent review, as requested.
- A same-case score is not general accuracy, token savings, or pipeline improvement.
- The earlier 1.0.0 row has no full fingerprints; it is historical, not comparable.
- The new folder initially had no Git history, so the live 1.0.1 row recorded
  `+dirty` without a commit prefix. Its definition fingerprint and local API receipt
  identify that candidate. After the live call, Git lookup was corrected to use the
  containing retro skill with HEAD fallback. No additional paid call was made.
- Input-only and full-request hashes are now separate for future runs; the first
  1.0.1 row's `input_hash` covered the full request. That row remains untouched and
  will not silently join future comparison groups.
- Source-anchor checks catch missing phrases, not changed policy meaning.
- Names extracted from titles are not verified runtime agents. Missing named children
  do not prove a skipped stage; a stopped run may never reach its acceptance gates.
- Reported work spans are not billing or active-compute time. Errors do not prove
  children are dangling. The LLM judge must check these interpretations.
