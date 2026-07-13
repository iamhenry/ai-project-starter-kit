# App Tiny Bets Rubric

Use this rubric before admitting and ranking any opportunity. Defaults are conservative for a new app with no authority.

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

Inspect the top 10 results, then research 3-5 relevant competitors internally. The final table may contain fewer competitors under the numeric revenue-row contract. Judge ratings and release dates together: four apps with `100+` ratings can still be attractive when the category and ranking entrants are recent.

| Class | Evidence | Eligibility |
| --- | --- | --- |
| Open | Few authoritative competitors, recent entrants rank, or exact-result quality is weak | Eligible; favorable ranking signal |
| Competitive | Many established competitors, but reviews/features expose a specific better-or-faster wedge | Eligible with explicit wedge and risk |
| Closed | Dominant substitutes and no concrete product, workflow, trust, or audience wedge | Reject |

Record relevant top-10 density, apps with `100+` ratings, release dates, review/feature gaps, repeated screenshot promises, and related keywords. Do not count visual polish or lower price alone as a wedge.

## Native Apple Substitute Gate

Reject an opportunity when a first-party Apple app or built-in iOS feature already performs the primary searched job competently for ordinary users. This is a portfolio preference, not a claim that third-party apps cannot succeed.

Check both App Store results and built-in system capabilities. Examples include Voice Memos for basic voice recording, Notes for basic document scanning, Photos for duplicate-photo cleanup, Measure for basic measuring or leveling, Passwords for password management, and Calculator for basic calculation or conversion.

Apply the gate to the core job, not incidental overlap:

- Reject when the proposed app's primary promise is substantially the same job with polish, privacy, reliability, AI, or extra features.
- Keep when Apple provides only a component and the searched outcome is a materially different specialized job.
- When uncertain, record the Apple substitute and exclude until the distinction is proven.

If the exact keyword is already a competitor's app name, do not assume you can use that phrase as the product name. Keep it as a keyword target or find an adjacent phrase.

## Problem Evidence

State the user's job and concrete friction or consequence in one concise line, supported by cited complaint or competitor evidence. This gate comes before Ideal Customer. Do not use reviews as demand proof.

## Ideal Customer Evidence

Define a narrow ideal customer from public app listings, reviews, or other public evidence. Describe behavior and problem, the desired outcome, and the current workaround or incumbent; cite the source. Do not invent age, gender, income, or other demographics. Positioning inferences are allowed when clearly presented as synthesis rather than direct quotes.

## Competitor Weighting

Use this order instead of fake numeric precision:

1. Keyword relevance: does the app solve the exact searched problem?
2. Ratings/reviews: is there meaningful market pull and authority?
3. Monetization: is there credible evidence users pay?
4. Entry evidence: can a newer, narrower, or materially better workflow enter?

Label a competitor `Strong` when it is directly relevant with meaningful traction or payment proof, `Medium` when evidence is partial, and `Weak` when relevance or traction is low. Freshness supports enterability; it is not a documented App Store ranking factor.

Weighting is an internal research method. The Evidence Appendix contains one validated-competitor table per opportunity. Use exactly four columns: `Competitor`, `Market traction`, `Revenue evidence`, and `Evidence implication`. `Market traction` contains current keyword rank, exact US rating count, average rating, and relevant freshness evidence. `Evidence implication` contains only scope, freshness, entry evidence, weakness, or counter-evidence affecting relative evidence strength.

## Revenue And Payment Bar

Display only competitors with evidenced positive app-level revenue estimates or positive numeric maker disclosures. Every displayed range must have a lower bound greater than zero. Every `Revenue evidence` cell must include the numeric amount or range, period, platform/storefront or stated scope, source URL/provider, evidence type, capture date, and confidence. If a researched competitor has nonpositive, unknown, or upper-bound-only evidence, search relevant competitors for a profitable replacement; otherwise omit the row. The final report table may contain fewer rows when evidence is scarce.

Qualifying evidence, strongest first:

1. Maker disclosure tied to the named app and a clear period/scope.
2. App-level estimate from Sensor Tower, Appfigures, AppMagic, data.ai, or another named commercial intelligence provider, with period and storefront/scope clear.
3. Public modeled estimate with published methodology, corroborated by a second independent numeric source or a commercial estimate.

Never derive or calculate revenue from downloads, ratings, rank, pricing, reviews, or other proxies. Never average weak guesses into a synthetic estimate. Ratings, rank, IAPs, subscriptions, and prices are traction or monetization context only and never prove revenue. Ratings count may strengthen or weaken traction confidence and competitor weight, but must never change revenue evidence, amounts, or thresholds.

The comparison `Revenue proof` cell and profile `Payment receipt` must state the descriptive monthly range across displayed competitors. Use the lowest displayed lower bound as the range floor and the highest displayed upper bound as the ceiling; a precise value supplies both bounds. Do not average estimates. Preserve every source value and scope in the Evidence Appendix, and identify qualifying anchors separately from weaker modeled context. This range describes displayed evidence; it is not a synthesized estimate for the market or proposed app.

Never display `$0`, nonpositive, unknown, upper-bound-only, or missing-value revenue rows, and never present an upper bound as a numeric estimate. Preserve them only in internal research context. Public modeled positive ranges may appear with confidence, but do not satisfy the payment bar unless corroborated under the source hierarchy above.

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

Illustrative pass shapes, not an exhaustive list:

- Camera/photo -> AI identification -> result -> history
- Draft/import -> preview or present -> save/share
- Select a few inputs -> create a bounded plan or layout -> save/export

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

Also require a bounded concrete wedge: one product, workflow, trust, or audience advantage that makes the core job better or more efficient than inspected competitors. Keep it to 1-2 sentences and use one representative review excerpt per primary complaint theme, including reviewer, app, date, source URL, and recurrence strength. Support it with recurring complaints across independent reviews or apps when available; otherwise label a single complaint as high-signal rather than recurring. Keep Wedge separate from Product, and reject generic clones whose only claim is pricing, polish, or AI.

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
| Confidence | High / Medium / Low |

## Final Inclusion Rule

Include an opportunity only when it passes the Keyword, Entry Assessment, Native Apple Substitute, Revenue And Payment, and Tiny-Bet Fit bars above, includes an evidence-backed Problem and ideal customer, and includes a complaint-backed Wedge plus the feasibility answers. The Native Apple Substitute gate is an internal qualification check, not a standalone report field. Exclude `Closed` candidates and every other failed candidate from the final artifact.

Compare and rank only opportunities that pass every gate. Rank expresses relative evidence strength across the qualified set; it must not make the user's build decision, assign a product status, or imply that rank 1 is a recommendation.

Post-launch signal: after release, winners are apps whose organic rankings or downloads stabilize or grow after the initial launch period. Any new-app boost is a practitioner heuristic, not a guaranteed ranking behavior. This skill does not run post-launch analysis.

When evidence conflicts, exclude the candidate. A tiny bet should be cheap to validate, not a justification for ignoring weak demand.
