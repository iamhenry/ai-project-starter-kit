---
name: aso-hillclimber
description: Repeatable, closed-loop App Store keyword optimization for one iOS app using the asc CLI and Astro MCP. Measures the last metadata test against the app's goal (sales, trials, or downloads), keeps a standing list of 10 competitors, scores keywords by real search demand and beatable top-10 results, and writes a plain-English proposal with current and expected ranks. Use whenever the user wants to improve App Store rankings or downloads, run or re-run ASO, pick a title, subtitle, or keyword field, check how the last metadata change performed, or asks "why isn't my app ranking". Prefer this over aso-worker for keyword selection.
compatibility: Requires the Astro MCP server and an authenticated asc CLI (App Store Connect). Stops with BLOCKED if either is unavailable. Works for paid-upfront, free-trial, and free apps.
---

# ASO Hillclimber

One run = one app, one storefront (start with `us`), one language. Every run ends with one entry appended to the app's log, so the next run starts where this one stopped.

## Why this works (read once)

People find apps by searching. Apple shows apps whose **title, subtitle, or hidden keyword field** contain the searched words, ordered mostly by how well each app has done on that search (downloads, taps, ratings). Only the top ~10 get seen. A small app can't beat the leaders on big searches, so it starts where real people search **and** the top 10 holds other small apps, earns downloads there, and climbs.

The trap: picking phrases because they're *easy to rank on*. Easy almost always means *nobody searches it* (Astro popularity 5). Ranking #1 there brings no one. That is why rule 1 exists.

## Hard rules

1. **Real demand only.** Targets need Astro popularity ≥ 20. Popularity 5 = no searches; never a target.
2. **Exactly 10 competitors**, kept in `config.json` and including the app's inspiration if it has one.
3. **Beatable.** Count top-10 apps with < 100 ratings ("small apps"). More small apps = easier.
4. **Honest.** Only words the app delivers today. No competitor or brand names.
5. **Keep winners, drop losers.** Never remove a phrase ranking top 10; never keep one with no searches. Never re-propose a dropped phrase without a new reason.
6. **Judge by the goal metric and App Store Search impressions**, not rank counts.
7. **Human approves before anything is staged** in App Store Connect.

## The app's ASO memory

In the app repo, `_ai/aso/` (examples in `assets/`):

| File | Holds | Who writes it |
|---|---|---|
| `config.json` | IDs, store, goal metric and target, business model, seed and core phrases, the 10 competitors | Set on the first run; edit when the goal or a competitor changes |
| `playbook.json` | Phrases to keep, hold, drop (with reasons), learnings | Updated at the end of every run |
| `log.jsonl` | One JSON line per event: `baseline`, `measure`, `proposal`, `shipped` | Append only; never edit old lines |
| `runs/YYYY-MM-DD/` | `research.md`, `proposal.md`, `evidence.json` (raw Astro output) | One folder per proposal |

Live metadata isn't stored: read it from App Store Connect each run.

## Gate — data or stop (before anything else)

Every number this skill reports must come from a tool, not from memory or general knowledge. Check both sources first:

| Source | Check | Gives |
|---|---|---|
| Astro MCP | `list_apps` returns a result | Popularity, difficulty, ranks, top-10 apps, rating counts |
| App Store Connect | `asc auth status --validate` passes | Live metadata, version, price, release date |

If either check fails, **stop**. Report `BLOCKED: <source> unavailable — <error>` and do no research, scoring, or proposal. Don't fall back to web search, App Store pages, or estimates.

Funnel numbers (impressions, page views, downloads, sales) come from `asc analytics` or from App Store Connect screenshots the user provides. If neither is available, stop before judging a test; ranks alone can't decide the goal.

While working:
- Cite the source and date beside every number (`Astro 2026-11-04`, `ASC screenshot Aug 6–Nov 3`). Save the raw Astro responses to `runs/YYYY-MM-DD/evidence.json`.
- If Astro fails mid-run, stop and report what is done; never fill gaps with guesses.
- Estimates (expected tiers, funnel math) must be labelled as estimates and built only from those numbers.

## Step 0 — Which run is this?

- **New app** (no `_ai/aso/`): create `config.json` and `playbook.json` from `assets/`. Ask for the goal in plain words, e.g. "5 sales in 14 days" (paid), "10 trial starts in 14 days" (trial), "50 downloads in 14 days" (free). Run step 1 and log a `baseline`. Then steps 2–8.
- **Existing app**: read all three files. Find the last `shipped` line and count days since it went live. Run step 1 and log a `measure`. Then, if the user wants a new change, steps 2–8 using the playbook.

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

**Funnel** for the window (since the last ship, or the last 90 days for a baseline) from App Store Connect → Analytics. Use **Sources → App Store Search** for keyword judgement and the total for the goal: impressions, product page views, first-time downloads, goal metric. If the API key lacks the Analytics role, ask the user for screenshots.

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
- Add: the user's "problem" phrasing ("help me sleep"), head term + extra word ("budget app for couples"), feature words from the app's user stories, the playbook's keep/hold list. Skip dropped phrases.
- `add_keywords` to the research app in batches of ≤ 30. Run searches one at a time; Astro rate-limits parallel calls.

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

Write `runs/YYYY-MM-DD/proposal.md` from `assets/proposal-template.md`: plain English, one table per field, each targeted phrase showing **now rank** and **expected tier**. Placement:

- **Title (30):** brand + strongest honest job phrase + easiest real-search phrase.
- **Subtitle (30):** next-best phrases, readable at a glance.
- **Keywords (100):** single words, commas, no spaces, no repeats of title/subtitle words, no plurals of existing words. Apple combines words across all three fields.
- **Promotional text (170):** selling points people don't search for. Not indexed; editable without review.
- **Description:** plain use cases. Not indexed on iOS, but AI assistants read it.

Validate lengths and repeats: `python3 scripts/check_metadata.py --title ... --subtitle ... --keywords ... --promo ...`.

Tag every targeted phrase **Proposed**. Append a `proposal` line to `log.jsonl` with the metadata and each phrase's predicted tier. Ask the human to approve.

## Step 8 — Ship and record

After approval only, draft the new version in App Store Connect with `asc` (commands in `references/tools.md`). The human submits it; never submit for review.

1. **Pick the build — don't assume.** `asc status --app <ID>` and list recent builds. Show the user the newest valid build (version, build number, upload date) and any existing draft version. If no valid build is newer than the live version, stop and say so. Use only the build the user confirms.
2. **Create the version** with `--copy-metadata-from <live version>` so description, URLs, screenshots and release settings carry over. Reuse an existing draft instead of creating a second one.
3. **Attach the confirmed build.**
4. **Set only the approved fields:** keywords and promotional text on the version; title and subtitle on the editable (`PREPARE_FOR_SUBMISSION`) app info. "What's New" is required for updates: draft it from the build's changes and flag it for the user to review.
5. **Verify** by reading back the draft and the live version: every field not in the proposal must match, and screenshot counts must match. Report the diff.

Append a `proposal` line with `"approved": true` and the drafted version and build. When the version is live, append a `shipped` line (live date, version, exact metadata). That date is day 0 for the next measure.
