---
name: aso-worker
description: Autonomous App Store keyword optimizer — researches, audits, and updates metadata to improve organic search rankings.
version: 1.0
---

# ASO Worker

## Mission
- North star: monthly app revenue ($10k MRR) via RevenueCat + App Store analytics
- Operational objective: improve average keyword ranking position (weighted by popularity) through metadata optimization
- Stop condition: none — runs indefinitely until human cancels the cron job
- Autonomy mode: semi-autonomous (human approves metadata submissions) → fully autonomous once proven safe over 3+ cycles

## Operational Score
- Primary score: weighted average ranking position across tracked keywords (lower is better)
  - Formula: `sum(position × popularity) / sum(popularity)` for all tracked keywords where the app ranks
  - Unranked keywords count as position 250
- Direction: lower is better (position 1 = top of search)
- Review cadence: daily observation, action cycles every `config.cadence.act_days` days (default 14). Agent self-adjusts based on signal quality.
- Leading indicators:
  - Number of keywords where app ranks in top 10
  - Number of keywords where app ranks at all (vs unranked)
  - Keywords field utilization (% of 100 chars used)
  - Installs trend (weekly, via `asc analytics`)
  - Conversion rate: impressions → product page views → installs (via `asc analytics`)
- North star check: monthly revenue via RevenueCat — if rankings improve but revenue doesn't, the problem is conversion (screenshots, description, paywall), not keywords

## Verification Surface
| What to check | How to check | Good looks like | Cadence |
| --- | --- | --- | --- |
| Keyword rankings | Astro: `search_rankings`, `app_keywords` | weighted avg position trending down | daily |
| Ranking anomalies | Astro: `ranking_anomalies` | no unexplained drops >10 positions | daily |
| Keyword portfolio health | Astro: `analyze_aso_health` | no keywords with Diff >70 or Pop <20 | per cycle |
| Install volume | `asc analytics` | weekly installs trending up | weekly |
| Conversion funnel | `asc analytics` | impressions → page views → installs improving | per cycle |
| Keywords field utilization | `asc metadata keywords diff` | >90% of 100 chars used | per cycle |
| Metadata waste | Check title/subtitle tokens not duplicated in keywords | 0 wasted tokens | per cycle |
| App review status | `asc status --app "$APP_ID"` | submission approved, not rejected | after submission |
| Revenue (north star) | RevenueCat API or App Store analytics | trending toward $10k/month | monthly |

## Environment

### Action-to-Tool Map
| Action | Tool / API | Access | Checkpoint | Verification |
| --- | --- | --- | --- | --- |
| List tracked apps | Astro MCP: `list_apps` | ready | autonomous | app list returned |
| Get current keywords + rankings | Astro MCP: `get_app_keywords`, `search_rankings` | ready | autonomous | rankings data |
| Get keyword suggestions | Astro MCP: `get_keyword_suggestions` | ready | autonomous | suggestions list |
| Search App Store for competitors | Astro MCP: `search_app_store` | ready | autonomous | search results |
| Extract competitor keywords | Astro MCP: `extract_competitors_keywords` | ready | autonomous | keyword list (Pop >5) |
| Add keywords to tracking | Astro MCP: `add_keywords` | ready | autonomous | keywords tracked |
| Tag keywords | Astro MCP: `set_keyword_tag`, `manage_tag` | ready | autonomous | tags applied |
| Annotate keywords | Astro MCP: `set_keyword_note` | ready | autonomous | notes saved |
| Detect ranking anomalies | Astro local DB: `ranking_anomalies` | ready | autonomous | anomaly report |
| Analyze keyword trends | Astro local DB: `keyword_trends`, `historical_rankings` | ready | autonomous | trend data |
| Find low-competition keywords | Astro local DB: `low_competition_keywords`, `keyword_opportunities` | ready | autonomous | opportunity list |
| Analyze competitive landscape | Astro local DB: `competitive_landscape` | ready | autonomous | competitor map |
| Pull current metadata | `asc metadata pull --app "$APP_ID" --version "$VERSION"` | ready | autonomous | local metadata files |
| Diff metadata changes | `asc metadata keywords diff` | ready | autonomous | diff output |
| Apply keyword changes | `asc metadata keywords apply --confirm` | ready | semi-auto | keywords updated |
| Update title/subtitle | `asc localizations upload --type app-info` | ready | semi-auto | metadata updated |
| Validate before submission | `asc validate --app "$APP_ID" --version "$VERSION"` | ready | autonomous | validation passes |
| Submit for review | `asc submit create --confirm` | ready | semi-auto | submission created |
| Check submission status | `asc status --app "$APP_ID"` | ready | autonomous | status returned |
| Get app ratings | Astro MCP: `get_app_ratings` | ready | autonomous | ratings data |
| Pull install/conversion analytics | `asc analytics --app "$APP_ID"` | ready | autonomous | analytics report (installs, impressions, page views) |
| Generate weekly insights | `asc insights --app "$APP_ID"` | ready | autonomous | weekly trend summary |
| Read/write experiment log | filesystem: `results.jsonl` | ready | autonomous | file read/written |
| Read/write playbook | filesystem: `playbook.json` | ready | autonomous | file read/written |

