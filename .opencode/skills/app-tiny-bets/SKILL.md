---
name: app-tiny-bets
description: Use when finding validated tiny iOS app ideas or explicitly validating a wedge for one opportunity from an existing App Tiny Bets report. Phase 1 performs keyword-first discovery with Astro and competitor evidence. Phase 2 runs only when explicitly requested with a report and one selected opportunity, then mines competitor reviews and creates a wedge brief.
---

# App Tiny Bets

Find qualified iOS app opportunities using a keyword-first tiny-bet workflow: keyword demand, competitor proof, one core feature, ship lean. This skill is research-only and has two separate, explicit phases.

## Phase Boundary

- **Phase 1: Discovery** turns a seed into ranked opportunities and a research artifact. Stop after comparing the evidence.
- **Phase 2: Wedge Validation** starts from a completed Phase 1 artifact and one user-selected opportunity. It deepens review research, tests candidate wedges against evidence, and saves a separate brief artifact.
- Never run Phase 2 automatically after Phase 1. Expect it to run in a fresh session.
- Never infer the selected opportunity from rank, prior conversation, or the artifact. The user must select exactly one.

## Job

Turn a seed into up to 5 evidence-backed iOS opportunities using Astro MCP and competitor revenue evidence. Use the builder profile as a soft discovery, product-shaping, and tie-breaking signal, never as market proof. Save one mixed lean report that compares and ranks the strongest qualified opportunities by relative evidence strength, whether profile-aligned or not, without making the user's final build decision or assigning product statuses. Treat App Store search terms as user problems and post-launch data as the final judge.

A good tiny bet has:

- A keyword people already search for
- Competitors already serving the intent
- Evidence users pay or tolerate monetization
- An evidence-backed Problem stating the user's job and concrete friction or consequence
- A behavior- and problem-based ideal customer grounded in public evidence
- A complaint-backed wedge that improves the core job
- One obvious core feature that can ship fast
- Bounded cost, reliability risk, and external dependencies
- Ideally, adjacent keywords for follow-up apps

Avoid ideas that are only interesting, clever, or technically fun. The point is validated demand, not originality.

## Inputs

Accept any one starting mode:

| Mode | User gives | First move |
| --- | --- | --- |
| App inspiration | App Store URL or app name | Extract category, keywords, competitor cluster |
| Keyword seed | `stamp identifier`, `math AI`, `pdf scanner` | Validate search demand and related keywords |
| Category seed | `student tools`, `collector apps`, `AI identifiers` | Expand the category into varied user jobs and keywords, then use evidence to narrow |
| Discover for me | No seed | Generate a broad candidate mix; use the builder profile as one source, not the boundary |

If the input is vague, ask one short question only when necessary: `Do you want iOS only, or iOS plus Mac later?` Default to iOS US.

## References

Load only what the task needs:

- `references/builder-profile.md` — product taste, preferred mechanics, constraints, and discovery boundaries
- `references/tools.md` — Astro MCP and web revenue research tool map
- `references/rubric.md` — pass bars, kill criteria, and decision rules
- `references/subagents.md` — evidence-only subagent packet protocol
- `references/report-template.md` — final report contract
- `references/wedge-validation.md` — explicit Phase 2 entry gate, review-mining workflow, and wedge brief contract

## Parallel Evidence Gathering

Use subagents only for read-only evidence gathering when it saves time. Keep all decisions and report writing centralized in the main agent. Use `references/subagents.md` for packet format and tool instructions.

## Phase 1 Workflow

### 1. Normalize The Starting Point

Examples throughout this skill illustrate how inputs become search hypotheses or bounded core flows. They are not preferred candidates, reusable defaults, or limits on categories or mechanics.

Turn the user input into 1-5 seed keywords. These are search hypotheses, not the final candidate set. Preserve meaningful variety until Astro provides evidence for narrowing.

For a broad category seed, first map the category to distinct user jobs and product families without filtering by the builder profile. Then read `references/builder-profile.md` and add useful profile-aligned angles without removing the independent candidates.

With no seed, use the profile as one candidate source alongside simple App Store app families and credible outside-profile directions. Do not require every candidate to match the profile.

For discovery runs, rotate 10-keyword batches across three pools instead of repeatedly mining one theme: profile-aligned jobs, adjacent reusable app families, and independent wildcard categories. Rotate the research inputs, not the final results; evidence still determines ranking and no pool receives a quota.

Within each discovery batch, compare both user jobs and product mechanics when checking for premature clustering around one audience, category lens, or mechanic. Different topics that use the same mechanic still count as clustered. If candidates have clustered, replace redundant seeds with credible iOS jobs that vary the clustered dimension before Astro validation. Lenses and mechanics may be combined or extended; they are not an allowlist or result quota.

Never create separate discovery and profile-aligned reports for the same run. Research both pools together, apply the same evidence bars, and rank them in one artifact. Do not enforce a profile-aligned or outside-profile quota; evidence wins.

