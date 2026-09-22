# Visual Direction

This reference defines the stable base composition for Apple App Store screenshots.
Adapt brand variables for each app, but keep the campaign rhythm stable while
using target-native device geometry.

## Core rule

Borrow the wrapper, never the app. Current code and release evidence govern
product claims. Supplied UI references govern visual content; a supplied mock is
not proof of shipped UI.
Do not copy another product's brand, text, content, controls, theme, or UI.

## Stable base composition

- Use a full-bleed brand color or quiet neutral field.
- Place one large, benefit-oriented headline above the device or window.
- Use the selected target device or native Mac window as the primary visual anchor.
- For iPhone, start with a straight-on upright phone at roughly 75% of canvas
  height and 80–84% of canvas width, with a small bottom margin.
- For iPad, use the actual tablet layout and target-native proportions rather than
  enlarging an iPhone composition.
- For Mac, use native macOS window or desktop framing rather than a phone frame.
- Keep the app screen large enough to read after App Store resizing.
- Use restrained organic shapes or edge accents only when they support the brand.
- Keep one visual rhythm across the campaign; do not redesign the device/window
  geometry for each screen.
- Use a shared font family, weight, line-break approach, and comfortable tracking
  across every headline.
- Approve one screenshot before generating the rest. Include it as the visual
  standard in every subsequent generation, with typography, colors, frame, and
  proportions locked.

## Brand variables

These may change per app:

- background and foreground colors;
- headline typeface and weight;
- logo, mascot, or supporting illustration;
- accent shapes and level of visual energy;
- screen-specific headline and target UI source; and
- target-specific device/window treatment; and
- light/dark panel alternation when it belongs to the campaign.

Changing these variables must not change the app UI or introduce unsupported
product claims.

## Optional project references

Future projects may provide local visual references beside this skill or in their
own campaign workspace. Use those references only to tune wrapper mood, headline
scale, color-field treatment, device placement, and supporting-shape ideas. They
are optional inputs, never required dependencies, and must not contribute another
product's UI or claims to the final asset.

## Review boundary

For exact-composite output, a supplied real capture inside the device or window
must remain unchanged. For generated-bitmap output, the user must explicitly
accept the possibility of UI redraw; inspect every result and label any fidelity
risk. Generate or revise the complete raster instead of patching frames, icons,
or text over a rejected generated raster. Move rejected or exploratory outputs to
`image-gen-direction`, never the approved set.
