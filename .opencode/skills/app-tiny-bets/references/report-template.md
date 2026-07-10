# App Tiny Bets Report Template

Save this complete structure as the markdown artifact. In chat, return only `Short Verdict` and the artifact path.

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

## Short Verdict
[One sentence: best app to build first and why.]

## Top Opportunities

[Repeat this opportunity block up to 3 times.]

### 1. [App idea]
- Keyword case: [primary keyword; popularity; difficulty; intent; competitor source or independent; store/date]
- Adjacent keywords: [2-6 keywords, or None]
- Market case: [Demand High/Medium/Low; Competition Easy/Medium/Hard; relevant top-10 results; apps with 100+ ratings; newer entrant signal; name collision]
- Commercial case: [Payment Strong/Medium/Weak; revenue estimate; source/date/confidence; monetization model]
- Product: [one core feature; 1-3 MVP items; positioning or quality gap]
- Feasibility: [Execution fit Strong/Medium/Weak; dependency fit; reuse or main unknown; cost cap; trust assumption]
- Main risk: [risk]
- Confidence: [High/Medium/Low + missing evidence]
- Verdict: [Build / Watch / Skip]

Competitors:
| Competitor | Weight | Ratings | Freshness or quality gap | Revenue/payment evidence |
| --- | --- | --- | --- | --- |
| [app] | Strong/Medium/Weak | [count] | [brief signal] | [$ amount/range or Unknown + source] |

## Rejected Ideas
| Idea | Failed bar | Reason rejected |
| --- | --- | --- |

## Next Step
[The single next research or build step.]
```

Keep the report short. Prefer evidence and decisions over explanation. Do not include raw Astro/web dumps or personal/private data.

If no candidate passes, omit `Top Opportunities`, say that no validated opportunity was found, list the strongest rejected ideas, and give one next seed or category to test.
