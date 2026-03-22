---
name: viral-producer
description: >
  Spec-in, content-out Reel renderer. Receives a complete production spec (format tier,
  topic, hook, CTA, caption, imagery direction) from the viral-ig-marketer orchestrator and
  produces a rendered .mp4 + caption file + metadata. Use this skill whenever you need
  to render a faceless Instagram Reel from a fully-defined spec. Trigger when creating
  Reels, rendering animations, or producing video from a production spec. Also trigger
  when referencing Remotion, fal.ai, video rendering, or motion graphics. This skill
  does NOT make creative decisions — format selection, virality scoring, caption writing,
  and content strategy are handled upstream by viral-ig-marketer. It validates the incoming
  spec, generates assets, renders via Remotion, saves the caption, and packages output.
version: "1.0"
---

# Viral Producer — Faceless Reel Production Pipeline

## Purpose

Receive a complete production spec from the viral-ig-marketer orchestrator and render it into a
ready-to-post Instagram Reel. This skill owns the production pipeline from validated spec
to final .mp4. It does not select content angles, score virality, or write captions — those
decisions are made upstream.

The input is a spec. The output is content.

## Scope

- **Platform:** Instagram Reels (`9:16` vertical, `1080x1920`, h264+aac, `.mp4`)
- **Content type:** Faceless only — no face-on-camera content
- **Format tiers:** T1-T4 (niche formats) and P1-P3 (premium formats)
- **Rendering engine:** Remotion (programmatic React-based video)
- **Asset generation:** fal.ai (AI imagery), stock footage, Figma/SVG design assets
- **Output:** Rendered `.mp4` package at `output/reels/<slug>/`, ready for posting via Postiz or manually

## Prerequisites

- **Remotion** — installed and configured. See `references/remotion-guide.md` for setup.
- **fal.ai API key** — required for AI image/video generation. Set in `references/production-config.json`
- **ffmpeg** — required for video verification and post-processing
- **Node.js** — required by Remotion
- **Research brief** — a completed brief from the viral-research skill, or at minimum a content
  angle with a specified format tier

Read `references/production-config.json` before every production session. It defines the
niche, brand voice, visual system, and tool configuration.

Read `../viral-ig-marketer/references/soul.md` before writing any text content (hooks, captions, CTAs). All copy
must align with the brand voice defined there.

## Production Workflow

### Phase 1: Spec Validation

**Goal:** Validate the incoming production spec before starting work.

**Spec contract:** See `../viral-ig-marketer/references/production-spec.md` for the full contract (required fields, optional fields, example). This is the single source of truth for the spec interface.

**Process:**

1. Read the production spec (passed as input from viral-ig-marketer)
2. Validate all required fields are present and non-empty
3. Verify `format_tier` is a recognized tier from `references/format-templates.md`
4. Read `references/production-config.json` for brand colors, fal.ai settings, Remotion composition mapping
5. If any required field is missing → error immediately with a clear message listing missing fields. Do not proceed.

**Output:** Validated spec ready for asset preparation.

### Phase 2: Asset Preparation

**Goal:** Generate or source all visual and text assets needed for the Reel.

Read `references/format-templates.md` for the exact asset requirements per format tier.

Audio is sourced from `../viral-ig-marketer/audio/` using the production spec's `audio_track` field. Treat `audio_track` as the selected filename to resolve from that directory.

**For T1 (Meme Reel):**

- Source stock footage that visually contradicts the text message
- Write 1-2 text overlays (setup text + optional label)
- No custom assets needed

**For T2 (Quote Card):**

- Generate background image via fal.ai or source stock photo
- Write the quote text (read `../viral-ig-marketer/references/soul.md` for voice)
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

2. **Pre-render validation (T2 motion check):**

   Before invoking the render, verify the composition contains actual motion — not a single static frame:

   - If `format` is `T2`: inspect the Remotion input props and composition code. The composition **must** include at least one animation sequence:
     - **Text animation:** fade-in, typewriter, staggered reveal, or equivalent text motion
     - **Background motion:** Ken Burns zoom/pan, parallax shift, subtle particle effect, or slow camera drift
   - If both are missing (i.e., the composition would render a single static image for the entire duration), **fail the render** with error: `"T2 motion check failed: composition contains no animation sequences. T2 Quote Card requires text animation + background motion. Add at least one text reveal and one camera/background movement before rendering."`
   - For all other format tiers (T1/T3/T4/P1-P3): motion is inherent to their composition templates — no additional check needed.

3. Invoke the Remotion render:

