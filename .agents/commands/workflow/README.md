# New Workflow (Oct 20, 2026)

1. Rough idea or mocks to HTML prototype (web or mobile) using the `html-prototype` skill.
    1. For unfinished screens/states, use existing mocks from Figma or wireframe sketches and have ChatGPT generate those on the fly. BB IDE can then convert those into Figma layers via the built-in browser in BB using the `figma-automation` skill if we need those layers.
2. Flush out the prototype until I'm happy with it for all of the screens and states, then generate a `design.html` that contains the elements, components, etc. as specs within the HTML within the `design.html` (all with fake seed data).
3. Use the `generate-designmd` skill.
4. Use the `prototype.html` as a spec to create `user-stories.md` to flush out user behaviors (use `00-user-stories.md`).
    1. Use agent-browser to generate screenshots for screens/states which then get passed in to the other specs.
5. Generate `architecture.html` from `prototype.html` and `user-stories.md` (use the `architectural-soundness` skill).
6. `/product-isa` command to generate the `ISA.md` (or `ISA.html`) from `architecture.html`, `prototype.html`, and `user-stories.md`.
7. Refine `ISA.html` for truthfulness and correctness with second-agent reviews (second-agent review is already built into the command).
8. Final `isa.html` to implementation:
    1. via the `hivecall` watchdog skill (preferred),
    2. the "orchestrator" OpenCode custom agent (second-best option),
    3. Swarm Tools, or
    4. `/isa-factory`.
