# Carousel Workflow

Self-contained SOP for generating carousel PNG slides using Remotion.
Remotion renders React components to video or still images — for carousels, each slide is rendered as a PNG still.
No content strategy, no style rules — this doc covers tool invocation only.

For Remotion-specific patterns (compositions, stills, fonts, animations, text), load the Remotion skill:
see `.opencode/skills/remotion/SKILL.md`

---

## Pre-flight — Install Remotion (once per environment)

Verify Remotion is installed in the carousel project:

```bash
ls <carousel.projectDir>/node_modules/@remotion/renderer
```

If missing, install dependencies:

```bash
npm install
```

Also verify the `npx remotion` CLI is available:

```bash
npx remotion --version
```

If `carousel.projectDir` is not set in `references/config.json`, check whether a Remotion project exists anywhere in the current working directory by running:

```bash
find . -name 'remotion.config.*' -not -path '*/node_modules/*' | head -5
```

If found, set `carousel.projectDir` to that directory and continue. If not found → hard stop. Record `skipped_steps: "Remotion project not found"` in `results.jsonl` and surface to human.

---

## Step 1 — Prepare output directory

```bash
mkdir -p output/carousels/<slug>/
```

Slug format: `{MM-DD-YY}-{topic-slug}` (e.g. `03-13-26-sleep-recovery`).

---

## Step 2 — Write the input data file

Write the 5 contract inputs to a JSON file that the Remotion composition will read as props:

```bash
cat > <carousel.projectDir>/carousel-inputs.json << EOF
{
  "topic": "<topic>",
  "targetAudience": "<targetAudience>",
  "angle": "<angle>",
  "cta": "<cta>",
  "visualStyle": "<visualStyle or omit field>"
}
EOF
```

Do not add fields beyond these 5. The Remotion composition owns the content schema — do not pass slide structure, character limits, or style rules.

---

## Step 3 — Render slides as PNG stills

Use Remotion's `still` command to render each slide as a PNG. The composition name and slide count are defined in the Remotion project — check `references/config.json` → `carousel.composition` and `carousel.slideCount`:

```bash
for i in $(seq 1 <carousel.slideCount>); do
  npx remotion still \
    --props=<carousel.projectDir>/carousel-inputs.json \
    --output=output/carousels/<slug>/slide-${i}.png \
    <carousel.composition> \
    <frame-for-slide-i>
done
```

The frame number for each slide depends on how the Remotion composition sequences slides. If the composition exports a dedicated still per slide, use the composition ID directly. Refer to the Remotion compositions rule for details: `.opencode/skills/remotion/rules/compositions.md`.

If the project provides a render script that wraps this loop, use it instead:

```bash
<carousel.renderScript> \
  --props <carousel.projectDir>/carousel-inputs.json \
  --output output/carousels/<slug>/
```

---

## Step 4 — Verify output

```bash
ls output/carousels/<slug>/*.png
```

Count must be greater than zero. If zero PNGs exist → hard stop. Record `skipped_steps: "carousel render produced no PNGs"` in `results.jsonl`. Do NOT log `"format": "carousel"` for this cycle. Surface to human.

---

## Step 5 — On success

PNG slides confirmed. Proceed to draft to Postiz as described in `SKILL.md`.

---

## Key rules

- Never log `"format": "carousel"` in `results.jsonl` unless PNGs are confirmed present after Step 4.
- Never pass content schema, style rules, or slide structure as props — the Remotion composition owns those.
- One attempt only. On failure, stop and surface — do not retry.
- For any Remotion-specific questions (animations, fonts, stills API, compositions), load `.opencode/skills/remotion/SKILL.md`.
