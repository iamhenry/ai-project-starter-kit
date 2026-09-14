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
- KISS, YAGNI, reuse before invent.
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

| Option | How It Works (User & Product Lens) | Complexity & Effort | Key Trade-offs |
|---|---|---|---|
| **1. Minimal** (Fastest) | | Low | |
| **2. Balanced** (Idiomatic) | | Medium | |
| **3. Comprehensive** (Full) | | High | |

7. Recommended Proposal: pick one option. Why, using KISS/YAGNI. Step-by-step in plain English.
8. Decision Gate: 1–2 jargon-free questions for sign-off before any execution contract.

Do not implement after this output. Wait for the user.
