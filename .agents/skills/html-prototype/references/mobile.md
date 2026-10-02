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
- `apple-mobile-web-app-capable`, `mobile-web-app-capable`, and a `theme-color` meta that updates with the theme.
- `overscroll-behavior-y: none` and `-webkit-tap-highlight-color: transparent` on `html, body`.
- Optional for real installs: a web app manifest and a 180 × 180 apple-touch-icon beside the HTML file.
- Primary actions within thumb reach on phones; on tablets, keep them near the content they act on.

## Navigation and overlays

- Screens are sections toggled by one `go(name)` function; deeper screens show a back control on phones.
- Modals use `<dialog>` with `showModal()` (top layer, Esc to close). On phones, bottom sheets use daisyUI `modal modal-bottom md:modal-middle` with a visible grab bar.
- Toasts sit below the top safe area and never block input except for their own action button.

## Gestures

Gestures are where mobile prototypes earn their feel. Use the `animation-principles` skill, especially its gesture reference, for the mechanics and recipes (swipe actions, reorder, drag to dismiss, edge swipe back, pan and zoom, long press). interact.js reads the pointer; Motion animates the outcome. Every gesture also needs a tap path.

## Motion on mobile

Follow the `animation-principles` skill. Screen pushes slide a few pixels in the navigation direction; lists may stagger in on first view; everything stays interruptible by the next touch.

## Testing on a real phone

Storage and installability depend on how the file is opened (see `stack.md`). Opening the file from disk works on a desktop browser. On a phone or tablet, the page must be served from a real origin without a sandbox policy. Choose a host with the user; never open public ports or publish without permission.
