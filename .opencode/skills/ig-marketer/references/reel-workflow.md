# Reel Remix Workflow

Self-contained instructions for downloading and remixing an Instagram or TikTok reel.
No external skills or repos required.

---

## Pre-flight — Install Dependencies (once per environment)

```bash
_install() {
  local pkg=$1
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install "$pkg"
  elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y "$pkg"
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y "$pkg"
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm "$pkg"
  else
    echo "ERROR: Cannot auto-install $pkg — unsupported package manager. Install manually." >&2
    exit 1
  fi
}

if ! command -v yt-dlp &>/dev/null; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install yt-dlp
  else
    pip3 install yt-dlp --user 2>/dev/null || pip install yt-dlp --user
  fi
fi

command -v ffmpeg &>/dev/null || _install ffmpeg
command -v magick &>/dev/null || _install imagemagick
```

---

## Step 1 — Download Source Video

```bash
WORK_DIR="$(pwd)/reel-remix-work"
mkdir -p "$WORK_DIR"
yt-dlp --no-playlist -o "$WORK_DIR/original.mp4" "<SOURCE_URL>"
```

If yt-dlp fails (geo-block, login-required, private), surface the error — do not continue.

---

## Step 2 — Inspect the Video

```bash
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration \
  -show_entries format=duration \
  -of default "$WORK_DIR/original.mp4"
```

Extract and store:
- `VIDEO_W` — width
- `VIDEO_H` — height
- `AUDIO_DUR` — total duration (master clock)

Extract 3 probe frames to detect the original caption text zone:

```bash
ffmpeg -i "$WORK_DIR/original.mp4" \
  -vf "select=eq(n\,0)+eq(n\,15)+eq(n\,30)" \
  -vsync 0 "$WORK_DIR/probe_%d.png" -y 2>/dev/null

TEXT_ZONE_H=9999
for f in "$WORK_DIR"/probe_*.png; do
  OFFSET=$(magick "$f" -fuzz 8% -trim -format "%O" info: 2>/dev/null \
    | grep -oE '\+[0-9]+$' | tr -d '+')
  [ -n "$OFFSET" ] && [ "$OFFSET" -lt "$TEXT_ZONE_H" ] && TEXT_ZONE_H=$OFFSET
done

if [ "$TEXT_ZONE_H" -eq 9999 ] || [ "$TEXT_ZONE_H" -lt 50 ]; then
  echo "ERROR: Could not detect text zone. Inspect probe frames manually." >&2
  exit 1
fi

TEXT_ZONE_H=$(( TEXT_ZONE_H + 150 ))
echo "TEXT_ZONE_H=$TEXT_ZONE_H"
```

Read `probe_1.png` to identify:
- `HOOK_BG` — background color of the text zone (e.g. `black`, `white`)
- `HOOK_FG` — text color (inverse of background)
- The original hook text verbatim (input for copy generation)

---

## Step 3 — Generate New Hook and CTA

Using the original hook text, the source video's engagement signals, and the app defined in `references/config.json`:

**Hook:**
- Adapt the original hook to an angle relevant to the app's niche and the topic researched this cycle
- Format and structure follow from what resonated in research — do not impose a fixed line count or structure
- Fit the length and style to how text physically renders on the video (constrained by `TEXT_ZONE_H` from Step 2)
- Must pass the virality gate in `references/virality-model.md` before proceeding

**CTA:**
- Drive the action determined by the current experiment variable in `references/playbook.json` → `activeCTA`
- If `activeCTA` is null, choose the CTA angle that best matches the topic and hook from the `ctaVariants` list
- Style, line count, and placement follow from what reads clearly at the render size — not a prescribed template

Generate 3 hook options + 3 CTA options. Present for one user confirmation before rendering.

---

## Step 4 — Confirmation Checkpoint (ONE PAUSE)

```
PROPOSED REMIX

━━━ HOOK OPTIONS ━━━
[1] Line 1 / Line 2
[2] Line 1 / Line 2
[3] Line 1 / Line 2

━━━ CTA OPTIONS ━━━
[A] Full CTA text (2-3 lines)
[B] Full CTA text (2-3 lines)
[C] Full CTA text (2-3 lines)

━━━ OUTPUT ━━━
output/reels/{MM-DD-YY}-{topic-slug}/{3-4-word-seo-filename}.mp4

CTA duration: 3 seconds
Reply with hook # and CTA letter (e.g. "2A") or request changes.
```