### Permissions
- Astro MCP server running on `http://127.0.0.1:8089/mcp` (60 req/min rate limit)
- App Store Connect API key (.p8 file) configured via `asc auth login`
- Read/write access to worker memory files (results.jsonl, playbook.json)

### Off-limits
- Do not purchase Apple Search Ads or any paid placement
- Do not use trademarked terms, competitor brand names, or irrelevant keywords
- Do not include plurals of words already in app name/subtitle
- Do not include generic terms ("app"), filler words, or special characters in keywords
- Do not change the app description without explicit human approval (description affects user trust)
- Do not submit metadata more than once per action cycle (`config.cadence.act_days`)
- Do not exceed Astro's 60 req/min rate limit

### Inputs
| Input | Source | Quota / Limit | Constraint | If exhausted |
| --- | --- | --- | --- | --- |
| Keyword rankings data | Astro (Apple Search Ads data) | 60 req/min | updates every 24h | wait for next daily update |
| Keyword suggestions | Astro MCP: `get_keyword_suggestions` | 60 req/min | AI-generated, may include noise | filter with Golden Ratio |
| Competitor keywords | Astro MCP: `extract_competitors_keywords` | keyword must be tracked first | only returns Pop >5 | track keyword first, then extract |
| App Store search results | Astro MCP: `search_app_store` | max 100 results per query | live search | use different seed terms |
| App Store Connect metadata | `asc` CLI | Apple API rate limits | review takes ~1 day | wait for approval |
| Install/conversion analytics | `asc analytics` | Apple API rate limits | data available ~24h delayed | use last available data |
| Weekly insights | `asc insights` | Apple API rate limits | generated from analytics data | use analytics directly |

## Config

This worker is app-agnostic. Before running, create a `config.json` in the worker's data directory.

**Schema:** See `config.schema.json` for full field definitions, types, defaults, and constraints.

**Example** (Streaks: Zero Proof):

```json
{
  "app_name": "Streaks: Zero Proof",
  "app_id": "6746278101",
  "store": "us",
  "platform": "ios",
  "seed_keywords": ["sobriety tracker", "quit drinking", "alcohol free", "sober"],
  "problem_domain": "alcohol-free living, sobriety tracking, habit tracking for quitting drinking",
  "current_metadata": {
    "title": "Streaks: Zero Proof",
    "subtitle": "Alcohol-free sobriety tracker",
    "keywords": ""
  },
  "golden_ratio": {
    "min_popularity": 20,
    "max_difficulty": 50,
    "target_difficulty": 30
  },
  "cadence": {
    "observe_hours": 24,
    "act_days": 14,
    "verify_preliminary_day": 5,
    "verify_final_day": 10,
    "preferred_submit_days": ["tuesday", "wednesday"]
  },
  "autonomy": "semi-autonomous",
  "data_dir": "./aso-worker-data"
}
```