For an explicit app or keyword seed, keep the user's direction primary. Use the profile only to simplify the product shape or resolve close choices.

Illustrative seed transformations:

- App link for a stamp app -> `stamp identifier`, `stamp value`, `stamp scanner`, `stamp appraisal`
- Category `creator tools` -> `teleprompter`, `video captions`, `thumbnail maker`, `podcast clips`
- Category `small-business tools` -> `invoice maker`, `inventory count`, `appointment reminder`, `shift planner`

Keep candidates close to real App Store search phrases. Do not invent broad startup ideas.
Profile alignment does not count as keyword demand and must not raise an evidence score.
Do not discard a plausible candidate merely because it falls outside the profile; narrow the set using Astro and the rubric.

### 2. Validate Keywords In Astro

Create one fresh temporary Astro app for each research run; never reuse a real or older temporary app. Then follow `references/tools.md` for the search and tracking sequence and `references/rubric.md` for pass bars. Search each seed, then expand each promising category from 2-3 relevant ranking competitors. Prefer evidence-derived phrases over model-invented synonyms.

Record the raw popularity and difficulty, store, capture date, intent, and top-result shape. Sort qualifying keywords by popularity descending. Research in deduplicated batches of up to 10 before deeper research; a batch is a checkpoint, not a permanent cap. At least one final keyword should come from competitor evidence when Astro exposes a relevant one; otherwise state that none was found.

### 3. Build A Competitor Set

For each surviving idea, inspect the top 10 results and research 3-5 relevant competitors internally. Summarize how many results are relevant, how many have `100+` ratings, competitor release dates, whether newer entrants have traction, and whether the exact phrase collides with an app name. Classify entry as `Open`, `Competitive`, or `Closed` using `references/rubric.md`; incumbents validate demand and do not cause rejection by themselves. Keep competitor weighting as an internal research method, not a report column.

Run the native Apple substitute check in `references/rubric.md` before revenue research. Exclude an opportunity when a first-party Apple app or built-in iOS feature already provides the searched core job at a competent baseline. A narrower wedge, stronger privacy, or extra features do not override this portfolio preference; move to a different keyword instead. This is an internal qualification check and is not printed as a standalone opportunity field.

For each surviving idea, first define an evidence-backed Problem: the user's job plus concrete friction or consequence supported by cited complaint or competitor evidence. Then define the ideal customer from public app listings, reviews, or other public sources: behavior, desired outcome, and current workaround or incumbent. Cite both and never invent age, gender, income, or other demographics.

Research reviews and listings from 2-3 profitable relevant competitors to define a complaint-backed wedge. Keep Wedge to 1-2 sentences and include a representative review excerpt with reviewer, app, date, source URL, and an honest recurrence label. Distinguish recurring themes across independent reviews or apps from a single high-signal complaint, and never present one anecdote as recurring.

### 4. Check Payment Evidence

Use `references/tools.md` for web searches and `references/rubric.md` for the authoritative revenue-evidence policy and payment grading. One directly relevant top competitor with a credible app-level estimate or maker disclosure clearly above the `$100-200/month` floor validates that the market pays. Additional estimates strengthen confidence but are not mandatory. IAPs and other payment proxies never establish a revenue amount on their own. If using subagents, follow `references/subagents.md`.

Print exactly one competitor table per opportunity in the Evidence Appendix; never add a separate revenue-proof table. Use only `Competitor`, `Market traction`, `Revenue evidence`, and `Evidence implication`. Display only competitors with evidenced positive app-level revenue estimates or positive numeric maker disclosures; every displayed range must have a lower bound greater than zero. The table may contain fewer than 3 rows when evidence is scarce. Every revenue cell must include the numeric amount or range, period, platform/storefront or stated scope, source URL/provider, evidence type, capture date, and confidence. In the comparison `Revenue proof` cell and profile `Payment receipt`, summarize the monthly displayed-competitor range from the lowest displayed lower bound to the highest displayed upper bound, then distinguish qualifying anchors from weaker modeled context and preserve their scopes. If a researched competitor lacks qualifying positive numeric evidence, search relevant competitors for a replacement and otherwise omit the row. Never display `$0`, nonpositive, unknown, upper-bound-only, or missing-value revenue rows, and never convert an upper bound into an estimate. Every opportunity still needs at least one directly relevant qualifying above-floor anchor.

### 5. Define The Core Feature And Feasibility

For each viable idea, state the smallest feature that satisfies the keyword and the simplest likely monetization model.

Illustrative core-flow shapes:

- `stamp identifier` -> scan stamp -> AI value and historical insight
- `teleprompter` -> draft or import script -> controlled playback
- `garden planner` -> choose space and plants -> save or share layout

Monetization heuristic: recurring-use apps fit subscriptions better; single-use or occasional utilities may fit lifetime/one-time unlocks better.

Do not add community, marketplace, complex accounts, or heavy backend unless the keyword cannot be satisfied without it.

