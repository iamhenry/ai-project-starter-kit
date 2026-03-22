# Reel QA Checklist — Mandatory Before Human Review

This checklist MUST be completed by the reviewing agent (Zigzag) before any reel is sent to Henry. Every check is pass/fail. If ANY check fails, the reel is rejected and sent back to the producer with specific failure reasons.

## Automated Checks (run these commands)

### 1. File exists and is a real video
```bash
# Must be .mp4, must exist, must be > 100KB
FILE="output/reels/<slug>/<slug>.mp4"
[ -f "$FILE" ] && [ $(stat -c%s "$FILE") -gt 100000 ] && echo "PASS" || echo "FAIL: missing or too small"
```
**FAIL = reject immediately.** A render-instructions.md file is NOT a reel.

### 2. Video specs (resolution, codec, duration)
```bash
ffprobe -v quiet -print_format json -show_format -show_streams "$FILE" | \
  jq '{duration: .format.duration, streams: [.streams[] | {codec_type, width, height, codec_name}]}'
```
- Resolution: 1080x1920 (9:16 vertical) → **PASS/FAIL**
- Video codec: h264 → **PASS/FAIL**
- Audio track present: yes → **PASS/FAIL** (no silent reels)
- Duration: 5-15 seconds → **PASS/FAIL**

### 3. Motion check — extract frames and compare
```bash
# Extract 6 evenly-spaced frames
FRAMES_DIR="/tmp/qa-frames-$(basename $FILE .mp4)"
mkdir -p "$FRAMES_DIR"
TOTAL_FRAMES=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$FILE")
INTERVAL=$((TOTAL_FRAMES / 6))
ffmpeg -y -i "$FILE" -vf "select=not(mod(n\,$INTERVAL))" -vsync vfr -frames:v 6 "$FRAMES_DIR/frame_%02d.jpg" 2>/dev/null

# Compare consecutive frames for differences (SSIM)
for i in 1 2 3 4 5; do
  NEXT=$((i+1))
  SSIM=$(ffmpeg -i "$FRAMES_DIR/frame_$(printf '%02d' $i).jpg" -i "$FRAMES_DIR/frame_$(printf '%02d' $NEXT).jpg" -lavfi ssim -f null - 2>&1 | grep "All:" | awk '{print $NF}')
  echo "Frame $i→$NEXT SSIM: $SSIM"
done
```
- If ALL consecutive frame pairs have SSIM > 0.98 → **FAIL: static video** (the frames are nearly identical, meaning no real motion)
- At least 2 frame pairs must have SSIM < 0.95 → **PASS** (meaningful visual change between frames)

### 4. Visual review — send frames to vision model
```bash
# Copy frames to media/inbound for vision model access
cp "$FRAMES_DIR"/*.jpg /home/node/.openclaw/media/inbound/
```
Then use the `image` tool to review all 6 frames with this prompt:
> "This is supposed to be an Instagram Reel. Rate it on: (1) Does it have visible motion/animation between frames? (2) Is the text readable and well-positioned? (3) Does it have a clear hook in frame 1? (4) Does it have a payoff/CTA? (5) Would you stop scrolling for this? Score 1-5 on each."

- Average score must be ≥ 3.0 → **PASS/FAIL**
- Any individual dimension scoring 1 → **FAIL** (critical deficiency)

## Manual Checks (reviewer judgment)

### 5. Content completeness
- [ ] Hook is clear in first 1-2 seconds
- [ ] There's a payoff or revelation (not just a question with no answer)
- [ ] CTA exists (even if subtle — "follow for more", app mention, etc.)
- [ ] Caption file exists and is non-empty
- [ ] Caption matches the reel content (not generic)

### 6. Brand alignment
- [ ] Visual style matches Zero Proof brand (dark/moody/cinematic, not bright/corporate)
- [ ] Text tone matches soul.md voice (raw, not preachy)
- [ ] No competitor mentions or trademarked content

### 7. Render quality
- [ ] No rendering artifacts (black frames, glitched text, misaligned overlays)
- [ ] Text is readable at mobile size (not too small, not too many words per frame)
- [ ] Audio is present and not jarring

## Verdict

ALL automated checks pass + ALL manual checks pass = **APPROVED — send to Henry**
ANY check fails = **REJECTED — send back with specific failures listed**

## Rejection Template

```
🔄 Reel rejected: <slug>

Failed checks:
- [list specific failures]

What needs fixing:
- [specific instructions]

This is revision X/2.
```

## When Remotion Isn't Working

If the producer outputs `render-instructions.md` instead of an actual `.mp4`, treat it as a **hard render failure**, not graceful degradation. The reviewer must:

1. Flag that Remotion rendering failed
2. Fail the issue immediately — do NOT pass render instructions through as "content ready for review"
3. Send it back to production to fix the Remotion pipeline and produce an actual `.mp4`

Optional manual instructions may remain in the folder as debugging artifacts, but they do not change the verdict.

**A render instruction file is never "ready for Henry."**