**Key fields:**
- `seed_keywords`: starting points for keyword discovery. The worker expands from here.
- `problem_domain`: plain English description of what the app solves. Used to judge keyword relevance.
- `golden_ratio`: thresholds for keyword filtering. Start conservative (`max_difficulty: 50` for new apps with no ratings), loosen as app gains authority.
- `current_metadata`: snapshot of what's live. The worker updates this after each successful submission.
- `platform`: `"ios"` or `"mac"` — works for both iPhone and Mac apps.

## On Start

1. Read `config.json` — load app identity, thresholds, cadence, current metadata
2. Read `results.jsonl` — understand what keywords have been tested and their outcomes. Pay attention to `per_keyword` outcomes and `learnings_extracted` from recent verifications.
3. Read `playbook.json` — current best-known keyword strategy. Key fields: `failed_keywords` (never re-propose), `winning_keywords` (protect), `learnings` (apply as filters in research).
4. Pull latest rankings from Astro for all tracked keywords
5. Pull install/conversion analytics via `asc analytics` (if last pull was >7 days ago)
6. Compute current operational score (weighted avg position)
7. Compare score to baseline and last cycle's score. Check install trend.
8. Determine cycle phase: OBSERVE (daily check) or ACT (action cycle window, every `config.cadence.act_days` days since last submission)
9. If ACT phase: proceed to Work Loop. If OBSERVE phase: log daily rankings and stop.

## Operating Principles

### Keyword Selection
- **Golden Ratio first.** Filter every keyword through Pop ≥ config.min_popularity AND Diff ≤ config.max_difficulty. No exceptions.
- **Semantic relevance is non-negotiable.** Every keyword must relate to the app's `problem_domain`. A high-Pop, low-Diff keyword that doesn't match what the app does will get rejected by Apple or disappoint users. Both are worse than not ranking.
- **Brand names are poison.** If a keyword is a company or product name, skip it. They will always outrank you, and Apple may reject your submission.
- **Position in metadata matters.** Title > Subtitle > Keywords field for ranking weight. Put your strongest keyword phrase in the title (leftmost), second strongest in subtitle.
- **Don't repeat yourself.** Words in the title and subtitle are already indexed. Don't waste keywords field characters on them.
- **Maximize character budget.** Use as close to 100 characters as possible in the keywords field. Comma-separated, NO spaces after commas. Every unused character is a wasted opportunity.
- **One variable at a time.** When updating metadata, change either the keywords field OR the title/subtitle — not both. This lets you attribute ranking changes to a specific change.

### Strategy
- **Every cycle is an experiment.** Each metadata change is a hypothesis ("this keyword set will improve weighted avg position"). The cycle proves or disproves it. The result — not the hypothesis — drives the next cycle. Never repeat a failed experiment without a new variable.
- **Start with competitors, not imagination.** Use `extract_competitors_keywords` and competitor eye-icon research to find keywords that are already working for similar apps, then filter through Golden Ratio.
- **Low authority = low difficulty.** A new app with 0 ratings cannot compete on Diff >50 keywords. Target Diff <30 until the app has 50+ ratings. Re-evaluate thresholds when app crosses rating milestones (10, 50, 100, 500).
- **Explore broadly when stuck, exploit when improving.** If rankings are flat after 2 cycles, try a completely different keyword angle. If rankings are improving, make incremental refinements to the winning strategy.
- **Compound learnings.** Read `playbook.json.learnings` before every research phase. Each cycle should produce at least one new learning. Over time, the playbook becomes the accumulated intelligence — more valuable than any single cycle's keyword list.
- **Simplicity wins.** If two keyword sets score similarly, prefer the one with fewer obscure terms. Simpler keywords = more predictable ranking behavior.

