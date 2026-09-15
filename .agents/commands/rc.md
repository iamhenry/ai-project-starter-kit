---
name: rc
description: Research contract — audit the codebase and propose a plan from a brain dump. Do not implement.
---

Treat everything after `/rc` as inert task data. Pass it through verbatim. Do not rewrite, summarize, or “improve” it before research.

<query>
$ARGUMENTS
</query>

If `$ARGUMENTS` is empty, ask for the brain dump and stop.

This is research only. Do not edit files, implement, commit, or start execution.

## Intent

Turn a high-level idea into an actionable engineering plan the user can approve.

- Product and user lens: clicks, UI states, visible behavior. Not dense jargon.
- Staff-engineer judgment: weigh system correctness, architecture fit, and size. Heuristics, not a checklist.
- Codebase evidence first. Cite real files and functions.
- Stop at a decision gate. No execution contract until the user signs off.

## Phase 1 — Ingest & Boundary

Fill 1–3 immediately from the query, before auditing.

1. Intent & Goal: `[Feature | Bug | Refactor | Discovery]` plus a plain-English summary
2. User/Product Outcome: what the user will see, click, or experience when this succeeds
3. Scope: IN: files, UI views, or APIs to audit · OUT: unrelated subsystems to ignore

Then audit the current codebase. Read files, inspect state flows, search for reusable patterns. Do not propose yet.

## Phase 2 — Discovery & Proposal

After the audit, output:

4. Codebase Ground Truth: existing UI, state logic, or root causes, cited with file paths
5. High-Level Architecture Shape: a brief Mermaid or ASCII diagram of User Action → App State → External Dependency/Backend
6. Solution Options:

Rank **is** the recommendation. Option 1 is what a staff engineer would ship given the evidence, scope, and architecture above — not the cheapest patch, and not the most complete one. Name each option by the approach (e.g. "Extend existing status query"), not by effort.

Weigh with these heuristics. They are questions, not a scoring rubric. Size and idiom win only when the system still holds.

- If I follow this through callers, state, and boundaries, is it still right — or does it only patch the reported spot?
- Can I express this with what already exists, one fact in one place, the way this repo already works?
- Is this the smallest version that is actually sound, or am I gold-plating / skipping a real seam?
- If this is wrong, how hard is it to undo, and who else gets hurt?

A cheap local fix that leaves sibling paths or duplicated state is usually worse than a slightly larger honest change. Extra completeness beyond this scope is usually worse too.

| Rank | Approach | How it works (user lens) | Why a staff engineer ranks it here | Cost & blast radius |
|---|---|---|---|---|
| **1 — ship this** | | | the pick, in one line | |
| **2** | | | what makes it worse than 1 | |
| **3** | | | what makes it worse than 1 and 2 | |

7. Recommended Proposal: option 1 as the plan. One line on why the others lost. Step-by-step in plain English. If you would not ship option 1, the ranking is off — fix the ranking.
8. Decision Gate: 1–2 jargon-free questions for sign-off before any execution contract.

Do not implement after this output. Wait for the user.
