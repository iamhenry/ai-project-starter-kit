# Stack

Pinned. Do not substitute. Both starters already include the base set.

## CDNs

Pinned. Do not substitute. Both starters already include the base set. Add an optional library only when the idea calls for it; this table is a guide, not a checklist.

| Library | What it does | Reach for it when |
|---|---|---|
| **Base (always)** | | |
| Tailwind v4 browser build | Utility classes, compiled in the browser | Always: layout and anything novel |
| daisyUI 5 + themes | Standard controls and the light/dark themes | Always: buttons, inputs, cards, navbar, tabs, drawer, modal |
| Google Fonts (from `design.md`) | Brand type | Always, unless the user asks for the system font |
| Motion 13.5 (vanilla) | Animates values and elements: tweens, springs with velocity | Always for the motion pass |
| Iconify + Tabler | Icons as a web component | Always for icons |
| **Optional** | | |
| interact.js 1.10 | Reads pointer drags, swipes, pinches, drag and drop | Gestures on mobile; drag and drop on web |
| Tone.js 15.1 | Synthesizes sound in code, no audio files | Short UI sounds that confirm actions; audio-driven ideas |
| dotLottie web 0.80 | Plays Lottie animations (designer files, or Lottie JSON built in code) | Celebrations, illustrations, empty states, animated icons; anything better drawn than coded |
| Matter.js 0.20 | 2D physics: gravity, collisions, bodies | Playful, tactile surfaces where things fall, stack, bounce, or collide |
| Three.js 0.186 | 3D scenes with WebGL | Spatial or 3D views, data in 3D, objects to turn and inspect |

Prefer the browser's own features before adding a library (native inputs, View Transitions, `<dialog>`, popovers). See the domain reference for platform-native details.

```html
<!-- Base: fonts (from design.md) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cal+Sans&family=Inter:wght@400..600&display=swap" rel="stylesheet">

<!-- Base: daisyUI 5 + themes, then the Tailwind v4 browser build -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/themes.css" rel="stylesheet" type="text/css" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>

<!-- Base: icons (Iconify web component, Tabler set by default) -->
<script src="https://cdn.jsdelivr.net/npm/iconify-icon@3/dist/iconify-icon.min.js"></script>

<!-- Optional classic scripts (globals: interact, Tone, Matter) -->
<script src="https://cdn.jsdelivr.net/npm/interactjs@1.10.28/dist/interact.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/tone@15.1.22/build/Tone.js"></script>
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.20.0/build/matter.min.js"></script>
```

```js
// Base: Motion (vanilla, not Framer Motion). Exports animate, plus press, hover, inView, scroll.
import { animate } from "https://cdn.jsdelivr.net/npm/motion@13.5.0/+esm";

// Optional, heavy: load on first use with dynamic import so they never slow the first paint.
const THREE = await import("https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js");
const { DotLottie } = await import("https://cdn.jsdelivr.net/npm/@lottiefiles/dotlottie-web@0.80.0/+esm");
```

Every optional library is an enhancement: if it fails to load, the prototype still works without that piece.

## Icons

Use Tabler icons through the Iconify web component. It loads each icon on demand, inherits `currentColor`, and sizes with font size or width and height.

```html
<iconify-icon icon="tabler:heart" width="20" height="20" aria-hidden="true"></iconify-icon>
```

