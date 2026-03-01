---
name: gather-context
description: Research-first SOP before implementing any code change. Use when starting any task that involves modifying an existing codebase — features, bugs, refactors, open source contributions. Triggers on: "I want to work on X", "help me implement/fix/refactor X", "gather context for X", "let's work on this". Launches 3 parallel voyager subagents to map current behavior, dependencies/blast radius, and codebase style — then presents 3 ranked approaches (minimal diff first) for user approval before any code is written.
---

# Gather Context

Research a codebase before touching it. Parallel research → synthesis → 3 ranked approaches → wait for approval.

**Primary goal for open source:** Changes must look like the maintainer wrote them. Minimal diff. Maximum style alignment.

---

## Phase 1 — Launch 3 Voyager Agents in Parallel

Spawn all three simultaneously using the Task tool with `subagent_type: voyager`.

### Agent 1: Code Archaeology
> What does this code do today, and how?

- Locate entry points, relevant files, core logic
- Trace the current implementation end-to-end
- Identify existing tests covering this area
- Note any TODOs, FIXMEs, or known issues near the target

### Agent 2: Dependency Map
> What breaks if we touch this?

- Map callers (what depends on this code)
- Map callees (what this code depends on)
- Identify public API surface vs internal details
- Assess blast radius: files, modules, tests at risk
- Flag any breaking change risks

### Agent 3: Style Fingerprint
> How does this codebase write code?

Start with files adjacent to the task. Expand repo-wide when touching shared infrastructure.

Look for:
- Naming conventions (variables, functions, types, files)
- Error handling patterns (exceptions vs return values vs Result types)
- How similar problems are solved elsewhere in the codebase
- Test structure and naming
- Code organization within files (imports, grouping, ordering)
- Linting/formatting config (`.eslintrc`, `pyproject.toml`, `.editorconfig`, etc.)
- Commit/PR style if relevant (small focused changes vs large PRs)

Output: A concise **style cheatsheet** — bullet points only, no prose.

---

## Phase 2 — Synthesize

After all 3 agents return, combine findings:

1. **Current behavior** — what the code does today
2. **Constraints** — what must not change (public API, test contracts, style rules)
3. **Style rules** — the extracted cheatsheet from Agent 3
4. **Blast radius** — scope of impact from Agent 2

---

## Phase 3 — Present 3 Approaches

Use `references/approach-template.md` for consistent output format.

Rank by: **minimal diff + style alignment first** → more involved last.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

---

## Phase 4 — Hard Stop

Present the 3 options and **wait for explicit user selection**.

Do not begin implementation until the user picks an approach.
