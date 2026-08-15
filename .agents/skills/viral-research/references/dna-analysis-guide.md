# DNA Analysis Guide

How to deconstruct a Reel frame-by-frame and extract its viral DNA.

## Prerequisites

Before analyzing, ensure you have:
- The video file (.mp4)
- Frames extracted via ffmpeg at 2fps (videos ≤15s) or 1fps (videos >15s)
- The post's engagement data (likes, views, follower count, post date)

## Step 1: Video Metadata

Run ffprobe and record:

```bash
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration,r_frame_rate \
  -show_entries format=duration \
  -of default <video-file>
```

Document:
- Duration (seconds)
- Resolution (width × height)
- Frame rate (fps)
- Audio presence (yes/no)
- Number of frames extracted

## Step 2: Sequential Frame Reading

Read every extracted frame in order. Do not skip frames — the DNA is in the transitions.

For each frame, note:
- **What's visible** — background imagery, text, icons, logos, animations
- **What changed** — compared to the previous frame. If nothing changed, note "static"
- **Text content** — exact words visible, position (top/center/bottom), styling (bold, color, size)

## Step 3: Beat Mapping

Map the Reel's temporal structure. A "beat" is a distinct moment where the viewer's
experience shifts — new text appears, visual changes, emotional tone shifts, or a
punchline lands.

Common beat structures observed in faceless Reels:

**Single-beat (T1 Meme, T2 Quote Card):**
The entire Reel is one beat. Text appears on frame 1 and never changes. The "progression"
comes from the viewer's reading time or from dynamic footage underneath static text.

**Two-beat (T3 Text Card):**
Beat 1: Myth/problem/expectation (top of frame)
Beat 2: Reality/solution/subversion (bottom of frame, longer and more detailed)
Both visible simultaneously — the "beat" is the viewer's eye movement from top to bottom.

**Multi-beat (T4 Truth Bomb, P2 Data Viz):**
Beat 1: Hook (0-2s)
Beat 2: Escalation (2-5s)
Beat 3: Peak/punchline (5-8s)
Beat 4: Resolution or CTA (8-10s)

**Functional loop (P1):**
Beat 1: Action prompt ("Inhale")
Beat 2: Transition
Beat 3: Counter-action ("Exhale")
Beat 4: Return to start (seamless loop)

Document the beat structure as a timeline table:

| Time | Frame | Visual                | Text               | Beat                 |
| ---- | ----- | --------------------- | ------------------ | -------------------- |
| 0.0s | 1     | Description of visual | Exact text visible | BEAT NAME — function |
| ...  | ...   | ...                   | ...                | ...                  |

## Step 4: DNA Field Extraction

For each Reel, extract all of these fields. Every field matters — a missing field is a
gap in the analysis.

### Hook (first 1-3 seconds)

- **Hook type:** One of:
  - `statement` — bold claim or provocative assertion
  - `question` — asks the viewer something
  - `curiosity-gap` — implies information the viewer doesn't have
  - `contrast` — sets up an expectation that will be subverted
  - `visual-only` — no text, pure visual/animation hook
  - `interactive` — asks the viewer to do something ("double-tap," "try this")
- **Hook text:** Exact words (if text-based)
- **Scroll-stop mechanism:** What specifically would make a thumb pause mid-scroll?

### Content Structure

- **Text content:** Every word in the video, mapped to the frame where it appears
- **Word count:** Total words visible across all frames
- **Text changes:** Number of times text changes during the video (0 = fully static)
- **Information density:** Words per second of video
- **Argument structure:** (if applicable) How the content builds its case
  - Single assertion (T2)
  - Comparison/contrast (T3)
  - Logical escalation: fact → irony → conclusion (T4)
  - Narrative arc: hook → tension → reframe → punchline (adapted from face content)

### Visual Style

- **Background type:** One of:
  - `stock-footage` — real video (nature, lifestyle, drone)
  - `stock-photo` — single static image
  - `ai-generated` — AI-created imagery
  - `timelapse` — slow-moving footage (sunset, clouds)
  - `solid-color` — flat background color
  - `gradient` — color gradient
  - `custom-illustration` — original vector/raster art
  - `motion-graphics` — animated shapes, particles, data viz
  - `screen-recording` — app UI or data display
- **Color palette:** Dominant colors (be specific: "deep blue #0000CC" not just "blue")
- **Typography:**
  - Font style: serif / sans-serif / handwritten / monospace
  - Weight: bold / regular / light
  - Size: relative to frame (large/centered vs small/lower-third)
  - Color: text color + any accent colors
- **Frosted glass / blur effects:** Present or absent (premium signal)
- **Visual metaphor:** Does the background relate to the text's meaning? (volcano = chaos, sunrise = new beginning, rapids = difficult journey)

### Emotional Trigger

- **Primary emotion:** The dominant feeling the content creates. One of:
  - `validation` — "I've felt this way too"
  - `reframe` — "I never thought of it that way"
  - `humor` — "this is funny because it's true"
  - `urgency` — "I need to act on this"
  - `aspiration` — "I want to be/feel like this"
  - `outrage` — "this is wrong and people need to know"
  - `surprise` — "I didn't know that"
  - `calm` — "this makes me feel peaceful" (functional content)
- **Secondary emotion:** (if present)
- **Shareability driver:** Why would someone send this to a friend?
  - "This is us" (relatability)
  - "You need to see this" (urgency/importance)
  - "This is so true" (validation)
  - "Try this" (functional/interactive)

### Production Assessment

- **Format tier:** Classify using `references/format-taxonomy.md` (T1-T4, P1-P3)
- **Production cost estimate:** Time to reproduce this format (5 min / 15 min / 1-2 hrs / 4-8 hrs)
- **Remotion feasibility:** Can this be built programmatically? (HIGH / MEDIUM / LOW)
- **fal.ai potential:** Could AI generation replace any visual element? (background, illustration)
- **Loop behavior:** Does the last frame match the first? (seamless loop / hard cut / fade to black)
- **Audio role:** Does the audio contribute to the content or is it just background music?

### Engagement Metrics

- **Likes:** raw count
- **Views:** raw count (if visible)
- **Like-to-view ratio:** likes / views (if both available)
- **Follower count:** of the posting account
- **Engagement rate:** likes / followers
- **Engagement density:** likes / duration_seconds
- **Post age:** days since posting (engagement may still be accumulating)

### Sobriety Adaptation Notes

For each Reel, note:
- How could this format be adapted to the sobriety/alcohol-free niche?
- What sobriety-specific topics would fit this structure?
- What visual metaphors from recovery/sobriety would work as backgrounds?
- Specific content ideas (1-3 concrete examples)

## Step 5: Write the Analysis

Combine everything into a structured section for the research brief. Use this format:

```markdown
### Reel N — @handle | X likes | Xs | FACELESS | TIER

**Video specs:** WxH, Xfps, codec, N frames extracted at X intervals

**Frame-by-frame breakdown:**

| Time | Frame | Visual | Text | Beat |
| ---- | ----- | ------ | ---- | ---- |
| ...  | ...   | ...    | ...  | ...  |

**DNA findings:**
- [Key finding 1]
- [Key finding 2]
- [Key finding 3]
- **Key insight:** [The single most important takeaway]

**Sobriety adaptation:** [How to use this format for the target niche]
```
