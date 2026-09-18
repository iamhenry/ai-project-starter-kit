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
- Capture the actual iPhone UI from the running app or an authoritative source
  image.
- Store sources under `store/ios/screenshots/`.
- Use the stable upright-phone composition as the starting profile.

### iPad — deliberate extension

- Select iPad explicitly during preflight.
- Capture the actual iPad layout when the app supports one; do not upscale or
  stretch an iPhone capture into an iPad listing asset.
- Confirm the required orientation and dimensions for the selected iPad class.
- Store sources under `store/ipad/screenshots/`.
- Preserve the campaign hierarchy while adapting device proportions and layout.

### Mac — deliberate extension

- Select Mac explicitly during preflight.
- Capture the native macOS app or window; do not place Mac UI in a phone frame.
- Confirm the current Mac screenshot dimensions and orientation requirements.
- Store sources under `store/macos/screenshots/`.
- Use native window or desktop framing while preserving the campaign's headline,
  palette, and visual rhythm.

## Rules for every target

- Record the selected target, current requirements source, dimensions, orientation,
  capture source, output path, and validation result in the campaign receipt.
- Use target-specific real UI as the authoritative product surface.
- Treat a generated redraw as a fidelity tradeoff, not as proof of exact UI.
- If a target's current requirements or capture source are unclear, stop and ask
  rather than guessing.