```bash
npx remotion render <composition-id> \
  --props=<props-file> \
  --output=output/reels/<slug>.mp4 \
  --codec=h264
```

4. Verify the output:

```bash
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration \
  -show_entries format=duration \
  output/reels/<slug>.mp4
```

Expected: 1080x1920, h264 video + aac audio, duration matches target ±0.5s.

**If Remotion is not set up or render prerequisites are missing, fail the cycle loudly. Do not silently degrade to a static/manual package.**

Required behavior:

- Stop before claiming the reel is ready.
- Emit a clear error explaining why automated render could not run.
- Mark the cycle/output as `render_failed`, not `ready-for-review` and not `ready-for-manual-render`.
- If you generated useful inputs (backgrounds, props, caption drafts), keep them as debugging artifacts only — not as the primary deliverable.
- Never treat `render-instructions.md` as a successful reel output.

**Output:** Rendered `.mp4` in `output/reels/<slug>.mp4` or an explicit render failure.

### Phase 4: Caption Save

**Goal:** Save the caption provided in the production spec.

The caption is written upstream by viral-ig-marketer. This phase saves it to the output package.

1. Extract the `caption` field from the production spec
2. Save to `output/reels/<slug>/caption.txt`
3. Verify the caption is non-empty

**Output:** Caption text saved to `output/reels/<slug>/caption.txt`

### Phase 5: Output Package

**Goal:** Deliver a complete, ready-to-post package.

For each produced Reel, the final output includes:

```
output/reels/<slug>/
├── <slug>.mp4          — rendered Reel (1080x1920, h264+aac)
├── caption.txt         — full caption with CTA and hashtags
├── metadata.json       — production metadata (format tier, topic, hook type,
│                         virality score, assets used, render settings, audio)
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
  "resolution": "1080x1920",
  "productionDate": "YYYY-MM-DD",
  "assetsUsed": {
    "background": "fal.ai generated / stock / custom",
    "typography": "font name, weight, color",
    "audio": "track filename from production spec"
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
- **Spec is the contract.** The production spec from viral-ig-marketer defines what to produce.
  Do not second-guess creative decisions (topic, hook, CTA, caption) — produce exactly
  what the spec says. If the spec is incomplete, error with missing fields.
- **Virality gate is upstream.** The orchestrator (viral-ig-marketer) runs the virality gate before
  delegating to this skill. Viral-producer produces what it's told — it does not re-score.
- **Faceless only.** All content must be producible without a human appearing on camera.
  If a content angle requires face-on-camera, adapt the narrative structure to a faceless
  format (text overlay, animation, stock footage) or discard it.
- **Under 10 seconds by default.** The research data consistently shows sub-10-second Reels
  get higher completion rates and more algorithmic distribution. Only exceed 10 seconds for
  P2 (Data Viz) formats where the escalation arc requires it.
- **Soul for visual tone.** Read `../viral-ig-marketer/references/soul.md` for brand voice context.
  Use it to guide visual tone and typography choices — not to rewrite copy (that's upstream).
- **Fail loudly on Remotion unavailability.** If Remotion isn't available, record an explicit render failure instead of shipping an instructions-only package as the deliverable. If fal.ai budget is hit, fall back to stock or gradient backgrounds, but the pipeline must still produce a real `.mp4` to count as complete.
- **Loop everything possible.** Seamless loops (last frame = first frame) maximize watch time,
  which is the algorithm's #1 ranking signal. For static formats (T1, T2), the loop is inherent.
  For animated formats (P1, P2), engineer the loop point intentionally.
- **All Reels MUST contain motion — no static frames.** Every rendered Reel must include at least one animation sequence. For T2 Quote Card specifically: require text animation (fade-in, typewriter, or staggered reveal) + slow background motion (Ken Burns zoom/pan, parallax, or subtle particle effect). Duration 5-7s. T1/T3/T4/P1-P3 inherently contain motion. Never render a single static frame as a Reel — Instagram's algorithm deprioritizes static images published as Reels vs actual video content.

## Memory

All paths relative to this skill's directory:

- **Production config:** `references/production-config.json`
- **Brand voice:** `../viral-ig-marketer/references/soul.md` (single source of truth — no local copy)
- **Format templates:** `references/format-templates.md`
- **Remotion guide:** `references/remotion-guide.md`
- **Caption guide:** `../viral-ig-marketer/references/caption-guide.md` (owned by viral-ig-marketer — creative decisions live upstream)
- **Output directory:** `output/` (created on first run if missing)
- **Asset directory:** `output/assets/` (generated assets per production run)
- **Reel directory:** `output/reels/` (final rendered Reels)