Before including an opportunity, define a bounded concrete wedge that solves the searched job better or more efficiently than the inspected competitors and is supported by cited complaint research, not pricing or polish alone. Keep it separate from the core Product and label recurrence strength honestly. Confirm one developer can deliver the bounded core flow without introducing multiple uncertain subsystems or a new operational system, variable costs can be capped, and the result can be reliable enough to protect user trust. Classify external dependencies as `Offline core`, `Optional online services`, or `Online required`.

### 6. Rank Opportunities

Rank no more than 5 final ideas. Prefer the best mix of demand, revenue confidence, concrete wedge, and build simplicity. An `Open` opportunity usually outranks an otherwise equal `Competitive` one, but a competitive market with materially stronger demand, revenue, and wedge remains eligible. Use builder-profile fit, including offline capability, only after the evidence bars pass or to break otherwise close calls.

Rank only opportunities that pass every admission gate. Rank reflects relative evidence strength across the qualified set; it is not a build recommendation, final user decision, or product status. Explain rank 1 through neutral evidence rationale and ranks 2-5 through explicit ranking tradeoffs.

### 7. Stop Or Escalate

Stop research when you have 5 viable opportunities. If a batch of 10 produces fewer than 5, continue with the next category pool or a competitor-derived cluster when useful candidates remain and Astro is available. Ask the user before exceeding 50 total candidates so research cost stays bounded. Return fewer than 5 rather than weakening any inclusion gate.

If all candidates fail, save the `No Qualified Opportunities` report defined in `references/report-template.md`: state neutrally that no opportunity met every admission gate within the research cap and give only one evidence-driven next seed or category to test. Do not expose failed candidates.

Ask the user before continuing if:

- Astro MCP is unavailable
- The highest-ranked opportunity requires a risky domain or heavy backend
- The user must choose between two categories with different tradeoffs

### 8. Save The Report Artifact

Save the complete report using the path and naming contract in `references/report-template.md`. One research run produces one canonical artifact; update that artifact as the run expands instead of creating profile-specific variants. Require a concise comparison table, ranked evidence profiles, and a detailed Evidence Appendix; keep keyword and competitor details in the appendix. Do not add an imperative next step to a qualified-opportunity report. Keep it lean and exclude raw tool dumps or private/personal data.

## Output Format

Use `references/report-template.md`. In chat, return only the saved artifact path, or a neutral completion line followed by the path.

## Phase 2 Workflow

Run Phase 2 only when the user explicitly asks for wedge validation and supplies:

1. A completed App Tiny Bets research artifact.
2. Exactly one selected opportunity from that artifact.

If either input is missing, ask one short question and stop. Do not choose an opportunity for the user.

When both inputs are present, read `references/wedge-validation.md` and follow it. Save a separate wedge brief; do not append to or overwrite the Phase 1 artifact.

## Guardrails

- Keep the report high-signal; do not produce a long brainstorm dump.
- Use Astro before web revenue research; demand comes before monetization checks.
- Include an opportunity only when it passes every inclusion gate in `references/rubric.md`, including an evidence-backed Problem, complaint-backed Wedge, and one credible direct competitor-revenue anchor.
- Do not target competitor brand names or trademarks.
- Exclude core jobs already competently provided by a first-party Apple app or built-in iOS feature.
- Describe all third-party numbers as estimates; never present them as actual revenue unless they are direct maker disclosures.
- Never calculate or synthesize revenue from downloads, ratings, rank, pricing, reviews, or other proxies.
- Cite uncertainty. Say `payment evidence is weak` rather than stretching weak data.
- Preserve raw Astro scores and evidence dates; thresholds are practitioner heuristics, not universal market facts.
- Keep Mac as a later expansion unless the user explicitly asks for Mac.
- Do not treat builder-profile alignment as demand, competitor, or payment evidence.
- Do not constrain discovery to profile themes when stronger validated opportunities exist elsewhere.
- Do not split profile-aligned and independent candidates into separate artifacts.
- Do not expose or infer private project history in reports; describe only the research seed and public evidence.
- Do not make a build recommendation or assign product statuses in the artifact. Evidence ranking is allowed because it compares only qualified opportunities by relative evidence strength.
- Use `N/A` for unavailable keyword metrics; never invent missing evidence.
- Do not continue from Phase 1 into Phase 2 without an explicit request and selected opportunity.
- In Phase 2, treat the Phase 1 wedge as a hypothesis to revalidate, not a product decision.

## Tiny-Bet Playbook

Use this sequence:

1. Find a keyword users type into App Store search.
2. Check popularity and difficulty in Astro.
3. Expand from relevant competitor keywords.
4. Inspect the result shape and 3-5 competitors.
5. Confirm at least one relevant top competitor clears the numeric revenue floor.
6. Define one feasible core feature and a concrete better-or-faster wedge tied directly to the keyword, then compare qualified opportunities by relative evidence strength.
7. Ship a lean MVP, then move on unless organic data floats.
8. Return only to winners that show traction.

For Phase 1, stop at step 6. Phase 2 is a separate invocation and stops after saving the wedge brief.
