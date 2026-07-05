# App Tiny Bets Report Template

Return this structure and save the same content as a markdown artifact.

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

## Short Verdict
[One sentence: best app to build first and why.]

## Top Opportunities

### 1. [App idea]
- Primary keyword: [keyword]
- Adjacent keywords: [3-6 keywords]
- Demand: [High/Medium/Low + evidence]
- Competition: [Easy/Medium/Hard + evidence]
- Estimated monthly revenue: [$ amount/range or Unknown + source/confidence]
- Payment evidence: [Strong/Medium/Weak + citations or source notes]
- Monetization model: [subscription / lifetime / one-time / unclear + why]
- One core feature: [feature]
- Competitor positioning notes: [1 short sentence on screenshot/value promises]
- MVP scope: [1-3 bullets]
- Build complexity: [Easy/Medium/Hard]
- Risk: [main risk]
- Verdict: [Build / Watch / Skip]

Competitors:
| Competitor | Weight | Est. monthly revenue | Why it matters | Monetization signal |
| --- | --- | --- | --- | --- |
| [app] | Strong/Medium/Weak | [$ amount/range or Unknown] | [brief rationale] | [IAP/revenue/reviews/unknown] |

## Rejected Ideas
| Idea | Reason rejected |
| --- | --- |

## Next Step
[The single next research or build step.]
```

Keep the report short. Prefer evidence and decisions over explanation. Do not include raw Astro/web dumps or personal/private data.
