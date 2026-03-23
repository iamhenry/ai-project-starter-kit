# Remotion Guide

How to use Remotion for rendering faceless Instagram Reels.

Remotion renders React components to video. Each format tier is a React composition
that accepts props (text, assets, timing) and outputs an .mp4. The power of this approach
is that once a composition exists, producing variations is just changing the props — no
manual video editing required.

## Setup

### Install

```bash
# In the Remotion project directory
npm install @remotion/cli @remotion/renderer react react-dom
```

### Project structure

```
remotion-project/
├── src/
│   ├── compositions/
│   │   ├── MemeReel.tsx        — T1 format
│   │   ├── QuoteCard.tsx       — T2 format
│   │   ├── TextCard.tsx        — T3 format
│   │   ├── TruthBomb.tsx       — T4 format
│   │   ├── FunctionalLoop.tsx  — P1 format
│   │   ├── DataVizHumor.tsx    — P2 format
│   │   └── CulturalEdutainment.tsx — P3 format
│   ├── components/
│   │   ├── FrostedCard.tsx     — reusable frosted glass overlay
│   │   ├── TextOverlay.tsx     — text with shadow/outline
│   │   ├── Counter.tsx         — animated number counter
│   │   └── BreathingCircle.tsx — expanding/contracting shape
│   ├── Root.tsx
│   └── index.ts
├── public/
│   └── assets/                 — background images, footage, fonts
├── remotion.config.ts
└── package.json
```

### Key Remotion concepts

```tsx
// useCurrentFrame() gives the current frame number (0-indexed)
// interpolate() maps frame ranges to output values
// spring() creates physics-based animations

import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

const MyComponent = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in text over 15 frames (0.5s at 30fps)
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Breathing animation using sine wave
  const scale = 1 + 0.1 * Math.sin((frame / fps) * Math.PI * 0.5);

  return (
    <div style={{ opacity, transform: `scale(${scale})` }}>
      Hello
    </div>
  );
};
```

## Rendering

### Render a single Reel

```bash
npx remotion render <composition-id> \
  --props='{"text":"Your quote here","background":"./public/assets/bg.png"}' \
  --output=output.mp4 \
  --codec=h264 \
  --image-format=jpeg \
  --quality=80
```

### Render a still frame (for thumbnails)

```bash
npx remotion still <composition-id> \
  --props='{"text":"Your quote here"}' \
  --output=thumbnail.png \
  --frame=0
```

### Render with a props file

```bash
npx remotion render <composition-id> \
  --props=./props.json \
  --output=output.mp4
```

## Composition Specs Per Format

### T1: MemeReel
- Duration: 150-240 frames (5-8s at 30fps)
- Inputs: `{ backgroundVideo: string, setupText: string, labelText?: string }`
- The background video plays at full speed. Text layers are static (no animation).

### T2: QuoteCard
- Duration: 150-210 frames (5-7s at 30fps)
- Inputs: `{ backgroundImage: string, quoteLines: string[], handle?: string }`
- Static background image. Static text. The composition exists purely to create a
  valid video file from a still image (Instagram classifies Reels differently from photos).

### T3: TextCard
- Duration: 180-300 frames (6-10s at 30fps)
- Inputs: `{ backgroundVideo: string, mythHeader: string, mythItems: string[], realityHeader: string, realityItems: string[], brandLogo?: string }`
- Background video plays. All text is static and present from frame 0.

### T4: TruthBomb
- Duration: 210-300 frames (7-10s at 30fps)
- Inputs: `{ backgroundVideo: string, parts: [string, string, string] }`
- Background video plays. Text can optionally fade in with stagger (part 1 at frame 0,
  part 2 at frame 30, part 3 at frame 60) or all present from frame 0.

### P1: FunctionalLoop
- Duration: 240-360 frames (8-12s at 30fps)
- Inputs: `{ actionWord: string, counterWord: string, brandColor: string, particleCount?: number }`
- The main element (circle, globe) uses sine-based scaling synced to the action/counter
  word transitions. Last frame must equal first frame.
- Use `interpolate()` with a full sine cycle mapped to the composition duration.

### P2: DataVizHumor
- Duration: 120-600 frames (4-20s at 30fps)
- Inputs: `{ metric: string, startValue: number, endValue: number, visualType: "destruction" | "escalation", accentColor: string, hookText?: string, ctaText?: string }`
- Counter animates from startValue to endValue. Visual element reacts to counter position.
- For destruction: `spring()` with high damping for the shatter effect.
- For escalation: linear interpolation on the counter, `spring()` on the visual intensity.

