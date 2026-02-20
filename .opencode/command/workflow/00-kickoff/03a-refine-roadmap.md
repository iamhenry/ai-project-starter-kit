> Use when I need to review and flush out spec.md from `kickoff` workflow, technical-requirements.md
> This is a prompt (not a slash command) to pass into `.opencode/command/workflow/01-plan/multi-perspective-ensemble.md`

# Instructions
Carefully review this entire plan for me and come up with your best revisions in terms of better architecture, what low hanging fruit can enhance current experience, changed features, etc. to make it better, more robust/reliable, more performant, more compelling/useful, etc.
For each proposed change, give me your detailed analysis and rationale/justification for why it would make the project better along with the git-diff style changes relative to the original markdown plan shown below: `Insert spec.md or similar doc`

# Output
- Markdown doc with yaml frontmatter including date/time, and version
- filename should include model name (ex. opus, gemini 3, gpt 5.2 xtra). It MUST include the reasoining level (ex. high, xtra, etc.)
- append to existing review view to keep track of already made suggestions and changes
- doc must contain the contents from the review in VERBATIM
