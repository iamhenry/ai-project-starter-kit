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

## Invoke

1. Load skill `technical-requirements` (`.opencode/skills/technical-requirements/SKILL.md`).
2. Pass the product requirements file from the command arguments (e.g. `@_ai/docs/product-adr.md`).
3. Execute the skill end-to-end. Do not reimplement the flow in this command.

**Input:** Product requirements path (required).  
**Output:** `_ai/docs/tech-adr.md`

If no file is provided, respond with the skill's INPUT error block (same copy as skill).

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