- Outline is the default style; filled variants end in `-filled` (`tabler:heart-filled`). Browse names at [tabler.io/icons](https://tabler.io/icons).
- Another set only when the idea calls for it, same component with a different prefix (`heroicons:`, `iconoir:`, `ion:`, `mingcute:`, `feather:`). Keep one set per prototype.
- Icons need a network connection on first load, like the rest of the stack. For an offline handoff, paste the SVG inline.

## Sound (optional)

Use Tone.js to synthesize UI sounds in code, so no audio files are needed. Add a sound only where it confirms an action the user cares about.

- **Distinct sounds per meaning.** Each action gets its own sound, and its opposite gets a different, related one. A rising bell for done and a soft low knock for undone. Never play a sound backwards as its undo.
- **Quiet and short.** Under about 0.2 s, low volume (around -14 to -18 dB), no reverb tails. Frequent actions get the smallest sounds; a richer sound is for rare moments.
- **Every path.** Play the same sound however the action is triggered (tap, swipe, keyboard, another screen).
- **User control.** A "Sounds" setting, saved with the rest of the state.
- **Unlock on the first tap.** Browsers only start audio from a user gesture. Call `Tone.start()` on the first `pointerdown`.
- **Fail silent.** If `window.Tone` is missing, the app works without sound.
- **Throttle.** Skip a sound that starts within about 50 ms of the last, so rapid taps never stack into noise.

```js
const bell = new Tone.Synth({ oscillator: { type: "sine" },
  envelope: { attack: 0.002, decay: 0.12, sustain: 0, release: 0.06 }, volume: -16 }).toDestination();
const knock = new Tone.MembraneSynth({ pitchDecay: 0.012, octaves: 2,
  envelope: { attack: 0.001, decay: 0.09, sustain: 0, release: 0.03 }, volume: -14 }).toDestination();
document.addEventListener("pointerdown", () => Tone.start(), { once: true, capture: true });
const done   = () => { const t = Tone.now(); bell.triggerAttackRelease("E6", 0.05, t); bell.triggerAttackRelease("G#6", 0.08, t + 0.06); };
const undone = () => knock.triggerAttackRelease("A3", 0.06);
```

To let the user hear a sound without the page, render it with `Tone.Offline` and save the buffer as a WAV.

## Rich media (optional)

- **dotLottie.** `new DotLottie({ canvas, src: "file.lottie" })` for a designer's file, or `data: JSON.stringify(lottieJson)` for an animation generated in code (no asset needed). Make the first and last frames empty so one animation can play forward for an action and backward (`setMode("reverse")`, `setFrame(last)`, `play()`) for its undo. Scale size and length to frequency: a small, short version for everyday actions, a fuller one for rare moments. One shared canvas can be moved to wherever the action happened.
- **Matter.js.** Use `Render` with `background: "transparent"` and `pixelRatio: devicePixelRatio`, and theme colors read from CSS variables (rebuild when the theme changes). Run the runner only while the surface is visible; stop and clear it when leaving. Add invisible guides where falling bodies could come to rest somewhere unintended. With reduced motion, step the engine to rest before the first render instead of animating.
- **Three.js.** Render only while the view is visible (`renderer.setAnimationLoop(null)` when hidden). Read colors from CSS variables. Direct manipulation follows `animation-principles`: follow the pointer 1:1, resist past limits, and hand the release velocity to a Motion spring. Set `touch-action: pan-y` on the canvas so vertical page scroll still works.
- **Build after layout.** Canvas-based views measure their container. Create them after the surface is visible (one `requestAnimationFrame` after a screen change).

## Known pitfalls

- **Motion's vanilla build has no drag, pan, or swipe.** Use interact.js to read the pointer and Motion to animate the result. interact.js is a classic script exposing the global `interact`, so modules can use it once the script has loaded.
- **interact.js does not set `touch-action`.** Set it in CSS on every gesture surface, or the browser scrolls instead of dragging.
- **Do not use use-gesture.** Its jsDelivr `+esm` build is broken and it has not been released since 2024.
- **Tailwind browser build** scans the DOM at runtime, so classes added by JavaScript work. Only `<style type="text/tailwindcss">` is processed by Tailwind; plain `<style>` is plain CSS.
- **Pointer velocity on release.** Some gesture readers report zero velocity on the release event. Measure it yourself from the last ~100 ms of moves, and treat a pointer that stopped before lifting as zero.
- **Cal Sans ships one weight.** Use `font-weight: 400`; its regular already reads as the design's 600. Faux bold looks wrong. Check word gaps in large display text visually after applying negative tracking.

## Theme mapping (design.md → daisyUI)

Override daisyUI's built-in `light` and `dark` themes on `html[data-theme=…]` rather than inventing new themes. Map tokens by role:

| daisyUI variable | Role |
|---|---|
| `--color-base-100` | Page canvas |
| `--color-base-200` | Card / soft surface |
| `--color-base-300` | Hairline / strong surface |
| `--color-base-content` | Ink (primary text) |
| `--color-primary` / `-content` | Primary action and its text |
| `--color-info`, `-success`, `-warning`, `-error` | Semantic states |
| `--radius-field`, `--radius-box`, `--radius-selector` | Control, card, small-control radii |
| `--depth: 0`, `--noise: 0` | Flat surfaces; add explicit shadows only where the design calls for them |

Derive dark values from the design's dark surfaces when it only documents light. Keep extra roles (muted text, pill background, press color) as custom properties beside the daisyUI ones.

## Enhancement hooks

The app script declares no-op hooks and calls them at the right moments. Modules replace them.

```js
window.fx = { screen(){}, list(){}, check(){}, toast(){} /* add what the idea needs */ };
// e.g. go(name) calls window.fx.screen(el, prev, name) after switching screens
// Separate hook groups keep layers independent, e.g. window.sfx (sound), window.media (rich media).
```

Motion module pattern:

```js
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const ease = [0.22, 1, 0.36, 1];
  Object.assign(window.fx, {
    screen(el) { animate(el, { opacity: [0, 1], x: [8, 0] }, { duration: 0.2, ease }); },
  });
}
```

Timing, easing, springs, and what deserves motion come from the `animation-principles` skill.

## Persistence (localStorage)

- One versioned key per prototype, e.g. `"<slug>:data"`, holding the whole state as JSON. Theme choice in its own key.
- Save at the chokepoints every change already passes through (render functions, the one change handler), not scattered across call sites.
- Load once at startup; fall back to seed data when nothing is saved. Keep a "Restore sample data" action.
- If data is time-based (daily habits, streaks, schedules), reconcile elapsed time on load.
- Detect whether storage works and say so in the UI. Storage throws in sandboxed pages, so a silent `try/catch` makes saving look broken:

```js
const canSave = (() => { try { localStorage.setItem("<slug>:test", "1"); localStorage.removeItem("<slug>:test"); return true; } catch { return false; } })();
```

Where storage does not persist:
- Pages served with `Content-Security-Policy: sandbox` (no `allow-same-origin`), which some in-app preview hosts use. The page's origin is `null`.
- Quick Look style previews (for example, opening the file from a phone's file browser).
- Data is per origin: a moved or copied file, a different browser, or an installed home-screen web app each start fresh.
