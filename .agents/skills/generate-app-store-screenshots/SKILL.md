---
name: generate-app-store-screenshots
description: Run the complete evidence-first workflow for Apple App Store screenshots across iPhone, iPad, and Mac, with iPhone portrait as the default. Use whenever a user needs to plan, generate, compose, review, normalize, or prepare Apple screenshot assets. Start with shipped-product evidence and the caption skill, then create a consistent campaign with target-specific device geometry and explicit generated-UI tradeoffs.
---

# Generate App Store Screenshots

This is the primary workflow for creating a complete app-store screenshot
campaign. It owns planning, visual direction, production, review, cleanup, and
final validation. Do not create a separate wrapper around this skill for the
caption stage; read and reference
`../generate-app-store-screenshot-captions/SKILL.md` inside this workflow.

## Outcome

Produce a small, coherent set of approved screenshot assets that:

- communicate real, shipped product value;
- use a consistent campaign system across every screen;
- preserve the real app UI when upload-safe fidelity is required;
- make any generated-UI tradeoff explicit when the user accepts it; and
- are normalized and validated for the target store before delivery.

The final deliverable is the approved image set plus enough source and decision
context to reproduce the campaign for another app.

## Preflight

Use the question tool when it is available. Ask the required questions together
before doing campaign work; if it is unavailable, ask them in plain text and wait
for answers.

Required:

- Which Apple target is this campaign for: iPhone, iPad, or Mac? Default to iPhone portrait when unspecified.
- What current App Store Connect screenshot dimensions and orientation are required for that target?
- Where are the supplied target UI images, relevant brand assets, and any already-approved campaign image?
- Which shipped release or Git range should the feature audit cover?
- Is the production mode `exact-composite` or `generated-bitmap`?
- What is the desired screenshot count, if it is not obvious from the inputs?

Optional:

- Which brand colors, typeface, logo, or mascot should guide the wrapper?
- Are there visual references to study for composition only?
- Are there screen-specific cleanup notes or privacy constraints?

Sensible defaults are iPhone portrait, current App Store Connect requirements,
the supplied target UI images as source material, generated-bitmap when the user
accepts its fidelity tradeoff, one screen per generation, the locked base
composition, and no image generation until the campaign brief is explicitly
approved.

## Source-of-truth order

Use evidence in this order, resolving conflicts toward the currently shipped
release:

1. Current implementation and user-facing routes in the codebase.
2. Recent Git history, especially commits touching the relevant screens. Read
   `git log --oneline --decorate`, then use path-specific history when needed.
   Commit history helps distinguish implemented behavior from user stories,
   plans, mocks, and abandoned work.
3. Product documents such as user stories, changelog, store metadata, and release
   notes.
4. Supplied target UI images, approved campaign image, and brand assets, which
   govern visual content but not product claims.
5. User-provided visual references, which describe the wrapper and campaign mood,
   never product truth.

If a required asset or reference is missing, ask the user to provide it. Do not
launch the app, set up a simulator, build the app, or fill the gap with plausible
UI, claims, or roadmap functionality.

## End-to-end workflow

### 1. Define the campaign boundary

Confirm or infer before generating anything:

- selected Apple target and App Store surface;
- current target-specific pixel dimensions and orientation;
- number of screenshots;
- upload-safe, internal-review, or visual-direction intent;
- audience and primary user outcome; and
- brand, typography, color, and tone constraints.

Use the smallest scope that proves the product's value. iPhone portrait is the
default, but iPad and Mac are supported when deliberately selected. Read
`references/apple-platform-requirements.md` and confirm current App Store Connect
requirements instead of treating iPhone dimensions or geometry as universal.

### 2. Build the evidence-backed campaign brief

Read `../generate-app-store-screenshot-captions/SKILL.md` and use it to:

1. audit the codebase, release evidence, product documents, and Git history;
2. identify compelling production-ready features;
3. choose the benefits-first screenshot sequence;
4. write one short headline per selected screen; and
5. describe the supplied source screen, user outcome, and visual composition for each one.

