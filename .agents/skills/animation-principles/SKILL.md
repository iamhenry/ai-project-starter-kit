---
name: animation-principles
description: Baseline principles and starter snippets for UI motion and interaction feel, covering timing, easing, springs, staging, gestures, momentum, and interruptibility. Use when designing, implementing, or reviewing animations, transitions, micro-interactions, gestures, or interactive components, including during the motion and interaction passes of html-prototype.
---

# Animation Principles

A baseline for motion that feels intentional. Each principle is a rule, when to use it, when not to, and a starting snippet to refine. Snippets use vanilla [Motion](https://motion.dev) (`animate`) and plain JavaScript; translate them to the project's stack.

Sources: Raphael Salaja, [12 Principles of Animation](https://www.raphaelsalaja.com/library/12-principles-of-animation); Rauno Freiberg, [Invisible Details of Interaction Design](https://rauno.me/craft/interaction-design); Apple, [Designing Fluid Interfaces (WWDC18)](https://developer.apple.com/videos/play/wwdc2018/803/).

For gestures and direct manipulation (drag, swipe, pinch, throw), also read [references/gestures.md](references/gestures.md).

## How to apply

1. Name what each animation communicates: a state change, where something came from or went, or confirmation of an action. If it communicates nothing, do not animate it.
2. Start from the baseline tokens below. Reuse them so similar actions feel the same.
3. Check frequency: the more often an action happens, the less it should animate.
4. Make everything interruptible, and honor reduced motion.
5. Judge in the running UI, at real speed, then slowed down. Adjust from there.

## Baseline tokens

```js
const DUR  = { instant: 0.12, fast: 0.2, base: 0.3 };            // seconds; most UI motion stays under 0.3
const EASE = { out: [0.22, 1, 0.36, 1], inOut: [0.65, 0, 0.35, 1], in: [0.55, 0, 1, 0.45] };
const SPRING = { ui: { type: "spring", bounce: 0, duration: 0.3 },      // default for layout and settling
                 lively: { type: "spring", bounce: 0.2, duration: 0.45 } }; // thrown or playful elements
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
```

## Foundations

### 1. Timing
**Rule:** Short and consistent. About 120 ms for small feedback, 200 ms for most transitions, up to 300 ms for large surfaces.
**Use:** Define the scale once and reuse it.
**Avoid:** Anything the user waits on. A tooltip at 150 ms feels right; at 400 ms it annoys.

### 2. Easing (slow in, slow out)
**Rule:** Nothing in nature starts or stops instantly.
**Use:** Ease-out for things that appear or respond to input (fast start feels snappy). Ease-in for things leaving. Ease-in-out for things moving from one place to another on screen.
**Avoid:** Linear motion for UI movement. Keep linear for progress, rotation loops, and scrubbing.

```js
animate(panel, { opacity: [0, 1], y: [8, 0] }, { duration: DUR.fast, ease: EASE.out });
```

### 3. Springs
**Rule:** Springs feel physical and pick up from the current velocity, so they handle interruption gracefully.
**Use:** Settling after a drag, layout changes, anything the user can grab. No bounce for standard UI; a little bounce only for thrown or playful elements.
**Avoid:** Visible wobble on everyday controls.

```js
animate(card, { x: 0 }, SPRING.ui);
```

### 4. Frequency and novelty
**Rule:** The more often an action happens, the less it should animate.
**Use:** Command menus, context menus, keyboard navigation, and list selection appear instantly. A short fade on exit is fine. Save motion for rare or meaningful moments.
**Avoid:** Animating something people do hundreds of times a day. It turns into waiting.

### 5. Staging
**Rule:** One focal point at a time.
**Use:** Sequence complex entrances: backdrop, then panel, then the primary control. Dim or blur what is behind.
**Avoid:** Animating many unrelated things at once. Skip staging for simple interactions.

```js
animate(backdrop, { opacity: [0, 1] }, { duration: DUR.fast });
animate(sheet, { y: ["100%", "0%"] }, { ...SPRING.ui, delay: 0.04 });
```

### 6. Follow-through and overlapping action
**Rule:** Related elements do not start or stop at the same instant.
**Use:** Stagger list items 20 to 40 ms apart; let a container lead and its contents follow.
**Avoid:** Long cascades. Cap the total so the last item lands within about 300 ms.

```js
items.forEach((el, i) => animate(el, { opacity: [0, 1], y: [6, 0] },
  { duration: DUR.fast, delay: Math.min(i * 0.03, 0.15), ease: EASE.out }));
```

### 7. Anticipation
**Rule:** Hint before a significant action happens.
**Use:** Destructive or irreversible actions (hold-to-delete fills before it fires), and teaching an affordance (a card nudges to show it can be swiped).
**Avoid:** Adding delay to routine actions.

```js
// Hold to confirm: the fill is the anticipation; release early to cancel.
const fill = animate(bar, { scaleX: [0, 1] }, { duration: 0.8, ease: "linear" });
fill.then(confirmDelete);
button.addEventListener("pointerup", () => fill.stop(), { once: true });
```

### 8. Squash and stretch
**Rule:** A little deformation conveys mass and responsiveness.
**Use:** Press states, toggles, icons changing state.
**Avoid:** Anything that reads as cartoonish. Stay within a few percent.

```js
el.addEventListener("pointerdown", () => animate(el, { scale: 0.97 }, { duration: DUR.instant }));
el.addEventListener("pointerup",   () => animate(el, { scale: 1 }, SPRING.ui));
```

### 9. Arcs
**Rule:** Organic movement follows curves, not straight lines.
**Use:** Larger transitions and objects travelling a long way (an item flying into a cart).
**Avoid:** Small UI moves, where arcs read as wobble. Takes experimentation.

```js
// Animate x and y with different easings to curve the path.
animate(el, { x: dx }, { duration: 0.4, ease: EASE.inOut });
animate(el, { y: dy }, { duration: 0.4, ease: EASE.out });
```

### 10. Secondary action
**Rule:** Small flourishes support the main action without competing with it.
**Use:** A checkmark that pops after a successful save; a count that ticks up.
**Avoid:** Flourishes on failure paths or on frequent actions.

### 11. Exaggeration
**Rule:** Push a motion past realism when the message must not be missed.
**Use:** An error field that shakes; a confirmation in onboarding or an empty state.
**Avoid:** Using it often. It loses meaning.

```js
animate(field, { x: [0, -6, 6, -4, 4, 0] }, { duration: 0.35 });
```

### 12. Depth (solid drawing)
**Rule:** Layers, shadows, and perspective tell the user what is on top and what can be moved.
**Use:** Lifted items gain shadow and a slight scale; 3D rotation uses `perspective`.
**Avoid:** Inconsistent depth (an element that flattens or flips wrong mid-move).

### 13. Spatial consistency
**Rule:** Things enter from where they come from and leave toward where they live.
**Use:** A detail view grows from the tapped item; a sheet slides from the edge it is dismissed to; back navigation reverses forward navigation.
**Avoid:** Generic fades when the origin is known.

### 14. Appeal
**Rule:** The sum of the details makes an interface people want to use.
**Use:** A final pass at real speed: does it feel crafted and calm? Remove anything showy.

## Direct manipulation

Full mechanics and recipes are in [references/gestures.md](references/gestures.md).

### 15. Respond from the first pixel
**Rule:** Follow the input immediately and 1:1. Thresholds decide the outcome; they never delay the feedback.
**Avoid:** Nothing happening until a threshold, then a canned 0-to-1 animation.

### 16. Everything is interruptible
**Rule:** The user can grab, reverse, or redirect anything mid-animation, the way you can stop a page turning.
**Use:** Start gestures from the element's current value; stop running animations when a new input arrives.

### 17. Trigger timing matches intent
**Rule:** Light, reversible actions may fire during the gesture once the element reaches its logical position (revealing search, peeking a panel). Destructive actions fire only on release, however far the drag went.
**Use:** For release actions, show an armed state past the threshold (label, color, haptic) and let the user drag back to cancel.

### 18. Momentum projection
**Rule:** On release, pick the destination from where the gesture is going, not where it stopped.

```js
// From Apple's "Designing Fluid Interfaces". 0.998 = normal scroll feel, 0.99 = snappier.
const project = (velocity /* px/s */, rate = 0.998) => (velocity / 1000) * rate / (1 - rate);
const target = nearest(snapPoints, position + project(velocity));
```

### 19. Velocity handoff
**Rule:** The settle animation starts at the release velocity, so a flick carries through without a hitch.

```js
animate(position, target, { ...SPRING.ui, velocity, onUpdate: v => (el.style.transform = `translateY(${v}px)`) });
```

### 20. Resistance at limits
**Rule:** Past a boundary, move a fraction of the input (rubber band) instead of stopping dead.

```js
const rubber = (over, dim, k = 0.55) => (1 - 1 / ((Math.abs(over) * k) / dim + 1)) * dim * Math.sign(over);
```

### 21. Keep the target visible
**Rule:** A finger hides what it touches. Show a magnified value or a label above the touch point, and keep the drag alive when the finger drifts off a small control.

### 22. Fitts's law
**Rule:** Bigger and closer targets are faster to hit. Screen edges and corners are effectively infinite.
**Use:** Primary actions within thumb reach; minimum 40 to 44 px touch targets; radial or pointer-anchored menus for power actions.

## Reduced motion

When `prefers-reduced-motion` is set, replace movement with instant changes or short opacity fades. Keep gesture tracking (it is direct input), but drop decorative settling, staggers, and parallax.
