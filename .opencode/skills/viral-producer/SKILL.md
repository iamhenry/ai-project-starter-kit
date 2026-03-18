---
name: viral-producer
description: >
  Faceless Instagram Reel production from research brief to rendered video. Use this skill
  whenever the user wants to create, generate, produce, or render a faceless Instagram Reel
  or short-form video. Trigger when the user mentions creating Reels, making content, producing
  videos, rendering animations, building carousel slides, or adapting a research brief into
  actual content. Also trigger when the user references Remotion, fal.ai, video rendering,
  motion graphics, or wants to turn content ideas into publishable Reels. This skill consumes
  a research brief (from the viral-research skill) and produces rendered video files ready
  for posting. It handles format selection, asset generation, Remotion rendering, caption
  writing, and output packaging. It does not research content or browse Instagram — that's
  the viral-research skill's job.
version: "1.0"
---

# Viral Producer — Faceless Reel Production Pipeline

## Purpose

Take a research brief (produced by the viral-research skill) and turn its recommended content
angles into rendered, ready-to-post Instagram Reels. This skill owns the entire production
pipeline from concept to final .mp4.

The input is intelligence. The output is content.

## Scope

- **Platform:** Instagram Reels (9:16 vertical, 720x1280, h264+aac, .mp4)
- **Content type:** Faceless only — no face-on-camera content
- **Format tiers:** T1-T4 (niche formats) and P1-P3 (premium formats)
- **Rendering engine:** Remotion (programmatic React-based video)
- **Asset generation:** fal.ai (AI imagery), stock footage, Figma/SVG design assets
- **Output:** Rendered .mp4 files + caption drafts, ready for posting via Postiz or manually

## Prerequisites

- **Remotion** — installed and configured. See `references/remotion-guide.md` for setup.
- **fal.ai API key** — required for AI image/video generation. Set in `references/production-config.json`
- **ffmpeg** — required for video verification and post-processing
- **Node.js** — required by Remotion
- **Research brief** — a completed brief from the viral-research skill, or at minimum a content
  angle with a specified format tier

Read `references/production-config.json` before every production session. It defines the
niche, brand voice, visual system, and tool configuration.

Read `../ig-marketer/references/soul.md` before writing any text content (hooks, captions, CTAs). All copy
must align with the brand voice defined there.

## Production Workflow

### Phase 1: Brief Intake

**Goal:** Read the research brief and select what to produce this session.

**Process:**

1. Read the research brief (provided by user or located at a known path)
2. Review the "Recommended Content Angles" section
3. Check the account's current phase in `references/production-config.json` → `account.currentPhase`
4. Filter content angles to format tiers appropriate for the current phase:
   - Phase 1 (0-1K followers): T1, T2, and optionally P3
   - Phase 2 (1K-10K): T3, T4, P3
   - Phase 3 (10K+): P1, P2, P3, plus any lower tier
5. Select 1-3 content angles to produce this session
6. For each selected angle, confirm with the human:
   - Topic
   - Format tier
   - Hook approach
   - Target emotion

**Output:** A production queue of 1-3 content pieces with format, topic, and hook defined.

### Phase 2: Asset Preparation

**Goal:** Generate or source all visual and text assets needed for the Reel.

Read `references/format-templates.md` for the exact asset requirements per format tier.

**For T1 (Meme Reel):**

- Source stock footage that visually contradicts the text message
- Write 1-2 text overlays (setup text + optional label)
- No custom assets needed

**For T2 (Quote Card):**

- Generate background image via fal.ai or source stock photo
- Write the quote text (read `../ig-marketer/references/soul.md` for voice)
- Style: bold, stacked, center-aligned

**For T3 (Text Card):**

- Source subtle background footage (timelapse, nature, gradient animation)
- Write both text sections (myth list + reality list, or equivalent comparison)
- Design text hierarchy (bold headers, lighter body)

**For T4 (Truth Bomb):**

- Source contemplative footage (real timelapse preferred over AI)
- Write the 3-part argument (fact → irony → conclusion)
- Choose clean serif typography

**For P1 (Functional Loop):**

- Design the interactive element (breathing circle, day counter, progress ring)
- Choose monochromatic brand palette from `references/production-config.json`
- Plan the loop point (last frame must match first frame)
- Text: 1-2 words maximum

**For P2 (Data Viz Humor):**

- Design the data element (gauge, counter, EKG, progress bar)
- Plan the visual metaphor or gamification hook
- Dark UI aesthetic (black + single accent color)
- Plan the destruction/escalation/resolution arc

**For P3 (Cultural Edutainment):**

- Source premium footage (drone aerial, cinematic nature — real, not AI)
- Design the frosted glass dictionary card
- Write: term, pronunciation, part of speech, definition, "see also" (humorous)
- Choose monochromatic palette aligned to footage

**Asset generation via fal.ai:**

```bash
# Example: generate a background image
curl -X POST "https://fal.run/fal-ai/flux/dev" \
  -H "Authorization: Key $FAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "aerial drone shot of ocean waves at sunset, cinematic, 9:16 vertical",
    "image_size": {"width": 720, "height": 1280}
  }'
```

Respect the budget ceiling in `references/production-config.json` → `fal.budgetCeilingUSD`.
Fall back to stock footage or solid/gradient backgrounds if the budget is hit.

**Output:** All assets saved to `output/assets/<slug>/` — images, footage clips, SVGs, text files.

### Phase 3: Remotion Rendering

**Goal:** Render the final .mp4 using Remotion.

Read `references/remotion-guide.md` for detailed rendering instructions per format tier.

**General process:**

1. Prepare the Remotion input props (JSON file with all content and asset paths):

