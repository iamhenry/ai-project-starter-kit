# Format Templates — Production Specs Per Tier

Each format tier has specific production requirements. This file defines the exact assets,
layout, timing, and rendering parameters for each tier. When producing a Reel, look up the
tier here and follow its spec.

## Universal Specs

All Reels share these base parameters:

- **Resolution:** 1080x1920 (9:16 vertical)
- **Codec:** h264 video + aac audio
- **Format:** .mp4
- **Safe zones:** Keep text within 80% of frame width (72px padding each side) and between
  15%-85% of frame height (avoid top/bottom where Instagram overlays username and controls)

---

## T1: Meme Reel

**Duration:** 5-8 seconds
**FPS:** 25-30
**Audio:** Trending audio or original ambient (from the footage)

**Assets needed:**
- 1 stock video clip (5-10 seconds) showing something chaotic, absurd, or escalating
- 1-2 text overlays (static, do not animate)

**Layout:**
```
┌──────────────────────┐
│                      │
│   [Setup text]       │  ← top 25%, bold white, black outline/shadow
│                      │
│                      │
│   [Label text]       │  ← center, pill-shaped background box
│                      │
│  ┌────────────────┐  │
│  │  Stock footage  │  │  ← fills entire frame behind text
│  │  (the punchline)│  │
│  └────────────────┘  │
│                      │
└──────────────────────┘
```

**Typography:**
- Setup text: Bold sans-serif, white, 48-64px, black stroke/shadow for readability
- Label text: Regular weight, white on dark semi-transparent pill background

**Remotion composition:** Static text layers over video background. No animation on text.
The footage does all the visual work.

**Rendering:**
```bash
npx remotion render MemeReel --props=props.json --output=output.mp4
```

---

## T2: Quote Card

**Duration:** 5-7 seconds
**FPS:** 30
**Audio:** Calm/ambient music or trending audio (soft, not distracting)

**Assets needed:**
- 1 background image (AI-generated via fal.ai or stock photo, 1080x1920)
- 1 quote text block (the viral quote)

**Layout:**
```
┌──────────────────────┐
│                      │
│                      │
│    [Quote line 1]    │
│    [Quote line 2]    │  ← center-aligned, stacked vertically
│    [Quote line 3]    │     each phrase on its own line
│    [Quote line 4]    │
│                      │
│                      │
│      @handle         │  ← bottom, subtle, small text
└──────────────────────┘
```

**Typography:**
- Quote: Bold sans-serif, white, 52-68px. Each logical phrase on its own line.
  Line breaks at natural speech pauses, not at fixed character widths.
- Handle: Light weight, 24px, 40% opacity white

**Background generation (fal.ai):**
Prompt pattern: "[scenic description], cinematic lighting, 9:16 vertical, no text, no people"
Examples: "tropical sunset beach with palm trees", "mountain lake at dawn, misty",
"autumn forest path with golden light"

**Remotion composition:** Static background image + static text centered vertically.
The entire Reel is one frame repeated — the "video" is just enough for Instagram to
classify it as a Reel rather than a photo post.

---

## T3: Text Card

**Duration:** 6-10 seconds
**FPS:** 30
**Audio:** Soft ambient music or trending audio

**Assets needed:**
- 1 background video (timelapse: sunset, clouds, water — subtle motion, 6-10 seconds)
- 2 text blocks (myth/expectation section + reality/truth section)

**Layout:**
```
┌──────────────────────┐
│                      │
│  [Header 1 — bold]   │
│    item 1             │
│    item 2             │  ← top section: short, dismissive (3 items)
│    item 3             │
│                      │
│  [Header 2 — bold]   │
│    item 1             │
│    item 2             │
│    item 3             │  ← bottom section: long, aspirational (6-9 items)
│    item 4             │
│    item 5             │
│    item 6             │
│                      │
│      brand logo       │  ← bottom, subtle
└──────────────────────┘
```

**Typography:**
- Headers: Bold sans-serif, white, 36-44px
- Items: Regular weight, white, 24-28px, centered
- The visual asymmetry between sections IS the design — short myth list vs long reality list

**Key production note:** The myth/negative section must be visually smaller than the
reality/positive section. This asymmetry is the emotional engine — the reality side
"wins" spatially, which reinforces the message.

---

## T4: Truth Bomb

**Duration:** 7-10 seconds
**FPS:** 30
**Audio:** Contemplative ambient music

**Assets needed:**
- 1 background video (real timelapse preferred: sunset, sky, ocean — contemplative mood)
- 1 text block with 3-part argument structure

**Layout:**
```
┌──────────────────────┐
│                      │
│                      │
│  [Part 1 — fact]     │
│                      │  ← three sections, vertically stacked
│  [Part 2 — irony]    │     with breathing room between each
│                      │
│  [Part 3 — call]     │
│                      │
│                      │
└──────────────────────┘
```

**Typography:**
- Clean serif or refined sans-serif (NOT bold/heavy — this format reads as "elevated")
- White, 32-40px, center-aligned
- Good line spacing (1.6x line height minimum)
- Ellipsis (...) at the end of parts 1 and 2 to create reading momentum

