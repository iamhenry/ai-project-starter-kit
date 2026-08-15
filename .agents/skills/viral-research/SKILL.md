---
name: viral-research
description: >
  Viral content research and DNA extraction for Instagram Reels. Use this skill whenever
  you need to research what's performing in a niche on Instagram, find viral faceless Reels,
  download and analyze them frame-by-frame, identify patterns, and produce a structured research
  brief. Trigger whenever the user mentions viral content research, Instagram research, Reel
  analysis, content DNA, swipe file building, niche research, competitor analysis for social
  content, or wants to understand why certain content performs. Also trigger when the user wants
  to find content formats to adapt, study what's working in a niche, or build a research-backed
  content strategy. This skill is research-only — it does not generate or publish content.
version: "1.0"
---

# Viral Research — Content DNA Extraction for Instagram Reels

## Purpose

Study what's already working in a niche on Instagram, deconstruct it frame-by-frame, identify
the structural and emotional patterns that drive virality, and produce a research brief that
any content production skill can consume.

This skill answers one question: **"What content is spreading in this niche, and why?"**

The output is a research brief — not content. Content generation is a separate downstream step.

## Scope

- **Platform:** Instagram (Reels primary, Carousels secondary)
- **Content type:** Faceless only (no face-on-camera content unless flagged as structural reference)
- **Analysis method:** Frame-by-frame video deconstruction via ffmpeg
- **Output:** Structured research brief (markdown) + swipe file (JSONL)

## Prerequisites

- **ffmpeg** — required for frame extraction (`ffprobe` + `ffmpeg`)
- **Browser access** — required for Instagram browsing (agent-browser or Chrome via MCP)
- **Video download method** — cobalt.tools (browser-based) or yt-dlp (CLI) for downloading Reels
- **references/research-config.json** — must be filled with niche and target app details before starting

Read `references/research-config.json` before every research session. All research is scoped
to the niche defined there.

On your first session, also read `references/example-brief.md` — a real research brief from
a sobriety niche session analyzing 10 Reels. This is the quality bar and depth of analysis
the skill should produce. Use it to calibrate your output format, DNA analysis depth, and
pattern recognition detail.

## Research Workflow

Every research session follows these phases in order. Each phase has a clear input, process,
and output. Do not skip phases — the quality of later phases depends on earlier ones.

### Phase 1: Discovery

**Goal:** Find 8-12 candidate Reels in the target niche that show signs of high engagement.

**Process:**

1. Read `references/research-config.json` to load niche keywords, hashtags, and target accounts
2. ⛔ NEVER open instagram.com in a browser — automated or manual. Use web search only.
3. Use Brave or Google to run 3-5 search variations derived from the niche:
   - Direct niche terms (e.g., `site:reddit.com sobriety reels`, `"sobriety myths" reel`)
   - Emotional angles (e.g., `"sober benefits nobody tells you" reel`, `"viral" "sober" tiktok compilation`)
   - Contrarian angles (e.g., `"alcohol is a scam" reel`, `"quit drinking truth" short video`)
   - Adjacent premium brands (e.g., `Calm reel`, `Headspace tiktok compilation`, `WHOOP sobriety video`)
4. From search results, open only result pages surfaced by search and look for **faceless short-form videos** — identified by:
   - Reel/short video URLs surfaced in search results
   - No human face visible in thumbnail
   - Text overlay, illustration, animation, or stock/nature footage as the visual
5. For each candidate surfaced by search, record:
   - URL
   - Account handle
   - Like count
   - View count (if visible)
   - Follower count of the account (if visible)
   - Post date (if visible)
   - Visual format (static text card, text on footage, animation, data viz, etc.)
6. Prioritize candidates by engagement-to-follower ratio, not raw likes. A post with 5K likes
   from a 10K-follower account is more interesting than 50K likes from a 5M-follower account.

**Output:** A list of 8-12 candidate URLs with metadata, saved to `references/swipe-file.jsonl`.

### Phase 2: Download

**Goal:** Obtain the video files for frame-by-frame analysis.

**Process:**

1. For each candidate Reel, download the video using one of these methods (in priority order):
   - **yt-dlp (primary)** — `yt-dlp --no-playlist -o "output/reels/%(id)s.mp4" <URL>`.
     Install: `pip install yt-dlp` or `brew install yt-dlp`. This is the preferred method
     because it's CLI-native and doesn't require browser interaction.
   - **gallery-dl** — `gallery-dl -d output/reels/ <URL>`. Alternative CLI downloader.
   - **Manual download by human** — if CLI methods fail (geo-block, auth wall, rate limit),
     provide the URL list to the human and ask them to download via cobalt.tools (browser-based).
     Name files by account handle (e.g., `calm.mp4`).
2. Save all downloaded videos to a working directory: `output/reels/`
3. Verify each download: `ffprobe -v quiet -show_entries format=duration <file>` — must return
   a valid duration. If 0 or error, the download failed — retry or flag.

**Output:** Video files in `output/reels/`, one per candidate.

### Phase 3: Frame Extraction

**Goal:** Extract individual frames from each video for visual analysis.

**Process:**

For each video file:

```bash
# Create output directory
mkdir -p output/frames/<account-handle>/

# Get video metadata
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration,r_frame_rate \
  -show_entries format=duration \
  -of default <video-file>

# Extract frames at 2fps (one frame every 0.5 seconds)
# This gives enough granularity for videos under 15 seconds
ffmpeg -i <video-file> \
  -vf "fps=2" \
  output/frames/<account-handle>/frame_%03d.png -y

# For longer videos (>15 seconds), use 1fps instead:
ffmpeg -i <video-file> \
  -vf "fps=1" \
  output/frames/<account-handle>/frame_%03d.png -y
```

