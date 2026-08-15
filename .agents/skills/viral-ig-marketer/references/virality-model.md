# Virality Model

This file is owned and updated by the agent. It is a living plain-English description of what makes content go viral in this niche, based on accumulated research and experiment data.

The agent reads this file at every cycle start. After each cycle (analytics pull + content creation), the agent updates this file with new evidence. No human edits needed.

---

## What This Model Is

A simple, opinionated filter the agent applies before creating any piece of content.

The model answers one question: **"Can this content hit 100k+ views?"**

We're building a viral content engine, not a slow-growth brand account. Content that spreads earns reach without relying on followers. Content that sits requires an existing audience. Since we are starting from near-zero followers, viral reach is everything. If a content idea can't plausibly hit 100k views, it doesn't get made.

---

## Platform Mechanics (refreshed monthly — last update: 2026-03-17)

How Instagram distributes content — the foundation for format and creative decisions.

**Reels vs Carousels:**
- Reels are **discovery-first**: Instagram's Reels algorithm is specifically designed to surface content to non-followers. ~55% of Reel views come from non-followers. For accounts with few followers, reels are the primary path to reach.
- Carousels are **engagement-first**: highest engagement rate (~0.55% vs ~0.52% for reels), but they mostly reach existing followers. Best for educational, save-worthy content once an audience exists.
- Static images: declining in both engagement and posting volume. Deprioritize.

**Reels ranking signals (in order of weight):**
1. **Watch time / completion rate** — the single most important signal. 70%+ completion = significantly wider distribution. Instagram tracks: did viewers watch past 3 seconds? Watch to the end? Replay?
2. **DM sends per reach** — the strongest signal for non-follower reach. Adam Mosseri confirmed DM shares carry the most weight for unconnected reach. Make content people want to send to someone.
3. **Likes per reach** — most relevant for connected reach (existing followers). The ratio matters more than raw count.

**Reels eligibility rules (must pass ALL to be recommended):**
- No watermarks from other platforms (TikTok, CapCut logos)
- Original or properly licensed audio
- Meets community guidelines
- No recycled/reposted content — Instagram uses an "Originality Score" via visual fingerprinting. Original content gets 40-60% reach boost; recycled content gets tanked.
- Under 3 minutes (longer = ineligible for recommendations)

**"Your Algorithm" feature (Dec 2025):** Users can now explicitly choose which topics they see. Niche clarity matters more than ever — the hook, on-screen text, and audio all need to clearly signal the topic so Instagram categorizes it correctly.

**Small account advantage:** Accounts under 5K followers get ~3.79% avg engagement on reels vs ~0.55% on carousels. Reels are the format to bet on during the growth phase.

**What this means for us:** Default to reels. Optimize for watch time (hook + pacing) and shareability (make it worth sending to a friend). Use carousels for deep educational content that earns saves.

---

## Virality Proxies (signals we can measure)

These are the signals the agent uses to score content retroactively and calibrate the model forward.

| Signal         | What it means                                                     | How to read it                                                                                     |
| -------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Views          | Algorithmic reach — how many people Instagram showed it to        | High = algorithm pushed it beyond followers                                                        |
| Watch time     | How long people watched — the #1 Reels ranking signal             | 70%+ completion = wide distribution. Track 3s retention (hook test) and full completion separately |
| DM sends       | Viewers sharing via DM — strongest signal for non-follower reach  | Any DM sends = strong discovery signal. Optimize for "would someone send this to a friend?"        |
| Saves          | Perceived future value — "I want this again"                      | High save rate (>3%) = strong utility or emotion                                                   |
| Profile visits | Curiosity triggered — viewer wanted to know more about the source | High = content created identity pull                                                               |
| Share rate     | Social currency — viewer wanted to pass this on                   | Any sharing = strong virality signal                                                               |

---

## Initial Virality Hypotheses

These are starting assumptions. The agent replaces them with evidence-backed findings as experiments run.

**Hook virality:**
Content that opens with a tension, a surprising contrast, or a question the viewer is already asking themselves performs better than content that opens with a statement of fact. The first line determines whether the algorithm shows it to anyone.

**Format virality:**
Different formats have different viral mechanics on different platforms and in different niches. The agent discovers which formats perform through experimentation — no format is pre-characterized. Track each format separately in results.jsonl. Let accumulated data reveal which formats drive reach vs. conversion in this specific niche.

**Emotional register:**
Content that makes someone feel understood or seen spreads faster than content that informs. Information is shareable. Emotional resonance is viral.

**Specificity:**
Specific, concrete content outperforms generic advice. A post addressing a precise pain point the audience recognizes outperforms broad tips. Specificity signals expertise and signals that the creator knows the audience's exact experience.

**Niche-fit:**
Content that looks like it belongs in this niche (uses the right tone, vocabulary, visual style) gets shared within the niche. Content that looks imported from outside gets ignored.

---

## Virality Score (simple decision gate)

Before creating any post, score the planned content against these 5 questions. Each yes = 1 point.