**Three-part structure pattern:**
- Part 1: Factual statement that's hard to argue with
- Part 2: Ironic contrast that reveals a societal contradiction
- Part 3: Short, punchy conclusion (5-8 words maximum)

---

## P1: Functional Loop

**Duration:** 8-12 seconds (one full cycle)
**FPS:** 30
**Audio:** Calming ambient tone or gentle chime synced to the action

**Assets needed:**
- Custom illustration or animated element (breathing circle, progress ring, counter)
- Brand color palette from `production-config.json`
- 1-2 words of text maximum

**Layout:**
```
┌──────────────────────┐
│                      │
│     [Text word]      │  ← top-center, appears/fades
│                      │
│    ┌──────────┐      │
│    │ Animated  │      │  ← center, the interactive element
│    │ element   │      │     (circle, globe, ring, counter)
│    └──────────┘      │
│                      │
│                      │
│                      │
└──────────────────────┘
```

**Animation spec:**
- Main element: smooth easing (ease-in-out), breathing rhythm (~4s inhale, ~4s exhale)
- Text: fade in/out with 0.3s ease, synced to the action phase
- Particles/ambient: gentle drift, low speed, subtle opacity variation
- **Loop point:** frame N must be pixel-identical to frame 1. Design the animation to
  return to its starting state.

**Remotion composition:** React components with `useCurrentFrame()` + `interpolate()` for
all animations. The breathing/pulsing rhythm should use sine curves, not linear interpolation.

**Production cost note:** The first Reel in this format takes 4-8 hours because you're
building the Remotion composition from scratch. Every subsequent Reel using the same
template takes 15-30 minutes (swap text, colors, timing).

---

## P2: Data Viz Humor

**Duration:** 4-20 seconds (depends on the escalation arc)
**FPS:** 30
**Audio:** Sound effects synced to data changes (optional but recommended)

**Assets needed:**
- Animated data element (gauge ring, counter, EKG line, progress bar)
- Visual metaphor or 3D element (optional: brain, heart, bar chart)
- Dark background (solid black or subtle gradient)
- Brand accent color for the data element

**Layout:**
```
┌──────────────────────┐
│                      │
│   [Text/metric]      │  ← top, the changing number or label
│                      │
│    ┌──────────┐      │
│    │ Visual    │      │  ← center, the metaphor that reacts to data
│    │ metaphor  │      │     (builds, destroys, pulses)
│    └──────────┘      │
│                      │
│   [Data viz line]    │  ← bottom, supporting animation (EKG, graph)
│                      │
└──────────────────────┘
```

**Two sub-patterns:**

**Destruction arc** (like WHOOP brain):
- Start at 100% — everything intact
- Count down rapidly — visual element deteriorates/shatters
- Hit bottom — maximum destruction (the punchline)
- Loop back to 100% — seamless reset

**Gamification hook** (like WHOOP heartbeat):
- Open with interactive prompt ("Double-tap to match...")
- Escalate the metric (60 → 100 → 140 → 180)
- Visual element intensifies with each step
- End with CTA tagline

**Remotion composition:** Counter component + visual state keyed to counter value.
Use `spring()` for the destruction/escalation feel. SVG paths for EKG/graph lines.

---

## P3: Cultural Edutainment

**Duration:** 8-12 seconds
**FPS:** 30
**Audio:** Ambient/cinematic background music (subtle, not dominant)

**Assets needed:**
- Premium background footage (drone aerial, cinematic nature — real footage preferred)
- Frosted glass card overlay
- Dictionary-style text content

**Layout:**
```
┌──────────────────────┐
│                      │
│                      │
│  ┌────────────────┐  │
│  │░░░░░░░░░░░░░░░░│  │  ← frosted glass card (backdrop-filter: blur)
│  │  [Term]         │  │     semi-transparent white or dark
│  │  "def" · noun   │  │
│  │  See also: [x]  │  │
│  │  ─────────────  │  │
│  │  etym = meaning │  │
│  │  etym = meaning │  │
│  │░░░░░░░░░░░░░░░░│  │
│  └────────────────┘  │
│                      │
│                      │
└──────────────────────┘
```

**Frosted glass card spec:**
- Background: `rgba(255, 255, 255, 0.15)` or `rgba(0, 0, 0, 0.3)` depending on footage brightness
- Blur: `backdrop-filter: blur(20px)` equivalent in Remotion
- Border: 1px solid `rgba(255, 255, 255, 0.2)`
- Border radius: 16px
- Padding: 32px

**Typography within the card:**
- Term: Bold serif, 44-56px, white
- Pronunciation + part of speech: Regular, 24px, 70% opacity white
- "See also": Italic, 20px, 60% opacity white (this line should be slightly humorous)
- Divider: thin horizontal line, 40% opacity white
- Etymology: Regular, 28px, white

**Content writing pattern:**
- Term: The concept being defined (real word, niche slang, or invented compound)
- Definition: Concise, evocative, 1-2 sentences maximum
- "See also": The humor bridge — connects the highbrow term to internet culture or everyday experience
- Etymology breakdown: Optional, adds educational depth

**Remotion composition:** Video background + frosted glass `<div>` with CSS backdrop-filter
(or equivalent shader). Text can fade in with stagger (term first, then definition, then "see also")
for a reveal effect, or appear all at once for simplicity.
