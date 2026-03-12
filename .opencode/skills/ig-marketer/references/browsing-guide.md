# Niche Research — Browsing Guide

Self-contained instructions for researching a niche on Instagram and TikTok without logging in.
Uses agent-browser (CLI tool). No external skills required.

---

## Install agent-browser (once per environment)

```bash
npx agent-browser:install
```

Verify:
```bash
npx agent-browser:version
```

---

## Usage Pattern

```bash
# Open a URL and wait for it to load
npx agent-browser open <URL>
npx agent-browser wait --load networkidle

# Take an accessibility snapshot (structured page content — no screenshot)
npx agent-browser snapshot -i

# Close when done
npx agent-browser close
```

The snapshot returns a structured accessibility tree. Extract:
- Visible hook text from posts (first 1–2 lines of captions)
- Post format signals (carousel indicator, video duration)
- Engagement signals if visible (like/comment counts)
- Trending hashtags or audio references

---

## Research Workflow

Run at the start of each week, and any time score drops 2 consecutive posts.

### 1. Browse niche hashtags

Load the hashtags seeded in `references/config.json` → `app.hashtagSeeds`. For each:

```bash
npx agent-browser open https://www.instagram.com/explore/tags/<HASHTAG>/
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
npx agent-browser close
```

Extract from snapshot:
- Hook patterns (what's being said in the first line of top posts)
- Format mix (carousel vs reel)
- Emotional angle (fear, pride, curiosity, humor, identity)
- Content gaps (topics present in comments but not posts)

### 2. Browse adjacent niches

Identify 2–3 adjacent communities your audience likely overlaps with. Browse their top hashtags the same way. Look for content angles that are performing there but haven't crossed into the primary niche yet.

### 3. Find remix candidates

When looking for a reel to remix:

```bash
npx agent-browser open https://www.instagram.com/explore/tags/<HASHTAG>/
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
```

Look for:
- Short video posts with high visible engagement
- A clear structural premise (before/after, reaction, contrast, list)
- A topic angle that maps naturally to the app's niche
- Public account (not private/login-required)

Extract the post URL from the snapshot. Pass it to `references/reel-workflow.md` for download + remix.

---

## Fallback: Web Search

If agent-browser cannot access Instagram (rate limit, captcha, geo-block):

Use web search instead:
- `site:instagram.com <niche keyword> most saved`
- `"<niche keyword>" instagram carousel 2025`
- Look for embed previews, blog roundups, or social listening tools

Update `references/competitor-research.json` with findings regardless of source.

---

## Output

After each research session, update `references/competitor-research.json`:

```json
{
  "lastResearchDate": "YYYY-MM-DD",
  "accounts": [],
  "nicheInsights": {
    "topHookPatterns": [],
    "contentGaps": [],
    "formatMix": {},
    "emotionalAngles": [],
    "adjacentNiches": []
  }
}
```

Record patterns, not individual post data. No usernames, no follower counts, no PII.
