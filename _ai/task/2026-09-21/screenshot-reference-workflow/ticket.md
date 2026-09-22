# Screenshot reference workflow

## Approved requirements

1. Use supplied assets. Remove simulator/build capture instructions. Ask for
   missing references instead of setting up the app.
2. Generate or revise one complete raster with the role-labeled UI mock,
   approved campaign image, and brand assets together. Never patch frames,
   icons, or text over a rejected image.
3. Approve one screenshot first, then include it as the visual standard in every
   subsequent generation. Lock typography, colors, frame, and proportions.
4. Inspect every final exported image against the approved example for
   typography, colors, complete UI, and legibility. Never stretch an image to
   fit dimensions.

Retain exact-composite as an explicit opt-in, truthful generated-UI warnings,
the caption workflow, and Apple target support.

## Repair constraints

- Allow proportional resizing. Never stretch; regenerate when the aspect ratio is
  incompatible, then inspect final quality.
- Treat the role-labeled UI mock, approved campaign image, and relevant brand
  assets as generation inputs, not a collage. The first dry run has no approved
  campaign image yet.
- Scope complete-raster and no-patch rules to generated-bitmap. Keep exact-
  composite opt-in and make generated-bitmap the default with accepted fidelity
  risk.
- Only supplied real captures qualify for exact-upload fidelity. Mocks are not
  proof of shipped UI. Product claims follow current code/release evidence;
  supplied UI references govern visual content.

## Boundaries

- Documentation and skill wording only.
- No cleanup redesign, backend work, app edits, global installation changes,
  image generation, or new evaluation infrastructure.
- User authorized committing the scoped changes and opening a PR. No merge or
  global installation update is authorized.
- Replace contradictory lines minimally. Do not rewrite the whole skill.

## Verification contract

The user requested one direct correctness check, not double verification.
Review the diff against the four approved instructions and bundled references,
then run `git diff --check`. Actual image-generation quality remains unverified;
no image generation is required for this docs-only patch.
