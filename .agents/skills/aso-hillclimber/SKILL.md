---
name: aso-hillclimber
description: Repeatable, closed-loop App Store keyword optimization for one iOS or Mac app using the asc CLI and Astro MCP. Measures the last metadata test against the app's goal (sales, trials, or downloads), keeps a standing list of 10 competitors, scores keywords by real search demand and beatable top-10 results, and writes a plain-English proposal with current and expected ranks. Use whenever the user wants to improve App Store rankings or downloads, run or re-run ASO, pick a title, subtitle, or keyword field, check how the last metadata change performed, or asks "why isn't my app ranking". Prefer this over aso-worker for keyword selection.
compatibility: Requires the Astro MCP server and an authenticated asc CLI (App Store Connect). Stops with BLOCKED if either is unavailable. Works for paid-upfront, free-trial, and free apps.
---

# ASO Hillclimber

One run = one app and its chosen storefronts. A one-market app needs only its one listing. Every store has its own memory and log, so the next run starts where that store's last run stopped.

Research each market in its own store; never copy keywords between markets, even US, UK, Canada, and Australia.
For multiple listings, establish which listings each target storefront reads before making proposals; Apple's display-language table alone does not establish search indexing.

## Why this works (read once)

People find apps by searching. Apple shows apps whose **title, subtitle, or hidden keyword field** contain the searched words, ordered mostly by how well each app has done on that search (downloads, taps, ratings). Only the top ~10 get seen. A small app can't beat the leaders on big searches, so it starts where real people search **and** the top 10 holds other small apps, earns downloads there, and climbs.

The trap: picking phrases because they're *easy to rank on*. Astro popularity is Apple Ads' relative, exponential 5-100 score; 5 means below Apple's reporting threshold, not zero. Never add or sum popularity scores.

## Hard rules

1. **Real demand only.** Targets need Astro popularity ≥ 20; popularity 5 is never a target.
2. **Exactly 10 competitors**, kept in `config.json` and including the app's inspiration if it has one.
3. **Beatable.** Count top-10 apps with < 100 ratings ("small apps"). More small apps = easier.
4. **Honest.** Only words the app delivers today. No competitor or brand names.
5. **Keep winners, drop losers.** Never remove a phrase ranking top 10; never keep one with popularity below 20. Never re-propose a dropped phrase without a new reason.
6. **Judge by the goal metric and App Store Search impressions**, not rank counts.
7. **Human approves before anything is staged** in App Store Connect.

## The app's ASO memory

In the app repo, keep each store's memory in `_ai/aso/<store>/` (examples in `assets/`). Bare memory paths below refer to this store folder:

| File | Holds | Who writes it |
|---|---|---|
| `_ai/aso/<store>/config.json` | IDs, store, goal metric and target, business model, seed and core phrases, the 10 competitors | Set on the first run; edit when the goal or a competitor changes |
| `_ai/aso/<store>/playbook.json` | Phrases to keep, hold, drop (with reasons), learnings | Updated at the end of every run |
| `_ai/aso/<store>/log.jsonl` | One JSON line per event: `baseline`, `measure`, `proposal`, `shipped` | Append only; never edit old lines |
| `_ai/aso/<store>/runs/YYYY-MM-DD/` | `research.md`, `proposal.md`, `evidence.json` (raw Astro output) | One folder per proposal |

Use the same `goal.metric` for every store: sales per 14 days by default, since downloads can include free trials. Use downloads only for a free app with no sales. Set each store's `goal.target` against the revenue the app needs, informed by its own baseline, not just a small step above it; record the reason in `goal.target_basis`. Never copy a target between stores.

Live metadata isn't stored: read it from App Store Connect each run.

## Gate — data or stop (before anything else)

Every number this skill reports must come from a tool, not from memory or general knowledge. Check both sources first:

| Source | Check | Gives |
|---|---|---|
| Astro MCP | `list_apps` returns a result | Popularity, difficulty, ranks, top-10 apps, rating counts |
| App Store Connect | `asc auth status --validate` passes | Live metadata, version, price, release date |

If either check fails, **stop**. Report `BLOCKED: <source> unavailable — <error>` and do no research, scoring, or proposal. For any Astro error (rate limit, HTTP error, or timeout), include the count completed and "restart the Astro app"; never retry, resume, or fill in partial results. Don't fall back to web search, App Store pages, or estimates.

Funnel numbers (impressions, page views, downloads, sales) come from `asc analytics` or from App Store Connect screenshots the user provides. If neither is available, stop before judging a test; ranks alone can't decide the goal.

While working:
- Cite the source and date beside every number (`Astro 2026-11-04`, `ASC screenshot Aug 6–Nov 3`). Save the raw Astro responses to `_ai/aso/<store>/runs/YYYY-MM-DD/evidence.json`.
- Call Astro MCP tools directly, one at a time, at most 20 Astro calls per minute total across all runs. Pause between every call; never batch or loop several calls inside one tool call without a pause, use scripts or background jobs, or retry. The server limit is 30 per rolling minute; hitting it can stop the MCP server until the Astro app is manually restarted.
- Estimates (expected tiers, funnel math) must be labelled as estimates and built only from those numbers.

