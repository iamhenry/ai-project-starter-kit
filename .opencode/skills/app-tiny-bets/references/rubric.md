# App Tiny Bets Rubric

Use this rubric before recommending any idea. Defaults are conservative for a new app with no authority.

## Keyword Pass Bar

| Signal | Pass | Strong pass | Reject |
| --- | --- | --- | --- |
| Popularity | `20+` in Astro, or clear search demand if scale differs | `30+` with relevant results | Below `20` unless it is a paid niche with strong competitors |
| Difficulty | `<= 60` for a new app | `<= 50` | Above `60`, unless payment proof and an enterable quality gap justify `Watch` |
| Intent | User is searching for an app solution | Search phrase maps to one obvious feature | Informational, brand-led, or vague intent |
| Adjacent keywords | Helpful but not required | Cluster supports future tiny bets | Never reject solely because the keyword is isolated |

Treat these as practitioner defaults on Astro's scale, not universal market facts. Preserve raw scores, store, and capture date. If the scale changes, explain the calibration instead of silently replacing the thresholds.

Discard keywords when demand is weak, results are irrelevant, top results are all giant incumbents, the query is brand/trademark-led, or user intent is not app-download intent.

## Competitor Proof Bar

Inspect the top 10 results, then choose 3-5 relevant competitors and judge whether the market is real but still enterable.

| Signal | Pass | Strong pass | Reject |
| --- | --- | --- | --- |
| Ratings | At least some competitors have `100+` ratings | 2-4 competitors have meaningful ratings, not every result is huge | No one has ratings, or all top apps are massive incumbents |
| Density | 3-5 relevant competitors exist | Keyword looks competitive, but only a few apps have `100+` ratings | No relevant apps, or every top result is too authoritative |
| Freshness | Recent entrants show traction | Multiple newer apps have earned ratings or ranking visibility | Only old entrenched apps dominate |
| Quality gap | Existing apps have obvious UX, screenshot, review, or feature gaps | Users complain about price, accuracy, ads, UX, or missing feature | Competitors are polished, broad, and hard to beat |
| Positioning | Competitor screenshots show clear value promises to learn from | Competitors reveal repeated promises you can satisfy with one feature | No clear value promise or screenshots imply a broad app |
| Related keywords | Competitors rank across related terms | Multiple keyword angles exist for the same audience | Competitor set is unrelated/noisy |

If the exact keyword is already a competitor's app name, do not assume you can use that phrase as the product name. Keep it as a keyword target or find an adjacent phrase.

## Competitor Weighting

Use this order instead of fake numeric precision:

1. Keyword relevance: does the app solve the exact searched problem?
2. Ratings/reviews: is there meaningful market pull and authority?
3. Monetization: is there credible evidence users pay?
4. Freshness/quality gap: can a newer or narrower app enter?

Label a competitor `Strong` when it is directly relevant with meaningful traction or payment proof, `Medium` when evidence is partial, and `Weak` when relevance or traction is low. Freshness supports enterability; it is not a documented App Store ranking factor.

## Revenue And Payment Bar

Revenue benchmark: require credible direct evidence that at least one relevant competitor makes roughly `$100-200/month equivalent` or more. Use this as a floor, not a forecast for the proposed app.

Capture hard monthly revenue numbers wherever a credible source provides them. A market with competitors around `$100/mo` is very different from one with competitors around `$1k+/mo`; reflect that in the verdict.

| Grade | Evidence |
| --- | --- |
| Strong | Credible direct estimate for a relevant competitor, especially `$1k+/mo`, supported by multiple monetized competitors or paid-user signals |
| Medium | Credible direct estimate for a relevant competitor at or above the `$100-200/month` floor |
| Weak | Revenue is below the floor, unknown, inferred only from IAPs, or supported only by adjacent-category evidence |
| Reject | No direct revenue estimate, no paid competitors, and no credible reason users would pay |

Do not recommend `Build` unless payment evidence is `Medium` or `Strong`. Payment proxies without a credible direct estimate can justify only `Watch`.

Revenue estimate labels:

- `Exact`: source gives a specific monthly number.
- `Range`: source gives a range or directional estimate.
- `Unknown`: no credible number found; use payment signals instead.

## Tiny-Bet Fit Bar

The idea must map to one bounded core flow that relies mostly on an existing app foundation, platform capabilities, or mature libraries. Judge implementation shape and uncertainty, not elapsed time; human and AI-assisted execution speeds vary too much for calendar estimates to be reliable.

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

Before `Build`, answer three questions:

1. Can one developer deliver the core result without introducing multiple uncertain subsystems or a new operational system?
2. Can API, infrastructure, and support costs be capped conservatively?
3. Can the result be reliable enough to preserve user trust?

Rate execution fit:

- `Strong`: mostly reuses an existing foundation or mature capabilities, with limited unknowns.
- `Medium`: one meaningful technical unknown must be proven first.
- `Weak`: multiple uncertain subsystems or ongoing operations are required.

Classify external dependency fit as:

- `Offline core`: the core outcome works without a network connection.
- `Optional online services`: sync, StoreKit, analytics, backup, or enhancements may use the network.
- `Online required`: the core outcome depends on a backend or third-party API.

Offline capability improves builder fit but never substitutes for demand, competitor, or payment evidence. A stronger validated online app can beat a weaker offline app.

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
| Execution fit | Strong / Medium / Weak |
| External dependency fit | Offline core / Optional online services / Online required |
| Confidence | High / Medium / Low |

## Final Decision Rules

- `Build`: Keyword passes, 3-5 real competitors, direct competitor revenue meets the floor, payment evidence is Medium/Strong, and the feasibility questions pass.
- `Watch`: Demand exists but one key proof is missing; give the next data point to verify.
- `Skip`: Weak demand, weak payment evidence, too much competition, or MVP is not tiny.

Post-launch signal: after release, winners are apps whose organic rankings or downloads stabilize or grow after the initial launch period. Any new-app boost is a practitioner heuristic, not a guaranteed ranking behavior. This skill does not run post-launch analysis.

When evidence conflicts, prefer the safer verdict. A tiny bet should be cheap to validate, not a justification for ignoring weak demand.