Do not begin image generation until every selected screen has a named supplied
source. If a source is unavailable, ask the user to provide it. Keep claims
grounded in what the current app actually supports.

Present the feature audit, sequence, headlines, and visual notes as a draft and
wait for explicit user approval. Do not invoke an image-generation or composition
command before that approval.

### 3. Organize supplied source assets

Use the supplied target UI images, role-labeled UI mocks, approved campaign image,
and brand assets as source references. If any required reference is missing, ask
the user to provide it. Do not launch the app, set up a simulator, build the app,
or capture new screens.

Store sources separately by selected Apple target:

```text
store/
  ios/
    screenshots/
      raw/
      mockups/
        store-safe-exact/
        image-gen-direction/
  ipad/
    screenshots/
      raw/
      mockups/
        store-safe-exact/
        image-gen-direction/
  macos/
    screenshots/
      raw/
      mockups/
        store-safe-exact/
        image-gen-direction/
```

Verify supplied source dimensions immediately and label each source honestly.
A mock, even if approved, is not proof of shipped UI. Use target-native UI:
do not substitute an iPhone layout for iPad or put a Mac window inside a phone frame.

### 4. Lock one campaign system

Before making the full set, choose and document the shared visual rules:

- background and foreground palette;
- headline family, weight, size, case, line breaks, and comfortable tracking;
- headline area and target-device placement;
- target-specific device/window scale, frame treatment, and bottom margin;
- supporting shapes, blobs, badges, or other accents; and
- the rules for alternating panels or screen-specific variations.

Use optional project-provided references only for wrapper patterns: benefit-first
headline, flat color field, upright device, restrained organic accents, and a
consistent campaign rhythm. Never copy another product's brand, text, UI, data,
or unsupported claims. Read
`references/visual-direction.md` for the available direction references.

The default composition profile is a full-bleed color field, a large headline
above the target device or window, a dominant product surface, a small bottom
margin, and restrained organic accents behind it. For iPhone, start with a
straight-on upright phone occupying roughly 75% of the canvas height and 80–84%
of its width. For iPad and Mac, preserve the hierarchy and rhythm but use
target-native proportions and framing rather than reusing phone geometry. Treat
these as starting geometry, not hard-coded pixels. Adapt colors, type, logo, copy,
and accents to each app while keeping the campaign system stable.

Start with one representative dry run using the supplied UI mock and relevant
brand assets when available. There is no approved campaign image yet. Obtain
explicit approval, then include that approved campaign image as the visual
standard in every subsequent generation. Lock its typography, colors, frame, and
proportions. Do not redesign the composition independently for every screen.

### 5. Choose the production mode explicitly

Select one mode for the campaign and record it in the brief:

#### Exact compositing — explicit opt-in

- Use a supplied real capture as an unchanged image layer. A supplied mock is not
  proof of shipped UI or exact-upload fidelity.
- Add only the frame, background, headline, and truthful surrounding treatment.
- Keep this mode when exact UI text, controls, and pixel fidelity matter.

#### Generated bitmap — default with explicit creative tradeoff

- Use this by default when the user accepts that the image model may redraw
  details.
- Pass the role-labeled reference bundle described in step 6 for each image.
- Generate one screen at a time, not a loose batch with drifting art direction.
- Repeat the same typography and geometry specification across the whole set.
- Treat every output as a candidate until visual review confirms it is acceptable.

A generated bitmap that changes or hallucinates the app UI is not exact upload-safe
artwork. If the user needs upload-safe fidelity, switch to deterministic
compositing. Read `references/store-safe-rules.md` for the safety checklist.

### Codex generation adapter

Codex is an optional image-generation adapter for `generated-bitmap` mode, not a
required dependency of this skill. Keep this section high-level so the adapter can
change without rewriting the workflow:

1. Check the current Codex CLI help or tool contract before invoking it.
2. Send the screen-specific reference bundle from step 6, shared campaign prompt, and one output path per
   generation.
