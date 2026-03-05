---
name: file-cells
description: Convert a structured plan document into hive cells for swarm execution
---

## /file-cells - Plan to Cells Conversion

Convert the provided document into hive cells (epic + subtasks) for swarm execution.

**INPUT:** $ARGUMENTS (path to plan/spec/prd document)

---

### PHASE 1: Document Analysis

Read the document and **identify line ranges** (do NOT duplicate content into cells):

| Element             | What to Find                                                  |
| ------------------- | ------------------------------------------------------------- |
| Deliverables        | Files to create/modify (look for file paths)                  |
| Tasks               | Discrete units of work (numbered lists, phases, steps)        |
| Code Snippets       | Implementation details (fenced code blocks with line numbers) |
| Acceptance Criteria | Success conditions (checkboxes, "should", "must")             |
| ADRs/Decisions      | Architectural choices (decision records, "why" sections)      |
| Out of Scope        | Explicit exclusions                                           |
| Patterns            | Auth, styling, utilities mentioned in codebase sections       |

**CRITICAL:** Never duplicate code snippets into cells. Reference line ranges instead.
- Format: `plan.md:L15-L42` (filepath + line range in one reference)
- Workers read directly from source document
- Prevents drift when plan.md updates

---

### RESPONSIBILITY SPLIT

**Workers read plan.md for:**
- Code snippets (implementation details)
- Acceptance criteria (success conditions)
- Styling reference (UI patterns)
- Error handling (failure modes)

**Cells contain only:**
- SOURCE_REF: filepath + line range
- GOAL: 1-line objective
- FILES: paths to modify
- DAG dependencies

This ensures plan.md stays the single source of truth.

---

### PHASE 2: Auto-Detect Dependencies

Analyze task relationships to determine execution waves and explicit DAG edges:

1. **Identify file dependencies** - Which tasks create files that other tasks import
2. **Identify logical dependencies** - Config before components, components before integration
3. **Build dependency edges** - For each task, list prerequisite task keys
4. **Cycle check** - Topologically validate edges; if cycle exists, stop and report cycle path
5. **Group into waves** - Tasks with no dependencies = Wave 1, tasks depending on Wave 1 = Wave 2, etc.

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
SOURCE_REF: {document_path}:L{start}-L{end}
GOAL: {one-line high-level objective}
FILES: {file_paths to create/modify}

---

MANDATORY: Read {document_path}:L{start}-L{end} before starting.

TASK SPEC: {document_path}:L{start}-L{end}
CODE SNIPPET: {document_path}:L{start}-L{end}

NOTE: {directory creation if new path, other special instructions}

ADR: {relevant decisions with line refs if applicable}

ACCEPTANCE: {success criteria from document}

DAG_DEPENDS_ON_KEYS: {comma-separated task keys or NONE}
DAG_DEPENDS_ON_IDS: {comma-separated cell IDs or PENDING_RESOLUTION}
```

**Rules:**
- **SOURCE_REF + GOAL + FILES** are mandatory in every subtask (shared_context pattern)
- Include filepath in all line references: `plan.md:L15-L42`
- Never duplicate code snippets—workers read from source document
- Add directory creation notes for new paths
- Reference ADRs inline where relevant
- Include DAG dependency lines in every subtask description
- Verification is handled by `swarm_complete` (built-in)
- For each milestone, add one terminal task cell: `Verify + Commit milestone work`.
- Terminal gate cell MUST depend on all prior task cells in the same milestone.
- Gate cell acceptance MUST require committing milestone changes so Husky pre-commit runs; on hook failure, create fix task(s) and retry commit.

---

### PHASE 4: Create Cells

1. `hive_create_epic(epic_title, epic_description, subtasks)` - Create structure
2. Resolve predecessor task keys to created cell IDs
3. Persist structured dependency edges on each task (`dependencies` array) using available hive/swarm tooling
4. Read back updated cells and verify `dependencies` match planned predecessors
5. `hive_update(id, description)` - Add detailed descriptions with line refs + DAG lines
6. `hive_sync()` - Sync to git

---

### PHASE 5: Verification Pass

Re-read document and verify:

- [ ] Every deliverable file has a corresponding cell
- [ ] No code snippets duplicated in cells (only filepath:line references)
- [ ] Line references include filepath: `plan.md:L15-L42` format
- [ ] Wave groupings make sense (no circular dependencies)
- [ ] Every non-Wave-1 task has explicit predecessors
- [ ] Cell `dependencies` arrays match DAG plan (no text-only dependencies)
- [ ] Missing context added (directory creation, patterns, ADR notes)
- [ ] Acceptance criteria in each cell
- [ ] Every milestone has exactly one terminal `Verify + Commit milestone work` cell
- [ ] Terminal gate cell depends on all other cells in its milestone

Update cells with corrections via `hive_update` if needed.

If structured `dependencies` cannot be persisted/read back, mark result as BLOCKED and report tooling gap (do not claim DAG-complete).

---

### OUTPUT

Display summary table:

| Wave | Cell ID | Title | Priority | Files |
| ---- | ------- | ----- | -------- | ----- |

Then: "Cells created. Run swarm coordinator to execute waves."
