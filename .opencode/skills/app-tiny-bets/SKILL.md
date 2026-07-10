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
- Adjacent keywords for follow-up apps

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

Turn the user input into 3-10 candidate keywords. Diverge before converging: preserve meaningful variety until Astro provides evidence for narrowing.

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

Read `references/tools.md` for tool order and `references/rubric.md` for pass bars. Check popularity, difficulty, intent, adjacent keywords, and top ranking apps.

### 3. Build A Competitor Set

For each surviving idea, select 3-5 competitors. Weight them using `references/rubric.md`: keyword relevance, ratings/reviews, monetization evidence, freshness/quality gap, and what value their screenshots/positioning emphasize.

### 4. Check Payment Evidence

Use `references/tools.md` for web searches and `references/rubric.md` for Strong/Medium/Weak/Reject payment grading. If using subagents for competitor revenue checks, use `references/subagents.md`. Downgrade good keywords when payment proof is weak.

### 5. Define The One Core Feature

For each viable idea, state the smallest feature that satisfies the keyword and the simplest likely monetization model.

Examples:

- `stamp identifier` -> scan stamp -> AI value and historical insight
- `tree identifier` -> photo -> identify tree or related object
- `math AI` -> scan/input problem -> answer and explanation

Monetization heuristic: recurring-use apps fit subscriptions better; single-use or occasional utilities may fit lifetime/one-time unlocks better.

Do not add community, marketplace, complex accounts, or heavy backend unless the keyword cannot be satisfied without it.

### 6. Rank Opportunities

Rank no more than 3 final ideas. Prefer the best mix of demand, payment evidence, and build simplicity. A smaller keyword with obvious paid intent can beat a bigger crowded keyword. Use builder-profile fit only after the evidence bars pass or to break otherwise close calls.

### 7. Stop Or Escalate

Stop research when you have 3 viable opportunities or when 10 candidate keywords fail the rubric.

Ask the user before continuing if:

- Astro MCP is unavailable
- Revenue evidence is missing for every candidate
- The best idea requires a risky domain or heavy backend
- The user must choose between two categories with different tradeoffs

### 8. Save The Report Artifact

Save the final report as markdown in `app-tiny-bets-reports/` at the workspace root. Create the folder if it does not exist.

Use a readable filename: `YYYY-MM-DD-[seed-or-topic]-research.md`.

Keep the artifact lean: final recommendation, top opportunities, competitors, rejected ideas, and next step. Do not save raw tool dumps or private/personal data.

## Output Format

Use `references/report-template.md`. In the chat response, include the saved artifact path.

## Guardrails

- Keep the report high-signal; do not produce a long brainstorm dump.
- Use Astro before web revenue research; demand comes before monetization checks.
- Do not recommend `Build` unless the idea passes the Keyword, Competitor, Payment, and Tiny-Bet bars in `references/rubric.md`.
- Do not target competitor brand names or trademarks.
- Do not claim exact revenue unless the source explicitly provides it.
- Cite uncertainty. Say `payment evidence is weak` rather than stretching weak data.
- Keep Mac as a later expansion unless the user explicitly asks for Mac.
- Do not treat builder-profile alignment as demand, competitor, or payment evidence.
- Do not constrain discovery to profile themes when stronger validated opportunities exist elsewhere.
- Do not expose or infer private project history in reports; describe only the research seed and public evidence.

## Tiny-Bet Playbook

Use this sequence:

1. Find a keyword users type into App Store search.
2. Check popularity and difficulty in Astro.
3. Inspect top competitors and related keywords.
4. Confirm competitors make at least some money or clearly monetize.
5. Pick one core feature tied directly to the keyword.
6. Ship a lean MVP, then move on unless organic data floats.
7. Return only to winners that show traction.

For this skill, stop at step 5 and recommend what to research or build next.
