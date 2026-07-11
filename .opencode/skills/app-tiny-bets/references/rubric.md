# App Tiny Bets Rubric

Use this rubric before recommending any idea. Defaults are conservative for a new app with no authority.

## Keyword Pass Bar

| Signal | Pass | Strong pass | Reject |
| --- | --- | --- | --- |
| Popularity | `20+` in Astro, or clear search demand if scale differs | `30+` with relevant results | Below `20` unless it is a paid niche with strong competitors |
| Difficulty | `<= 60` preferred; `61-70` viable with strong supporting evidence | `<= 50` | Above `70` |
| Intent | User is searching for an app solution | Search phrase maps to one obvious feature | Informational, brand-led, or vague intent |
| Adjacent keywords | Helpful but not required | Cluster supports future tiny bets | Never reject solely because the keyword is isolated |

Treat these as practitioner defaults on Astro's scale, not universal market facts. Preserve raw scores, store, and capture date. If the scale changes, explain the calibration instead of silently replacing the thresholds.

Discard keywords when demand is weak, results are irrelevant, the query is brand/trademark-led, or user intent is not app-download intent. Incumbents validate demand; assess whether a credible wedge exists instead of rejecting on authority alone.

## Entry Assessment

Inspect the top 10 results, then choose 3-5 relevant competitors. Judge ratings and release dates together: four apps with `100+` ratings can still be attractive when the category and ranking entrants are recent.

| Class | Evidence | Eligibility |
| --- | --- | --- |
| Open | Few authoritative competitors, recent entrants rank, or exact-result quality is weak | Eligible; favorable ranking signal |
| Competitive | Many established competitors, but reviews/features expose a specific better-or-faster wedge | Eligible with explicit wedge and risk |
| Closed | Dominant substitutes and no concrete product, workflow, trust, or audience wedge | Reject |

Record relevant top-10 density, apps with `100+` ratings, release dates, review/feature gaps, repeated screenshot promises, and related keywords. Do not count visual polish or lower price alone as a wedge.

If the exact keyword is already a competitor's app name, do not assume you can use that phrase as the product name. Keep it as a keyword target or find an adjacent phrase.

## Competitor Weighting

Use this order instead of fake numeric precision:

1. Keyword relevance: does the app solve the exact searched problem?
2. Ratings/reviews: is there meaningful market pull and authority?
3. Monetization: is there credible evidence users pay?
4. Entry evidence: can a newer, narrower, or materially better workflow enter?

Label a competitor `Strong` when it is directly relevant with meaningful traction or payment proof, `Medium` when evidence is partial, and `Weak` when relevance or traction is low. Freshness supports enterability; it is not a documented App Store ranking factor.

## Revenue And Payment Bar

The revenue-proof set contains only directly relevant competitors with qualifying app-level commercial evidence. Each claim must include the exact source value, source URL, estimate period, storefront/scope, evidence type, capture date, and confidence.

Qualifying evidence, strongest first:

1. Maker disclosure tied to the named app and a clear period/scope.
2. App-level estimate from Sensor Tower, Appfigures, AppMagic, data.ai, or another named commercial intelligence provider, with period and storefront/scope clear.
3. Public modeled estimate with published methodology, corroborated by a second independent numeric source or a commercial estimate.

Never derive or calculate revenue from downloads, ratings, rank, pricing, reviews, or other proxies. Never average weak guesses into a synthetic estimate. Ratings count may strengthen or weaken traction confidence and competitor weight, but must never change revenue evidence, amounts, or thresholds.

Use roughly `$100-200/month equivalent` as the minimum useful estimate for the required anchor, not as a forecast for the proposed app. Normalize a disclosed period only with direct arithmetic from the source's revenue figure, preserve the original period/value, and label the normalized amount as an estimate.

Every passing opportunity needs at least one precise commercial estimate or maker disclosure clearly above the floor from a directly relevant top competitor. An upper bound such as `<$5k/month` does not prove the floor and cannot serve as the required anchor. Preserve upper bounds exactly as sourced; never present one as `$5k`, a precise estimate, or proof of any minimum. Visible monetization is market context only.

| Grade | Evidence |
| --- | --- |
| Strong | Multiple directly relevant competitors have precise estimates above the floor, or one anchor is materially above it with high-confidence scope |
| Medium | One directly relevant competitor has a precise qualifying estimate clearly above the floor |
| Weak | Only upper bounds, monetization proxies, old/ambiguous figures, or low-confidence evidence exist |
| Reject | No credible numeric app-level revenue evidence exists |

Only `Medium` or `Strong` passes this bar. No credible precise above-floor anchor excludes the opportunity from the final artifact.

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

Before including an opportunity, answer three questions:

1. Can one developer deliver the core result without introducing multiple uncertain subsystems or a new operational system?
2. Can API, infrastructure, and support costs be capped conservatively?
3. Can the result be reliable enough to preserve user trust?

Also require a concrete wedge: one product, workflow, trust, or audience advantage that makes the core job better or more efficient than inspected competitors. Reject generic clones whose only claim is polish, AI, or lower price.

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
| Entry class | Open / Competitive |
| Payment evidence | Strong / Medium / Weak |
| Execution fit | Strong / Medium / Weak |
| External dependency fit | Offline core / Optional online services / Online required |
| Portfolio leverage | Strong / Medium / Weak |
| Distribution fit | Strong / Medium / Weak |
| Confidence | High / Medium / Low |

## Final Inclusion Rule

Include an opportunity only when it passes the Keyword, Entry Assessment, Revenue And Payment, and Tiny-Bet Fit bars above, including a concrete wedge and all feasibility questions. Exclude `Closed` candidates and every other failed candidate from the final artifact.

Post-launch signal: after release, winners are apps whose organic rankings or downloads stabilize or grow after the initial launch period. Any new-app boost is a practitioner heuristic, not a guaranteed ranking behavior. This skill does not run post-launch analysis.

When evidence conflicts, exclude the candidate. A tiny bet should be cheap to validate, not a justification for ignoring weak demand.
