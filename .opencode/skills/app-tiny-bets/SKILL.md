---
name: app-tiny-bets
description: Use when finding validated tiny iOS app ideas to build. Applies keyword-first research with Astro MCP, competitor weighting, and web revenue/payment evidence. Trigger for app ideas, App Store inspiration links, category choice, ASO demand checks, or tiny-bet app portfolios.
---

# App Tiny Bets

Find small iOS app opportunities using a keyword-first tiny-bet workflow: keyword demand, competitor proof, one core feature, ship lean. This skill is research-only. Stop at a build/watch/skip recommendation.

## Job

Turn a seed into up to 3 validated iOS app opportunities using Astro MCP and payment evidence. Use the builder profile as a soft discovery and tie-breaking signal, never as market proof. Save the final lean report as a markdown artifact so the user can read it later. Treat App Store search terms as user problems.

A good tiny bet has:

- A keyword people already search for
- Competitors already serving the intent
- Evidence users pay or tolerate monetization
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

## Parallel Evidence Gathering

Use subagents only for read-only evidence gathering when it saves time. Keep all decisions and report writing centralized in the main agent. Use `references/subagents.md` for packet format and tool instructions.

## Workflow

### 1. Normalize The Starting Point

Turn the user input into 1-5 seed keywords. These are search hypotheses, not the final candidate set. Preserve meaningful variety until Astro provides evidence for narrowing.

For a broad category seed, first map the category to distinct user jobs and product families without filtering by the builder profile. Then read `references/builder-profile.md` and add useful profile-aligned angles without removing the independent candidates.

With no seed, use the profile as one candidate source alongside simple App Store app families and credible outside-profile directions. Do not require every candidate to match the profile.

For an explicit app or keyword seed, keep the user's direction primary. Use the profile only to simplify the product shape or resolve close choices.

Examples:

- App link for a stamp app -> `stamp identifier`, `stamp value`, `stamp scanner`, `stamp appraisal`
- Category `student tools` -> `math AI`, `chemistry AI`, `physics AI`, `homework scanner`
- Category `hobby collector` -> `coin identifier`, `stamp identifier`, `rock identifier`, `antique appraisal`

Keep candidates close to real App Store search phrases. Do not invent broad startup ideas.
Profile alignment does not count as keyword demand and must not raise an evidence score.
Do not discard a plausible candidate merely because it falls outside the profile; narrow the set using Astro and the rubric.

### 2. Validate Keywords In Astro

Create one fresh temporary Astro app for each research run; never reuse a real or older temporary app. Then follow `references/tools.md` for the search and tracking sequence and `references/rubric.md` for pass bars. Search each seed, then expand from relevant ranking competitors. Prefer evidence-derived phrases over model-invented synonyms.

Record the raw popularity and difficulty, store, capture date, intent, and top-result shape. Filter to no more than 10 unique candidates before deeper research. At least one final keyword should come from competitor evidence when Astro exposes a relevant one; otherwise state that none was found.

### 3. Build A Competitor Set

For each surviving idea, inspect the top 10 results and select 3-5 relevant competitors. Summarize how many results are relevant, how many have `100+` ratings, whether newer entrants have traction, and whether the exact phrase collides with an app name. Weight competitors using `references/rubric.md`.

### 4. Check Payment Evidence

Use `references/tools.md` for web searches and `references/rubric.md` for payment grading. `Build` requires credible direct revenue evidence from a relevant competitor at roughly the rubric floor; IAPs and other payment proxies can support only `Watch`. If using subagents, follow `references/subagents.md`.

### 5. Define The Core Feature And Feasibility

For each viable idea, state the smallest feature that satisfies the keyword and the simplest likely monetization model.

Examples:

- `stamp identifier` -> scan stamp -> AI value and historical insight
- `tree identifier` -> photo -> identify tree or related object
- `math AI` -> scan/input problem -> answer and explanation

Monetization heuristic: recurring-use apps fit subscriptions better; single-use or occasional utilities may fit lifetime/one-time unlocks better.

Do not add community, marketplace, complex accounts, or heavy backend unless the keyword cannot be satisfied without it.

Before recommending `Build`, confirm one developer can deliver the bounded core flow without introducing multiple uncertain subsystems or a new operational system, variable costs can be capped, and the result can be reliable enough to protect user trust. Classify external dependencies as `Offline core`, `Optional online services`, or `Online required`. Offline capability is a builder-fit advantage, not market proof or a hard requirement.

### 6. Rank Opportunities

Rank no more than 3 final ideas. Prefer the best mix of demand, payment evidence, and build simplicity. A smaller keyword with obvious paid intent can beat a bigger crowded keyword. Use builder-profile fit, including offline capability, only after the evidence bars pass or to break otherwise close calls.

### 7. Stop Or Escalate

Stop research when you have 3 viable opportunities or when 10 candidate keywords fail the rubric.

If all candidates fail, still save a useful `Skip` report: show the strongest rejected candidates, the failed bar for each, and one next seed or category to test.

Ask the user before continuing if:

- Astro MCP is unavailable
- Revenue evidence is missing for every candidate
- The best idea requires a risky domain or heavy backend
- The user must choose between two categories with different tradeoffs

### 8. Save The Report Artifact

Save the complete report using the path and naming contract in `references/report-template.md`. Keep it lean and exclude raw tool dumps or private/personal data.

## Output Format

Use `references/report-template.md`. In chat, return only the short verdict and saved artifact path.

## Guardrails

- Keep the report high-signal; do not produce a long brainstorm dump.
- Use Astro before web revenue research; demand comes before monetization checks.
- Do not recommend `Build` unless the idea passes every bar in `references/rubric.md`, including its direct competitor-revenue floor.
- Do not target competitor brand names or trademarks.
- Do not claim exact revenue unless the source explicitly provides it.
- Cite uncertainty. Say `payment evidence is weak` rather than stretching weak data.
- Preserve raw Astro scores and evidence dates; thresholds are practitioner heuristics, not universal market facts.
- Keep Mac as a later expansion unless the user explicitly asks for Mac.
- Do not treat builder-profile alignment as demand, competitor, or payment evidence.
- Do not constrain discovery to profile themes when stronger validated opportunities exist elsewhere.
- Do not expose or infer private project history in reports; describe only the research seed and public evidence.

## Tiny-Bet Playbook

Use this sequence:

1. Find a keyword users type into App Store search.
2. Check popularity and difficulty in Astro.
3. Expand from relevant competitor keywords.
4. Inspect the result shape and 3-5 competitors.
5. Confirm competitors make at least some money or clearly monetize.
6. Pick one feasible core feature tied directly to the keyword.
7. Ship a lean MVP, then move on unless organic data floats.
8. Return only to winners that show traction.

For this skill, stop at step 6 and recommend what to research or build next.