---

## Step 5 — Render Hook Overlay PNG

```bash
if [[ "$OSTYPE" == "darwin"* ]]; then
  FONT="Helvetica"
else
  magick -list font 2>/dev/null | grep -qi "DejaVu-Sans" && FONT="DejaVu-Sans" || FONT=""
fi
FONT_ARG=${FONT:+-font "$FONT"}

LINE1_Y=$(( TEXT_ZONE_H / 2 - 40 ))
LINE2_Y=$(( TEXT_ZONE_H / 2 + 40 ))

magick -size ${VIDEO_W}x${TEXT_ZONE_H} xc:${HOOK_BG} \
  $FONT_ARG \
  -pointsize 48 \
  -fill ${HOOK_FG} \
  -draw "gravity North text 0,${LINE1_Y} '{{LINE_1}}'" \
  -draw "gravity North text 0,${LINE2_Y} '{{LINE_2}}'" \
  "$WORK_DIR/hook_overlay.png"
```

Read the PNG to verify text is centered and fully covers the original text zone.

---

## Step 6 — Render CTA Frame PNG

```bash
magick -size ${VIDEO_W}x${VIDEO_H} xc:black \
  $FONT_ARG \
  -pointsize 54 \
  -fill white \
  -draw "gravity Center text 0,-50 '{{CTA_LINE_1}}'" \
  -draw "gravity Center text 0,50 '{{CTA_LINE_2}}'" \
  "$WORK_DIR/cta_frame.png"
```

For 3-line CTAs add: `-draw "gravity Center text 0,150 '{{CTA_LINE_3}}'"`. Read PNG to verify.

---

## Step 7 — Extract Audio

```bash
ffmpeg -i "$WORK_DIR/original.mp4" -vn -c:a copy "$WORK_DIR/audio.aac" -y
```

---

## Step 8 — Build Remixed Video (no audio)

```bash
ffmpeg -i "$WORK_DIR/original.mp4" \
  -i "$WORK_DIR/hook_overlay.png" \
  -filter_complex "[0:v][1:v]overlay=0:0" \
  -an -c:v libx264 -preset fast \
  "$WORK_DIR/remixed_full.mp4" -y
```

---

## Step 9 — Build Silent CTA Clip

```bash
ffmpeg -loop 1 -i "$WORK_DIR/cta_frame.png" \
  -t 3 -r 30 -an \
  -c:v libx264 -preset fast -pix_fmt yuv420p \
  "$WORK_DIR/cta_silent.mp4" -y
```

---

## Step 10 — Concatenate + Mux Final Output

```bash
cat > "$WORK_DIR/concat.txt" << EOF
file '$WORK_DIR/remixed_full.mp4'
file '$WORK_DIR/cta_silent.mp4'
EOF

ffmpeg -f concat -safe 0 -i "$WORK_DIR/concat.txt" \
  -c:v libx264 -preset fast \
  "$WORK_DIR/video_only.mp4" -y

TOTAL_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$WORK_DIR/video_only.mp4")
ffmpeg -stream_loop -1 -i "$WORK_DIR/audio.aac" \
  -t "$TOTAL_DUR" -c:a aac \
  "$WORK_DIR/audio_looped.m4a" -y

# Output path relative to wherever the agent is running
FOLDER="{MM-DD-YY}-{topic-slug}"
OUTPUT_DIR="output/reels/${FOLDER}"
mkdir -p "$OUTPUT_DIR"

ffmpeg -i "$WORK_DIR/video_only.mp4" \
  -i "$WORK_DIR/audio_looped.m4a" \
  -c:v copy -c:a copy -shortest \
  "$OUTPUT_DIR/{FILENAME}.mp4" -y
```

Verify with ffprobe: duration ≈ AUDIO_DUR + 3s, h264 + aac streams present.

---

## Key Rules

- All intermediate files go into `reel-remix-work/` (relative to cwd). Never use `/tmp`.
- Output goes into `output/reels/` (relative to skill dir).
- Audio covers the full output — loop original audio to fill video + CTA so the reel is never silent.
- PNG overlay only — do not use ffmpeg drawtext (requires libfreetype which may be absent).
- One confirmation pause only — do not ask the user anything else unless there is an error.