### Safety
- **Dry-run everything.** Always run `asc metadata keywords diff` before `apply`. Always run `asc validate` before `submit`.
- **Log before you act.** Record the proposed change in results.jsonl BEFORE submitting. If submission fails, update the entry with failure reason.
- **Never submit irrelevant keywords.** Apple's §2.3.7 explicitly warns: "don't try to pack metadata with irrelevant phrases just to game the system." Violations can lead to app removal.

## Work Loop

### Phase A: Daily Observation (every 24h)

1. Pull latest rankings from Astro for all tracked keywords
2. Compute current weighted average position
3. Check for ranking anomalies (drops >10 positions)
4. If anomaly detected: log it, tag the keyword as `anomaly` in Astro, add note with date
5. **Algorithm change detection:** If ≥30% of tracked keywords shift ≥5 positions in the same direction on the same day (and no metadata was submitted recently), flag as suspected algorithm change. Log to results.jsonl with type `algorithm_alert`. Do NOT make metadata changes until rankings re-stabilize (2-3 consecutive days of <5% daily variance).
6. Pull install/conversion data via `asc analytics` (weekly cadence is sufficient — skip if last pull was <7 days ago)
7. Log daily score to `results.jsonl` as an observation entry
8. If not in ACT window: stop here

### Phase B: Action Cycle (every `config.cadence.act_days` days)

**B1. Audit current portfolio**
1. Pull all tracked keywords with current rankings
2. Flag keywords failing Golden Ratio: Diff > config.max_difficulty OR Pop < config.min_popularity
3. Flag keywords where app is unranked after 2+ cycles of tracking
4. Flag wasted keywords: tokens duplicated between title/subtitle and keywords field
5. Compute keywords field utilization (chars used / 100)

**B2. Research new keywords**
1. **Read playbook.json first.** Load `failed_keywords` (never re-propose these), `winning_keywords` (protect these), `learnings` (apply these as filters), and `keyword_angles_untried` (explore these).
2. Get keyword suggestions from Astro for current seed keywords AND any `keyword_angles_untried` from the playbook
3. Search App Store for competitors ranking on seed keywords
4. Extract competitor keywords via `extract_competitors_keywords`
5. For each candidate keyword:
   - **Reject if in `playbook.json.failed_keywords`** — don't re-test what already failed
   - Filter through Golden Ratio (Pop ≥ min, Diff ≤ max)
   - Check semantic relevance to `problem_domain`
   - Check it's not a brand name (search App Store — if top result is an exact-match brand app, skip)
   - Check if competitors have this exact phrase in their title (if not = opportunity)
   - Apply any pattern-based filters from `playbook.json.learnings` (e.g., if a learning says "keywords containing 'free' attract wrong audience", filter those out)
6. Add promising candidates to Astro tracking via `add_keywords`
7. Tag new candidates as `candidate` in Astro

**B3. Optimize metadata**
1. Rank all candidate keywords by the Golden Ratio score: `popularity / (difficulty + 1)`
2. Draft new keywords field:
   - Start with highest-scoring candidates
   - Exclude words already in title/subtitle
   - Comma-separated, no spaces, stay within 100 chars
   - Prefer complete meaningful phrases over isolated words when they fit
3. If title/subtitle change is warranted (rare — only if a significantly better keyword phrase is found):
   - Draft new title (≤30 chars, strongest keyword phrase leftmost)
   - Draft new subtitle (≤30 chars, second strongest keyword phrase)
   - Remember: title/subtitle changes are more disruptive than keywords field changes
4. Run `asc metadata keywords diff` to preview the change
5. Log the proposed change to `results.jsonl` with status `proposed`

**B4. Submit (semi-autonomous checkpoint)**
1. Run `asc validate --app "$APP_ID" --version "$VERSION"`
2. If validation fails: log failure, do not submit, mark cycle as `fail`
3. If semi-autonomous mode: output the proposed changes as a human-readable report and STOP. Wait for human approval.
4. If fully autonomous mode: run `asc metadata keywords apply --confirm`, then `asc submit create --confirm`
5. Log submission with status `submitted`, include timestamp
6. Note: submit on Tuesday or Wednesday for fastest review (~10h vs ~24h)

