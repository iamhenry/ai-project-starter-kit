# Rules & Principles

Verbatim critical rules, principles, and frameworks from technical-requirements Phase 2.

---

## CRITICAL RULES

### Questioning Rules
1. **One question at a time** - Ask exactly ONE question per response
2. **Numbered options required** - Every question MUST provide 3-5 numbered options
3. **Plain-language scenario framing** - Frame each question as a concrete scenario in everyday words a non-developer could understand. Avoid technical jargon in the question itself (e.g. "type contracts", "schema migration", "reactive subscriptions"). Describe the *decision being made* in terms of what happens, not how it's implemented.
   - Plain language test: "Could someone who doesn't code understand what's being decided from the question alone?"
   - Before/after example — BAD: "How should types flow between the Convex schema and the React client?" | GOOD: "When the database defines what a result looks like, does your UI code use that definition directly — or define its own copy?"
4. **Complete option format** - Each option MUST include: Why pick this, User impact, Tradeoff, Complexity with time estimate, Technical details
   - Option titles must be acceptance-criteria-style statements in simple natural language that are scannable at a glance.
5. **Grounded suggestions only (adaptive)** - Memory is a starting point, not final evidence.
   - Use retrieval when claims are factual and impactful (pricing, API behavior, security, limits, version-specific behavior)
   - Skip retrieval when the decision is preference-only and does not depend on external facts
   - Be liberal with focused verification subagents when factual uncertainty exists; prefer quick verification over unverified memory
   - Keep verification subagents narrow: 1 for quick checks, up to 3 for deep checks
   - If uncertain, state explicitly: "I need to research this"
   - Source priority: Official docs > Maintainer docs/repo > Recent issues/changelog > Third-party blogs
   - Then present grounded options with citations (URL + accessed date + version/date context)
6. **Reference product requirements** - Tie technical decisions back to product needs
7. **Favor idiomatic & pragmatic** - Weight recommendations toward options that are idiomatic to the stack and pragmatic for solo dev context
8. **Avoid layered solutions by default** - In solo dev validation phase, do not propose multi-layered solutions when one simple approach meets the need (see Progression Rule 3).

### Progression Rules
1. **90% clarity threshold** - Cannot move to next category until current is at 90%+
2. **Self-assessed applicability** - Before each category:
   - Re-read product requirements + all previously clarified decisions
   - Self-assess: Is this category fully, partially, or not applicable?
   - State reasoning briefly to the user (do NOT ask the user)
   - Proceed with applicable portions, skip what doesn't apply
   - User can override if AI's assessment is wrong
3. **No over-engineering** - Recommend simplest solution that meets requirements
4. **Thin end-to-end first** - Prioritize decisions for the tracer bullet implementation

### Artifact Rules
1. **Preview before writing** - Before appending to `tech-adr.md`, show a preview and ask: "Does this look correct before I append?"
2. **Create directory if needed** - If `_ai/docs/` doesn't exist, create it
3. **Incremental append** - After each category clears, append that section to the artifact
4. **Never overwrite** - Always append, never replace existing content
5. **Capture decision rationale** - For each significant decision in a category, record the options considered and why the choice was made
6. **Full detail** - Include schemas, contracts, versions - detailed enough for a jr dev to start building

---

## FORMATS (Reference)

Use these templates while running the category loop.

---

## TRACKING FORMAT (MANDATORY)

Display this status block in EVERY response:

```
| Field        | Value                         |
| ------------ | ----------------------------- |
| **OVERALL**  | [X]% remaining                |
| **GROUP**    | [Phase Name] ([N]/6)          |
| **CATEGORY** | [Name] ([X]/15)               |
| **CLARITY**  | [X]/[Y] items resolved ([Z]%) |
```

**Calculation:** `[X]% remaining = 100 - ((completed categories / 15) × 100)` — represents how much of the entire 15-category workflow remains to be done.

## QUESTION FORMAT (MANDATORY)

