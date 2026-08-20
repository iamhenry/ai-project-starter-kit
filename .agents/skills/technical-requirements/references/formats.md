# Session Formats

Verbatim mandatory formats used during the category loop.

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

## HYBRID ASK (MANDATORY)

Before every Question tool call, in the same response:
1. TRACKING FORMAT status block
2. Full QUESTION FORMAT markdown for all residual gaps this turn (batch per category by default)
3. Then Question tool (`question` = one short sentence; `label` = 1–5 words + optional `(Recommended)`; `description` = one line `MUST: … | PRO: … | CON: …`)

Never Question-tool-only.

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

2–N. **[Same structure as option 1]** — repeat for each remaining choice (typically 3–5 total options)

N. **[Search for best practices]** (optional last option)
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

When a category reaches 90%+ clarity:
1. Write the **full** section per `ARTIFACT STRUCTURE` (Minimum bar — not summary-only)
2. **Auto-append** to `_ai/docs/tech-adr.md` (do not wait for yes/no)
3. Optionally show a short notice (non-blocking):

```
═══════════════════════════════════════════════════════════════════════
CATEGORY COMPLETE: [Category Name] — APPENDED
CLARITY: [X]%
═══════════════════════════════════════════════════════════════════════

Appended §[N] to `_ai/docs/tech-adr.md`. Next: Category [N+1]
```

Session may still include Simple Decision / How It Works / Category Decisions / Code Evidence in chat for transparency; **file write must be full artifact-structure depth.**

---