## Step 0 — Which run is this?

- **Legacy memory at `_ai/aso/`**: use the root `config.json` to identify its store, then move its config, playbook, log, and runs into `_ai/aso/<store>/` before continuing. Preserve all log lines and run history; merge existing store history without overwriting it.
- **No memory for this store** (new app or live app without `_ai/aso/<store>/`): create the store folder and its `config.json` and `playbook.json` from `assets/`. Run step 1: for a live app, use the live listing, Astro ranks and rank history for this store, and this store's Analytics data (use the screenshot checklist in `references/tools.md` if API access is unavailable), then set an ambitious target for the revenue the app needs, informed by the baseline; if the app is not live, ask for the initial goal in plain words. Record why in `goal.target_basis`. Log a `baseline`, then steps 2–8.
- **Existing store**: read all three files from `_ai/aso/<store>/`. Find the last `shipped` line and count days since it went live. Run step 1 and log a `measure`. Then, if the user wants a new change, steps 2–8 using the playbook.

No fixed calendar. Measure whenever the user runs it. A measure under 7 days after going live is **early**: new metadata is still being indexed, so report ranks but don't drop phrases on it. Shipping a new change before the last one was measured is allowed; note `"previous_unmeasured": true` in the proposal line, since results will be mixed.

## Step 1 — Measure

Live listing with `asc` (see `references/tools.md`): title, subtitle, keywords, promo text, version state, price.

**App maturity** — how much ranking history Apple has to work with:

| Signal | Source |
|---|---|
| First release date → age in months | `asc` app/versions |
| Rating count and average | Astro `get_app_ratings` |
| First-time downloads in the window | App Store Connect Analytics |

| Band | Rule | Effect on step 5 |
|---|---|---|
| New | < 50 ratings or < 6 months old | Caps as written |
| Growing | 50–500 ratings and ≥ 6 months | Climb now: difficulty ≤ 40 · Stretch: 41–60 · tiers ≤ 40 / ≤ 60 |
| Established | > 500 ratings | Climb now: difficulty ≤ 50 · Stretch: 51–70 · tiers ≤ 50 / ≤ 70 |

These bands are starting rules; the prediction hit rate decides whether they move.

**Funnel** for the window (since the last ship, or the last 90 days for a baseline) from App Store Connect → Analytics, filtered to this store. Use **Sources → App Store Search** for impressions, product page views, and first-time downloads to judge keywords. Get the goal metric (sales by default) from this store's totals. If the API key lacks the Analytics role, follow the screenshot checklist in `references/tools.md`.

**Ranks** from Astro (the real app, not the research app) for every phrase in the last `proposal` line and the playbook's keep/hold lists.

Then judge, comparing with the previous `baseline`/`measure` line:

| What happened | Meaning | Next |
|---|---|---|
| Goal met | Climbing works | Keep winners; raise the target in `config.json`; next phrase tier |
| Search impressions up, page views flat | Keywords bring views; taps didn't follow | Report the numbers; the cause is unmeasured here, so don't guess it |
| Page views up, goal flat | People open the page but don't buy | Report the numbers; outside keyword work |
| Ranks didn't move | Phrases too hard for the app's maturity | Easier phrases (lower tier) |

Phrase verdicts (not on an early measure): top 10 → **keep**; 11–50 and rising → **hold**; unranked or > 50 → **drop**. Compare each with its predicted tier for the hit rate. Update `playbook.json` and add at least one learning.

## Step 2 — Astro setup

- Real app tracked by its App Store ID (live ranks).
- New temporary research app per ship run: `<App> ASO Research YYYY-MM-DD`. All candidate keywords go here so a human can audit in the Astro Mac app.
- Tags: **Climb now** (green), **Stretch** (yellow), **Later** (orange), **Drop** (gray), **Proposed** (blue). Create once with `manage_tag`.

## Step 3 — Competitors (reuse, don't redo)

Use the competitors in `config.json`. Each run: refresh rating counts. Swap a competitor only when it no longer ranks top 10 on any of the app's core phrases, or a new app holds top 5 on 2+ core phrases. Note swaps in `playbook.json` learnings with a date and reason.

First run: `search_app_store` (limit 15) on 5–9 core job phrases. Keep apps that solve the same job for the same user; mix leaders with small apps that rank beside them; include the inspiration app if there is one. Record App Store ID, name, subtitle, ratings, why.

## Step 4 — Keyword pool (≥ 100 phrases)

- `extract_competitors_keywords` on 15+ seed phrases (the app's jobs plus the competitors' best phrases).
- For non-English markets, research in that market's language and culture: seed with how locals phrase the need and what local competitors use, not translations of English keywords. Keep English terms only where Astro shows locals search them.
- Treat accented and unaccented spellings (e.g. `días` and `dias`) as separate candidates until Astro shows they behave the same.
- Add: the user's "problem" phrasing ("help me sleep"), head term + extra word ("budget app for couples"), feature words from the app's user stories, the playbook's keep/hold list. Skip dropped phrases.
- If a major shopping or holiday season in this store's market is about 2–8 weeks away and fits the app, add one seasonal phrase as a labelled experiment, with popularity ≥ 20; otherwise skip it. Look up holidays per market.
- Account for words already covered by listings the storefront reads; do not assume coverage from display-language support alone.
- `add_keywords` to the research app in batches of ≤ 30. Pace all calls as described in the Gate.

