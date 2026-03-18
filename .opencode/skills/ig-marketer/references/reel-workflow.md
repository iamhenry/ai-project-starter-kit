# Reel Workflow

Two paths: **Original Reel** (generate from scratch) and **Remix** (adapt an existing viral reel).

---

## Instagram Reels Specs

These are Instagram's technical requirements. All reels must meet these regardless of visual style.

- **Dimensions:** 1080×1920 (9:16 portrait)
- **Duration:** 15–90 seconds recommended for discovery (max 3 minutes, but shorter performs better)
- **Frame rate:** 30fps
- **Codec:** H.264 video + AAC audio
- **No watermarks** from other platforms (TikTok, CapCut) — Instagram penalizes these
- **Generate images at `portrait_4_3`** (1440×1920) using the model in `config.json` → `fal.defaultImageModel`. This produces images slightly larger than 1080×1920 — Remotion downscales them (sharp, no quality loss, no wasted pixels)

---

## Rendering Engine: Remotion

All reels are rendered using Remotion.

**Project structure (separated):**

```
/home/node/remotion-runtime/          # Remotion tool (shared across skills)
├── src/
│   ├── index.ts       # Entry point
│   ├── Root.tsx       # Composition definition
│   └── Reel.tsx       # Main reel component
├── public/             # Images + audio go here before render
├── package.json        # Dependencies
└── remotion.config.ts

skills/ig-marketer/scripts/           # Reel code (part of skill, shareable)│   ├── Reel.tsx        # Component definition (copied to runtime)
│   ├── Root.tsx        # Composition definition
│   └── index.ts        # Entry point
```

**How it works:**
1. Scripts in `scripts/` define the component structure (shareable, versioned with skill)2. Runtime at `/home/node/remotion-runtime/` has the actual Remotion installation
3. When rendering, copy scripts to runtime, add assets to public/, render, move output back

### How the Reel component works

The `Reel` component renders a **6-slide reel** (hook + 4 content + CTA). Props:

- `images: string[]` — 5 filenames in `public/` (or full URLs): 1 hook image + 4 content images
- `hookText: string` — text overlay on slide 1 (centered, large)
- `sceneTexts: string[]` — text overlays for slides 2-5 (4 entries, bottom-positioned)
- `ctaText: string` — text on slide 6 (CTA card)
- `audioFile: string` — filename in `public/`
- `secondsPerScene: number` — duration per image scene (use 3)

Built-in features:
- **Ken Burns zoom:** Each scene zooms 100% → 106% over its duration
- **Fade transitions:** 0.5s crossfade between scenes via `@remotion/transitions`
- **Text overlays:** Spring-animated text on every slide — hook (centered, bold) and content slides (bottom-positioned with glass-blur background)
- **CTA card:** Black card with spring-scale text + "⬇ Link in bio"
- **Audio:** Plays the selected track across the full reel

### Render command

```bash
# Copy component files to runtime
cp skills/ig-marketer/scripts/*.tsx /home/node/remotion-runtime/src/
cp skills/ig-marketer/scripts/*.ts /home/node/remotion-runtime/src/ 2>/dev/null || true# Copy assets to runtime public/cpcp output/assets/audio/*.mp3 /home/node/remotion-runtime/public/ 2>/dev/null || truecp output/assets/scene-*.png /home/node/remotion-runtime/public/ 2>/dev/null || true

# Render (6-slide reel: 5 images + CTA card)
cd /home/node/remotion-runtime
npx remotion render src/index.ts Reel \
  --props='{"images":["scene-1.png","scene-2.png","scene-3.png","scene-4.png","scene-5.png"],"hookText":"Your hook here","sceneTexts":["Point 1","Point 2","Point 3","Point 4"],"ctaText":"Your CTA here","audioFile":"calm-reflective.mp3","secondsPerScene":3}' \
  --output=out/reel.mp4 \
  --codec=h264

# Move output back to skill output folder
mv /home/node/remotion-runtime/out/reel.mp4 skills/ig-marketer/output/reels/<date>-<topic>/reel.mp4
```

### Adapting the template

The agent can modify `src/Reel.tsx` to change:
- Animation style (zoom amount, transition type, text position)
- Typography (font size, color, shadow)
- CTA design (colors, layout)
- Scene timing

Read the Remotion skill at `skills/remotion/SKILL.md` for best practices on animations, transitions, text, and timing.

---

## Path A: Original Reel

Create a reel from scratch using generated images + audio.