3. Reuse the locked headline, typography, geometry, palette, and cleanup rules for
   every screen.
4. Inspect the returned image before accepting it; a successful command is not
   evidence of visual or UI fidelity.

Do not couple this workflow to a particular image-generation skill. If Codex is
unavailable, ask whether to use exact compositing or another explicitly approved
adapter instead of silently changing the production mode.

### 6. Generate or compose one screen at a time

Use stable source filenames and a shared prompt/template with per-screen values.
For generated-bitmap mode, pass the role-labeled UI mock, approved campaign
image, and relevant brand assets together as reference inputs. The UI mock
controls product content, the approved campaign image controls wrapper
typography, colors, frame, and proportions, and brand assets control identity.
For the first dry run, omit the approved campaign image because it does not exist
yet. Do not render the references as a collage. Generate or revise one complete
raster at a time. Never patch a rejected generated raster by overlaying a frame,
icon, or text. Regenerate or revise the complete raster instead.

For each screen, provide:

- headline;
- screen source;
- background and foreground colors;
- device and composition rules;
- visible UI elements to preserve; and
- known cleanup exceptions.

For generated bitmap mode, explicitly state the shared font family, headline
weight, line breaks, and relaxed tracking. Keep the screen story and cleanup rules
specific: remove stray labels or artifacts, but never paint in an unshipped
feature or erase a truthful product state.

### 7. Review the whole campaign, then regenerate selectively

Inspect each output individually and as a contact sheet. Check:

- headline spelling, line breaks, kerning, and consistency across screens;
- device/window scale, alignment, crop, z-order, and bottom spacing;
- brand colors and contrast;
- UI fidelity, legibility, and truthful visible features;
- stray labels, duplicate elements, malformed UI glyphs, and gibberish;
- private data, unsupported claims, and accidental reference-brand content;
- whether the set reads as one campaign rather than four unrelated images;
- typography, colors, complete UI, and legibility of each export against the
  approved example.

For generated-bitmap mode, reject candidates with these problems and regenerate
or revise the complete raster. Do not edit around a rejected generated raster.
Keep rejected explorations out of the approved folder.

### 8. Clean and name the approved set

After approval:

- keep only the final candidate for each screen in the approved folder;
- preserve supplied source assets and reference assets separately;
- move or delete rejected experiments so they cannot be mistaken for deliverables;
- use stable screen names such as `screen1-home-v1.png`; and
- avoid keeping exploratory version clutter once a final is selected.

### 9. Normalize and validate for the store

Only after visual approval, export each final at the target dimensions and format.
Resize proportionally when needed. If the aspect ratio is incompatible, regenerate
the complete raster or adjust the opt-in exact-composite canvas rather than stretch
or distort it. Inspect the final export against the approved example before
presenting it. Correct dimensions alone do not prove visual quality. Validate:

- pixel dimensions and orientation;
- PNG/JPEG format and color mode;
- alpha behavior where the store requires it;
- filename and ordering;
- typography, colors, complete UI, and legibility against the approved example;
- readable text at the exported dimensions;
- no private data or unsupported claims; and
- real app UI where the selected mode promises exact fidelity.

Do not call the campaign App Store-ready while this step is outstanding.

### 10. Deliver with a receipt

Report the selected Apple target, final paths, dimensions, production mode, source
references, known tradeoffs, and validation result. A screenshot set is a listing
asset and does not enter the application binary.

## Required output

Return:

1. campaign summary and target platform;
2. evidence-backed feature and screen sequence;
3. headline and composition brief;
4. selected production mode and fidelity tradeoff;
5. approved asset paths;
6. validation receipt; and
7. any remaining blocker, especially missing final dimensions or unverified UI
   fidelity.

## Guardrails

- Never expose tokens, credentials, private customer data, or personal information.
- Never invent screens, controls, navigation, themes, features, or claims.
- Never use a visual reference's product content as another app's evidence.
- Never hide a generated-UI fidelity problem behind a passing file check.
- Prefer graceful partial progress: one failed screen should not discard approved
  screens from the same campaign.