### P3: CulturalEdutainment
- Duration: 240-360 frames (8-12s at 30fps)
- Inputs: `{ backgroundVideo: string, term: string, pronunciation?: string, partOfSpeech: string, definition: string, seeAlso: string, etymology?: [{ word: string, meaning: string }], cardStyle: "light" | "dark" }`
- Background video plays. Frosted card is centered vertically. Text can optionally
  reveal with stagger (term first, then definition, then "see also" last).

## Frosted Glass Card (Reusable Component)

The frosted glass effect is central to the P3 format and can elevate any tier.

```tsx
const FrostedCard: React.FC<{ children: React.ReactNode; style?: "light" | "dark" }> = ({
  children,
  style = "dark",
}) => {
  const bg = style === "dark" ? "rgba(0, 0, 0, 0.3)" : "rgba(255, 255, 255, 0.15)";
  const border = style === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(255, 255, 255, 0.2)";

  return (
    <div
      style={{
        backgroundColor: bg,
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: `1px solid ${border}`,
        borderRadius: 16,
        padding: 32,
      }}
    >
      {children}
    </div>
  );
};
```

Note: `backdropFilter` works in Remotion because it renders via Chromium. This is one of
Remotion's advantages over pure ffmpeg — you get full CSS capabilities.

## Post-Render Verification

After every render, verify:

```bash
# Check codec, resolution, duration
ffprobe -v quiet \
  -show_entries stream=codec_name,width,height,duration \
  -show_entries format=duration \
  output.mp4

# Expected output:
# codec_name=h264, width=720, height=1280, duration=~target
# codec_name=aac (audio stream)

# Check file size (Instagram limit: 250MB for Reels)
ls -lh output.mp4
```

If the audio stream is missing and you need background music, mux it in:

```bash
ffmpeg -i output.mp4 -i audio.mp3 \
  -c:v copy -c:a aac -shortest \
  output-with-audio.mp4 -y
```

## Ken Burns Effect (Default Motion)

All compositions with a background image or video should apply the Ken Burns effect by default.
This adds subtle camera-like motion that prevents the "slideshow" feel.

### Default parameters

| Property | Start | End | Notes |
|---|---|---|---|
| scale | 1.0 | 1.18 | ~25% more motion than the original 1.08; applied over the full composition duration |
| translateX | 2% | -2% | Gentle horizontal drift |
| translateY | -1% | 1% | Gentle vertical drift |

### Implementation

```tsx
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

const KenBurnsWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.18], {
    extrapolateRight: "clamp",
  });

  const translateX = interpolate(frame, [0, durationInFrames], [2, -2], {
    extrapolateRight: "clamp",
  });

  const translateY = interpolate(frame, [0, durationInFrames], [-1, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        transform: `scale(${scale}) translate(${translateX}%, ${translateY}%)`,
        transformOrigin: "center center",
      }}
    >
      {children}
    </div>
  );
};
```

Wrap any background layer with `<KenBurnsWrapper>` to apply the effect. The scale
overshoots slightly (1.18 vs 1.08) to ensure the motion is perceptible on small
phone screens — the original 1.08 was too subtle for Instagram viewing.

## Ambient Audio Layer

Add a low-volume ambient audio track to every composition. This dramatically improves
watch time — silent reels or reels with only music feel "hollow."

### Usage

```tsx
import { Audio, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

const AmbientAudio: React.FC<{ track?: string }> = ({
  track = "audio/ambient-drone.wav",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const volume = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.6, 0.6, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return <Audio src={staticFile(track)} volume={volume} />;
};
```

### Volume curve

- **Fade in:** 0 → 0.6 over the first 15 frames (0.5s at 30fps)
- **Sustain:** 0.6 for the body of the composition
- **Fade out:** 0.6 → 0 over the last 30 frames (1s at 30fps)

The fade-out is longer than the fade-in to avoid an abrupt cut at the end.

### Available ambient tracks

Place these in `public/audio/`:

| File | Description | Best for |
|---|---|---|
| `ambient-drone.wav` | Low atmospheric hum (default) | Most formats — neutral, non-distracting |
| `ambient-ocean.wav` | Soft ocean waves | Wellness, mindfulness, calm content |
| `ambient-rain.wav` | Gentle rain | Cozy, reflective, storytelling content |
| `ambient-guitar.wav` | Soft acoustic loop | Warm, human, personal content |

Pass the track name as a prop:

```tsx
<AmbientAudio track="audio/ambient-ocean.wav" />
```

If no track is specified, `ambient-drone.wav` is used as the default.