Record for each video:

- Duration (seconds)
- Resolution (width x height)
- Frame rate (fps)
- Codec (h264, etc.)
- Number of frames extracted

**Output:** PNG frames in `output/frames/<account-handle>/`, metadata logged.

### Phase 4: DNA Analysis

**Goal:** Deconstruct each Reel's content DNA by examining every frame.

Read `references/dna-analysis-guide.md` before starting this phase. It contains the full
analysis framework and the fields to extract for each Reel.

**Process:**

For each set of extracted frames:

1. **View every frame** — read each PNG sequentially. Do not skip frames.
2. **Map the beat structure** — identify what changes between frames:
   - When does text appear/change/disappear?
   - When do visual transitions occur?
   - What is the pacing (how long does each element persist)?
   - Where is the hook? The punchline? The CTA?
3. **Extract DNA fields** — for each Reel, document:
   - Hook type (what stops the scroll in the first 1-2 seconds)
   - Text content (every word visible in the video, mapped to timestamps)
   - Visual style (color palette, typography, background type)
   - Emotional trigger (what feeling does this create?)
   - Viral mechanism (why would someone share this?)
   - Production tier (classify using `references/format-taxonomy.md`)
   - CTA strategy (if any)
   - Loop behavior (does the last frame match the first?)
4. **Write the analysis** — produce a structured DNA report for each Reel using the format
   in `references/dna-analysis-guide.md`

**Output:** DNA analysis for each Reel, written into the research brief.

### Phase 5: Pattern Recognition

**Goal:** Identify recurring patterns across the swipe file that explain what's working.

**Process:**

1. Compare all analyzed Reels along these dimensions:
   - **Duration vs engagement** — is there a sweet spot?
   - **Hook type vs engagement** — which hooks drive the most likes/views?
   - **Production tier vs engagement** — does higher production = better performance?
   - **Emotional trigger vs engagement** — which emotions drive shares?
   - **Visual style commonalities** — what do the top performers share visually?
2. Calculate engagement density: `likes / duration_seconds` for each Reel
3. Flag the **taste vs virality tension** — track production quality as a separate axis from
   engagement. A Reel can score high on taste but low on virality, or vice versa.
   Read `references/format-taxonomy.md` for the tier definitions.
4. Identify the **niche gap** — what formats are proven in adjacent niches (wellness, fitness)
   but nobody is doing in the target niche?

**Output:** Pattern analysis section in the research brief.

### Phase 6: Research Brief

**Goal:** Produce the final deliverable — a structured research brief.

Read `references/research-brief-template.md` for the output format.

The brief must include:

1. **Metadata** — niche, date, target app, number of Reels analyzed
2. **Frame-by-frame DNA analysis** — one section per Reel with the full beat-by-beat breakdown
3. **Format taxonomy** — which tiers are represented, with examples
4. **Cross-Reel pattern analysis** — the patterns identified in Phase 5
5. **Duration vs engagement table** — ranked by engagement density
6. **Recommended production ladder** — phased recommendations for the target account
7. **Top content angles** — specific content ideas derived from the research
8. **Production tools notes** — what tools can produce each format tier

Save the brief to `output/research-brief.md`.
Update `references/swipe-file.jsonl` with the full analysis data for each Reel.

## Operating Principles

- **Research only, never create content.** This skill observes and analyzes. It does not
  generate captions, slides, or posts. That's for a downstream content skill.
- **Faceless by default.** Flag face-on-camera content only as structural references for
  narrative arc analysis. All production recommendations should be faceless.
- **Engagement relative to followers, not raw numbers.** 1K likes on a 5K-follower account
  is more signal than 10K likes on a 2M-follower account.
- **Taste and virality are separate axes.** Track both. A Reel can be premium but low-engagement
  (Headspace) or tacky but wildly viral (AI sunset quotes). The research brief surfaces both
  dimensions so the human can decide where to position.
- **Under 10 seconds is the sweet spot.** The data consistently shows that faceless Reels under
  10 seconds get higher completion rates and more algorithmic distribution. Flag any Reel over
  15 seconds as an outlier.
- **Frame-by-frame is non-negotiable.** Do not analyze Reels from thumbnails or screenshots alone.
  Download the video, extract frames with ffmpeg, and read every frame. The DNA is in the details
  — text timing, visual transitions, pacing, loop points — that are invisible without frame extraction.
- **Document the process, not just the findings.** Every research session should record the search
  terms used, the number of results scanned, and the selection criteria applied. This makes the
  research reproducible and improvable.

## Memory

All paths relative to this skill's directory:

- **Swipe file (append-only):** `references/swipe-file.jsonl`
- **Research config:** `references/research-config.json`
- **Format taxonomy:** `references/format-taxonomy.md`
- **DNA analysis guide:** `references/dna-analysis-guide.md`
- **Brief template:** `references/research-brief-template.md`
- **Example brief (read-only):** `references/example-brief.md` — real output from a sobriety niche session. Read on first session to calibrate quality bar.
- **Output directory:** `output/` (created on first run if missing)

The swipe file accumulates across sessions. Each research session adds entries;
nothing is deleted. Over time this builds a rich dataset of niche-specific patterns.
