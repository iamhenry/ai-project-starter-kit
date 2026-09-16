# Add Definition of Done section to AGENTS.md

## Framed problem

Agents treat "tests pass" as done. Done must mean the user-observable outcome is proven via the most direct, cheapest real user journey on the exact candidate. AGENTS.md needs a section of high-level principles with inline rules so every task carries the same done contract.

## Evidence base

Sampled BB thread history: SON-1 Now Playing smoke (lock-screen card visible during real narration), Safari discriminator on same simulator, non-ui config verifications where resulting files/routing text is the terminal observation.

## Endpoint

New "Definition of Done" section in `AGENTS.md`, consistent with `verification-gate` (which owns how to prove; section owns what done means).

## Follow-up (same task)

User supplied a draft "Instrumented Tight Feedback Loop" (bug-in-live-flow cadence: reproduce → instrument minimally → smallest fix → targeted regression + fresh live smoke → 5-line report) and asked for a compact high-level principles section in AGENTS.md, adjacent to Definition of Done. Not all tasks merit the loop — the use/skip decision must be explicit so agents neither skip proof on live bugs nor run verification theater on trivial changes. User open to collapsing with DoD; decision: keep separate (bar vs cadence), adjacent, with a linking sentence. Frontier-lab research (this thread) supports the framing: Vercel "Green CI is no longer proof of safety", Anthropic runnable-check loop, OpenAI Goal-mode criteria.

## Revision v2 (2026-09-16, after user feedback)

User: v1 "right direction but a bit too verbose… shorten by half without losing practicality, intent, behavior"; make it universal — no codebase-specific coupling (agent used across other codebases); use/skip boundary should default most coding tasks INTO the loop (docs/skill edits don't need it). Also corrected: `tc.md`/`rc.md` DO exist at `.agents/commands/`.

Changes applied to AGENTS.md:

- DoD: 8 rules → 6, 24 lines → 13. Dropped Lock Screen/Safari/SON-1 examples and "this workflow" phrasing (repo-specific); folded core question into the intro; merged journey/entry-point rules; merged skip-list into DoD rule 5 (non-executable consumer rule); added closing line defining done UP FRONT via `/tc` (`.agents/commands/tc.md` fills Verification + E2E smoke before implementation). Anti-pattern list collapsed into two closing imperatives.
- TFL: 18 lines → 12. Boundary flipped from "use for X" to default-ON with an exception list (no live surface: docs/skill/config edits → DoD rule 5, research/review-only, deterministic-covered). Dropped best-for enumeration and "errors in work log" line. Kept: 5 steps verbatim (user-supplied), 5-line report, ownership lines (reproduce-bug / verification-gate).
- Verified: `git diff --check` clean; sections at AGENTS.md:11-36; header order intact.

## Skill principle comments (2026-09-16)

Added contextual `<!-- -->` principle blocks under the frontmatter of the five skills that own stages of the done/verification contract: `verification-gate` (receipt + honest verdict), `code-quality-gate` (approval ≠ done, judge the outcome surface), `reproduce-bug` (repro = user journey, faithful smoke, honest taxonomy), `gather-context` (done defined up front, user-observable falsifiable claims), `5-whys` (evidence-first cause analysis). Format: markdown comments so they don't render; each block self-contained, skills not coupled to each other. Deliberately skipped: dogfood (exploratory lens), tc/rc (already embody the contract), agent prompts (inherit AGENTS.md), delegation skill (brief template carries probes). Total diff: AGENTS.md +27, five skills +37 lines.