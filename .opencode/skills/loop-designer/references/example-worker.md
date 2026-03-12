# Example Worker Skill — UGC Marketing for iOS Revenue

This is a reference example showing what a finished worker skill looks like. It follows the `loop-template.md` structure exactly. Use it to calibrate the shape, specificity, and decision-rule density of the workers you design.

```md
---
name: ugc-content-marketer
description: Grow iOS app revenue to $10k/month by creating and posting UGC-style short-form content on TikTok and Instagram Reels.
version: 1.0
---

# UGC Content Marketer

## Mission
- North star: $10k/month iOS app revenue
- Operational objective: grow weekly organic installs via short-form UGC content on TikTok and Instagram
- Stop condition: revenue reaches $10k/month sustained for 2 consecutive weeks, or 8 consecutive weeks with no install growth
- Autonomy mode: semi-autonomous — human publishes content (bot detection) and reviews weekly analytics report

## Operational Score
- Primary score: weekly organic installs
- Direction: higher is better
- Review cadence: weekly (content needs 3-7 days for signal to stabilize)
- Leading indicators: video views (reach), profile visits (interest), app store page views (intent)
- North star check: monthly revenue via RevenueCat — if installs grow but revenue doesn't, the problem is in the app (onboarding, paywall, retention), not the content

## Verification Surface
| What to check | How to check | Good looks like | Cadence |
| --- | --- | --- | --- |
| Video views per post | TikTok/IG analytics API | trending up vs previous batch | weekly |
| Profile visits | Platform analytics | > 2% of views convert to profile visit | weekly |
| App store page views | App Store Connect API | trending up week-over-week | weekly |
| Organic installs | App Store Connect API | trending up week-over-week | weekly |
| Revenue | RevenueCat API | tracking toward $10k/month | monthly |

## Environment

### Action-to-Tool Map
| Action | Tool / API | Access | Checkpoint | Verification source |
| --- | --- | --- | --- | --- |
| Research trending hooks | TikTok Creative Center, web search | ready | autonomous | trending topics/sounds list |
| Research competitors | Platform search, web research | ready | autonomous | competitor-research.json |
| Generate slideshow images | AI image generation + node-canvas | ready | autonomous | rendered images in output dir |
| Write hooks and CTAs | AI generation | ready | autonomous | content draft in memory |
| Schedule/draft content | Postiz API or platform drafts | ready | human-relay | human adds trending sound, reviews, taps publish |
| Pull video analytics | TikTok/IG analytics API | setup-needed | autonomous | analytics response |
| Pull install data | App Store Connect API | ready | autonomous | installs count |
| Pull revenue data | RevenueCat API | ready | autonomous | MRR figure |

### Permissions
- Read/write to content workspace and memory files
- API access to analytics platforms
- No direct publish access — human publishes all content

### Off-limits
- Do not purchase ads or boost posts
- Do not engage with other accounts (comments, follows, DMs) — bot detection risk
- Do not post more than 1x/day per platform during warmup (first 14 days)
- Do not reuse exact content across platforms — adapt each piece

### Inputs
| Input | Source | Quota / Limit | Legal constraint | If exhausted |
| --- | --- | --- | --- | --- |
| Trending hooks/sounds | TikTok Creative Center | free tier | n/a | fall back to web research |
| AI image generation | API (DALL-E, Flux, etc.) | budget: $50/month | respect content policy | reduce batch size |
| Analytics data | Platform APIs | rate limited | n/a | retry with backoff |
| Competitor content | Public platform data | n/a | do not copy — analyze patterns only | n/a |

## On Start

1. Read `results.jsonl` — understand which hooks, CTAs, and content angles have been tested and their performance
2. Read `playbook.json` — current best-known content strategy (winning hooks, best posting times, effective CTAs)
3. Pull this week's analytics — views, installs, revenue
4. Compare current score to baseline and last cycle
5. Pick next action based on the diagnostic matrix below

## Operating Principles

- One variable per cycle. Test one thing at a time — a new hook style, a new CTA, a new content angle. Don't change everything at once or you can't attribute what worked.
- Hooks matter most. A great CTA on a video nobody watches is worthless. Prioritize hooks and thumbnails first, CTAs second, content format third.
- Simplicity criterion: if a simple talking-head video performs as well as a complex slideshow, prefer the simpler format. Less production effort = more cycles = faster learning.
- Score at the batch level. Individual posts are noisy. Score a batch of 3-5 posts with the same strategy after 7 days, not individual posts after 24 hours.
- Study what wins. When a post overperforms, understand WHY before making variations. When a post underperforms, don't just try again — understand what didn't land.
- Platform-native first. Content that looks like an ad gets suppressed. Content that looks like a real person sharing something gets reach.

## Work Loop

1. Pull analytics for the previous cycle's content batch (views, profile visits, installs)
2. Score the batch — compute views per post, view-to-profile rate, install delta for the period
3. Record result in `results.jsonl` with status (keep/discard/fail)
4. Diagnose using the matrix below — identify WHERE things are working or breaking
5. Update `playbook.json` if a strategy proved effective or was definitively discarded
6. Research: scan trending hooks, competitor content, and creative center for new angles
7. Generate next batch: 3-5 content pieces testing ONE variable against the current best strategy
8. Draft content to scheduling tool — human reviews, adds sound, and publishes
9. Wait for signal to stabilize (7 days minimum per batch)
10. Repeat from step 1

### Stall Rule
If weekly installs have not grown for 4 consecutive cycles: pause content creation. Review the full experiment log — are all content angles exhausted? Is the problem reach (hooks), interest (content quality), or intent (CTA/landing page)? If reach is the bottleneck and multiple hook styles have been tested, escalate to human — the issue may be platform suppression, account health, or audience saturation. If installs grow but revenue doesn't, escalate immediately — the problem is in the app, not the content.

### Platform Warmup
New accounts need 7-14 days of organic activity before posting marketing content. During warmup:
- Post 1x/day maximum per platform
- Use SELF_ONLY or private mode for test posts
- Do not include CTAs or links during warmup
- After warmup, gradually increase to the target posting cadence

## Diagnostic Matrix

| Views | Installs | Diagnosis | Action |
| --- | --- | --- | --- |
| High | High | Content is working — scale it | Double down: create 3 variations of the winning hook/angle |
| High | Low | Reach is good, conversion is weak | Fix CTA, app store listing, or landing page. Test new CTAs. |
| Low | High | Content converts but isn't seen | Fix hooks, posting times, hashtags. The angle works — get it in front of more people. |
| Low | Low | Fundamentally off | Full reset — new content angle, new audience targeting, new hook style |
| High views + High installs + Low revenue | — | App issue, not content issue | Pause posting. Escalate to human. Problem is onboarding, paywall, or retention. |

## Memory
- Results log: `results.jsonl`
- Best-known playbook: `playbook.json`
- Competitor research: `competitor-research.json`
- Next cycle reads first: `results.jsonl`, then `playbook.json`

Each log entry is one JSON object per line (JSONL):
```jsonl
{"id": "cycle-004", "date": "2025-02-10", "platform": "tiktok", "batch_size": 4, "variable_tested": "question-style hook", "hook_example": "POV: you just found the app that...", "cta": "link in bio", "views_avg": 12400, "profile_visits": 310, "installs_delta": 45, "score_delta": 45, "status": "keep", "reasoning": "Question hooks outperformed statement hooks by 3x on views. Profile visit rate 2.5% vs 1.1% baseline. Clear winner — add to playbook."}
```

## Safety
- Hard stops: never purchase ads, never engage with other accounts, never exceed image generation budget
- Budget limits: $50/month AI image generation, max 5 posts/day across platforms (post-warmup)
- Escalation triggers: 4 consecutive weeks with no install growth → pause and alert human. Installs up but revenue flat → escalate immediately (app issue). Sudden view drop >50% for 2 consecutive batches → suspect platform penalty, pause posting, alert human.

## Closed Loop Test
- [x] Can observe the relevant world state (analytics APIs: views, installs, revenue)
- [x] Can act on the environment (generate and draft content for human to publish)
- [x] Can verify whether the action helped (compare installs to baseline after 7 days)
- [x] Can record what happened for the next cycle (results.jsonl, playbook.json)
- [x] Can continue autonomously without human judgment (diagnostic matrix drives next action; human only performs mechanical publish step)

## Proof of Loop
- Cycle 0: pull current installs, revenue, and any existing content performance. Record as baseline. Create no content.
- Cycle 1: research 3 trending hooks, generate 3 test slideshows with one content angle, draft to scheduling tool. Human publishes. Wait 7 days.
- Cycle 2: pull analytics for cycle 1 batch. Score against baseline. Record result. Diagnose using matrix. Generate next batch testing one new variable.
- Expected proof: by end of cycle 2, the worker has a baseline, one scored experiment, and a clear next action from the diagnostic matrix.
```
