---
name: technical-requirements (02)
description: Phase 2 - Clarify technical requirements from product specs. Requires @product-adr.md.md as input. Outputs tech-adr.md.
subtask: false
verrsion: 1.0.0
date: 2026-02-20 9:50 PM PST
---
<!-- OPUS 4.5 / SONNET 4.6 MUST USE EITHER OF THESE MODELS. OTHER MODELS SUCK

<!--
PHASE 1: WHAT THE PRODUCT IS (NOT THIS WORKFLOW)
PHASE 2: HOW THE PRODUCT WORKS (THIS WORKFLOW)
-->

# Technical Requirements Clarification (Phase 2)

Thin entrypoint. Full flow lives in the `technical-requirements` skill.

## PRE-FLIGHT (run before anything else)

1. Resolve paths: `$ARGUMENTS` overrides defaults in the table below.
2. **Search** each input at its resolved path.
3. For each input:
   - **Found** → record path (mocks: inventory media files).
   - **Missing + required** → ask once (path / paste). Do not continue until provided.
   - **Missing + optional** → ask once (path / paste / not available). "Not available" → proceed without.
4. Print one-line checklist (`✓ path` | `✗ waiting` | `– skipped`), then start the workflow.

**Inputs:**
| Input | Default path | Required? | Purpose |
| ----- | ------------ | --------- | ------- |
| User stories | `_ai/docs/USER_STORIES.md` | **Yes** | Seed product vision; ask gaps only |
| ETHOS | `_ai/docs/ETHOS.md` | **Yes** | Ground Recommended options and keep decisions in alignment with build principles |
| Mocks | `_ai/docs/mocks/**/*.{png,jpg,jpeg,webp,gif}` | No | Baseline screens/flows; gap questions only |
| Product ADR | `_ai/docs/product-adr.md` | **Yes** | Locked product decisions Phase 2 implements |

If a required input cannot be provided after ask, stop (Product ADR miss: suggest `/product-requirements` first). Same copy as skill INPUT.

## Invoke

1. Run **PRE-FLIGHT** above.
2. Load skill `technical-requirements` (`.opencode/skills/technical-requirements/SKILL.md`).
3. Pass resolved paths (especially product ADR). Execute the skill end-to-end. Do not reimplement the flow in this command.

**Output:** `_ai/docs/tech-adr.md`

## Skill layout (do not inline)

| File | Role |
| ---- | ---- |
| `skills/technical-requirements/SKILL.md` | Orchestration, I/O, load map |
| `skills/technical-requirements/references/workflow.md` | Steps, category loop, verify, completion |
| `skills/technical-requirements/references/rules.md` | Critical rules + principles |
| `skills/technical-requirements/references/research-phase.md` | 6 agents + synthesis + ADR-000 |
| `skills/technical-requirements/references/categories.md` | 15 categories + thinking framework |
| `skills/technical-requirements/references/formats.md` | Status / question / applicability / append |
| `skills/technical-requirements/references/artifact-structure.md` | `tech-adr.md` skeletons |
| `skills/technical-requirements/references/web-search.md` | Adaptive retrieval |
