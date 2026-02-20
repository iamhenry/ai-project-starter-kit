# WORKFLOW
This workflow is from idea to product spec. It has not been testing on individual features. Mostly brand new project.

## PHASE 1
1. Freeform ideas then convert to users stories gherking using `_ai/tools/tdd/generate_bdd_scenarios.md`
2. Define Product Specs using  `.opencode/command/project-kickoff/01-product-requirements.md`
3. Feed product specs to tech wizard `.opencode/command/project-kickoff/02-technical-requirements.md`
4. Feed tech specs to generate Roadmap `_ai/tools/_project-starter-workflow/3-generate-roadmap(exp).md`
    1. Do 3 rounds (1 for each model) to suggest improvements 
    2. Pass prompt to command `.opencode/command/workflow/00-kickoff/03a-refine-roadmap.md`
    3. Use command `.opencode/command/workflow/01-plan/multi-perspective-ensemble.md` [models: gemini 3 pro, gpt 5.2 med, opus 4.5] review the `tech-requirements.md`
    4. Feed that review back to opus to help decide
5. Convert roadmap to cell `/file-cells.md` for `Swarm Tools`
6. Build cells using `Swarm Tools` 

# Tools
- Swarm Tools: http://github.com/joelhooks/swarm-tools/