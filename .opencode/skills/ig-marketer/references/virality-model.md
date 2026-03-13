# Virality Model

This file is owned and updated by the agent. It is a living plain-English description of what makes content go viral in this niche, based on accumulated research and experiment data.

The agent reads this file at every session start. After each batch score and each research cycle, the agent updates this file with new evidence. No human edits needed.

---

## What This Model Is

A simple, opinionated filter the agent applies before creating any piece of content.

The model answers one question: **"Is this content likely to spread on its own, or will it just sit there?"**

Content that spreads earns reach without relying on followers. Content that sits requires an existing audience. Since we are starting from near-zero followers, reach is everything. High virality potential is non-negotiable.

---

## Virality Proxies (signals we can measure)

These are the signals the agent uses to score content retroactively and calibrate the model forward.

| Signal             | What it means                                                     | How to read it                                   |
| ------------------ | ----------------------------------------------------------------- | ------------------------------------------------ |
| Views              | Algorithmic reach — how many people Instagram showed it to        | High = algorithm pushed it beyond followers      |
| Saves              | Perceived future value — "I want this again"                      | High save rate (>3%) = strong utility or emotion |
| Profile visits     | Curiosity triggered — viewer wanted to know more about the source | High = content created identity pull             |
| Share rate         | Social currency — viewer wanted to pass this on                   | Any sharing = strong virality signal             |
| Watch-through rate | For reels — did people stay to the end?                           | >50% completion = hook + content both working    |

---

## Initial Virality Hypotheses (agent updates these based on evidence)

These are starting assumptions. The agent replaces them with evidence-backed findings as experiments run.

**Hook virality:**
Content that opens with a tension, a surprising contrast, or a question the viewer is already asking themselves performs better than content that opens with a statement of fact. The first line determines whether the algorithm shows it to anyone.

**Format virality:**
Carousels get saved. Reels get shared and discovered. Memes get shared fastest but convert least. The right format depends on the current goal: reach (reels/memes) vs. conversion (carousels). Track separately.

**Emotional register:**
Content that makes someone feel understood or seen spreads faster than content that informs. Information is shareable. Emotional resonance is viral.

**Specificity:**
Specific, concrete content outperforms generic advice. "Why you feel exhausted at day 3" outperforms "recovery tips." Specificity signals expertise and signals that the creator knows the audience's exact experience.

**Niche-fit:**
Content that looks like it belongs in this niche (uses the right tone, vocabulary, visual style) gets shared within the niche. Content that looks imported from outside gets ignored.

---

## Virality Score (simple decision gate)

Before creating any post, score the planned content against these 5 questions. Each yes = 1 point.

1. **Hook tension:** Does the first line create tension, surprise, or ask a question the viewer is already wondering?
2. **Specificity:** Is the topic specific enough that someone in this niche would think "this is exactly about me"?
3. **Emotional resonance:** Does the content make someone feel understood, validated, or motivated — not just informed?
4. **Shareable premise:** Would someone send this to a friend or save it to come back to later?
5. **Niche-native:** Does the format, tone, and visual style match what's already resonating in this niche right now?

**Score threshold:**
- 4–5: Green — proceed with this content
- 3: Yellow — revise before proceeding (usually fix the hook or specificity)
- 0–2: Red — discard — this is not worth posting. Research a better angle.

---

## Performance Baseline (agent-computed, not hardcoded)

The thresholds below are **bootstrap priors only** — used for the first 5 posts when no account data exists. After batch 1, the agent replaces them with its own computed baseline derived from `results.jsonl`. Internal data always wins over these priors.

### Bootstrap priors (cycles 1–5 only)

| Signal          | Bootstrap threshold | What it means            |
| --------------- | ------------------- | ------------------------ |
| Views           | > 300               | Algorithm pushed it out  |
| Save rate       | > 3% of views       | Strong utility signal    |
| Profile visits  | > 1.5% of views     | Curiosity / intent       |
| Watch-through   | > 50% (reels only)  | Hook + content both held |

### After batch 1: agent computes and writes its own baseline here

After scoring the first 5 posts, the agent computes:
- `avg_views` — mean views across all scored entries in results.jsonl
- `avg_save_rate` — mean (saves / views) across scored entries
- `avg_profile_visit_rate` — mean (profile_visits / views)
- `top_format` — format with highest avg save rate so far

These replace the bootstrap thresholds. The agent rewrites the table below after every batch score:

| Signal         | Current baseline | Source (batch #) | Last updated |
| -------------- | ---------------- | ---------------- | ------------ |
| avg_views      | —                | bootstrap        | —            |
| avg_save_rate  | —                | bootstrap        | —            |
| avg_visit_rate | —                | bootstrap        | —            |
| top_format     | —                | bootstrap        | —            |

**How to use this baseline:** when writing `reasoning.vs_baseline` in results.jsonl, compare the actual cycle outcome to the current baseline values here. A post is "above baseline" if views AND save rate both exceed current averages. A post is "below baseline" if both are under. Mixed results = flag for closer review.

**Threshold drift rule:** if the baseline shifts >50% in either direction across two consecutive batches, note the cause. Likely signals: account growing (good), content category shift, or algorithm change.

---

## How the Agent Updates This Model

**After every batch score (every 5 posts):**
- Look at the 2 highest-scoring posts in the batch. What did they have in common? Add finding to "Evidence" section below.
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

_Agent appends findings here after each batch score. Newest entries at the top._

| Date | Batch | Finding                                        | Model change |
| ---- | ----- | ---------------------------------------------- | ------------ |
| —    | —     | No data yet — populate after first batch score | —            |

---

## Research Sources

When updating this model, the agent may consult:
- Instagram niche hashtags (see `references/browsing-guide.md`)
- Web search: "what makes content go viral on Instagram [year]", "Instagram algorithm [niche] reach", "highest save rate Instagram content types"
- `references/results.jsonl` — internal experiment data (primary source after 10+ posts)
- `references/competitor-research.json` — niche patterns observed via browsing

Internal data (results.jsonl) always overrides external research when they conflict.
