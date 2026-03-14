# Niche Research — Browsing Guide

Self-contained instructions for researching the niche on Instagram.
Uses agent-browser (CLI tool). No external skills required. No permission needed — run autonomously.

**Auth failures:** If Instagram redirects to a login wall or throws a captcha, do not retry. Flag to human with the URL and error, then fall back to web search (see Fallback section).

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

Run every session. Run a deeper competitor dive any time score drops 2 consecutive posts.

### 1. Browse niche hashtags

Discover relevant hashtags for the niche. Start from the niche description in `references/config.json` → `app.niche` and the Instagram handle in `app.instagramHandle`. Browse the account's existing posts, the explore page, and web search to identify 3–5 active hashtags. If `references/playbook.json` already has discovered `hashtag_clusters` from previous cycles, use those. For each hashtag:

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

### 2. Competitor account deep-dive

Identify 3–5 active accounts in the niche from the hashtag feed above. Prioritise accounts that appear repeatedly across multiple hashtags or have high visible engagement. For each account:

```bash
npx agent-browser open https://www.instagram.com/<handle>/
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
npx agent-browser close
```

Extract per account:
- **Format mix** — ratio of carousels, reels, single images in the last 12 posts
- **Posting frequency** — estimated cadence from visible timestamps
- **Hook patterns** — first line of their top 3 most-engaged posts
- **CTA style** — what action they drive (download, comment, save, visit link)
- **Best vs. average engagement** — if visible, note the gap between top post and typical post (signals what's exceptional vs. baseline)
- **Trending audio** — any recurring audio/sound used across recent reels

Do not record usernames or follower counts in competitor-research.json. Record patterns and signals only.

### 3. Browse adjacent niches (inspiration only)

Identify 2–3 adjacent communities your audience likely overlaps with. Browse their top hashtags the same way. Look for content angles that are performing there but haven't crossed into the primary niche yet.

**Constraint:** Use findings as inspiration for hooks and angles only. All content must target `config.json → app.niche`. Never create content for an adjacent niche directly.

### 4. App Store competitor research

Browse competitor apps in the same category. Use `references/config.json` → `app.appStoreUrl` as anchor — find 3–5 competing apps from the "You might also like" section or category rankings.

For each competitor app:

```bash
npx agent-browser open <APP_STORE_URL>
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
npx agent-browser close
```

Extract:
- **Lead benefit** — what outcome they open with in the description
- **Screenshot story** — what moments/features they highlight (reveals what converts)
- **Rating + review count** — rough market validation signal
- **Review language** — if visible, exact words users use to describe the problem the app solves (these are content angles)

Cross-reference with hook patterns from steps 1–2. If competitor App Store copy uses a frame that's also getting high engagement on Instagram, that's a validated angle worth testing in the virality gate.

### 5. Find remix candidates (secondary format — gated)

**Gate:** Only applicable after 10+ scored carousel entries exist in results.jsonl AND the diagnostic matrix suggests a format change. If these conditions are not met, skip this section entirely.

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
  "nicheInsights": {
    "topHookPatterns": [],
    "contentGaps": [],
    "formatMix": {},
    "emotionalAngles": [],
    "adjacentNiches": [],
    "trendingAudio": []
  },
  "competitorAccounts": [
    {
      "formatMix": "e.g. 70% reels, 30% carousels",
      "postingFrequency": "e.g. ~5x/week",
      "topHooks": [],
      "ctaStyle": "",
      "engagementRange": "e.g. top post ~3x avg engagement",
      "notes": ""
    }
  ],
  "appStoreInsights": [
    {
      "leadBenefit": "",
      "screenshotAngles": [],
      "reviewLanguage": [],
      "notes": ""
    }
  ]
}
```

Record patterns and signals only. No usernames, handles, app names, follower counts, or PII.
