# Workflow

Verbatim workflow sections from technical-requirements Phase 2.

---

## EXECUTION ORDER

| Step | What                                           | Section                                       | When                              |
| ---- | ---------------------------------------------- | --------------------------------------------- | --------------------------------- |
| 0    | Check input file                               | INPUT                                         | First                             |
| 1    | Read and summarize product requirements        | WORKFLOW -> Initial Response                  | After input check                 |
| 2    | Spawn 6 research subagents                     | RESEARCH PHASE                                | Before categories                 |
| 3    | Synthesize findings and approaches             | RESEARCH PHASE -> Synthesis Format            | After all agents return           |
| 4    | User selects approach and create ADR-000       | RESEARCH PHASE -> After User Selects Approach | Before Category 1                 |
| 5    | Work through categories 1-15 in order          | CATEGORIES + WORKFLOW -> Category Loop        | Sequentially                      |
| 6    | Auto-append full category sections to artifact | CATEGORY APPEND FORMAT                        | After 90% clarity (no yes/no wait)|
| 7    | Completeness gate, then final verification     | WORKFLOW -> Completeness Gate + Final Verification | After all categories        |
| 8    | Display completion message                     | WORKFLOW -> Completion                        | After verification passes         |

**Key rules throughout:**
- Status block every response; hybrid Ask (QUESTION FORMAT markdown then Question tool); batch gaps per category (CRITICAL RULES).
- Gaps-only: skip product-adr / already-locked items.
- Run verification triage for factual decisions (WORKFLOW -> Category Loop).
- Completeness gate before PHASE 2 COMPLETE.

---

## WORKFLOW

### Progress Tracking

- MANDATORY: Use the built-in todo list to track category progress
- **Initialize** the todo list after Research Phase with all 15 categories
- Use `todoread` or `todowrite` or similar tools in your built-in tools to actively track progress

### Initial Response
1. Verify product requirements file was provided
2. Read and summarize the product requirements
3. Create `_ai/docs/` directory if it doesn't exist
4. Create/update `technical-requirements-workflow-feedback.md` (append friction live if user corrects workflow)
5. If repo stack exists (`package.json` / app): note it for codebase-first research (see research-phase)
6. **RESEARCH PHASE:** Spawn 6 parallel subagents (Product Teardown, Open Source Scan, Framework Compare, Cost Projection, Architecture Patterns, SaaS Boilerplate) — codebase-first when stack locked
7. **SYNTHESIS:** Present raw findings summary + 5 distinct approaches + recommendation
8. **APPROACH SELECTION:** User selects approach → Create ADR-000 (with selected + rejected approaches)
9. Start with Category 1 (Boundaries)
10. Ask applicability check: "Let's start with Boundaries. Based on the product requirements, let me identify what's technically out of scope."

### Category Loop
1. Display applicability check (self-assessed) for the category
2. Gaps-only: list already-locked items (product-adr / prior tech-adr); do not re-ask them
3. If NOT APPLICABLE: append short N/A section (why); continue
4. If applicable with residual gaps: **batch** all gap questions — status block + full QUESTION FORMAT markdown + Question tool (hybrid). If no gaps: append full section from locks/defaults
5. After user answers, run Verification Triage:
   - Decision type: Preference | Factual | High-risk factual
   - Confidence: High (>=85%) | Medium (50-84%) | Low (<50%)
   - Action:
     - Preference + High confidence -> proceed without retrieval
     - Factual + Medium confidence -> quick check (1 official source)
     - High-risk factual or Low confidence -> deep check (2+ sources, spawn 1-3 focused subagents when useful)
     - Default for factual/high-risk factual decisions: favor focused subagent verification unless recent, high-confidence evidence is already available
6. Track clarity after answers (use verified facts when retrieval is triggered)
7. When category reaches 90%:
   - Spawn subagent for current docs research when code examples would help
   - Auto-append **full** section to `tech-adr.md` (artifact-structure depth; no yes/no wait)
   - Brief "Appended §N" notice; move to next category

### Retroactive Updates

If new information surfaces that affects a previously skipped or completed category:

```
───────────────────────────────────────────────────────────────────────
CONTEXT UPDATE DETECTED

While clarifying [Current Category], you mentioned "[new info]."

This affects [Prior Category] which was [skipped/already completed].

Options:
1. Pause, revisit [Prior Category] now, then resume here
2. Continue, append [Prior Category] as follow-up at the end
3. Note for implementation phase

Which approach?
───────────────────────────────────────────────────────────────────────
```

### Completeness Gate (before Final Verification)

Before PHASE 2 COMPLETE / final verification:
1. Each applicable category section meets Minimum bar in `artifact-structure.md` (types/contracts/flows as relevant — not summary-only)
2. Each NOT APPLICABLE category has an explicit N/A section
3. Junior heuristic: implementable from `tech-adr.md` + `product-adr.md` alone
4. If thin: **expand pass** on weak sections, then continue

### Final Verification

Before completion, spawn 3 parallel verification subagents to validate the **full** `tech-adr.md` (post–completeness gate).

| Agent           | Mission                                             | Pass Criteria                           |
| --------------- | --------------------------------------------------- | --------------------------------------- |
| **Alignment**   | Decisions trace to product requirements             | All decisions linked or marked optional |
| **Consistency** | Types, APIs, data models consistent across sections | No contradictory definitions            |
| **Assumptions** | Flag claims without grounding/evidence              | Zero ungrounded assumptions             |

**Flow:**
1. Spawn 3 agents in parallel with full `tech-adr.md` content
2. Each returns: `STATUS: PASS | FAIL` + issues table if any
3. **Any FAIL:** Present issues, user must fix, re-verify
4. **All PASS:** Append verification summary, proceed to completion

**Agent Output:**
```
STATUS: PASS | FAIL

ISSUES:
| Section | Issue | Fix |
| ------- | ----- | --- |
```

**Verification Summary (append to tech-adr.md):**
```markdown
## Verification Summary
Verified: [DATE]
Result: PASS
```

### Completion
1. When all categories complete, append "Implementation Roadmap" section
2. Display final message:
```
═══════════════════════════════════════════════════════════════════════
PHASE 2 COMPLETE
═══════════════════════════════════════════════════════════════════════

Artifact: `_ai/docs/tech-adr.md`

All 15 categories have been clarified. The technical specification is ready.

This spec is detailed enough for a junior developer to begin implementation.

NEXT STEP: Create `roadmap.md` from the Implementation Roadmap section and begin building.
```

---
