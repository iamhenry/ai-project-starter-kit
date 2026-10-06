# DESIGN.md Template

This file is the template. Copy everything inside the `BEGIN TEMPLATE` / `END TEMPLATE` markers into `DESIGN.md` and replace every `[fill in ...]` with content from the supplied design input.

Rules:
- The format is universal. It fits any brand in any style. It was derived from a Cal.com style reference, but Cal.com is only the source of the structure. Do not carry over any Cal.com values, names, or wording.
- Keep the headings, section order, and table columns exactly. Add or remove table rows to fit the design.
- Omit a whole section only if the input has no evidence for it (for example, no imagery). Never reorder.
- Names, hex values, and token names must match across the tables, components, prompt guide, and CSS blocks. Do not use in prose a color, font, radius, or shadow that has no token.
- Use exact values when the input provides them. Say so when a value is estimated or proposed.
- Delete all `[...]` instructions from the final file. Do not include secrets or unrelated private data.

<!-- BEGIN TEMPLATE -->

# [fill in brand or product name] — Style Reference
> [fill in a short tagline naming the design's core tension, e.g. "X Y, Z W."] [fill in one sentence on the idea behind the system.]

**Theme:** [fill in light or dark]

Source measurements are normalized; roles and recommendations are interpreted. Font summary lists are independent, not paired by position. HTML examples are reconstructions, not source components.

[fill in one paragraph, 4-6 sentences: the overall feel, how color is used, what the typography does, the shape of buttons and cards, and the elevation approach.]

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| [short descriptive name] | `[CSS color, hex by default]` | `--color-[kebab-case-name]` | [where it is used, not just what it looks like] |
| [one row per color; include brand or logo colors only if present in the input and mark them "logos only"] | | | |

## Tokens — Typography

[repeat this block once per font family]
### [font name] — [one-line role and character] · `--font-[name]`
- **Substitute:** [web-safe or Google Fonts fallback]
- **Weights:** [list]
- **Sizes:** [list]
- **Line height:** [range]
- **Letter spacing:** [value and effect]
- **Role:** [where and why it is used]

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing | Token |
|------|--------|--------|------|-------------|----------------|-------|
| [semantic role, e.g. caption, body-sm, body, subheading, heading-sm, heading, heading-lg, display; smallest to largest] | [family, or — if unknown or inherited] | [weight or —] | [size] | [line height] | [letter spacing] | `--text-[role]` |

## Tokens — Spacing & Shapes

**Density:** [fill in compact, comfortable, or spacious]

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| [step, usually the pixel number] | [value] | `--spacing-[step]` |

### Border Radius

| Element | Value |
|---------|-------|
| [element, e.g. tags, cards, inputs, buttons] | [value] |

### Shadows

| Name | Value | Token |
|------|-------|-------|
| [name] | `[full CSS shadow value]` | `--shadow-[name]` |

### Layout

- **Page max-width:** [value]
- **Section gap:** [value]
- **Card padding:** [value]

## Components

[repeat this block once per component. Cover at least: primary button, secondary button, tag or chip, card, navigation link, and any signature or hero component.]
### [component name]
**Role:** [what it is for]

[One paragraph with exact values: background, text color, font and size, radius, padding, shadow. Refer to colors by token name and hex.]

## Do's and Don'ts

### Do
- [concrete, checkable rule using exact values: colors, radii, weights, fonts]

### Don't
- [concrete, checkable pitfall using exact values]

## Elevation

- **[component type]:** `[shadow value]`
[For flat designs, replace the list with a short explanation of the alternative: borders, tonal layers, color contrast.]

## Imagery

[fill in 1-2 paragraphs: photography vs. illustration vs. product UI, icon style, framing (contained or full-bleed), and what is not used.]

## Layout

[fill in prose: page container, section rhythm, hero composition, and the repeated content patterns, e.g. card grids.]

## Agent Prompt Guide

### Quick Color Reference
- **Page Background:** `[hex]` ([name])
- **Card Background:** `[hex]` ([name])
- **Headline Text:** `[hex]` ([name])
- **Body Text:** `[hex]` ([name])
- **Primary CTA:** `[hex]` ([name]) background, `[hex]` ([name]) text
- **Borders/Dividers:** `[hex]` ([name])

### Example Component Prompts
[3 self-contained prompts, each with exact hex values, font names, sizes, radii, padding, and shadows.]
1. **Hero Section:** "[prompt]"
2. **Primary CTA Button:** "[prompt]"
3. **Feature Card:** "[prompt]"

## Similar Brands

- **[brand]** — [one line on what is shared or different]
[3-4 entries]

## Quick Start

### CSS Custom Properties

```css
:root {
  /* Colors */
  [one line per color token in the Colors table]

  /* Typography — Font Families */
  [one --font-* per font, with a fallback stack]

  /* Typography — Scale */
  [--text-*, --leading-*, --tracking-* for each Type Scale row]

  /* Typography — Weights */
  [--font-weight-* for each weight used]

  /* Spacing */
  [one line per spacing token]

  /* Layout */
  [--page-max-width, --section-gap, --card-padding]

  /* Border Radius */
  [one --radius-* per scale value]

  /* Named Radii */
  [--radius-[element] for each row in Border Radius]

  /* Shadows */
  [one line per shadow token]
}
```

### Tailwind v4

```css
@theme {
  [same tokens and values as above, minus the Layout, Named Radii, and Weights groups]
}
```

<!-- END TEMPLATE -->
