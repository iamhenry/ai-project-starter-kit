# App Tiny Bets Report Template

Save this complete structure as the single canonical markdown artifact for the research run. Combine qualified profile-aligned and independent opportunities in this report; never create parallel profile-specific reports. In chat, return only `Short Result` and the artifact path.

Artifact path:

```md
app-tiny-bets-reports/YYYY-MM-DD-[seed-or-topic]-research.md
```

Create `app-tiny-bets-reports/` at the workspace root if it does not exist. Use a lowercase slug for `[seed-or-topic]`, e.g. `stamp-identifier` or `student-tools`.

```md
# App Tiny Bets Research

## Inputs Used
- Platform: iOS US
- Starting mode: [app link / keyword / category / discovery]
- Seed: [seed]
- Evidence captured: [YYYY-MM-DD]
- Candidate mix: profile-aligned and independent candidates researched together

## Short Result
[One sentence: best app to build first and why.]

## Top Opportunities

[Repeat this opportunity block up to 3 times. Any value that fails a rubric bar excludes the candidate from this section.]

### 1. [App idea]
- Keyword case: [primary keyword; popularity; difficulty; intent; competitor source or independent; store/date]
- Profile fit: [Aligned/Adjacent/Independent; short reason. Context only, never market evidence]
- Adjacent keywords: [2-6 keywords, or None]
- Market case: [Demand High/Medium; Entry Open/Competitive; relevant top-10 results; apps with 100+ ratings; release/newer entrant signal; exact-title collision]
- Commercial case: [Payment Strong/Medium; qualifying precise revenue anchors; monetization model]
- Product: [one core feature; concrete better-or-faster wedge; 1-3 MVP items]
- Feasibility: [Execution fit Strong/Medium; dependency fit; reuse or main unknown; cost cap; trust assumption]
- Portfolio leverage: [Strong/Medium/Weak; reusable code/UI and adjacent audience keywords]
- Distribution fit: [Strong/Medium/Weak; ASO plus demonstrable social or bounded paid-acquisition angle]
- Main risk: [risk]
- Confidence: [High/Medium + missing evidence]

Competitors:
| Competitor | Weight | Ratings | Freshness or quality gap | Payment context |
| --- | --- | --- | --- | --- |
| [app] | Strong/Medium/Weak | [count] | [brief signal] | [IAP/subscription signal or None found] |

Revenue-proof competitors:
| Competitor | Exact source value | Value type | Estimate period | Storefront/scope | Evidence type | Source URL | IAP/subscription evidence | Captured | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [directly relevant app] | [precise amount or range] | [Precise] | [period] | [storefront/scope] | [Maker disclosure/Commercial estimate/Corroborated public model] | [URL] | [optional] | [date] | [High/Medium/Low] |

[Include only precise anchors that qualify under the rubric. Never use `Unknown` or upper bounds in this table. Every opportunity has at least 1 row; additional precise anchors strengthen confidence.]

## Next Step
[The single next research or build step.]
```

Keep the report short. Prefer evidence and decisions over explanation. Do not include raw Astro/web dumps or personal/private data.
Rank strictly by qualification strength and tiny-bet quality. Do not reserve slots for either profile-aligned or independent ideas.

If no candidate passes, use this short artifact instead:

```md
# App Tiny Bets Research

## Inputs Used
- Platform: iOS US
- Starting mode: [app link / keyword / category / discovery]
- Seed: [seed]
- Evidence captured: [YYYY-MM-DD]

## Short Result
No build-ready opportunity was found within the research cap.

## Next Research Direction
[One seed or category to test next and why.]
```

Do not include candidate, opportunity, competitor, or rejection sections in a no-opportunity artifact.