## Step 5 — Score and bucket

For every phrase with popularity ≥ 20, `search_app_store` limit 10 and record popularity, difficulty, small apps in top 10, which competitors rank top 10, and intent (**pass** = results are apps like ours, **mixed**, **reject**).

| Tag | Rule (maturity band: New; see step 1 for other bands) |
|---|---|
| Climb now | difficulty ≤ 30 or ≥ 6 small apps; intent pass/mixed |
| Stretch | difficulty 31–55 and ≥ 3 small apps |
| Later | difficulty > 55 or 0–2 small apps |
| Drop | popularity < 20, wrong intent, brand, or the app can't deliver |

**Expected rank at the next measure** (an estimate; label it as one):

| Tier | Rule |
|---|---|
| A — top 10 likely | difficulty ≤ 30 and ≥ 6 small apps |
| B — 11–30 likely, top 10 possible | difficulty ≤ 50 and ≥ 4 small apps |
| C — top 50 at best | anything else |

Drop one tier when the phrase relies on the keyword field (Apple weights title > subtitle > keywords). Brand phrases: keep the current rank.

Write a note on each Climb/Stretch phrase in Astro (`set_keyword_note`: small apps + competitor ranks) and a one-line reason on notable drops.

## Step 6 — Product check

Read the app's user stories or feature list. Remove phrases the app can't honestly satisfy (e.g. "photo editor" for an app with no editing). Borrow the competitors' *job* words, not their *format* words.

## Step 7 — Proposal

Write `_ai/aso/<store>/runs/YYYY-MM-DD/proposal.md` from `assets/proposal-template.md`: plain English, one table per field, each targeted phrase showing **now rank** and **expected tier**. Placement:

- **Title (30):** brand + strongest honest job phrase + easiest real-search phrase.
- **Subtitle (30):** next-best phrases, readable at a glance.
- **Keywords (100):** single words, commas, no spaces, no repeats of title/subtitle words, no plurals of existing words. Apple combines words across all three fields.
  - Free space: remove words already in the title or subtitle (Apple counts each word once across the three fields) and words that add nothing.
  - Fill with words that combine with title or subtitle words into phrases with popularity >= 20; the individual words need not reach 20 alone.
  - Check how locals ask, including questions and synonyms, and check spelling or accent twins in Astro. Twins can differ in popularity; keep the one with data.
  - If the field stays under about 90 characters, list each skipped candidate and why in the proposal.
- **Promotional text (170):** selling points people don't search for. Not indexed; editable without review.
- **Description:** plain use cases. Not indexed on iOS, but AI assistants read it.

Validate lengths and repeats: `python3 scripts/check_metadata.py --title ... --subtitle ... --keywords ... --promo ...`.

For multiple listings, work in order: primary listing first, then hub listings read by other target storefronts, then local listings. Remove words already covered by earlier listings each storefront reads. Check all affected storefronts together with `--listings`; see `references/tools.md` for the input. If the app has one market, run its one listing only.

### Script checks and judgment

The script checks supplied listing lengths, repeated words, supplied names, categories and missing-feature terms, and target popularity when supplied. It warns about possible plurals. Provide missing-feature terms from this app's own feature files, not a generic list. The model must judge intent, native wording, reach, rank realism and plural warnings; a clean check does not prove those claims. Apple's [product page guidance](https://developer.apple.com/app-store/product-page/) advises against duplicate words, category names, “app” and plurals in keywords.

Tag every targeted phrase **Proposed**. Append a `proposal` line to `log.jsonl` with the metadata and each phrase's predicted tier. Ask the human to approve.

## Step 8 — Ship and record

After approval only, draft the new version in App Store Connect with `asc` (commands in `references/tools.md`). The human submits it; never submit for review.

1. **Pick the build — don't assume.** `asc status --app <ID>` and list recent builds. Show the user the newest valid build (version, build number, upload date) and any existing draft version. If no valid build is newer than the live version, stop and say so. Use only the build the user confirms.
2. **Create the version** with `--copy-metadata-from <live version>` so description, URLs, screenshots and release settings carry over. Reuse an existing draft instead of creating a second one.
3. **Attach the confirmed build.**
4. **Set only the approved fields:** keywords and promotional text on the version; title and subtitle on the editable (`PREPARE_FOR_SUBMISSION`) app info. "What's New" is required for updates: draft it from the build's changes and flag it for the user to review.
5. **Verify** by reading back the draft and the live version: every field not in the proposal must match, and screenshot counts must match. Report the diff.

Append a `proposal` line with `"approved": true` and the drafted version and build. When the version is live, append a `shipped` line (live date, version, exact metadata). That date is day 0 for the next measure.