1. **Hook tension:** Does the first 3 seconds create tension, surprise, or ask a question the viewer is already wondering? (This determines whether anyone watches past the opening.)
2. **Specificity:** Is the topic specific enough that someone in this niche would think "this is exactly about me"?
3. **Emotional resonance:** Does the content make someone feel understood, validated, or motivated — not just informed?
4. **Sendable:** Would someone DM this to a friend? (DM sends are the #1 driver of non-follower reach. Think: "you need to see this" moments.)
5. **Watchable:** Will someone watch to the end? Is the pacing tight enough that nothing drags? (Watch time is the #1 ranking signal — every second of dead time costs distribution.)

**Score threshold:**
- 4–5: Green — proceed with this content
- 3: Yellow — revise before proceeding (usually fix the hook or specificity)
- 0–2: Red — discard — this is not worth posting. Research a better angle.

---

## Performance Baseline (agent-computed, not hardcoded)

The thresholds below are **bootstrap priors only** — used until the first scored entry exists in `results.jsonl`.

After that, the agent computes a running baseline from the full history in `results.jsonl` (which is append-only and never modified) and **rewrites the summary table below** each cycle. The table is a computed snapshot, not a record — `results.jsonl` is the record. Internal data always wins over these priors.

### Bootstrap priors (before batch 1 is scored)

**These are generic platform averages used only until the first scored entry exists.** They are not niche-specific predictions. After the first scored cycle, the agent overwrites this entire section with computed baselines from `results.jsonl`. Do not treat these as targets — they are placeholder thresholds to avoid having no reference point on day 1.

| Signal         | Bootstrap threshold                   | What it means                              |
| -------------- | ------------------------------------- | ------------------------------------------ |
| Views          | > 100,000                             | Target: viral reach (100k+ views per post) |
| Save rate      | > 3% of views                         | Strong utility signal                      |
| Profile visits | > 1.5% of views                       | Curiosity / intent                         |
| Watch-through  | > 50% (reels only — secondary format) | Hook + content both held                   |

### After first scored entry: agent computes and writes its own baseline here

After the first scored entry exists in results.jsonl, the agent computes:
- `avg_views` — mean views across all scored entries in results.jsonl
- `avg_save_rate` — mean (saves / views) across scored entries
- `avg_profile_visit_rate` — mean (profile_visits / views)
- `top_format` — format with highest avg save rate so far

These replace the bootstrap thresholds. The agent rewrites the table below after every cycle. On the very first cycle there is no prior data — skip this step and use bootstrap priors until the first scored entry exists.

| Signal         | Current baseline | Sessions scored | Last updated |
| -------------- | ---------------- | --------------- | ------------ |
| avg_views      | —                | 0               | —            |
| avg_save_rate  | —                | 0               | —            |
| avg_visit_rate | —                | 0               | —            |
| top_format     | —                | 0               | —            |

**How to use this baseline:** when writing `reasoning.vs_baseline` in results.jsonl, compare the actual cycle outcome to the current baseline values here. A post is "above baseline" if views AND save rate both exceed current averages. A post is "below baseline" if both are under. Mixed results = flag for closer review.

**Threshold drift rule:** if the baseline shifts >50% in either direction across two consecutive cycles, note the cause. Likely signals: account growing (good), content category shift, or algorithm change.

---

## How the Agent Updates This Model

**After every cycle's analytics pull:**
- Look at the 2 highest-scoring posts in results.jsonl. What did they have in common? Add finding to "Evidence" section below.
- Look at the 2 lowest-scoring posts. What was weak? Add finding.
- Adjust any hypothesis above that the evidence contradicts.

**After every research cycle:**
- What hook patterns are getting the most engagement in the niche right now? Update "Initial Virality Hypotheses."
- Is a new format emerging (e.g., memes replacing carousels in this niche)? Update the format section.
- Adjust score threshold if the current threshold is too loose (posting low-virality content) or too tight (agent is stuck).

**After any shadow ban signal:**
- Document what content was posted immediately before the drop. Add to a "platform risk" note.
- Adjust model to avoid that content pattern.

---

## Evidence Log

_Agent appends findings here after each cycle's analytics pull. Newest entries at the top._

| Date       | Batch     | Finding                                                                                                                                                                                                                                                                                                                                                                                                                   | Model change                                                                                                                                                                                                                                                                            |
| ---------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-03-18 | cycle-004 | Formal experiment batch started (exp-001: shock_stat hooks). Using Surgeon General 2025 alcohol-cancer advisory as topic source — TIME, Reuters, ScienceDaily all covered it in Jan-Mar 2026. Hypothesis: concrete shocking numbers (100,000 cancers/year) create stronger knowledge-gap reactions than percentages or abstract claims. Text-on-gradient imagery as control. Cannot score yet — cycle-003 not published.  | No model change yet — awaiting first reel metrics.                                                                                                                                                                                                                                      |
| 2026-03-18 | cycle-002 | 0 reach on second consecutive carousel (myth-busting listicle). Two carousels, both 0 reach. Carousels are engagement-first — they mostly reach existing followers. With 2 followers, carousels get zero algorithmic distribution. Research confirms: small accounts under 5K get ~3.79% engagement on reels vs ~0.55% on carousels. DM shares weighted 3-5x higher than likes in 2026 algorithm (CreatorFlow, Feb 2026). | **Format switch: default to reels.** Carousels are wrong format for cold-start account. Reels get pushed to non-followers. Also: news-peg content (timely real-world events) maximizes DM-sendability — the #1 reach signal. Cycle-003 tests this with US dietary guidelines news hook. |
| 2026-03-17 | cycle-001 | 0 reach on first carousel (timeline/body-change topic). Account has 2 followers — this is a cold start distribution problem, not a content quality signal. Cannot draw conclusions about hook or topic effectiveness from zero-reach data.                                                                                                                                                                                | No model change — insufficient data. Key insight: content experiments are meaningless until the account has minimum distribution. Manual engagement (commenting in niche, following relevant accounts) may be needed to seed the algorithm.                                             |

---

## Research Sources

When updating this model, the agent may consult:
- Web search for niche trends — NO Instagram browsing
- Web search: "what makes content go viral on Instagram [year]", "Instagram algorithm [niche] reach", "highest save rate Instagram content types" — **3-month recency rule: only use sources from the last 90 days**
- `references/results.jsonl` — internal experiment data (primary source after 10+ posts)
- `../viral-research/references/swipe-file.jsonl` — niche patterns from research cycles

Internal data (results.jsonl) always overrides external research when they conflict.