```json
{
  "format": "T2",
  "topic": "sobriety regret quote",
  "hook": "I would've been 1 year sober today...",
  "backgroundImage": "output/assets/slug/background.png",
  "textOverlays": [
    { "text": "I would've been", "style": "bold", "position": "center" },
    { "text": "1 year sober today.", "style": "bold", "position": "center" },
    { "text": "If I quit drinking", "style": "bold", "position": "center" },
    { "text": "1 year ago.", "style": "bold", "position": "center" }
  ],
  "duration": 6,
  "fps": 30
}
```

2. Invoke the Remotion render:

```bash
npx remotion render <composition-id> \
  --props=<props-file> \
  --output=output/reels/<slug>.mp4 \
  --codec=h264
```

3. Verify the output:

```bash
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration \
  -show_entries format=duration \
  output/reels/<slug>.mp4
```

Expected: 720x1280, h264 video + aac audio, duration matches target ±0.5s.

**If Remotion is not set up**, the skill can still produce content by outputting:

- A complete asset package (background + text content + layout specs)
- A rendering instruction file that any video tool (CapCut, Canva, After Effects) can follow
- This is the graceful degradation path — the content strategy is still valuable even without
  automated rendering

**Output:** Rendered .mp4 in `output/reels/<slug>.mp4`

### Phase 4: Caption & CTA

**Goal:** Write the Instagram caption, hashtags, and call-to-action.

Read `references/caption-guide.md` for the full caption framework.
Read `../ig-marketer/references/soul.md` for brand voice constraints.

**Caption structure:**

1. **Hook line** — first line visible before "...more." Must compel the tap.
   Keep under 125 characters (Instagram truncates at this point in feed).
2. **Body** — expand on the content's message. 2-4 sentences.
   Match the emotional register of the Reel (don't be playful if the Reel is serious).
3. **CTA** — drive a specific action:
   - Comment-based: "Comment [KEYWORD] for [value]" (builds engagement + lead list)
   - Save-based: "Save this for day [X]" (drives saves, algorithm signal)
   - Share-based: "Send this to someone who needs it" (drives DM shares, top algorithm signal)
   - Link-based: "Link in bio" (drives app downloads — use sparingly)
4. **Hashtags** — max 5, from discovered clusters in the research brief or niche config.
   Place after the CTA, not inline with the body.

**Output:** Caption text saved to `output/reels/<slug>-caption.txt`

### Phase 5: Output Package

**Goal:** Deliver a complete, ready-to-post package.

For each produced Reel, the final output includes:

```
output/reels/<slug>/
├── <slug>.mp4          — rendered Reel (720x1280, h264+aac)
├── caption.txt         — full caption with CTA and hashtags
├── metadata.json       — production metadata (format tier, topic, hook type,
│                         virality score, assets used, render settings)
└── thumbnail.png       — first frame extracted for preview
```

Extract the thumbnail:

```bash
ffmpeg -i output/reels/<slug>.mp4 -vf "select=eq(n\,0)" -vsync 0 \
  output/reels/<slug>/thumbnail.png -y
```

Write `metadata.json`:

```json
{
  "slug": "<slug>",
  "format": "T2",
  "topic": "sobriety regret quote",
  "hookType": "urgency",
  "emotionalTrigger": "regret",
  "viralityScore": 4,
  "duration": 6.0,
  "resolution": "720x1280",
  "productionDate": "YYYY-MM-DD",
  "assetsUsed": {
    "background": "fal.ai generated / stock / custom",
    "typography": "font name, weight, color",
    "audio": "none / track name"
  },
  "caption": "first line of caption...",
  "hashtags": ["#tag1", "#tag2"],
  "status": "ready-to-post"
}
```

Present the package to the human for review before posting. The human makes the final
publish decision — this skill never posts directly.

## Operating Principles

- **Research first, produce second.** Never produce content without a research brief or at
  minimum a validated content angle. Uninformed content is wasted effort.
- **One variable per experiment.** When producing multiple Reels, vary only one element at a
  time (hook style OR topic OR format OR CTA). You can't attribute results if multiple
  variables change simultaneously.
- **Virality gate is upstream.** The orchestrator (ig-marketer) runs the virality gate before
  delegating to this skill. Viral-producer produces what it's told — it does not re-score.
- **Faceless only.** All content must be producible without a human appearing on camera.
  If a content angle requires face-on-camera, adapt the narrative structure to a faceless
  format (text overlay, animation, stock footage) or discard it.
- **Under 10 seconds by default.** The research data consistently shows sub-10-second Reels
  get higher completion rates and more algorithmic distribution. Only exceed 10 seconds for
  P2 (Data Viz) formats where the escalation arc requires it.
- **Soul before content.** Always read `references/soul.md` before writing any text. The brand
  voice is a constraint, not a suggestion. Content that doesn't sound like the brand is worse
  than no content.
- **Graceful degradation.** If Remotion isn't available, output the asset package + rendering
  instructions. If fal.ai budget is hit, fall back to stock or gradient backgrounds. The
  production pipeline should never hard-stop — there's always a lower-cost path to content.
- **Loop everything possible.** Seamless loops (last frame = first frame) maximize watch time,
  which is the algorithm's #1 ranking signal. For static formats (T1, T2), the loop is inherent.
  For animated formats (P1, P2), engineer the loop point intentionally.

## Memory

All paths relative to this skill's directory:

- **Production config:** `references/production-config.json`
- **Brand voice:** `../ig-marketer/references/soul.md` (single source of truth — no local copy)
- **Format templates:** `references/format-templates.md`
- **Remotion guide:** `references/remotion-guide.md`
- **Caption guide:** `references/caption-guide.md`
- **Output directory:** `output/` (created on first run if missing)
- **Asset directory:** `output/assets/` (generated assets per production run)
- **Reel directory:** `output/reels/` (final rendered Reels)
