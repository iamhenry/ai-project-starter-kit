# Architectural Soundness Report Design

Use this reference whenever creating or updating the living HTML report. It adapts the reader-first judgment of Vercel's `design.md` and the supplied Vercel Light VS Code palette. It does not copy Vercel branding and must not imply Vercel authorship.

Start from [example-report.html](example-report.html). It is both the deterministic scaffold and a finished reference for hierarchy and density. Its Journal (iOS app) content is not reusable project evidence: replace every project-specific fact, label, decision, source, and diagram while preserving the visual system and interaction patterns. The report itself is the durable visual artifact—do not create a PNG companion unless the user explicitly requests one.

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

Eight numbered sections, in this order, each answering a new reader question:

1. Overview: what is being built, for whom, and what is out of scope
2. Architectural goals: what wins when goals conflict, and which approach was chosen
3. System context: what the system talks to
4. Components: the pieces inside and who calls whom
5. Data models: where facts live and the flows whose order matters
6. Interfaces: the calls between pieces and the rules data must satisfy
7. Risks: what could go wrong, how likely, and the growth triggers
8. Appendix: verdict, open questions, decision log, handoff, glossary, sources

The header holds only the title and a status pill. No summary cards and no intro paragraph above section 1.

Do not repeat the same conclusion in multiple places. Each section answers a new reader question.

## Section anatomy

Every section uses the same parts, in this order, and drops any it does not need:

1. **Summary** (`p.summary`, under the `h2`): two to four plain sentences on how this part works and why, so the reader knows what to expect from the diagram.
2. **Behavior and translation** (`.pair`): "What the person experiences" beside "Technical translation". Behavior is what the person sees or does. The translation names the libraries, files, and mechanisms that deliver it.
3. **Diagram** (`.diagram`), with a one-line caption stating the takeaway.
4. **Table** for precise lookup.
5. **Build notes** (`details open`): technical detail per item, expanded by default.
6. **Your answers that shaped this section** (`.answers`): the interview question, the answer, and its technical consequence.

## Language

Lead with behavior in plain English. Keep technical language secondary.

| Prefer | Technical reference |
|---|---|
| The page asks for information | `API boundary` |
| Keeps the last good answer briefly | `Cache` |
| Where the real facts live | `Source of truth` |
| Checks every rule before saving | `Validation` |
| Explains old or incomplete results | `Error handling` |
| Only the person holding the phone uses it | `Authentication` |

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

All diagrams are inline SVG drawn with the `diagram-design` skill. Use the report palette above as the skin: paper `#fafafa`, ink `#171717`, muted `#5f5f5f`, rule `#e7e7e7`, accent `#005ee9`, accent tint `#edf5ff`, link `#7200c4`. This replaces the diagram-design onboarding gate for report diagrams. Prefix every SVG id per diagram, keep `role="img"` with a filled `<title>` and `<desc>`, set `min-width` to keep labels readable, and run `python3 <diagram-design>/scripts/verify-geometry.py` on each diagram (one diagram per file) until it reports 0 findings.

### System context diagram

The person, the system boundary, and every outside service, grouped into zones such as on the device, online, and switched off. The system itself is the one focal node.

### Module map

Zones for screens or entry points, services, storage, and outside services. Use the exact names from the module table. Label arrows with the action (for example `ADD NOTE`, `SCHEDULE`), mark the source of truth as focal, and draw the "data changes redraw screens" loop once. Put the module table directly below it with columns `Module`, `What the person gets`, `Built with`, then the build notes, open by default. Reconcile the map and table whenever either gains or loses a piece.

### Edge-case flows

For a behavior with many failure branches (permissions, offline, empty results), draw a flowchart, then a table of `Situation`, `What the person sees`, `How the app knows`.

### Data model and sequences

An entity diagram for the stored records. Sequence diagrams for the two or three flows whose step order protects data, such as copy, then record, then clean up on failure. Name participants in plain English.

### Risk map

A chance-by-impact quadrant with one focal risk to act on first, followed by a mitigation table. Growth triggers name what changes and the complexity it would justify. Never present speculative scaling machinery as required now.

### Approaches compared

Only when more than one approach is viable. Approaches are columns and the same criteria are rows: what must be built, coverage of the user's goal, security and privacy, cost and time to first value, ongoing care, failure behavior, main compromise, when it becomes appropriate. The chosen approach may have one restrained highlight.

### Decision log, assumptions, and handoff

Always visible in the appendix. Each decision has an accurate date, the decision, a short reason, and any revisit condition. Append; do not erase old reasoning. Assumptions and handoff use three plain groups: established, assumed, and what implementation planning must decide.

### Interaction

Diagrams are static and work offline. The only script is optional section highlighting in the side navigation. Do not add a UI framework, chart library, or icon package.

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
- Keep the report fully readable without JavaScript.
- Meet WCAG AA contrast and never encode meaning only through color.

## Final visual check

Inspect the rendered page top to bottom and at a narrow width. Ask:

1. Does every section open with a summary that sets up its diagram?
2. Does the context diagram show everything the system talks to?
3. Does the module map use the same names as the module table, with nothing missing from either?
4. Does each section pair behavior with its technical translation where both matter?
5. Are technical terms secondary and consistently styled?
6. Are assumptions, handoff, and decision history visible without a click?
7. Does every section answer a different question?

Fix the highest-impact failure and inspect again. A polished layout does not compensate for missing architecture.

Before presenting the report, search the copied HTML for `Journal`, `Expo`, `MapKit`, `Nearby`, `check-in`, and `Henry`. Remove each leftover unless it is independently true for the current project.

## Sources

- Vercel report design guidance, used for reader-first hierarchy and restrained evidence design: https://vercel.com/design.md
- Vercel Light VS Code theme, used for the palette: https://github.com/gantoreno/vscode-vercel/blob/main/themes/vercel-light.json
- diagram-design skill (MIT), used for every diagram: https://github.com/cathrynlavery/diagram-design
- Architecture HTML-report inspiration: https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/HTML-REPORT.md
