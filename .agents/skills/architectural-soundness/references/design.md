# Architectural Soundness Report Design

Use this reference whenever creating or updating the living HTML report. It adapts the reader-first judgment of Vercel's `design.md` and the supplied Vercel Light VS Code palette. It does not copy Vercel branding and must not imply Vercel authorship.

Start from [example-report.html](example-report.html). It is both the deterministic scaffold and a finished reference for hierarchy and density. Its GitHub Dash content is not reusable project evidence: replace every project-specific fact, label, decision, source, and diagram while preserving the visual system and interaction patterns. The report itself is the durable visual artifact—do not create a PNG companion unless the user explicitly requests one.

## Reader's job

The reader is product-minded, not necessarily an engineer. They need to understand:

1. what is being built
2. how the whole experience works
3. every piece required to make it work
4. what happens during normal and failed behavior
5. which approaches were considered and why one was chosen
6. what assumptions or growth conditions could change the design

Design for understanding, not decoration. The report should teach the system visually before asking the reader to parse supporting prose.

## Information hierarchy

The first viewport contains:

- the user's question or desired outcome
- the strongest supported architecture answer
- the decisive boundary or compromise

Then move from broad to specific:

1. needs and constraints
2. bird's-eye system
3. complete inventory
4. interactive subsystems
5. behavior and failure flows
6. growth and reliability
7. options and trade-offs
8. verdict
9. decision timeline
10. assumptions and implementation handoff
11. sources

Do not repeat the same conclusion in multiple cards. Each section answers a new reader question.

## Language

Lead with behavior in plain English. Keep technical language secondary.

| Prefer | Technical reference |
|---|---|
| The page asks for information | `API boundary` |
| Keeps the last good answer briefly | `Cache` |
| Where the real facts live | `Source of truth` |
| Makes GitHub status understandable | `Data rules` |
| Explains old or incomplete results | `Error handling` |
| Uses your existing GitHub login | `Authentication` |

Use the plain phrase as the heading or diagram label. Render the technical reference as a small consistent pill beside it. Never alternate among italics, bare text, and different badge shapes.

## Visual system

Use a continuous white canvas, strong typography, shared alignment, generous whitespace, and restrained borders. Avoid a dashboard made from repetitive cards.

### Palette

```css
:root {
  --ink: #171717;
  --canvas: #ffffff;
  --surface: #fafafa;
  --border-subtle: #ebebeb;
  --border-strong: #cccccc;
  --text-secondary: #666666;
  --text-tertiary: #a8a8a8;
  --blue: #005ee9;
  --purple: #7200c4;
  --green: #397c3b;
  --amber: #9e5200;
  --red: #c62128;
  --pink: #b32c62;
  --cyan: #027d70;
}
```

Use black, white, gray, and borders for most of the page. Use color only to distinguish meaning:

- blue — what the user sees or controls
- purple — behind-the-scenes coordination
- green — safe result, recovery, or temporary memory
- amber — external connection, assumption, or future trigger
- red or pink — failure or unsafe outcome
- black — source of truth or final decision

Pair color with words, shapes, or line styles. Never rely on color alone.

### Typography

- Use Geist when available, with Arial or system sans-serif fallback.
- Use one large page-defining statement.
- Use sentence-case headings that state what the reader learns.
- Keep body text at a comfortable size and roughly 60 to 70 characters per line.
- Use monospace only for literal paths, commands, or identifiers.
- Avoid decorative uppercase eyebrows. A small category pill is enough orientation.

### Surfaces

- Prefer spacing and alignment before adding a border or background.
- Use one strong dark decision surface near the end when the report has a selected direction.
- Use soft gray only for real grouping, diagrams, and table row labels.
- Keep radii restrained and consistent.
- Do not use gradients, glows, glass effects, ornamental shadows, stock imagery, or decorative icon tiles.

## Required visual patterns

### Bird's-eye diagram

Use Mermaid `flowchart LR` or `flowchart TB` to show:

- the person
- the product surface they use
- the new system boundary
- major components inside that boundary
- existing tools and external systems
- the source of truth
- information returning to the user

Group existing and proposed parts visibly. Use direct plain-English labels. A reader should understand the main loop without reading a paragraph.

### Complete system inventory

Place this immediately below the bird's-eye diagram. Use a semantic table with these columns in this exact order:

| Category | Piece | What it is for | What it does |
|---|---|---|---|