```
### QUESTION [N] of [TOTAL]: [Plain-language question — no jargon, describe what happens not how it works]

**USER IMPACT**: [1 sentence - why this matters to the user]

1. **[UX TITLE: What users experience if this is chosen]** (Recommended)
   - Why: [1 sentence explaining why this is better for current constraints]
   - How: [1 sentence detail implementation approach/mechanism (for engineering record)]
   - Tradeoff: [Primary downside or risk]
   - Complexity: [Low/Medium/High] | [Time estimate]
   - Over-engineered? [No / Yes: explanation/suggestion]

2. **[UX TITLE: What users experience if this is chosen]** 
   - Why: [1 sentence explaining why this is better for current constraints]
   - How: [1 sentence detail implementation approach/mechanism (for engineering record)]
   - Tradeoff: [Primary downside or risk]
   - Complexity: [Low/Medium/High] | [Time estimate]
   - Over-engineered? [No / Yes: explanation/suggestion]

3. **[UX TITLE: What users experience if this is chosen]** 
   - Why: [1 sentence explaining why this is better for current constraints]
   - How: [1 sentence detail implementation approach/mechanism (for engineering record)]
   - Tradeoff: [Primary downside or risk]
   - Complexity: [Low/Medium/High] | [Time estimate]
   - Over-engineered? [No / Yes: explanation/suggestion]

4. **[Search for best practices]**
   - I'll research current best practices and library options for this

RECOMMENDATION: [1-2 sentences - favor idiomatic/pragmatic options; tie to solo dev, validation phase constraints]

SOURCES (only when factual verification is used):
- [Source URL, accessed YYYY-MM-DD, version/date]
```

### Question Format Field Reference

| Field            | Purpose                                                        |
| ---------------- | -------------------------------------------------------------- |
| Question         | Concrete user/product scenario, not implementation-framed      |
| User Impact      | Sets context for why decision matters to users                 |
| Option Title     | Acceptance-criteria-style statement in simple natural language |
| Recommendation   | Opinionated guidance tied to constraints                       |
| Why              | Explains why this is better for current constraints            |
| How              | Full engineering context for implementation                    |
| Tradeoff         | Primary downside/risk in plain language                        |
| Complexity       | Includes time estimate to help prioritize                      |
| Over-engineered? | Flags if solution is unnecessarily complex for current phase   |
---

## APPLICABILITY CHECK FORMAT

Before each category, display this self-assessment:

```
───────────────────────────────────────────────────────────────────────
CATEGORY [N]: [Name]
───────────────────────────────────────────────────────────────────────

APPLICABILITY CHECK (self-assessed):

Reviewing:
  • Product requirements: [relevant mentions or lack thereof]
  • Prior decisions: [relevant clarifications from earlier categories]

ASSESSMENT: [APPLICABLE | PARTIALLY APPLICABLE | NOT APPLICABLE]
  • [Aspect 1]: [YES/NO] - [reason]
  • [Aspect 2]: [YES/NO] - [reason]

[If APPLICABLE]: Proceeding with full category.
[If PARTIALLY APPLICABLE]: Focusing on [X, Y], skipping [Z].
[If NOT APPLICABLE]: Skipping this category because [reason].

(Correct me if I'm missing something)
───────────────────────────────────────────────────────────────────────
```

---

## CATEGORY APPEND FORMAT

When a category reaches 90% clarity, present this preview.
For this category-finalization preview only, include `Simple Decision` and `How It Works (Plain)` sections.

**CRITICAL:** Preview is for session display. When writing to `tech-adr.md`, use the format defined for that category in `ARTIFACT STRUCTURE`.

```
═══════════════════════════════════════════════════════════════════════
CATEGORY COMPLETE: [Category Name]
CLARITY: [X]%
═══════════════════════════════════════════════════════════════════════

PREVIEW - I will append the following to `_ai/docs/tech-adr.md`:

---

## [Category Name]

[Formatted content based on clarified items]

### Simple Decision

[4-6 plain-language bullets explaining decision summary]

### How It Works (Plain)

[2-4 plain-language bullets explaining how the decision works]

### Category Decisions

#### [Topic]: [Choice Made]
- **Why:** [1-2 sentence rationale tying back to constraints]

#### [Topic]: [Choice Made]
- **Why:** [1-2 sentence rationale]

### Code Evidence
[Optional - include if subagent was spawned]

```typescript
// Source: [Framework] v[X.Y]
// URL: [docs URL]
[code snippet]

---

Does this look correct? Reply "yes" to append, or provide corrections.
```

---

## Principles
- Default to building a thin, working end-to-end slice as an mvp, then iterate.
- We start off with zero users at first so we dont need solutions that are scaled to tons of users
- I'm an indie solo dev so pricing is critical for me to keep low, so we must find a balance here.
- We are in the validation phase we should not be adding features or scope creep
- Always provide idiomatic options to your questions

### Pivot-Friendly Integration Pattern
- When data source implementation is uncertain (e.g., LLM API vs direct API), isolate behind stable output types
- Consumers depend on the WHAT (data shape), not the HOW (fetching mechanism)
- Swap cost should be ONE file change, not a refactor

---

## FRAMEWORKS APPLIED

1. **ADR (Architecture Decision Records)** - Structured format for "which approach and why"
2. **Five Whys** - Drill into technical constraints and rationale
3. **RFC-style Tradeoff Analysis** - Options table with pros/cons/complexity

---