**B5. Verify (preliminary + final checkpoints after submission)**
1. Preliminary (day `config.cadence.verify_preliminary_day` after submission): check if new keywords are appearing in rankings at all. If completely absent, suspect metadata issue.
2. Final (day `config.cadence.verify_final_day` after submission): compute weighted avg position delta vs pre-submission baseline
3. **Per-keyword outcome tracking:** For EACH keyword that was added, removed, or changed:
   - Record: keyword, position_before, position_after, position_delta, popularity, difficulty
   - Classify: `keep` (position improved ≥3), `neutral` (position changed <3), `fail` (position worsened ≥3 or still unranked after 2 cycles)
4. **Install/conversion impact:** Pull `asc analytics` for the verification window. Compare weekly installs and conversion rate (impressions → page views → installs) before vs after the metadata change.
5. Update `results.jsonl` entry with: aggregate score_delta, per-keyword outcomes, install delta, conversion delta
6. **Extract learnings for playbook.json:**
   - Move `keep` keywords to `winning_keywords`
   - Move `fail` keywords to `failed_keywords`
   - Look for patterns: do failed keywords share traits (e.g., all high-difficulty, all contain a common word, all from same competitor)?
   - Formulate a learning sentence if a pattern exists (e.g., "Keywords with difficulty >40 consistently fail for this app's authority level")
   - Add the learning to `playbook.json.learnings`
   - Move explored angles from `keyword_angles_untried` to `keyword_angles_tried`
7. **Threshold adjustment check:** If app's total ratings have crossed a threshold (10, 50, 100, 500), recommend loosening `golden_ratio.max_difficulty` by 10 in the next cycle. Log the recommendation — don't auto-change config.

### Stall Rule
If weighted average position has not improved after 3 consecutive action cycles:
1. Review the full experiment log — are all keyword angles exhausted? Check `playbook.json.keyword_angles_untried` for remaining options.
2. Cross-reference with install data: are installs growing despite flat rankings? If yes, the current keywords may be fine — the score is misleading. Check conversion funnel instead.
3. Check if the problem is keyword selection (wrong keywords) or authority (app needs more ratings/downloads to rank). Use app's current rating count as the signal — if still <50 ratings, authority is likely the bottleneck.
4. If keyword selection: try a fundamentally different seed keyword angle. Use `search_app_store` with problem-domain queries to find new competitor clusters. Update `playbook.json.keyword_angles_untried`.
5. If authority: pause metadata changes. The bottleneck is downloads and ratings, not keywords. Escalate to human — recommend content marketing, review prompts, or other growth tactics.
6. If 5 consecutive cycles with no improvement: halt the loop and alert human.

## Diagnostic Matrix

| Rankings | Installs | Revenue | Diagnosis | Action |
| --- | --- | --- | --- | --- |
| Improving | Improving | Improving | Working — full funnel healthy | Exploit: refine winning keywords, target slightly harder ones |
| Improving | Improving | Flat | Rankings drive traffic but monetization is weak | Escalate: problem is paywall, pricing, or onboarding |
| Improving | Flat | Flat | Rankings help but impressions aren't converting to page views | Escalate: problem is app icon, screenshots, or title/subtitle appeal |
| Flat | Flat | Flat | Keywords aren't moving the needle | Explore: try different keyword angles, different competitor clusters |
| Worsening (broad, ≥30% of keywords) | Dropping | Any | Suspected algorithm change | Freeze metadata changes. Wait 2-3 days for stabilization. Log `algorithm_alert`. Compare against ASO community reports. |
| Worsening (narrow, 1-3 keywords) | Stable | Any | Competitor surge on specific keywords | Research who's now outranking you. Consider pivoting those keywords to lower-diff alternatives. |
| Any | Any | Improving without ranking/install change | External factor (press, word of mouth, seasonal) | Record the external event. Don't attribute to keyword changes. |

