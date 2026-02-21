# WORKFLOW
This workflow is from idea to product spec. It has not been testing on individual features. Mostly brand new project.

## KICKOFF
1. Freeform ideas then convert to users stories gherking using `_ai/tools/tdd/generate_bdd_scenarios.md`
2. Define Product Specs using  `.opencode/command/project-kickoff/01-product-requirements.md`
3. Feed product specs to tech wizard `.opencode/command/project-kickoff/02-technical-requirements.md`
4. Feed tech specs to generate Roadmap `_ai/tools/_project-starter-workflow/03-generate-roadmap(exp).md`
   1. Run this process for a total of 3 times to increase accuracy and reduce gaps (opus/sonnet model)
5. Use command `/multi-perspective-ensemble.md` [models: opus 4.5, etc] to review the `roadmap.md`
   1. At least 3 models to suggest improvements
   2. Pass prompt `.opencode/command/workflow/00-kickoff/03a-refine-roadmap.md` to the next step
   3. Feed that review back to opus to help decide
6. Convert `roadmap.md` to cells `/file-cells.md` for `Swarm Tools`
7.  Build cells using `Swarm Tools` 

# Tools
- Swarm Tools: http://github.com/joelhooks/swarm-tools/
