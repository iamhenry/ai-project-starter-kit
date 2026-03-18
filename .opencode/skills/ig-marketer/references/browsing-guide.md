# Niche Research — Browsing Guide

Self-contained instructions for researching the niche.

---

## ⛔ Instagram Browsing — BANNED

**Do NOT use agent-browser to visit instagram.com.** This includes:
- Browsing hashtag pages
- Viewing competitor profiles
- Viewing the explore page
- Any Instagram URL whatsoever

**Reason:** Instagram flags automated browser access and will restrict or permanently disable the account. This has already triggered a security warning. There is zero tolerance for this risk.

**Do NOT use stealth-browser-auth for Instagram.** That skill exists for other sites only.

**Do NOT inject Instagram cookies into agent-browser for any reason.**

---

## Allowed Research Methods

All niche research uses **web search and public web pages only**. No Instagram login, no Instagram browsing, no Instagram scraping.

### ⏰ 3-Month Recency Rule

**Only use research from the last 3 months.** Anything older is likely stale — trends, algorithm behavior, hook patterns, and hashtag strategies decay fast. Apply this to every search:
- Add date filters: `after:YYYY-MM-DD` or use `date_after` parameter
- Calculate the cutoff date as today minus 90 days
- If a source doesn't have a clear date, check for contextual clues (references to seasons, events, platform changes)
- Discard anything that references outdated algorithm behavior or pre-2026 Instagram features
- Exception: evergreen strategy frameworks (e.g., "what makes a hook work") are fine regardless of date, but verify they still apply

### 1. Web Search for Niche Trends

Use web search to understand what's working in the niche **right now** (last 3 months only — use `date_after` parameter):

```
"sober curious" instagram viral 2026
"alcohol free" content strategy 100k views
sobriety niche viral posts carousel
what content goes viral sober curious instagram 2026
instagram carousel viral strategy 2026
```

Also search for:
- UGC marketing blogs and newsletters (Later, Hootsuite, Buffer, Social Media Examiner, Sprout Social)
- Creator economy newsletters (The Leap, Passionfruit, Creator Science)
- Niche-specific blogs and communities (sober curious subreddits, alcohol-free lifestyle blogs)
- Content strategy teardowns and case studies
- Platform algorithm updates (Instagram algorithm changes 2026)

### 2. Web Search for Content Angles

Search for the questions real people are asking:

```
"what happens when you stop drinking" site:reddit.com
"sober curious" questions people ask
"first week sober" what to expect
alcohol free benefits timeline
```

Extract:
- Exact language people use to describe their experience
- Most common questions and concerns
- Emotional framing (fear, curiosity, pride, relief)
- Gaps between what people ask and what existing content covers

### 3. Blog and Newsletter Research

Fetch and read marketing strategy content:

```bash
web_search "instagram carousel strategy 2026" --date_after <90_days_ago>
web_search "ugc marketing sobriety wellness niche" --date_after <90_days_ago>
web_search "instagram algorithm viral reach 2026" --date_after <90_days_ago>
web_search "how to get 100k views instagram carousel" --date_after <90_days_ago>
web_fetch <URL>  # read the actual articles — verify publication date
```

Extract:
- Current best practices for carousel format
- Hook patterns that are working across niches
- Algorithm changes that affect reach
- Hashtag strategy updates
- Posting time research

### 4. App Store Competitor Research

Browse competitor apps in the same category using agent-browser (App Store is safe — no automation detection):

```bash
agent-browser open <APP_STORE_URL>
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser close
```

Extract:
- **Lead benefit** — what outcome they open with
- **Screenshot story** — what features they highlight (reveals what converts)
- **Rating + review count** — market validation signal
- **Review language** — exact words users use (these are content angles)

### 5. Public Embed and oEmbed Data

Twitter/X posts can be read without auth:
```bash
curl -s "https://publish.twitter.com/oembed?url=https://twitter.com/<user>/status/<id>" | jq .html
```

Use this for cross-platform trend research when relevant.

### 6. Reel Research — Format, Visual Style, and Remix Candidates

Search for what reel formats and visual styles are performing in the niche right now:
```
"sober curious" viral reel 2026
"alcohol free" trending instagram reel
sobriety niche instagram reel format what works 2026
wellness app reel visual style high engagement
```

Look for:
- What visual styles are getting traction (still images with animation? talking head? text-only? lifestyle footage?)
- What pacing and transitions are common in high-performing reels
- Trending audio patterns in the wellness/sobriety space
- Remix candidates — high-performing reels worth adapting with a new hook/CTA

Find post URLs from blog roundups or embed previews. For remixes, pass to `references/reel-workflow.md`.

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
