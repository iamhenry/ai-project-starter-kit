# Generate App Store Screenshots

A primary workflow for creating **Apple App Store screenshot campaigns** from real
product evidence and supplied target UI assets. It defaults to reviewed iPhone
portrait candidates while supporting deliberate iPad and Mac targets with their
own device geometry and requirements.

## What it does

The core rule is simple: **preserve the real app UI**. Store screenshots must
represent the app a user can actually open. This skill helps you:

- Use supplied target UI images, approved campaign images, and brand assets.
- Run a preflight that confirms the Apple target, current requirements, source UI
  images, release scope, production mode, and screenshot count.
- Audit shipped functionality, including relevant Git history, before choosing
  screenshot claims.
- Use `../generate-app-store-screenshot-captions/SKILL.md` for feature selection,
  headlines, sequencing, and composition notes.
- Triage candidates that show the app's core value.
- Composite the exact supplied real capture into a designed marketing canvas.
- Pick the right output mode and keep upload candidates separate from exploration.
- Validate every asset against platform pixel requirements before submission.

It uses generated-bitmap by default when the user accepts the risk that an image
model may redraw details; that risk must never be hidden. Exact UI preservation
is an explicit opt-in and requires supplied real captures.

## Output modes

| Mode | Upload-safe? | Description |
|------|:---:|-------------|
| `raw` | ✅ | Supplied real captures only, with no framing. |
| `store-safe-exact` | ✅ | Designed mockups where the device content is the **exact** supplied real capture. |
| `generated-bitmap` | ⚠️ | User-approved generated candidates from supplied references; not exact-upload-safe. |
| `image-gen-direction` | ❌ | Rejected or exploratory concepts; never final deliverables. |

## Repository layout

```text
generate-app-store-screenshots/
├── SKILL.md                       # Core workflow and guardrails
├── README.md                      # This overview
└── references/
    ├── apple-platform-requirements.md
    ├── store-safe-rules.md
    └── visual-direction.md
```

## Workflow at a glance

1. **Preflight** — confirm Apple target, current target requirements, source UI
   images, release scope, production mode, and screenshot count.
2. **Audit product evidence** — read the caption skill, codebase, product docs,
   and relevant Git history.
3. **Draft and approve the story** — select evidence-backed screens, headlines, and the
   benefits-first sequence before generating anything.
4. **Lock the campaign system** — typography, palette, device geometry, and
   supporting shapes.
5. **Organize supplied sources** — save target UI assets under the selected
   `store/ios/`, `store/ipad/`, or `store/macos/` screenshot tree.
6. **Generate or compose** — use exact compositing or the decoupled Codex adapter.
7. **Review, clean, normalize, and validate** — keep only approved candidates and
   verify final store dimensions and fidelity.

## Recommended output folders

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

Keep rejected explorations out of the upload-candidate folders so they are never
mistaken for deliverables.

## See also

- [`SKILL.md`](SKILL.md) — full workflow and image-generation guardrails.
- [`references/apple-platform-requirements.md`](references/apple-platform-requirements.md) — target selection and current-requirements guidance.
- [`references/store-safe-rules.md`](references/store-safe-rules.md) — safe/unsafe enhancements and the triage checklist.
- [`references/visual-direction.md`](references/visual-direction.md) — shared campaign composition and target-native geometry.