### Steps1. **Generate images** via fal.ai using model from `config.json` → `fal.defaultImageModel`, size from `fal.defaultImageSize`
2. **Copy images** to `output/assets/` as `scene-1.png`, `scene-2.png`, etc.
3. **Get audio** from `output/assets/audio/<track>.mp3`
4. **Sync to runtime:** Copy componentfiles + assets to `/home/node/remotion-runtime/`
5. **Render** with the command above, passing the hook text, CTA text, and scene list
6. **Move output** from runtime back to `output/reels/<date>-<topic>/reel.mp4`

### Choosing audio

Pick from `output/assets/audio/`:
- `calm-reflective.mp3` — personal, vulnerable, introspective topics
- `uplifting-hopeful.mp3` — progress, milestones, positive outcomes
- `gentle-morning.mp3` — morning routines, fresh starts, daily habits
- `determined-empowered.mp3` — willpower, overcoming urges, strength topics
- `contemplative-deep.mp3` — deep reflection, identity, why-you-started topics

Match the track to the reel's emotional register. When in doubt, `calm-reflective` is the safest default.

### Output

- `.mp4` in `output/reels/<date>-<topic>/`
- Verify with ffprobe: 1080×1920, h264+aac, 15-90 seconds, 30fps

---

## Path B: Reel Remix

Download and remix an existing high-performing reel with a new hook and CTA.

### Steps

1. **Download** source video with `yt-dlp`
2. **Inspect** with ffprobe (dimensions, duration, audio)
3. **Extract probe frames** to detect text zone
4. **Generate** new hook + CTA text (3 options each, pass virality gate)
5. **Render** hook overlay PNG and CTA frame PNG
6. **Build** remixed video: overlay hook on original → append CTA → mux audio
7. **Output** to `output/reels/<date>-<topic>/`

### Pre-flight

```bash
# Ensure yt-dlp is available
command -v yt-dlp || pip3 install yt-dlp --user
```

### Download + Inspect

```bash
WORK_DIR="$(pwd)/reel-remix-work"
mkdir -p "$WORK_DIR"
yt-dlp --no-playlist -o "$WORK_DIR/original.mp4" "<SOURCE_URL>"

ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration \
  -show_entries format=duration \
  -of default "$WORK_DIR/original.mp4"
```

### Text Zone Detection

Extract probe frames and detect where the original text sits:

```bash
ffmpeg -i "$WORK_DIR/original.mp4" \
  -vf "select=eq(n\,0)+eq(n\,15)+eq(n\,30)" \
  -vsync 0 "$WORK_DIR/probe_%d.png" -y
```

Read the probe frames visually to identify the text zone height and colors.

### Hook + CTA Generation

Generate 3 hook options + 3 CTA options. Present for confirmation. Must pass virality gate before proceeding.

### Rendering Remix

Use Remotion if the remix is simple enough (overlay + CTA append). For complex remixes with existing video, ffmpeg is acceptable:

```bash
# Overlay hook on original
ffmpeg -i "$WORK_DIR/original.mp4" \
  -i "$WORK_DIR/hook_overlay.png" \
  -filter_complex "[0:v][1:v]overlay=0:0" \
  -an -c:v libx264 -preset fast \
  "$WORK_DIR/remixed_full.mp4" -y

# Create CTA clip
ffmpeg -loop 1 -i "$WORK_DIR/cta_frame.png" \
  -t 3 -r 30 -an -c:v libx264 -preset fast -pix_fmt yuv420p \
  "$WORK_DIR/cta_silent.mp4" -y

# Concatenate + mux audio
cat > "$WORK_DIR/concat.txt" << EOF
file '$WORK_DIR/remixed_full.mp4'
file '$WORK_DIR/cta_silent.mp4'
EOF

ffmpeg -f concat -safe 0 -i "$WORK_DIR/concat.txt" \
  -c:v libx264 -preset fast "$WORK_DIR/video_only.mp4" -y

ffmpeg -i "$WORK_DIR/video_only.mp4" \
  -stream_loop -1 -i "$WORK_DIR/audio.aac" \
  -c:v copy -c:a aac -shortest \
  "output/reels/<folder>/remix.mp4" -y
```

---

## Key Rules

- **Remotion for original reels.** It handles animations, text, and transitions properly.
- **ffmpeg only for remix operations** (overlaying on existing video, concatenation, audio muxing).
- All intermediate files go into working directories. Output goes into `output/reels/`.
- Audio must cover the full reel — never silent.
- One confirmation pause only — do not ask the user anything else unless there is an error.
