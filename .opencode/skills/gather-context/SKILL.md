---
name: gather-context
description: Research first SOP before implementing any code change. Use when starting any task that involves modifying an existing codebase features bugs refactors open source contributions. Triggers when I want to work on X help me implement or fix or refactor X gather context for X lets work on this. Launches 3 parallel voyager subagents to map current behavior dependencies blast radius and codebase style then presents 3 ranked approaches minimal diff first for user approval before any code is written.
---

# Gather Context

Research a codebase before touching it. Parallel research → synthesis → 3 ranked approaches → wait for approval.

**Primary goal for open source:** Changes must look like the maintainer wrote them. Minimal diff. Maximum style alignment.

---

## Phase 1 — Launch 4 Voyager Agents in Parallel

Spawn all four simultaneously using the Task tool with `subagent_type: voyager`.

**Evidence requirement:** All agents must cite findings with code snippets, file paths, and line numbers. No assertions without evidence. If results are thin or inconclusive, note gaps explicitly in Phase 2 — do not proceed with assumptions.

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

### Agent 3: UX Behavior
> What does the user see today, and what will they see after?

Given the feature/change being investigated, trace the user-facing path — not the code path.

- **Current UX** — step by step what the user sees and can do today (screens, states, limits, caps, hidden elements)
- **Post-change UX** — same walkthrough after the proposed change; explicitly call out anything that stays blocked, hidden, or broken

The main agent must tell this agent what feature is being added/changed so it can focus the trace. Output must be two clearly labelled sections: **Current UX** and **Post-change UX**. No prose beyond what is needed to describe user-visible behavior. Flag any gap where the post-change UX does not match user expectations.

### Agent 4: Style Fingerprint
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

After all 4 agents return, combine findings:

1. **Current UX** — what the user sees and can do today (from Agent 3, surfaced here verbatim)
2. **Post-change UX** — what the user will see after the change (from Agent 3, surfaced here verbatim)
3. **Current behavior** — what the code does today
4. **Constraints** — what must not change (public API, test contracts, style rules)
5. **Style rules** — the extracted cheatsheet from Agent 4
6. **Blast radius** — scope of impact from Agent 2

---

## Phase 3 — Present 3 Approaches

Use `references/approach-template.md` for consistent output format.

Rank by: **minimal diff + style alignment first** → more involved last.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

Reason from first principles: work backwards from the goal — what is the simplest change that satisfies the requirement without introducing concepts the codebase doesn't already use?

---

## Phase 4 — Hard Stop

Present the 3 options and **wait for explicit user selection**.

Do not begin implementation until the user picks an approach.