- Category is the leftmost scan anchor and uses the standard pill.
- Include every distinct piece shown in the architecture and subsystem diagrams.
- Use one row per responsibility owner.
- Explain what would be missing through the purpose and behavior, not through internal class names.
- Reconcile the table whenever a diagram gains or loses a piece.

### Interactive subsystem explorer

Show three to seven subsystem choices near the top of the detailed architecture section. Each choice contains:

- a plain-English job, such as “Keep the answer trustworthy”
- one standard technical category pill, such as `Server logic`
- one short sentence about what the subsystem enables

Selecting a subsystem replaces the main diagram with its Mermaid flow. The diagram, not a paragraph, carries the explanation. Keep keyboard focus and `aria-selected` correct.

### Behavior diagrams

Use Mermaid sequence diagrams for time-ordered behavior such as:

- normal user journey
- information retrieval
- save or update flow
- authentication
- failure and retry

Name participants in plain English. Use captions to state the takeaway, not to narrate every arrow.

### Growth diagram

Start from the current usage assumption and branch only on concrete triggers. Each branch names what changes and the added architecture it justifies. Never present speculative scaling machinery as required now.

### Trade-off table

Use aligned approaches as columns and the same decision criteria as rows. The recommended approach may have one restrained highlight.

Always compare:

- what must be built
- coverage of the user's goal
- security and privacy responsibility
- cost and time to first value
- ongoing care
- failure behavior
- main compromise
- when the option becomes appropriate

### Decision timeline

Keep the timeline always visible near the end. Each entry contains an accurate date, decision, short reason, and any material deferral or revisit condition. Append new decisions; do not silently erase old reasoning.

### Assumptions and handoff

Keep this section always visible. Use three plain groups:

- what is established
- what is assumed
- what implementation planning must decide

Technical handoff labels such as `Data model`, `Cache`, or `API contract` use the same category pill as the rest of the report.

## Mermaid implementation

Use Mermaid 11 with strict security:

```html
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "base"
  });
</script>
```

Keep diagram syntax readable in the HTML. Use `classDef` with the palette above. Avoid punctuation in node labels that Mermaid parses ambiguously. Give each material diagram a nearby text takeaway for accessibility.

Mermaid is best for dependencies and sequences. Use semantic HTML tables for precise lookup and small JavaScript only for subsystem selection. Do not add a UI framework, chart library, or icon package.

## Category pill

Use one style everywhere:

```css
.tech-tag {
  display: inline-block;
  padding: 3px 8px;
  border: 1px solid #ebebeb;
  border-radius: 999px;
  background: #fafafa;
  color: #666666;
  font-size: 11px;
  font-style: normal;
  font-weight: 600;
  line-height: 1.35;
  vertical-align: middle;
}
```

Use pills only for technical categories. Do not turn dates, ordinary metadata, recommendations, or decorative labels into pills.

## Accessibility and responsive behavior

- Use one `h1`, ordered headings, landmarks, and a skip link.
- Use semantic tables with scoped headers.
- Give buttons visible focus and accurate selected state.
- Provide a short text takeaway for each meaningful diagram.
- Keep source order equal to reading order.
- Reflow grids before shrinking text.
- Fit diagrams within their visible region by default. If an unusually dense diagram would become unreadable, give that diagram its own horizontal scroll region rather than clipping it.
- Keep the core report understandable if subsystem JavaScript fails.
- Meet WCAG AA contrast and never encode meaning only through color.

## Final visual check

Inspect the rendered first viewport, whole page, subsystem interactions, and a narrow viewport. Ask:

1. Can the reader state the chosen architecture after the first viewport?
2. Does the bird's-eye diagram explain the whole loop?
3. Does the inventory contain every diagrammed piece, with category first?
4. Do subsystem diagrams teach behavior faster than their supporting text?
5. Are technical terms secondary and consistently styled?
6. Are assumptions, handoff, and decision history visible without a click?
7. Does every section answer a different question?

Fix the highest-impact failure and inspect again. A polished layout does not compensate for missing architecture.

Before presenting the report, search the copied HTML for `Pull Requests`, `GitHub`, `GitHub CLI`, and `BB`. Remove each leftover unless it is independently true and cited for the current project. Adapt row counts and diagrams to the real architecture, and keep the inventory synchronized with every diagram.

## Sources

- Vercel report design guidance, used for reader-first hierarchy and restrained evidence design: https://vercel.com/design.md
- Vercel Light VS Code theme, used for the palette: https://github.com/gantoreno/vscode-vercel/blob/main/themes/vercel-light.json
- Architecture HTML-report inspiration: https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/HTML-REPORT.md
