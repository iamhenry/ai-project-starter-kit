# Motion recipes

Reusable motion, chosen by what triggers it rather than by component. A recipe that works for "anything that opens" works for a dialog, a popover, a menu, or a custom panel.

Recipes run on states the browser already tracks: pressed, open, checked, just appeared, closing. Nothing has to label elements with state, so there is no glue script to maintain. Timing and easing come from the `animation-principles` tokens (`DUR`, `EASE`); each recipe names the principle it follows.

## Which tool

| The change | Use | Why |
|---|---|---|
| Something is pressed, opens, closes, appears, disappears, or is checked | CSS, written as Tailwind classes (recipes below) | The browser triggers it; no script; it reverses on its own |
| Items in a list are added, removed, or reordered | AutoAnimate (optional, see `stack.md`) | One call animates every later change to that list |
| The finger drives it, it needs a spring with velocity, it must stop mid-way and turn around, or it is a sequence | Motion | Physics, interruption, and choreography are beyond CSS |
| One element becomes another across screens | View Transitions first (see the domain reference), Motion as fallback | Native, and continuity comes free |

Start at the top row and move down only when the row above cannot do it.

## Browser triggers

| Trigger | CSS | Tailwind variant |
|---|---|---|
| Pressed | `:active` | `active:` |
| Just appeared (inserted, or no longer `display: none`) | `@starting-style { … }` | `starting:` |
| Open (`<dialog>`, `<details>`, popover) | `[open]`, `:popover-open` | `open:` |
| Closing or hiding | transition back to the closed values; `transition-behavior: allow-discrete` keeps it visible until the transition ends | `transition-discrete` |
| Checked (checkbox, toggle, radio) | `:checked` | `checked:` |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` | `motion-reduce:` / `motion-safe:` |

## Already handled

**daisyUI does these on its own.** Don't redo them, just use the component:
- Modal: the backdrop and box fade and scale in and out.
- Modal sheets (`modal-bottom`): slide up and down.
- Dropdown: fades and scales in and out.
- Drawer: slides.
- Checkbox and toggle: animate on change.
- `collapse`: expands and collapses.
- `swap`: swaps icons, with `swap-rotate` and `swap-flip`.

**The starters add four recipes in their `<style>` block** (a "Motion recipes" section, off under reduced motion):
- **Press:** `.btn` and `[data-press]` shrink to 0.97 on touch-down.
- **Dialog and sheet:** a softer settle in, then a quicker exit.
- **Menu:** dropdowns use the same easing as dialogs.
- **Toast:** slides and fades in, and out again when hidden.

Give `data-press` to any custom pressable element (a card, a list row, an icon) and it gets the same press.

## Recipes

### Press (#8 squash, #16 first pixel)

```html
<div data-press class="card …">…</div>
<!-- or inline, for elements outside the starter -->
<div class="transition-[scale] duration-100 active:scale-[.97] motion-reduce:transition-none">…</div>
```

On iOS Safari, `:active` only fires on touch-down when the page has a touch listener. The mobile starter registers one.

### Appear and disappear: anything shown by removing `hidden` (#2 easing, #14 reversible)

```html
<div class="hidden transition-all transition-discrete duration-200 ease-out
            starting:opacity-0 starting:translate-y-2
            [&.hidden]:opacity-0 [&.hidden]:translate-y-2">…</div>
```

Toggle the `hidden` class; it animates both ways. Use this for inline messages, empty states, revealed fields, and banners.

### Open and close: dialogs and popovers not styled by daisyUI (#5 staging, #14 reversible)

```html
<div popover class="opacity-0 scale-95 open:opacity-100 open:scale-100
                    starting:open:opacity-0 starting:open:scale-95
                    transition-all transition-discrete duration-200 ease-out">…</div>
```

The same classes work on `<dialog>`. Set the origin to where it grows from (`origin-top`, `origin-top-right`), so a menu opens out of its button (#13 spatial consistency).

### Toast (#14 reversible)

In the starters. For a toast outside `.toast`, use the appear recipe. A top toast drops from above (`starting:-translate-y-2`); a bottom toast rises from below.

### Sliding indicator: tabs and segmented controls (#13 spatial consistency)

The one recipe that needs a few lines of script. CSS cannot move one highlight between siblings on its own.

```html
<div class="pill-group relative" role="tablist">
  <span class="tab-glider" aria-hidden="true"></span>
  <button class="tab relative tab-active">Day</button>
  <button class="tab relative">Week</button>
</div>
<style>
  .tab-glider { position: absolute; inset-block: 6px; left: 0; border-radius: 9999px; background: var(--pill-active);
    transition: translate .25s cubic-bezier(.22,1,.36,1), width .25s cubic-bezier(.22,1,.36,1); }
  .pill-group:has(.tab-glider) .tab-active { background: transparent; box-shadow: none; }
</style>
<script>
  function glide(group) {
    const on = group.querySelector(".tab-active"), g = group.querySelector(".tab-glider");
    if (on && g) { g.style.translate = `${on.offsetLeft}px 0`; g.style.width = `${on.offsetWidth}px`; }
  }
  // Call glide(group) after changing the active tab, and once on load.
</script>
```

### Lists (#6 overlapping action)

```js
import autoAnimate from "https://cdn.jsdelivr.net/npm/@formkit/auto-animate@0.10.0/+esm";
autoAnimate(listEl, { duration: 200 });
```

- AutoAnimate animates the children it sees added, removed, or moved. It needs the same DOM nodes to persist between renders. If `render()` rebuilds the list with `innerHTML`, every row counts as new. In that case, update rows by key, or keep the starter's `fx.list` stagger for the first load only (#4 frequency).
- It honors reduced motion by default.
- Don't combine it with Motion on the same rows.

## When to reach for Motion

- Drags, swipes, and flicks: momentum, velocity handoff, rubber band. See `animation-principles` and its gesture reference.
- Springs that must start from the current velocity, or animations that stop mid-way and reverse from where they are.
- Sequences and staggers beyond a list's first load, SVG paths drawing, and counting numbers.

## Handoff

Name the recipes used in the handoff comment block, for example "press, appear, open and close, toast, sliding indicator, lists". A production agent can map each one to its own stack: Tailwind and shadcn `animate-in` and `data-[state=open]`, or Framer Motion.
