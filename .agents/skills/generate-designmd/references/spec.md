# DESIGN.md Format

DESIGN.md is a self-contained, plain-markdown style reference for a brand or product. It carries the visual identity so it can be followed across design sessions and between AI agents and tools. It has no YAML front matter: tokens live in markdown tables and in a CSS block at the end. Tables and the CSS blocks are normative; prose explains how to apply them.

The reference shape is the Cal.com style reference. Follow its structure, section order, and heading names exactly.

## Document Shape

Sections appear in this order. Omit a section only if it has no evidence in the input (for example, no imagery). Never reorder.

1. Title and header block
2. Tokens — Colors
3. Tokens — Typography
4. Tokens — Spacing & Shapes
5. Components
6. Do's and Don'ts
7. Elevation
8. Imagery
9. Layout
10. Agent Prompt Guide
11. Similar Brands
12. Quick Start (CSS Custom Properties, Tailwind v4)

## 1. Title and Header Block

```markdown
# {Brand} — Style Reference
> {Two-to-four word concept}, {second half}. {One sentence on the idea behind the system.}

**Theme:** {light | dark}

Source measurements are normalized; roles and recommendations are interpreted. Font summary lists are independent, not paired by position. HTML examples are reconstructions, not source components.

{One paragraph (4-6 sentences): the overall feel, how color is used, what the typography does, the shape of buttons and cards, and the elevation approach.}
```

- Title is `# {Brand} — Style Reference`.
- The blockquote is a short tagline naming the design's core tension (for example, "Monochrome Utility, Human Touch.").
- Keep the provenance note line as shown.

## 2. Tokens — Colors

A table with columns `Name | Value | Token | Role`.

```markdown
## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Ink | `#101010` | `--color-ink` | Primary CTAs, primary text, active states. |
```

- Name is a short descriptive word (Ink, Paper, Slate). Value is a backticked CSS color, hex by default.
- Token is a backticked CSS custom property, `--color-{name}` in kebab-case.
- Role says where the color is used, not just what it looks like.
- Include integration or brand-logo colors only if present in the input, and mark them "logos only".

## 3. Tokens — Typography

One subsection per font family, then a type scale table.

```markdown
## Tokens — Typography

### {Font Name} — {one-line role and character} · `--font-{name}`
- **Substitute:** {web-safe or Google Fonts fallback}
- **Weights:** {list}
- **Sizes:** {list}
- **Line height:** {range}
- **Letter spacing:** {value and effect}
- **Role:** {where and why it is used}

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing | Token |
|------|--------|--------|------|-------------|----------------|-------|
| body | — | — | 16px | 1.5 | -0.19px | `--text-body` |
```

- Use `—` for family and weight cells when unknown or inherited.
- Scale roles are semantic (caption, body-sm, body, subheading, heading-sm, heading, heading-lg, display). Order smallest to largest.
- Token is `--text-{role}`.

## 4. Tokens — Spacing & Shapes

```markdown
## Tokens — Spacing & Shapes

**Density:** {compact | comfortable | spacious}

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 4 | 4px | `--spacing-4` |

### Border Radius

| Element | Value |
|---------|-------|
| cards | 12px |

### Shadows

| Name | Value | Token |
|------|-------|-------|
| sm | `rgba(36, 36, 36, 0.05) 0px 4px 8px 0px` | `--shadow-sm` |

### Layout

- **Page max-width:** {value}
- **Section gap:** {value}
- **Card padding:** {value}
```

- Spacing names are the pixel number; token is `--spacing-{n}`.
- Border Radius is keyed by element (tags, cards, inputs, buttons).
- Shadows are listed by name with the full CSS value.

## 5. Components

One `###` subsection per component, each with a bold `**Role:**` line followed by a one-paragraph spec that states background, text color, font and size, radius, padding, and shadow with exact values.

```markdown
## Components

### Primary CTA Button
**Role:** The main call-to-action on the page.

A pill-shaped button. Background: Ink (#101010). Text: White (#ffffff). Font: {font} at 14-16px. Radius: 9999px. Padding: ~12px 24px.
```

Cover at least: primary button, secondary button, tag or chip, card, navigation link, and any hero or signature component. Reference colors by name and hex.

## 6. Do's and Don'ts

Two `###` subsections, `### Do` and `### Don't`, each a bullet list of concrete, checkable rules using exact values (colors, radii, weights, fonts). These act as guardrails.

## 7. Elevation

A `## Elevation` section with bullets mapping component types to shadow values: `- **{Component}:** \`{shadow}\``. For flat designs, explain the alternative (borders, tonal layers).

## 8. Imagery

A `## Imagery` section with one or two paragraphs on the image language: photography vs. illustration vs. product UI, icon style, framing (contained or full-bleed), and what is not used.

## 9. Layout

A `## Layout` section with prose on the page container, section rhythm, hero composition, and the repeated content patterns (for example, 3-column card grids).

## 10. Agent Prompt Guide

```markdown
## Agent Prompt Guide

### Quick Color Reference
- **Page Background:** `#f4f4f4` (Paper)
- **Card Background:** `#ffffff` (White)
- **Headline Text:** ...
- **Body Text:** ...
- **Primary CTA:** ...
- **Borders/Dividers:** ...

### Example Component Prompts
1. **Hero Section:** "{ready-to-use prompt with exact values}"
2. **Primary CTA Button:** "{...}"
3. **Feature Card:** "{...}"
```

Prompts must be self-contained: exact hex values, font names, sizes, radii, padding, and shadows.

## 11. Similar Brands

A bullet list: `- **{Brand}** — {one line on what is shared or different}`. Three to four entries.

## 12. Quick Start

Two fenced `css` blocks under `## Quick Start`.

### CSS Custom Properties

`### CSS Custom Properties` contains a `:root { ... }` block with commented groups, in this order: Colors, Typography — Font Families, Typography — Scale (`--text-*`, `--leading-*`, `--tracking-*`), Typography — Weights, Spacing, Layout, Border Radius, Named Radii, Shadows.

### Tailwind v4

`### Tailwind v4` contains an `@theme { ... }` block with the same tokens, minus the Layout, Named Radii, and Weights groups.

Every token in the tables above must appear in both blocks with identical values.

## Consistency Rules

- Names, hex values, and token names must match across the tables, component specs, prompt guide, and CSS blocks.
- Do not use a color, font, radius, or shadow in prose that is not defined in a token table.
- Distinguish observed values from estimates or proposed choices in prose.
- Do not include secrets or unrelated private data.
