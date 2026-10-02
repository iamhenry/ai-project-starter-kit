# Stack

Pinned. Do not substitute. Both starters already include the base set.

## CDNs

```html
<!-- Fonts (from design.md) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cal+Sans&family=Inter:wght@400..600&display=swap" rel="stylesheet">

<!-- daisyUI 5 + themes, then the Tailwind v4 browser build -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/themes.css" rel="stylesheet" type="text/css" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>

<!-- Icons: Iconify web component, Tabler set by default -->
<script src="https://cdn.jsdelivr.net/npm/iconify-icon@3/dist/iconify-icon.min.js"></script>

<!-- Gestures and drag (only when the idea needs them) -->
<script src="https://cdn.jsdelivr.net/npm/interactjs@1.10.28/dist/interact.min.js"></script>
```

```js
// Motion (vanilla, not Framer Motion). Exports animate, plus press, hover, inView, scroll.
import { animate } from "https://cdn.jsdelivr.net/npm/motion@13.5.0/+esm";
```

## Icons

Use Tabler icons through the Iconify web component. It loads each icon on demand, inherits `currentColor`, and sizes with font size or width and height.

```html
<iconify-icon icon="tabler:heart" width="20" height="20" aria-hidden="true"></iconify-icon>
```

- Outline is the default style; filled variants end in `-filled` (`tabler:heart-filled`). Browse names at [tabler.io/icons](https://tabler.io/icons).
- Another set only when the idea calls for it, same component with a different prefix (`heroicons:`, `iconoir:`, `ion:`, `mingcute:`, `feather:`). Keep one set per prototype.
- Icons need a network connection on first load, like the rest of the stack. For an offline handoff, paste the SVG inline.

## Known pitfalls

- **Motion's vanilla build has no drag, pan, or swipe.** Use interact.js to read the pointer and Motion to animate the result. interact.js is a classic script exposing the global `interact`, so modules can use it once the script has loaded.
- **interact.js does not set `touch-action`.** Set it in CSS on every gesture surface, or the browser scrolls instead of dragging.
- **Do not use use-gesture.** Its jsDelivr `+esm` build is broken and it has not been released since 2024.
- **Tailwind browser build** scans the DOM at runtime, so classes added by JavaScript work. Only `<style type="text/tailwindcss">` is processed by Tailwind; plain `<style>` is plain CSS.
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
