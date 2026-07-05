# App Tiny Bets Rubric

Use this rubric before recommending any idea. Defaults are conservative for a new app with no authority.

## Keyword Pass Bar

| Signal | Pass | Strong pass | Reject |
| --- | --- | --- | --- |
| Popularity | `20+` in Astro, or clear search demand if scale differs | `30+` with relevant results | Below `20` unless it is a paid niche with strong competitors |
| Difficulty | `<= 60-70` for first exploration | `<= 50` for a new app | High difficulty with entrenched incumbents |
| Intent | User is searching for an app solution | Search phrase maps to one obvious feature | Informational, brand-led, or vague intent |
| Adjacent keywords | 2+ related terms exist | Cluster supports future tiny bets | One isolated keyword only |

If Astro uses a different scale, translate the spirit: meaningful demand, not overcrowded, and relevant to a narrow user problem.

Discard keywords when demand is weak, results are irrelevant, top results are all giant incumbents, the query is brand/trademark-led, or user intent is not app-download intent.

## Competitor Proof Bar

Look for 3-5 competitors, then judge whether the market is real but still enterable.

| Signal | Pass | Strong pass | Reject |
| --- | --- | --- | --- |
| Ratings | At least some competitors have `100+` ratings | 2-4 competitors have meaningful ratings, not every result is huge | No one has ratings, or all top apps are massive incumbents |
| Density | 3-5 relevant competitors exist | Keyword looks competitive, but only a few apps have `100+` ratings | No relevant apps, or every top result is too authoritative |
| Freshness | Recent apps can rank or have traction | Newer apps, e.g. 2024-2026, show the niche is still moving | Only old entrenched apps dominate |
| Quality gap | Existing apps have obvious UX, screenshot, review, or feature gaps | Users complain about price, accuracy, ads, UX, or missing feature | Competitors are polished, broad, and hard to beat |
| Positioning | Competitor screenshots show clear value promises to learn from | Competitors reveal repeated promises you can satisfy with one feature | No clear value promise or screenshots imply a broad app |
| Related keywords | Competitors rank across related terms | Multiple keyword angles exist for the same audience | Competitor set is unrelated/noisy |

If the exact keyword is already a competitor's app name, do not assume you can use that phrase as the product name. Keep it as a keyword target or find an adjacent phrase.

## Competitor Weighting

Use plain language, not fake precision.

| Signal | Weight | Why it matters |
| --- | --- | --- |
| Keyword relevance | 35% | They solve the exact searched problem |
| Ratings/reviews | 25% | Indicates market pull and App Store authority |
| Monetization evidence | 25% | Shows users may pay |
| Freshness/quality gap | 15% | New or mediocre apps mean room to compete |

Final competitor weight labels: `Strong`, `Medium`, or `Weak`.

## Revenue And Payment Bar

Revenue benchmark: look for proof the market makes money, roughly `100-200 EUR/month minimum` for small competitors. Use this as a floor, not a precise forecast.

Capture hard monthly revenue numbers wherever a credible source provides them. A market with competitors around `$100/mo` is very different from one with competitors around `$1k+/mo`; reflect that in the verdict.

| Grade | Evidence |
| --- | --- |
| Strong | Public monthly revenue estimate or maker post, especially `$1k+/mo`; multiple competitors with IAP/subscription; reviews mention trial, premium, paywall, price, or paid unlocks |
| Medium | Public estimate around `$100-999/mo`, one monetized competitor, visible IAPs, or adjacent category revenue evidence |
| Weak | Demand exists but monetization is unclear |
| Reject | No paid competitors, no IAP/subscription evidence, and no credible reason users would pay |

Do not recommend `Build` unless payment evidence is `Medium` or `Strong`.

Revenue estimate labels:

- `Exact`: source gives a specific monthly number.
- `Range`: source gives a range or directional estimate.
- `Unknown`: no credible number found; use payment signals instead.

## Tiny-Bet Fit Bar

The idea must map to one core feature that can ship quickly.

Pass examples:

- Camera/photo -> AI identification -> result -> history
- Text/photo input -> answer/explanation -> save/share
- Scan/import -> convert/extract/analyze -> export

Reject or downgrade when the app needs:

- Network effects or social graph
- Marketplace supply
- Medical, legal, or financial accuracy risk
- Heavy backend operations before the first user gets value
- Long content library creation before launch

## Monetization Fit

Use this monetization heuristic:

- Recurring-use apps can support weekly/yearly subscriptions.
- Single-use or occasional utilities may fit lifetime or one-time unlocks better.
- If competitors all monetize but the app is likely single-use, do not force a subscription recommendation; note the mismatch.

## Scorecard

| Dimension | Rating |
| --- | --- |
| Demand | High / Medium / Low |
| Competition | Easy / Medium / Hard |
| Payment evidence | Strong / Medium / Weak |
| Build complexity | Easy / Medium / Hard |
| Tiny-bet fit | Strong / Medium / Weak |
| Confidence | High / Medium / Low |

## Final Decision Rules

- `Build`: Keyword passes, 3-5 real competitors, payment evidence is Medium/Strong, one-feature MVP is clear.
- `Watch`: Demand exists but one key proof is missing; give the next data point to verify.
- `Skip`: Weak demand, weak payment evidence, too much competition, or MVP is not tiny.

Post-launch signal: after release, winners are apps whose organic boost does not sink quickly. This skill does not run post-launch analysis, but it should prefer ideas with adjacent keywords and a clear path to revisit if they float.

When evidence conflicts, prefer the safer verdict. A tiny bet should be cheap to validate, not a justification for ignoring weak demand.
