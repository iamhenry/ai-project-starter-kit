# Mobile / PWA

Touch-first and installable, for phones and tablets. Start from `assets/starter-mobile.html`. Verify at 390 × 844 (phone) and 820 × 1180 (tablet portrait), then rotate the tablet to landscape.

## Responsive: phone and tablet

Design the phone layout first, then let it open up on tablets. Do not stretch a phone column across a tablet.

| Width | Layout |
|---|---|
| Phone (< 768 px) | One column. Bottom tab bar. Deeper screens push over the list with a back control. |
| Tablet (≥ 768 px) | Side rail replaces the bottom tabs. List and detail sit side by side; selecting an item fills the detail pane instead of pushing a screen. Sheets become centered dialogs. |

- Use Tailwind breakpoints (`md:`) for layout and one `matchMedia("(min-width: 768px)")` check in the script for behavior that differs (push a screen vs fill a pane). Re-render when it changes so rotation works.
- Content line length stays readable on tablets (about 70 characters); use the extra width for side-by-side context, not wider text.
- Touch targets stay at least 40 × 40 px at every width.

## App shell

- Full-bleed, not a phone frame. `min-h-dvh`. The document scrolls, not an inner box.
- Sticky top bar; fixed bottom navigation on phones; leave bottom padding so content clears it.
- `viewport-fit=cover` plus `env(safe-area-inset-*)` on the top bar, bottom bar, side rail, sheets, and edge-pinned controls.
- Primary actions within thumb reach on phones; on tablets, keep them near the content they act on.

## Native feel (browser features, no libraries)

Use what the browser already does natively before reaching for a library.

- **Home screen.** `apple-mobile-web-app-capable`, `mobile-web-app-capable`, `apple-mobile-web-app-title`, `apple-mobile-web-app-status-bar-style`, and `color-scheme`. Give `theme-color` one meta per scheme (`media="(prefers-color-scheme: light)"` and `dark`) so the status bar is right on first paint, then update both when the in-app theme toggles. A 180 × 180 `apple-touch-icon` can be drawn on a canvas at startup and set as a data URL, so no image file is needed. Optionally show in settings whether it is running from the home screen (`matchMedia("(display-mode: standalone)")` or `navigator.standalone`) and how to add it.
- **Native inputs.** `type="date"`, `"time"`, and `<select>` open the platform's own pickers. Add `autocapitalize`, `enterkeyhint`, `inputmode`, and `autocomplete` so the keyboard fits the field.
- **Keyboard and viewport.** Add `interactive-widget=resizes-content` to the viewport meta so the on-screen keyboard shrinks the layout on Android, as it does on iOS, and bottom-pinned fields stay visible. Never disable zoom (`user-scalable=no`, `maximum-scale=1`); fix the cause instead (fields under 16 px). Set `-webkit-text-size-adjust: 100%` so text does not inflate in landscape.
- **Press feedback on touch-down.** Controls respond the moment the finger lands: style `:active`, or use `pointerdown` in script, not `click`. Keep it short (about 100 to 160 ms, ease-out); timing comes from `animation-principles`.
- **Hover only with a real pointer.** On touch, a tapped element keeps its hover style until the next tap. Put custom `:hover` rules inside `@media (hover: hover) and (pointer: fine)`. Tailwind v4's `hover:` variant and daisyUI already do this; hand-written CSS does not.
- **Capability, not device.** Decide input behavior with `(hover)` and `(pointer)` media queries, never user-agent sniffing. Width decides layout; capability decides touch versus mouse behavior. Touch and mouse can coexist (tablets with trackpads, touchscreen laptops), so support both at once.
- **Native scrolling first.** A swipeable row of cards or a pager is usually `overflow-x: auto` with `scroll-snap-type: x mandatory` on the track and `scroll-snap-align: start` on items. The browser's own scroll physics beat a custom gesture. Reach for interact.js only when the gesture does more than scroll.
- **Screen transitions.** Wrap screen changes in `document.startViewTransition()` where supported: deeper screens push in from the right while the screen underneath shifts about 30 % and dims; going back reverses it; same-level tabs cross-fade. Give persistent chrome (top bar, tab bar) its own `view-transition-name` so it stays still, and give a shared element the same name on both screens so it travels between them. Skip it during gestures (the finger already moved the screen) and with reduced motion, and keep the Motion fallback for browsers without it.
- **Haptics.** `navigator.vibrate` where it exists. iPhone Safari has none, but toggling a hidden native switch (`<input type="checkbox" switch>` inside a label, clicked from a user action) gives a light system haptic on recent iOS. Wrap both in one `haptic()` helper and call it for commits, not for every movement.
- **System font option.** A setting that swaps the brand fonts for `-apple-system, system-ui` lets the user compare against a stock platform feel.
- **Touch polish.** `touch-action: manipulation` on `html` (no double-tap zoom); no text selection or long-press callout on controls; inputs at 16 px on touch screens so Safari does not zoom into them; `overscroll-behavior: contain` on sheets and scrolling panels; `overscroll-behavior-y: none` and `-webkit-tap-highlight-color: transparent` on `html, body`.
- **Sound.** Optional; follow the sound rules in `stack.md`. Phones may mute web audio with the ring/silent switch, which matches native behavior.

Haptics, home-screen launch, and the silent switch can only be confirmed on a real device. Say so when reporting.

### Never ship (mobile self-check)

| Never | Instead |
|---|---|
| `user-scalable=no` or `maximum-scale=1` | 16 px fields |
| Hand-written `:hover` outside a hover-capable media query | `@media (hover: hover) and (pointer: fine)` |
| `100vh` for the app shell or bottom-pinned UI | `100dvh` (`min-h-dvh`) |
| Press feedback only on `click` | `:active` or `pointerdown` |
| `touchmove` with `preventDefault()` to stop page bounce | `overscroll-behavior` |
| `user-select: none` on body text | Only on controls |
| `touch-action: none` on something the user must scroll past | `pan-x` or `pan-y` |
| `env(safe-area-inset-*)` without `viewport-fit=cover` | Add it to the viewport meta, or the insets are 0 |
| One `theme-color` for both schemes | One per `prefers-color-scheme`, updated on toggle |
| User-agent or width checks to detect touch | `(hover)` and `(pointer)` media queries |

## Navigation and overlays

- Screens are sections toggled by one `go(name)` function; deeper screens show a back control on phones.
- Modals use `<dialog>` with `showModal()` (top layer, Esc to close). On phones, bottom sheets use daisyUI `modal modal-bottom md:modal-middle` with a visible grab bar.
- Toasts sit below the top safe area and never block input except for their own action button.

## Gestures

Gestures are where mobile prototypes earn their feel. Use the `animation-principles` skill, especially its gesture reference, for the mechanics and recipes (swipe actions, reorder, drag to dismiss, edge swipe back, pan and zoom, long press). interact.js reads the pointer; Motion animates the outcome. Every gesture also needs a tap path.

## Motion on mobile

Follow the `animation-principles` skill. Screen pushes follow the platform (see View Transitions above), with a short slide as the fallback; lists may stagger in on first view, not on every return; everything stays interruptible by the next touch.

## Testing on a real phone

Storage and installability depend on how the file is opened (see `stack.md`). Opening the file from disk works on a desktop browser. On a phone or tablet, the page must be served from a real origin without a sandbox policy. Choose a host with the user; never open public ports or publish without permission.
