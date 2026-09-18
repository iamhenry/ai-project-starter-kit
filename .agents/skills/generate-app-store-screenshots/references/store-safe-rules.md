# Store-Safe Screenshot Rules

## Upload-Safe Means Real UI

The visible app screen must match what the shipped app can render. If a tool
generates a new approximation of the UI, it is not upload-safe.

This workflow targets Apple App Store screenshots. iPhone portrait is the default;
iPad and Mac are supported only when explicitly selected with their own current
requirements, captures, geometry, and review pass. Do not silently reuse iPhone
dimensions or framing for another Apple target.

## Safe Enhancements

- Seed richer demo data in code or backend fixtures.
- Use real simulator/device screenshots or native Mac captures as the product layer.
- Add external marketing headline, background, badges, and device framing.
- Crop or rotate the whole device/screenshot layer when appropriate for the target.
- Increase figures only by changing app data before capture.

## Unsafe Enhancements

- Redrawing app UI with image generation.
- Switching to a theme the app does not support.
- Adding controls, tabs, features, or settings that do not exist.
- Fixing app errors by painting over them.
- Leaving unreadable or hallucinated UI text.

## Triage Checklist

- Required pixel size confirmed.
- Apple target, device class/window type, orientation, and App Store surface confirmed.
- Real app screenshot layer preserved.
- Shipped theme preserved.
- No private data.
- No test-only failures or unavailable placeholders.
- Store copy is truthful and visible claims are supported.
- Contact sheet reviewed before selecting final assets.

## Folder Labels

- `raw`: real captures only.
- `store-safe-exact`: upload candidates using real target screenshots.
- `image-gen-direction`: visual exploration, not upload candidates.
