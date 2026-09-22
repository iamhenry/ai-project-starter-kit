# Apple Platform Requirements

Use this reference to choose the Apple screenshot profile. It deliberately does
not hard-code pixel dimensions: Apple and App Store Connect requirements can
change, so confirm the current specification for the selected target at preflight
and again before delivery.

Official source:

- <https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/>

## Target profiles

### iPhone — default

- Use portrait iPhone App Store screenshots unless the user selects another
  supported orientation.
- Use a supplied real iPhone capture for exact-upload fidelity. A supplied mock
  can guide generated-bitmap composition but is not proof of shipped UI.
- Store sources under `store/ios/screenshots/`.
- Use the stable upright-phone composition as the starting profile.

### iPad — deliberate extension

- Select iPad explicitly during preflight.
- Use a supplied iPad layout, not a resized iPhone layout. Exact-upload fidelity
  requires a supplied real capture; mocks may guide generated-bitmap composition.
- Confirm the required orientation and dimensions for the selected iPad class.
- Store sources under `store/ipad/screenshots/`.
- Preserve the campaign hierarchy while adapting device proportions and layout.

### Mac — deliberate extension

- Select Mac explicitly during preflight.
- Use a supplied real macOS app or window capture for exact-upload fidelity; do
  not place Mac UI in a phone frame. A supplied mock can guide generated-bitmap
  composition but is not proof of shipped UI.
- Confirm the current Mac screenshot dimensions and orientation requirements.
- Store sources under `store/macos/screenshots/`.
- Use native window or desktop framing while preserving the campaign's headline,
  palette, and visual rhythm.

## Rules for every target

- Record the selected target, current requirements source, dimensions, orientation,
  source asset, output path, and validation result in the campaign receipt.
- Current code and release evidence govern product claims. Supplied real captures
  are the authoritative product surface for exact-upload fidelity; supplied UI
  mocks guide visual content but do not prove shipped UI.
- Treat a generated redraw as a fidelity tradeoff, not as proof of exact UI.
- If a target's current requirements or source asset are unclear, stop and ask
  rather than guessing.
