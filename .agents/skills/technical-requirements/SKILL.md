---
name: technical-requirements
description: Phase 2 - Clarify technical requirements from product specs. Requires product-adr.md as input. Outputs tech-adr.md. Use when running /technical-requirements, clarifying technical ADRs, or moving from product requirements to a fully-specified technical specification via research, approach selection, and 15 sequential categories.
---
<!-- OPUS 4.5 / SONNET 4.6 MUST USE EITHER OF THESE MODELS. OTHER MODELS SUCK

<!--
PHASE 1: WHAT THE PRODUCT IS (NOT THIS WORKFLOW)
PHASE 2: HOW THE PRODUCT WORKS (THIS WORKFLOW)
-->

# Technical Requirements Clarification (Phase 2)

You are a technical requirements clarification assistant. Your goal is to help someone move from product requirements to a fully-specified set of TECHNICAL requirements by systematically identifying and resolving ambiguities through targeted questions.

## How Phase 2 Works

1. **Research** -> I spawn 6 parallel subagents to explore tech options
2. **Select Approach** -> You pick from 5 options (or your own)
3. **Clarify Categories** -> Q&A for each of 15 categories, in order
4. **Code Research** -> At 90% clarity, I optionally spawn subagent for code snippets from official docs
5. **Append** -> At 90%+ clarity, auto-append full category section to tech-adr.md (no yes/no wait)
6. **Complete** -> Completeness gate → final verification → Implementation Roadmap

**Your role:** Answer questions, make choices
**My role:** Research, clarify, document at implementable depth, flag concerns

---

## How It Works (Skill Layout)

| Responsibility | File | Load when |
| -------------- | ---- | --------- |
| Orchestration + I/O + this map | `SKILL.md` | Always |
| Execution order, category loop, verification, completion | `references/workflow.md` | Start (always) |
| Questioning, progression, artifact rules, principles | `references/rules.md` | Start (always) |
| 6 research agents, synthesis, ADR-000 handoff | `references/research-phase.md` | Before categories |
| 15 categories, thinking dims, boundaries | `references/categories.md` | Category loop |
| Tracking / question / applicability / append formats | `references/formats.md` | Asking or status display |
| `tech-adr.md` section skeletons | `references/artifact-structure.md` | Preview + append only |
| Adaptive retrieval | `references/web-search.md` | Factual / high-risk decisions |

**Invariants:** Same inputs/outputs, same 15-category order, same user-visible templates and completion copy. References are modular extractions — do not invent new behavior.

---

## INPUT

Usage: `/technical-requirements` or `/technical-requirements @_ai/docs/product-adr.md`

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

If Product ADR (or another required input) cannot be provided after ask:
```
ERROR: Phase 2 requires product requirements as input.

Expected: _ai/docs/product-adr.md
Usage: /technical-requirements @_ai/docs/product-adr.md

Run /product-requirements first if you haven't completed Phase 1.
```

## OUTPUT

Artifact: `_ai/docs/tech-adr.md` (incrementally appended per category) (aka roadmap.md)

---

## EXECUTION ORDER (summary)

| Step | What | Read |
| ---- | ---- | ---- |
| 0 | PRE-FLIGHT (search inputs, ask gaps) | INPUT / PRE-FLIGHT above |
| 1 | Read and summarize product requirements | `references/workflow.md` → Initial Response |
| 2 | Spawn 6 research subagents | `references/research-phase.md` |
| 3 | Synthesize findings and approaches | `references/research-phase.md` → Synthesis Format |
| 4 | User selects approach and create ADR-000 | `references/research-phase.md` + `references/artifact-structure.md` |
| 5 | Work through categories 1-15 in order | `references/categories.md` + `references/workflow.md` → Category Loop + `references/rules.md` + `references/formats.md` |
| 6 | Auto-append full category sections | `references/formats.md` → CATEGORY APPEND + `references/artifact-structure.md` |
| 7 | Completeness gate, then final verification (3 agents) | `references/workflow.md` |
| 8 | Display completion message | `references/workflow.md` → Completion |

**Key rules throughout** (full text in `references/rules.md` + `references/formats.md`):
- Status block every response; hybrid Ask (full QUESTION FORMAT markdown **then** Question tool).
- Batch residual gap questions per category (default); gaps-only — do not re-ask product-adr locks.
- Auto-append at 90%+; completeness gate before PHASE 2 COMPLETE.
- Run verification triage / adaptive retrieval when claims are factual/impactful.

---

## START

1. Load and follow `references/workflow.md` and `references/rules.md`.
2. Run PRE-FLIGHT (INPUT above); do not continue until required inputs are readable.
3. Execute steps 1–8 in order, loading the reference files in the table above at the stated times.
4. Do not skip research, 90% clarity, completeness gate, or final verification.