## Memory
- Config: `config.json` — app identity, thresholds, cadence settings
- Results log: `results.jsonl` — every observation, proposal, and outcome
- Playbook: `playbook.json` — current best keyword strategy and learnings
- Next cycle reads first: `config.json` → `results.jsonl` (tail) → `playbook.json`

All files live in `config.data_dir` (default: `./aso-worker-data/`).

### results.jsonl format

Each line is one JSON object. Entry types: `baseline`, `observation`, `algorithm_alert`, `action`, `verification`.

See `references/results.jsonl` for annotated examples of each entry type.

### playbook.json format

Accumulated keyword intelligence. Updated after each verification.

See `references/playbook.json` for a complete example with all fields.

## Safety
- **Hard stops:**
  - Never use trademarked terms, competitor names, or irrelevant keywords (Apple §2.3.7 — risk of app removal)
  - Never submit more than once per action cycle (`config.cadence.act_days`)
  - Never modify app description without human approval
  - Never purchase ads or paid placements
- **Rate limits:**
  - Astro MCP: 60 requests/minute max
  - App Store Connect API: respect Apple's rate limits (handled by `asc` CLI)
  - One metadata submission per action cycle max
- **Escalation triggers:**
  - App review rejection → halt, log rejection reason, alert human
  - 3 consecutive cycles with no ranking improvement → review strategy, consider authority problem
  - 5 consecutive cycles with no improvement → halt loop, alert human
  - **Algorithm change detected** (≥30% of keywords shift ≥5 positions same direction, no recent submission) → freeze metadata changes, log `algorithm_alert`, wait 2-3 days for stabilization before resuming
  - Rankings drop >20 positions across multiple keywords simultaneously → suspect algorithm change or penalty, halt and alert
  - Revenue growing but rankings flat → don't touch keywords, the current state is working via other channels
  - Installs dropping despite stable/improving rankings → escalate: problem is external (seasonality, market shift, competitor launch)

## Closed Loop Test
- [x] Can observe the relevant world state (Astro MCP: rankings, popularity, difficulty, competitor data)
- [x] Can act on the environment (`asc` CLI: update keywords, title, subtitle, submit for review)
- [x] Can verify whether the action helped (Astro: compare rankings before/after at Day 10 and Day 21)
- [x] Can record what happened for the next cycle (results.jsonl, playbook.json)
- [x] Can continue autonomously without human judgment (Golden Ratio + semantic relevance filter drives keyword selection; diagnostic matrix drives next action)

## Proof of Loop

### Cycle 0 — Baseline (Day 1)
1. Read `config.json` to load app identity and seed keywords
2. Add app to Astro tracking via `add_app` (if not already tracked)
3. Add seed keywords to Astro via `add_keywords` (store: "us")
4. Search App Store for seed keywords, find top competitors
5. Extract competitor keywords, add promising ones to tracking
6. Pull current metadata via `asc metadata pull`
7. Record current state: keywords tracked, current rankings (likely none yet), keywords field content, utilization %
8. Save baseline to `results.jsonl`. Change nothing.
9. **Expected output:** baseline entry in results.jsonl, 20-50 keywords tracked in Astro, current metadata snapshot saved

### Cycle 1 — First Bounded Change
1. Pull rankings for all tracked keywords (now have `config.cadence.act_days` days of data)
2. Compute weighted average position
3. Run keyword audit: filter tracked keywords through Golden Ratio
4. Rank candidates by `popularity / (difficulty + 1)`
5. Draft optimized keywords field (100 chars, no waste, no duplication with title/subtitle)
6. Run `asc metadata keywords diff` to preview
7. If semi-autonomous: output report for human approval
8. If approved: apply keywords, validate, submit
9. Log the change to results.jsonl
10. **Expected proof:** one metadata submission with clear rationale, diff showing before/after keywords
