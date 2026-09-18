---
name: generate-ios-app-icon
description: Generate and validate an iOS app icon from a single 1024px master, then integrate it into an Expo or native iOS project. Use when creating, replacing, or preparing an app icon for the iOS App Store, iPhone, or iPad.
---

# Generate iOS app icon

Source workflow adapted from [prompt-to-asset app-icon](https://github.com/MohamedAbdallah-14/prompt-to-asset/blob/main/.claude/skills/app-icon/SKILL.md).

Create one strong, text-free 1024px master and let the project toolchain generate the native icon sizes. Do not generate separate platform variants: multiple independently generated icons drift visually and make review harder.

## iOS requirements

| Target | Size and format | Transparency | Safe zone |
|---|---|---|---|
| iOS App Store marketing icon | 1024×1024 PNG | Opaque; no alpha | Keep the subject in the central 824px area |
| iPhone and iPad device icons | Generated from the master by the project toolchain | Opaque | Use the same central safe zone |
| iOS 18 dark or tinted appearances | Add layered Icon Composer sources only when the project explicitly supports them | Follow the selected appearance format | Keep the mark legible at small sizes |

The system applies the rounded-square mask. Supply a square image with the background and safe-zone treatment already resolved; do not draw an extra iOS squircle unless the product design intentionally calls for one.

## Workflow

1. Inspect the project configuration and existing icon assets before generating anything. In Expo, confirm the `icon` path in `app.config.*` or `app.json`; in a native project, confirm the `AppIcon.appiconset` source of truth.
2. Confirm the brand palette, subject, background, and whether the user wants a new mark or a faithful adaptation of an existing asset. Ask before replacing an approved icon.
3. Generate or select one 1024×1024 RGBA master with no text, labels, or wordmark. Keep the subject centered, memorable, and readable at small sizes.
4. Flatten the final iOS marketing image onto its intended background so it has no alpha channel. Preserve the source master separately if later editing needs transparency.
5. Integrate the approved master through the existing project toolchain. For Expo, update the configured icon asset and let Expo/EAS prebuild generate native sizes; do not introduce a second export pipeline without a concrete need.
6. Inspect the generated result at App Store and small device sizes before calling it approved.

## Prompt scaffold

```text
A [flat vector | isometric 3D | glyph | soft gradient] app icon representing [SUBJECT, concrete noun phrase].
Bold, memorable silhouette. High contrast.
Subject fills 70–80% of the frame and is centered.
No text, no labels, no wordmark.
Palette: [#primary, #secondary, #accent].
Solid [BACKGROUND COLOR] background.
Square 1:1 composition, 1024×1024.
Designed for an iOS app icon with a clear central safe zone.
```

Use “iOS-style rounded-square backdrop” only to steer the visual direction. The final asset still needs to be a clean square master whose mask is applied by iOS.

## Validation

- The approved App Store image is exactly 1024×1024.
- The approved App Store image is a PNG with no alpha channel.
- The subject stays inside the central safe zone and is not clipped by the system mask.
- The mark remains recognizable at small preview sizes such as 16×16.
- Contrast and silhouette work on both light and dark surrounding cards.
- No text, labels, or accidental watermark appears in the icon.
- The configured Expo or native iOS path points to the approved asset.

## Output

Keep the project-specific output small and traceable:

```text
ios-app-icon/
├── master.png                 # Approved 1024×1024 iOS-ready master
├── master-source.png          # Optional editable/alpha-preserving source
└── README.md                  # Optional generation and validation notes
```

For an Expo project, the final `master.png` may instead live at the existing configured asset path, such as `assets/images/icon.png`. Do not create platform folders or native assets that the project does not use.
