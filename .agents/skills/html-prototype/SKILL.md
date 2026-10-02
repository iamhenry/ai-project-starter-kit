---
name: html-prototype
description: Build a high-fidelity, single-file HTML prototype (Tailwind browser build, daisyUI 5, Motion, Tabler icons, optional interact.js) that opens by double-click with no build step, then hand it off as a living spec for a production build. Use only when the user explicitly invokes html-prototype or /html-prototype, or explicitly asks for an HTML prototype using this stack. Do not use for production code, framework apps, or general UI work.
---

# HTML Prototype

Make an idea tangible fast, then refine it until it feels like the real product. The prototype is a lightweight, living spec: one HTML file that encodes every product decision (screens, flows, states, copy, motion, gestures, data shape) so another agent can build the production version from it.

Ambition is the point. Ordinary app UI and unconventional ideas (canvas tools, spatial layouts, game-like interactions, generative views) are both in scope. The stack below is the floor, not the ceiling.

## Pick the domain first

Each prototype targets exactly one domain. Do not mix them.

| Domain | Read | Start from |
|---|---|---|
| Mobile / PWA (touch, phones and tablets, installable) | [references/mobile.md](references/mobile.md) | [assets/starter-mobile.html](assets/starter-mobile.html) |
| Web (desktop-first, responsive down to phone, pointer and keyboard) | [references/web.md](references/web.md) | [assets/starter-web.html](assets/starter-web.html) |

If the user does not say, ask once. Always read [references/stack.md](references/stack.md) and [references/design.md](references/design.md). For the motion and interaction passes, use the `animation-principles` skill.

## Hard rules

- One `.html` file. It must work by double-clicking it: no npm, no bundler, no compile step, no local server.
- Use only the pinned CDNs in `stack.md`. No React, Vue, Framer Motion, shadcn, or package installs.
- Use daisyUI class names for standard controls (buttons, inputs, cards, navbar, tabs, drawer, modal, toggles). Build anything novel with Tailwind utilities, SVG, or canvas. Do not invent a component library or copy framework components.
- Every interactive element does something real: navigates, changes state, or opens a real modal. No dead buttons, no `href="#"`.
- Fake data lives in one clearly marked seed block. Every collection has an empty state.
- Light and dark themes from `design.md`, both first-class.
- Responsive across the domain's widths (see the domain reference). No horizontal page scroll at any width.
- Icons from Tabler via Iconify (see `stack.md`), one set per prototype.
- Never open public ports, deploy, or publish without explicit permission.

## Workflow

Work in passes. Prove each pass works before starting the next. Later passes are optional unless the user asks for them or the idea depends on them.

1. **Frame.** Restate the idea as the experience to feel, the screens or surfaces, the core actions, and the states each surface needs (empty, loading, error, success, edge cases). Ask only questions that would change the outcome.
2. **Base.** Copy the domain starter. Build every surface, flow, and state with no motion. All interactions work.
3. **Design.** Apply `design.md` through the theme variables already mapped in the starter. Tune hierarchy, spacing, and type until it reads as a real product in both themes.
4. **Motion.** Apply the `animation-principles` skill: micro-interactions that explain a change, keep continuity, or confirm an action. Premium, never showy. Respect reduced motion.
5. **Interaction depth.** Domain-specific input: gestures on mobile, keyboard, pointer, and drag and drop on web. Use the gesture reference in `animation-principles`.
6. **Persistence.** Save state locally so the prototype survives reloads and can be lived with (see `stack.md`).

The user may reorder or skip passes. Follow their call.

## Architecture

Keep the file readable for the next agent:

- **Head:** pinned CDNs, then one `<style>` block with the theme variables and the few custom classes.
- **Markup:** one section per screen or surface, then modals, then toast.
- **App script (classic `<script>`):** seed data, state, render functions, one delegated click listener driven by `data-nav`, `data-modal`, `data-action`, and similar attributes, and persistence.
- **Enhancement modules (`<script type="module">`):** motion and gestures, each in its own block. They fill named hooks on `window.fx` that the app script calls (no-ops by default). If a CDN fails, the prototype still works.
- **A small `window.app` API** for modules that need to change state (for example, reorder or remove), so they never reach into app internals.

## Prove it

Mechanical checks are not proof. Exercise the real thing:

- Open the file directly (`file://`) in a headless browser at each of the domain's verification widths.
- Walk every surface and flow; open every modal; check every state, including empty.
- Toggle the theme; capture screenshots in both themes.
- Use real input for interactions: pointer down, move, up for drags and swipes; keyboard for shortcuts.
- Reload to prove persistence.
- Confirm zero page errors.
- Wait for open animations to finish before clicking inside a modal or sheet, or the click lands behind it.

Report in plain language: the file path, what was proven, what was not (for example, "not tested on a real device"), and any decision the user needs to make.

## Handoff

When the prototype is ready to drive a production build, add a short comment block at the top of the file listing: surfaces, core flows, states, data model, interaction and motion decisions, and open questions. The file plus that block is the spec.
