# Dashboard design — Cal.com inspiration

Applied from the user's supplied **Design System Inspiration of Cal.com**.
This is the styling contract for `dashboard.template.html`, not a second theme.

## Theme and palette
- White canvas and surfaces; charcoal `#242424` headings and primary controls.
- Deep text `#111111`, gray labels `#898989`; use darker gray for small readable text.
- Light-gray `#f5f5f5` supporting surfaces. No gradients, decorative imagery, or brand colors.
- Blue is reserved for links (`#0099ff`) and visible keyboard focus (`#3b82f6`).
- Trend is grayscale. Words, not color, distinguish up/down/flat/insufficient evidence.

## Typography
- Cal Sans for display and headings, 600 weight, 1.10 line height, tight at large sizes.
- Inter for body and UI, weights 400–600, 14–16px, comfortable 1.5 line height.
- Heading 48px desktop / 36px mobile; card heading 24px. Cal Sans below 24px
  would require +0.2px tracking, so use Inter for the small dashboard labels instead.
- Prefer locally installed fonts; system sans-serif fallback keeps the dashboard offline
  and avoids external font requests. Do not claim the custom fonts are bundled.

## Cards and controls
- Card radius 12px; buttons 8px; comfortable touch targets of at least 44px.
- Use the supplied ring/contact/diffused shadow stack:
  `0px 1px 5px -4px rgba(19,19,22,.7), 0px 0px 0px 1px rgba(34,42,53,.08), 0px 4px 8px rgba(34,42,53,.05)`.
- Buttons: charcoal with white text. Avoid hover motion; a small opacity change is enough.
- No heavy dark shadows. Ring shadows contain cards without adding layout borders.

## Layout and responsive behavior
- Centered content, maximum 1200px; 8px spacing base, 24px card padding.
- 80px desktop section spacing, 48px mobile. Stack summary cards below 640px.
- Full-width SVG trend, then run history. History may scroll horizontally on narrow screens.
- No decorative navigation, illustration, or unnecessary dashboard controls.

## What the chart means
- Points show expected-finding agreement on the selected saved tuning case.
- Only connect comparable points: same case definition, same input, and same resolved
  models. Different checker versions may then be compared, not different task difficulty.
- Legacy points without fingerprints remain in history but do not imply a comparable trend.
- One comparable point is a baseline, not improvement. Never invent sample history.
- No animation or smoothed curves: show actual measurements and honest gaps.
