# Experiment Framework

How we test, learn, and iterate. Read this before every cycle.

## Locked Format: 6-Slide Reel

Every post uses this structure. This is NOT a variable — it's the container.

| Slide | Purpose                      | What changes between experiments    |
| ----- | ---------------------------- | ----------------------------------- |
| 1     | **Hook** — stop the scroll   | Hook text (the experiment variable) |
| 2-5   | **Content** — deliver value  | Imagery style + text overlays       |
| 6     | **CTA** — drive the download | CTA copy                            |

The format stays constant. We experiment with what goes INSIDE it.

## The Three Variables

We only test these three things. One at a time.

### 1. Hook (test first — determines if anyone sees the rest)
The first slide's text. What stops the scroll?
- Shock stat: "Your liver regenerates in 30 days. Here's what happens."
- Question: "Why do you feel worse before you feel better when you quit drinking?"
- Curiosity gap: "POV: Day 47 without alcohol and you check your phone"
- Contrarian: "Moderation doesn't work. Here's the data."
- Personal story: "I quit drinking 90 days ago. Nobody warned me about this."

### 2. Imagery (test second — determines engagement + watch time)
The visual style across slides 1-5.
- AI-generated scenes (fal.ai)
- Text-on-gradient (no images, just styled text cards)
- App screenshots / screen recordings
- Stock photography (Pexels)
- Mixed (e.g., hook on gradient, content slides as AI scenes)

### 3. CTA (test third — determines conversion)
Slide 6 text + caption CTA.
- "Track your streak → link in bio"
- "Download free — link in bio"
- "Start your streak today"
- "Comment SOBER and I'll send you the app"
- Specific benefit: "See how much money you've saved → link in bio"

## How Each Cycle Works

### Generate 3-5 variations → score → post the winner

Every cycle, the agent:

1. **Pick the current test variable** from the queue below
2. **Generate 3-5 variations** of that variable (e.g., 5 different hooks)
3. **Hold everything else constant** — same imagery style, same CTA, same audio, same posting time
4. **Score each variation** against the virality model's 5-question gate:
   - Hook tension (does it create an open loop?)
   - Specificity (does the target audience think "this is about me"?)
   - Emotional resonance (feel understood, not just informed?)
   - Sendable (would someone DM this to a friend?)
   - Watchable (will they finish it?)
5. **Pick the highest-scoring variation** — break ties with gut feel toward what's most unexpected
6. **Render only the winner** via Remotion
7. **Send to Henry** via Telegram for posting
8. **Log all 5 variations** in results.jsonl (the 4 runners-up go in `reasoning.discarded_variations` — they're data for future cycles)

### Why this matters
One post per day. Five ideas generated, one posted. The "losing" variations still teach the model — the agent learns which hooks it scored higher and why, building pattern recognition without burning posting slots.

## Experiment Queue

### Current batch: Hook testing

Test variable: **hook type**
Control: imagery = text-on-gradient, CTA = "Track your streak → link in bio", audio = calm-reflective, posting time = 16:30 PST

Each experiment = one cycle. Generate 3-5 hook variations of the specified type, score, post the winner.

```json
[
  {
    "id": "exp-001",
    "variable": "hook",
    "type": "shock_stat",
    "hypothesis": "A surprising statistic creates a knowledge gap that compels watching",
    "status": "posted",
    "cycle": "cycle-004",
    "winning_variation": "Alcohol causes 100,000 cancers a year in the US. Most people have no idea.",
    "posted_date": "2026-03-18"
  },
  {
    "id": "exp-002",
    "variable": "hook",
    "type": "question",
    "hypothesis": "Questions create an open loop — the viewer watches to find the answer",
    "status": "queued"
  },
  {
    "id": "exp-003",
    "variable": "hook",
    "type": "curiosity_gap",
    "hypothesis": "POV / 'what happens when...' hooks create anticipation that drives watch-through",
    "status": "queued"
  },
  {
    "id": "exp-004",
    "variable": "hook",
    "type": "contrarian",
    "hypothesis": "Challenging conventional wisdom triggers emotional response → comments + shares",
    "status": "queued"
  },
  {
    "id": "exp-005",
    "variable": "hook",
    "type": "personal_story",
    "hypothesis": "First-person POV feels authentic in the sobriety niche — high relatability",
    "status": "queued"
  }
]
```

### After hook batch completes:
1. Rank all 5 by views → pick the winning hook type
2. Lock it as control
3. Move to **imagery testing** (exp-006 to exp-010) — same winning hook, different visual styles
4. After imagery batch → lock winning style → move to **CTA testing** (exp-011 to exp-015)

## Scoring

After analytics come in (next cycle's Step 1), update the experiment:

```json
{
  "status": "scored",
  "result": {
    "views": 0,
    "saves": 0,
    "shares": 0,
    "profile_visits": 0,
    "new_subs": 0,
    "watch_through_rate": null,
    "winning_variation": "the hook text that was selected from the batch",
    "discarded_count": 4,
    "notes": "what this tells us"
  }
}
```

## Batch Analysis

After all 5 experiments in a batch are scored:

```
## Batch: [Variable] Testing (exp-NNN to exp-NNN)
Date range: YYYY-MM-DD to YYYY-MM-DD

### Results (ranked by views)
1. [type] — X views, Y saves, Z shares — "[the winning hook text]"
2. ...

### Winner: [type]
Why: [specific evidence from metrics]

### Control locked for next batch
[variable] = [winner]

### Next batch: [next variable] testing
```

## Current State

- **Locked format:** 6-slide reel (hook + 4 content + CTA)
- **Current batch:** Hook type testing (5 experiments)
- **Controls:** text-on-gradient imagery, "Track your streak → link in bio" CTA, calm-reflective audio, 16:30 PST
- **Next up:** exp-001 (shock stat hooks)
