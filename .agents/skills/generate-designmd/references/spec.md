# DESIGN.html Template

This file is the template. The content inside the `BEGIN TEMPLATE` / `END TEMPLATE` markers defines what `DESIGN.html` must say: sections, order, table columns, and token names. It is written in markdown for readability. [Rendering DESIGN.html](#rendering-designhtml) defines how that content becomes one visual page. Replace every `[fill in ...]` with content from the supplied design input.

Rules:
- The format is universal. It fits any brand in any style. It was derived from a Cal.com style reference, but Cal.com is only the source of the structure. Do not carry over any Cal.com values, names, or wording.
- Prefer tables over bullet lists wherever content has repeatable fields and the rendering section gives no visual form. Keep prose only for the overview, imagery, and layout sections.
- Keep the headings, section order, and table columns. Add or remove rows to fit the design. A table's columns may render as a card's fields instead of a literal table, as long as every column's value stays visible.
- Omit a whole section only if the input has no evidence for it (for example, no imagery). Never reorder. Optional sections (Playground, Motion) are inserted only where the rendering section places them.
- When the source's values are inconsistent (near-duplicates such as 15.5px next to 16px, or corners of 19px and 22px on sibling elements), propose a clean scale, round onto it, and list every rounding in a note under that scale, marked as proposed. Never round silently.
- Names, hex values, and token names must match across the tables, components, prompt guide, and CSS blocks. Do not use in prose a color, font, radius, or shadow that has no token.
- Use exact values when the input provides them. Say so when a value is estimated or proposed.
- Delete all `[...]` instructions from the final file. Do not include secrets or unrelated private data.

## Rendering DESIGN.html

Depth follows the input. Pick the level the evidence supports, or the one the user asks for:
- **Static base:** the input is a brief, screenshots, mockups, or a site with no behavior to copy. Render every section with static visuals (swatches, specimens, scales, component previews) and leave out the Playground and Motion sections. This is a valid finished result and a base to iterate on.
- **From a spec or prototype:** a written spec, Figma file, or partial prototype describes some behavior. Make only the components with described behavior interactive, and keep the rest static.
- **Interactive:** a working prototype or app exists. Rebuild its components as live demos with the same motion values, and add the Playground and Motion sections where they apply.

When iterating on an existing `DESIGN.html`, keep its structure and change only what the new input covers.

The page:
- One self-contained HTML file with no build step. It opens by double-click. CDN fonts, icons, and animation or audio libraries are allowed; the page must still read correctly if they fail to load.
- The page uses the system it documents. Define every token once as a CSS custom property in `:root` and style the page and demos with those tokens. Page-only chrome (panels, code backgrounds) uses separately named variables, commented as not part of the design system.
- Every value is visible text, not only in CSS or JS, so an agent can read the file without running it. Use semantic headings in template order.
- One scrolling page. A sticky top bar holds the product name, one anchor link per section (short labels that fit on one line), and an Auto / Light / Dark switch when the design has dark values. Label derived dark values as derived.
- The top bar, hero, and every section share one content width and side padding. Separate sections with spacing, not divider lines.
- Hero: a small eyebrow, the tagline as the headline, the one-sentence idea, the overview paragraph, and a row of fact chips (theme, platform, source). No extra summary cards.
- Mark estimates with small visible tags (`est.`, `inferred`). Do not add version or changelog tags.
- Respect `prefers-reduced-motion`. Sample content is generic; no personal data.

Each section:
- **Colors:** a grid of swatch cards. Each shows a chip (light and dark halves when both exist), name, value, token, and role. Clicking a card copies the value.
- **Typography:** one card per font family (large specimen, token, weights, fallback). Then the type scale as rows from largest to smallest: on the left the role name, `size · weight · line height · tracking` in monospace (add the family when it is not the default), the usage, and the token; on the right an editable sample at true size.
- **Spacing & Shapes:** spacing as proportional bars with value and usage; radius as one box per scale step with its token and the elements that use it; shadows as tiles; blur or overlay treatments as tiles over an image. Put any rounding note under its scale.
- **Playground** (optional; place it before Components when the source is an app or working prototype): a device or browser frame where the components work together, beside a short numbered "Try it" list.
- **Components:** one card per component, with a live demo on the left and the written spec on the right: name, one-line role, short prose, and a property list carrying the Components table columns. Show values inside prose as inline code chips so they can be skimmed. Make demos interactive wherever the source shows behavior (press, hover, typing, open and close, drag) and reuse the source's motion values. Otherwise keep them static.
- **Motion** (optional; place it after Components when the source has meaningful motion or sound): replayable demos with their timing or spring values as captions, a gestures table, and a sound table with play buttons if the source has sounds.
- **Do's and Don'ts:** two columns, Do and Don't, each a plain flush-left list of short, checkable rules. No per-item icons or dividers.
- **Elevation, Imagery, Layout:** cards with short prose or lists, with values as inline code.
- **Agent Prompt Guide:** the quick color table, then each example prompt in a card with a copy button.
- **Similar Brands:** a simple table.
- **Quick Start:** the full `:root` and Tailwind v4 `@theme` blocks in `<pre>` with copy buttons. They must match the page's own `:root` exactly.

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

### Font Families

| Font | Token | Substitute | Weights | Sizes | Line Height | Letter Spacing | Role |
|------|-------|------------|---------|-------|-------------|----------------|------|
| [font name] | `--font-[name]` | [web-safe or Google Fonts fallback] | [list] | [list] | [range] | [value and effect] | [where and why it is used, in one line] |
| [one row per font family] | | | | | | | |

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

| Property | Value |
|----------|-------|
| Page max-width | [value] |
| Section gap | [value] |
| Card padding | [value] |

## Components

[One row per component. Cover at least: primary button, secondary button, tag or chip, card, navigation link, and any signature or hero component. Use exact values and refer to colors by name and hex. Use — for properties that do not apply. Add columns for other properties the design needs, such as border, height, or states.]

| Component | Role | Background | Text | Font | Radius | Padding | Shadow |
|-----------|------|------------|------|------|--------|---------|--------|
| [name] | [what it is for] | [color] | [color] | [font and size] | [value] | [value] | [value or —] |

## Do's and Don'ts

**Do**
- [concrete, checkable rule using exact values: colors, radii, weights, fonts; one item per rule]

**Don't**
- [a pitfall to avoid, using exact values; one item per pitfall]

## Elevation

| Component | Shadow |
|-----------|--------|
| [component type] | `[shadow value]` |

[For flat designs, replace this table with one that maps component types to the alternative: borders, tonal layers, color contrast.]

## Imagery

[fill in 1-2 paragraphs: photography vs. illustration vs. product UI, icon style, framing (contained or full-bleed), and what is not used.]

## Layout

[fill in prose: page container, section rhythm, hero composition, and the repeated content patterns, e.g. card grids.]

## Agent Prompt Guide

### Quick Color Reference
| Use | Value | Name |
|-----|-------|------|
| Page Background | `[hex]` | [name] |
| Card Background | `[hex]` | [name] |
| Headline Text | `[hex]` | [name] |
| Body Text | `[hex]` | [name] |
| Primary CTA | `[hex]` background, `[hex]` text | [names] |
| Borders/Dividers | `[hex]` | [name] |

### Example Component Prompts

[3 self-contained prompts, each with exact hex values, font names, sizes, radii, padding, and shadows.]

| Component | Prompt |
|-----------|--------|
| Hero Section | "[prompt]" |
| Primary CTA Button | "[prompt]" |
| Feature Card | "[prompt]" |

## Similar Brands

[3-4 rows]

| Brand | Shared or Different |
|-------|---------------------|
| [brand] | [one line on what is shared or different] |

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
