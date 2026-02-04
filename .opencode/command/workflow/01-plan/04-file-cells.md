---
name: file-cells
description: Convert a structured plan document into hive cells for swarm execution
---

## /file-cells - Plan to Cells Conversion

Convert the provided document into hive cells (epic + subtasks) for swarm execution.

**INPUT:** $ARGUMENTS (path to plan/spec/prd document)

---

### PHASE 1: Document Analysis

Read the document and extract:

| Element             | What to Find                                                  |
| ------------------- | ------------------------------------------------------------- |
| Deliverables        | Files to create/modify (look for file paths)                  |
| Tasks               | Discrete units of work (numbered lists, phases, steps)        |
| Code Snippets       | Implementation details (fenced code blocks with line numbers) |
| Acceptance Criteria | Success conditions (checkboxes, "should", "must")             |
| ADRs/Decisions      | Architectural choices (decision records, "why" sections)      |
| Out of Scope        | Explicit exclusions                                           |
| Patterns            | Auth, styling, utilities mentioned in codebase sections       |

---

### PHASE 2: Auto-Detect Dependencies

Analyze task relationships to determine execution waves:

1. **Identify file dependencies** - Which tasks create files that other tasks import
2. **Identify logical dependencies** - Config before components, components before integration
3. **Group into waves** - Tasks with no dependencies = Wave 1, tasks depending on Wave 1 = Wave 2, etc.

**Default Heuristics:**
- Foundation (config, types, utils, schemas) → Wave 1 (Priority 3)
- Implementation (components, functions, adapters) → Wave 2 (Priority 2)
- Integration (routes, wiring, orchestration) → Wave 3 (Priority 1)

**Use `hive_cells` to check existing cells and avoid duplicates.**

---

### PHASE 3: Cell Structure

**Epic Description Template:**
```
{Brief description of overall task}

SOURCE OF TRUTH: {document_path}

EXECUTION PLAN:
- Wave 1 (parallel): {task list}
- Wave 2 (parallel): {task list}
- Wave 3 (sequential): {task list}

KEY REFERENCES:
- Acceptance Criteria: L{x}-L{y}
- Deliverables: L{x}-L{y}
- ADR Decisions: L{x}-L{y}
- Out of Scope: L{x}-L{y}

IMPORTANT PATTERNS:
- {Auth pattern if applicable}
- {Styling pattern if applicable}
- {Other codebase patterns}

TIME ESTIMATE: {from document or calculated}
```

**Subtask Description Template:**
```
MANDATORY: Read {document_path} before starting.

TASK SPEC: L{start}-L{end}
CODE SNIPPET: L{start}-L{end}

FILES: {file_paths}
NOTE: {directory creation if new path, other special instructions}

{One-line task description}

ADR: {relevant decisions with line refs if applicable}

ACCEPTANCE: {success criteria from document}
```

**Rules:**
- Always include BOTH task spec AND code snippet line ranges
- Add directory creation notes for new paths
- Reference ADRs inline where relevant
- Verification is handled by `swarm_complete` (built-in)

---

### PHASE 4: Create Cells

1. `hive_create_epic(epic_title, epic_description, subtasks)` - Create structure
2. `hive_update(id, description)` - Add detailed descriptions with line refs
3. `hive_sync()` - Sync to git

---

### PHASE 5: Verification Pass

Re-read document and verify:

- [ ] Every deliverable file has a corresponding cell
- [ ] Line references are accurate (task spec matches document)
- [ ] Wave groupings make sense (no circular dependencies)
- [ ] Missing context added (directory creation, patterns, ADR notes)
- [ ] Acceptance criteria in each cell

Update cells with corrections via `hive_update` if needed.

---

### OUTPUT

Display summary table:

| Wave | Cell ID | Title | Priority | Files |
| ---- | ------- | ----- | -------- | ----- |

Then: "Cells created. Run swarm coordinator to execute waves."