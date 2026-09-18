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
- Which target-specific UI images are authoritative inputs, and where are they located?
- Which shipped release or Git range should the feature audit cover?
- Is the production mode `exact-composite` or `generated-bitmap`?
- What is the desired screenshot count, if it is not obvious from the inputs?

Optional:

- Which brand colors, typeface, logo, or mascot should guide the wrapper?
- Are there visual references to study for composition only?
- Are there screen-specific cleanup notes or privacy constraints?

Sensible defaults are iPhone portrait, current App Store Connect requirements,
the supplied target UI images as source material, one screen per generation, the
locked base composition, and no image generation until the campaign brief is
explicitly approved.

## Source-of-truth order

Use evidence in this order, resolving conflicts toward the currently shipped
release:

1. The running app and real simulator/device captures.
2. Current implementation and user-facing routes in the codebase.
3. Recent Git history, especially commits touching the relevant screens. Read
   `git log --oneline --decorate`, then use path-specific history when needed.
   Commit history helps distinguish implemented behavior from user stories,
   plans, mocks, and abandoned work.
4. Product documents such as user stories, changelog, store metadata, and release
   notes.
5. User-provided visual references, which describe the wrapper and campaign mood,
   never product truth.

If evidence is missing, state the gap. Do not fill it with plausible UI, claims,
or roadmap functionality.

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
5. describe the real screen, user outcome, and visual composition for each one.

Do not begin image generation until every selected screen has a named real source
or an explicit reason why the source is not available. Keep claims grounded in
what the current app actually supports.

Present the feature audit, sequence, headlines, and visual notes as a draft and
wait for explicit user approval. Do not invoke an image-generation or composition
command before that approval.

### 3. Capture and preserve source screens

Prefer native simulator or device captures from the running app. If the user
provides design mocks or existing captures, preserve them as source references and
label them honestly; do not silently treat a Figma mock as shipped UI.

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

Verify source dimensions immediately. Use synthetic demo data only when it is
clearly non-sensitive and represents a real product path. Capture the actual
target UI: do not upscale an iPhone capture into an iPad asset or put a Mac
window inside a phone frame.

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

Do one composition dry run, measure what works, then lock it. Do not redesign the
composition independently for every screen.

### 5. Choose the production mode explicitly

Select one mode for the campaign and record it in the brief:

#### Exact compositing — upload-safe default

- Use the real screenshot as an unchanged image layer.
- Add only the frame, background, headline, and truthful surrounding treatment.
- Keep this mode when exact UI text, controls, and pixel fidelity matter.

#### Generated bitmap — explicit creative tradeoff

- Use this only when the user accepts that the image model may redraw details.
- Pass the relevant source screen and the locked campaign prompt for each image.
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
2. Send one approved screen source, one shared campaign prompt, and one output
   path per generation.
3. Reuse the locked headline, typography, geometry, palette, and cleanup rules for
   every screen.
4. Inspect the returned image before accepting it; a successful command is not
   evidence of visual or UI fidelity.

Do not couple this workflow to a particular image-generation skill. If Codex is
unavailable, ask whether to use exact compositing or another explicitly approved
adapter instead of silently changing the production mode.

### 6. Generate or compose one screen at a time

Use stable source filenames and a shared prompt/template with per-screen values:

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
- private data, unsupported claims, and accidental reference-brand content; and
- whether the set reads as one campaign rather than four unrelated images.

Reject a candidate when the problem is easier to fix by regenerating than by
editing around it. Keep rejected explorations out of the approved folder.

### 8. Clean and name the approved set

After approval:

- keep only the final candidate for each screen in the approved folder;
- preserve raw source captures and reference assets separately;
- move or delete rejected experiments so they cannot be mistaken for deliverables;
- use stable screen names such as `screen1-home-v1.png`; and
- avoid keeping exploratory version clutter once a final is selected.

### 9. Normalize and validate for the store

Only after visual approval, convert each final to the exact dimensions and format
for the selected Apple target. Validate:

- pixel dimensions and orientation;
- PNG/JPEG format and color mode;
- alpha behavior where the store requires it;
- filename and ordering;
- readable text after store resizing;
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
