---
description: TDD workflow for Unit and Integration Testing
alwaysApply: false
---

<full-tdd-workflow>
When building a new feature or fixing a bug:
1. `tdd-unit-workflow`
2. `tdd-integration-workflow`
3. Code Review: `_ai/tools/quality/hybrid-code-review.md`
4. Update Docs: `update-docs`
5. Merge Branch
</full-tdd-workflow>

<tdd-unit-workflow>
1. User Stories → BDD Scenarios: _ai/tools/tdd/generate_bdd_scenarios.md
2. Scenarios → SUT Scaffold: _ai/tools/tdd/generate-unit-sut-scaffold.md
3. SUT → Red Phase: _ai/tools/tdd/red-phase-unit.md
4. Red Phase → Green Phase: _ai/tools/tdd/green-phase-unit.md
5. Green Phase → Refactor: _ai/tools/tdd/refactor_phase.md
</tdd-unit-workflow>

<tdd-integration-workflow>
1. Red Phase: _ai/tools/tdd/red-phase-integration.md
2. Red Phase → Green Phase: _ai/tools/tdd/green-phase-integration.md
3. Green Phase → Refactor: _ai/tools/tdd/refactor_phase.md
</tdd-integration-workflow>

<update-docs>
1. Update filemap.md: _ai/tools/generators/generate_filemap_documentation.md
2. Update changelog.md
3. Update memory.md
4. Update roadmap.md
</update-docs>