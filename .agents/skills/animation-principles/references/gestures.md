# Gestures

Mechanics and recipes for direct manipulation. Default libraries for plain web pages: [interact.js](https://interactjs.io) reads the pointer; Motion animates the outcome.

```html
<script src="https://cdn.jsdelivr.net/npm/interactjs@1.10.28/dist/interact.min.js"></script>
<script type="module">
  import { animate } from "https://cdn.jsdelivr.net/npm/motion@13.5.0/+esm";
  // interact(...) is a global from the script above.
</script>
```

Touch gestures (swipe, edge swipe, pinch) belong to touch interfaces. On desktop, use pointer drag, drag and drop, and resize, and give every gesture a keyboard or click alternative.

## Mechanics that apply to every gesture

- **Every gesture has a tap path.** A visible button, menu item, or key does the same thing.
- **Own the axis with CSS.** interact.js does not set `touch-action`. Use `pan-y` on horizontal gestures inside a vertically scrolling page, and `none` on handles, sheets, and free-form canvases.
- **Lock the axis.** `startAxis: "x", lockAxis: "start"` for horizontal swipes, so vertical scrolling still wins when the user scrolls.
- **Limit where a drag can start.** `allowFrom: ".handle"` for handles; `ignoreFrom: "input, textarea, button"` so form controls keep working.
- **Keep your own position.** Track the element's offset in a variable, add `event.dx`/`event.dy` on move, and write one `transform`. Start the next drag from that value so a moving element can be caught mid-animation.
- **Stop running animations on grab.** Keep the Motion animation handle and call `.stop()` in the `start` listener.
- **Swallow the click after a drag.** A drag ends with a native click. On release, if the element moved more than a few pixels, add a one-shot capture-phase click blocker and remove it after about 100 ms so the next real tap works.
- **Settle with Motion, not interact.js inertia.** Use the release velocity (`event.velocityX`/`velocityY`, px/s) with momentum projection to choose the target, then a spring that starts at that velocity.
- **Arm, then commit.** For actions that fire on release, change the label or color once the threshold is crossed; dragging back disarms.
- **Undo over confirm** for fast destructive gestures. Keep a confirm dialog for the tap path.
- **Haptics:** `navigator.vibrate` works on Android only. Treat it as a bonus.
- **Platform conflicts:** in a mobile browser tab, the browser's own back swipe can win at the left edge. Installed home-screen web apps do not have this conflict.

## Reference implementation: drag to dismiss

Follows the finger, resists upward, uses projection to decide, and hands the release velocity to the spring.

```js
const project = (v, rate = 0.998) => (v / 1000) * rate / (1 - rate);
let y = 0, settle;
const paint = v => { y = v; sheet.style.transform = `translateY(${v}px)`; };

interact(sheet).draggable({
  startAxis: "y", lockAxis: "start", allowFrom: ".grabber",
  listeners: {
    start() { settle?.stop(); },
    move(e) { paint(y + (y + e.dy < 0 ? e.dy * 0.2 : e.dy)); },
    end(e) {
      const h = sheet.offsetHeight;
      const dismiss = y + project(e.velocityY) > h / 2;
      settle = animate(y, dismiss ? h : 0, { type: "spring", bounce: 0, duration: 0.3, velocity: e.velocityY, onUpdate: paint });
      if (dismiss) settle.then(close);
    },
  },
});
```

## Recipes

Shapes, not fixed components. Adapt them to the idea.

- **Two-stage swipe on an item** (rows, cards, tiles). A short swipe reveals action buttons to tap; a long swipe past about half the width commits on release. Each direction maps to one action, and only that side's color shows underneath. `touch-action: pan-y`, `startAxis: "x"`.
- **Drag to reorder.** Start from a visible handle (`allowFrom`), not a long press, to avoid fighting scroll. Lift the item (slight scale, raised shadow), slide siblings out of the way as the target index changes, settle into the slot, then commit the new order.
- **Drag and drop between areas** (boards, folders, trays). interact.js `dropzone` with `accept` and `overlap`; highlight the target on `dragenter`; snap into place on drop; spring back on a miss.
- **Drag to dismiss.** Sheets, cards, and overlays; see the reference implementation above.
- **Edge swipe back.** Only on screens with a back action, and only when the drag starts within about 24 px of the left edge. The screen follows the finger and fades slightly; commit past about 30 % width or on a projected flick.
- **Pan and zoom** for canvases, maps, and boards. `draggable` for pan, `gesturable` for pinch (`event.ds` for scale delta, `event.da` for rotation). Zoom around the point between the fingers, and clamp to sensible bounds with resistance.
- **Resize.** `resizable` with `edges` and `modifiers.restrictSize`; show the size while resizing.
- **Snap points** (carousels, drawers with stops, sliders). Project the release position, pick the nearest stop, spring to it with the release velocity.
- **Long press** for secondary menus when no visible affordance fits. interact.js `hold` pointer event; pair it with a visible alternative and give a slight scale-down as anticipation.
