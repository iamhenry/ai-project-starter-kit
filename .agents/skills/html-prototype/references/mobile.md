# Mobile / PWA

Touch-first, phone-sized, installable. Start from `assets/starter-mobile.html`. Verify at a 390 × 844 viewport.

## App shell

- Full-bleed, not a phone frame. `min-h-dvh`, content column `max-w-md mx-auto` so it also reads on a laptop.
- The document scrolls, not an inner box. Sticky top bar; fixed bottom navigation; leave bottom padding so content clears it.
- `viewport-fit=cover` plus `env(safe-area-inset-*)` on the top bar, bottom bar, sheets, and edge-pinned controls.
- `apple-mobile-web-app-capable`, `mobile-web-app-capable`, and a `theme-color` meta that updates with the theme.
- `overscroll-behavior-y: none` and `-webkit-tap-highlight-color: transparent` on `html, body`.
- Optional for real installs: a web app manifest and a 180 × 180 apple-touch-icon beside the HTML file.
- Touch targets at least 40 × 40 px; primary actions within thumb reach.

## Navigation and overlays

- Screens are sections toggled by one `go(name)` function; deeper screens show a back control.
- Modals use `<dialog>` with `showModal()` (top layer, Esc to close). Bottom sheets use daisyUI `modal modal-bottom` with a visible grab bar.
- Toasts sit below the top safe area and never block input except for their own action button.

## Gestures

Gestures are an enhancement: every gesture needs a tap path that does the same thing. use-gesture reads the pointer; Motion animates the outcome.

### Mechanics that apply to every gesture

- **Own the axis.** Set `touch-action` on the gesture surface: `pan-y` for horizontal gestures inside a vertically scrolling page, `none` for handles and free-form canvases.
- **One owner per pointer.** Container-level gestures (for example, a screen edge swipe) use `pointer: { capture: false }` so they do not steal the pointer from child gestures. Handles call `stopPropagation()` on `pointerdown` so parent gestures never start.
- **Swallow the click after a drag.** A drag ends with a native click. Add a one-shot capture-phase click blocker on release when movement exceeded a few pixels, and remove it after about 100 ms so the next real tap works.
- **Resume from where it is.** Use `from: () => [currentX, currentY]` and `offset` so a partially open element continues from its position.
- **Resistance, not walls.** Past a limit, move a fraction of the pointer distance (rubber band) instead of stopping dead.
- **Settle with Motion.** Animate numbers with `onUpdate` that writes the transform, using springs with no bounce, about 300 ms.
- **Arm, then commit.** For actions that fire on release, show a clear armed state once the threshold is crossed (label change, color fill, light haptic) and let the user drag back to cancel.
- **Undo over confirm** for fast destructive gestures; keep the confirm modal for the tap path.
- **Haptics:** `navigator.vibrate` works on Android only. Treat it as a bonus.
- **Platform conflicts:** in a mobile browser tab, the browser's own back swipe can win at the left edge. Installed home-screen apps do not have this conflict.

### Recipes

Adapt to the idea; these are shapes, not fixed components.

- **Two-stage swipe on an item** (rows, cards, tiles). A short swipe reveals action buttons to tap; a long swipe past about half the width commits the action on release. Each direction maps to one action, and only that side's color shows underneath.
- **Drag to reorder.** Start from a visible handle, not a long press, to avoid fighting scroll. Lift the item (slight scale, raised surface), slide siblings out of the way as the target index changes, settle into the slot, then commit the new order through the app API.
- **Drag to dismiss.** Sheets, cards, and overlays follow the finger and close past a distance or on a fast flick; otherwise they spring back. Limit the start area (grab bar, header) so forms inside stay usable.
- **Edge swipe back.** Only on screens that have a back action, only when the drag starts within about 24 px of the left edge. The screen follows the finger and fades slightly; commit past about 30 % width or on a flick.
- **Pan and zoom** for canvases, maps, and boards: `DragGesture` for pan and `PinchGesture` for zoom, clamped to sensible bounds.
- **Long press** for secondary menus when no visible affordance fits. Pair it with a visible alternative.

## Motion on mobile

Screen transitions slide by a few pixels in the navigation direction. Lists may stagger in on first view. Confirm taps with a quick scale. Keep everything interruptible by the next touch.

## Testing on a real phone

Storage and installability depend on how the file is opened (see `stack.md`). Opening the file from disk works on a desktop browser. On a phone, the page must be served from a real origin without a sandbox policy. Choose a host with the user; never open public ports or publish without permission.
