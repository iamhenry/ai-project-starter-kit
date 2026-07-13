# App Tiny Bets Report Template

Save this complete structure as the single canonical markdown artifact for the research run. Combine qualified profile-aligned and independent opportunities in this report; never create parallel profile-specific reports. In chat, return only the artifact path, or a neutral completion line followed by the artifact path.

Artifact path:

```md
app-tiny-bets-reports/YYYY-MM-DD-[seed-or-topic]-research.md
```

Create `app-tiny-bets-reports/` at the workspace root if it does not exist. Use a lowercase slug for `[seed-or-topic]`, e.g. `stamp-identifier` or `student-tools`. Update this artifact as a run expands instead of creating another report.

Use this qualified-opportunity form for 1-5 opportunities:

```md
# App Research — Opportunity Comparison

**Market:** [platform and storefront, e.g. iOS US]
**Evidence refreshed:** [YYYY-MM-DD]
**Admission rule:** Only opportunities that pass every keyword, entry, native Apple substitute, payment, problem, customer, wedge, and feasibility gate are compared.

## Comparison at a Glance

[Write 2-3 neutral sentences describing the qualified set and material evidence differences. Do not make a build decision, assign a product status, or recommend an opportunity.]

| Rank | Opportunity | Demand / entry | Strongest traction proof | Revenue proof | Build risk | Evidence-backed product wedge |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [Opportunity] | [Demand grade and raw primary-keyword metrics; entry class] | [Concise strongest rank, ratings, release, or entrant evidence] | [Payment grade; displayed competitor estimate range; strongest qualifying anchor] | [Low/Medium/High from execution fit] | [Concrete complaint-backed wedge, supporting evidence, and material counter-evidence] |
| 2 | [Opportunity] | [Demand grade and raw primary-keyword metrics; entry class] | [Concise strongest traction proof] | [Payment grade; displayed competitor estimate range; strongest qualifying anchor] | [Low/Medium/High from execution fit] | [Concrete complaint-backed wedge, supporting evidence, and material counter-evidence] |

[Add one row per qualified opportunity, up to rank 5, and remove unused placeholder rows.]

Notes:
- Include qualified opportunities only. Do not include a build decision, recommendation, product status, or rejection section.
- Rank reflects relative evidence strength across the qualified set, not what the user should build.
- Each wedge cell includes the key supporting evidence and material counter-evidence.
- Revenue values are third-party estimates unless explicitly identified as maker disclosures. Exact values, periods, scopes, sources, capture dates, evidence types, and confidence live in the Evidence Appendix.

## Ranked Evidence Profiles

### #1 [Opportunity]

**One-line product:** [One bounded core flow that satisfies the searched job]

**Customer:** [Behavior-based narrow customer; desired outcome; current workaround or incumbent; citation. Never invent demographics]

**Evidence supporting the wedge**
- **Demand receipt:** [Primary keyword, popularity, difficulty, intent, store, capture date, and relevant result shape. Use `N/A`, never an invented value, when a keyword metric is unavailable]
- **Payment receipt:** [Payment Strong/Medium; `Displayed competitor estimates span $[lowest displayed lower bound]-$[highest displayed upper bound]/month`; qualifying direct anchor versus weaker modeled context, preserving original scopes]
- **Entry receipt:** [Relevant top-10 results; apps with 100+ ratings; release/newer entrant signal; exact-title collision; Open/Competitive rationale]
- **Review-backed wedge:** [1-2 sentence concrete better way plus representative complaint excerpt with reviewer, app, date, source URL, and honest recurrence label]
- **Why bounded:** [1-3 MVP items; one-developer feasibility; cost cap; reliability/trust assumption; dependency fit]
- **Builder-profile context:** [Aligned/Adjacent/Independent and brief reason. Context only, never market evidence]

**Risks and counter-evidence:** [Main risks, contradictory evidence, complaint limitations, competition, and trust or dependency concerns]

**MVP boundary:** [Included core flow and explicit exclusions]

**Business model:** [Simplest likely subscription, lifetime, or one-time model and evidence-based fit]

**Key execution unknown:** [Single most important uncertainty to test]

**Confidence:** [High/Medium plus missing evidence or scope limitations]

**Evidence rationale:** [For rank 1, explain why its evidence is strongest relative to the other qualified opportunities without recommending it]

### #2 [Opportunity]

[Repeat the complete profile above. For ranks 2-5, replace `Evidence rationale` with `Ranking tradeoff` and explain which evidence is weaker and which evidence may be stronger than higher-ranked opportunities.]

## Evidence Appendix

## A. Research Inputs and Limits

- Platform / market: [platform and storefront]
- Discovery date: [YYYY-MM-DD]
- Evidence refresh date: [YYYY-MM-DD]
- Candidate coverage: [starting mode, seed, candidate pools, total candidates researched, and research cap]
- Sources: [Astro, App Store, review sources, commercial intelligence providers, maker disclosures, and other public sources used]
- Estimate limits: [Third-party estimates are not actual revenue; note period/storefront/scope ambiguity and model limitations]
- Review limits: [Coverage, recurrence strength, excerpt limitations, and possible review-selection bias]
- Missing metrics: [List unavailable metrics and use `N/A`; never infer or invent them]

## B. [Opportunity]

**Market:** [Neutral synthesis of demand, entry, payment, wedge, feasibility, risks, and confidence]

| Keyword | Role | Popularity | Difficulty | Note |
| --- | --- | --- | --- | --- |
| [Keyword] | [Primary / adjacent / competitor-derived] | [Raw score or `N/A`] | [Raw score or `N/A`] | [Intent, rank/result evidence, store, capture date, or limitation] |

| Competitor | Market traction | Revenue evidence | Evidence implication |
| --- | --- | --- | --- |
| [Directly relevant qualifying competitor] | [`[keyword]` rank; exact US rating count; average rating; release/freshness evidence] | [Positive numeric amount/range; period; platform/storefront or stated scope; source URL/provider; evidence type; captured YYYY-MM-DD; High/Medium/Low confidence] | [Scope, freshness, entry evidence, weakness, or counter-evidence affecting relative evidence strength] |
| [Positive-revenue competitor, if evidenced] | [Rank, ratings, rating average, release/freshness evidence] | [Positive numeric estimate or maker disclosure with complete metadata] | [Evidence implication and limitations] |

[Repeat appendix sections C-F for each remaining qualified opportunity. Research 3-5 competitors internally, but display only rows with evidenced positive app-level revenue estimates or positive numeric maker disclosures. Every displayed range must have a lower bound greater than zero. Search relevant competitors for a profitable replacement when evidence is nonpositive, unknown, or upper-bound-only; otherwise omit the row. Never display `$0`, nonpositive, unknown, upper-bound-only, or missing-value revenue rows, and never convert an upper bound into an estimate. Every opportunity still needs at least one directly relevant qualifying above-floor anchor. Ratings, rank, downloads, pricing, IAPs, and subscriptions never become revenue evidence.]
```

Keep the comparison concise and move detailed keyword and competitor evidence to the appendix. Preserve complaint excerpts, counter-evidence, feasibility, risks, MVP, business model, scope, confidence, and exact revenue metadata. Prefer evidence over explanation. Do not include raw Astro/web dumps or personal/private data.

If no candidate passes, use this short artifact instead:

```md
# App Research — Opportunity Comparison

**Market:** [platform and storefront, e.g. iOS US]
**Evidence refreshed:** [YYYY-MM-DD]
**Admission rule:** Only opportunities that pass every keyword, entry, native Apple substitute, payment, problem, customer, wedge, and feasibility gate are compared.

## No Qualified Opportunities

No opportunity met every admission gate within the research cap.

## Next Research Direction

[One evidence-driven seed or category to test next, with a neutral reason.]
```

Do not include candidate, opportunity, competitor, rejection, or failed-candidate sections in a no-opportunity artifact.
