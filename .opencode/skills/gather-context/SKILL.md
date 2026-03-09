---
name: gather-context
description: Research-first SOP for any codebase task implementation debugging refactor architecture review or claim validation. If user explicitly says gather context invocation is mandatory. Launches 3 parallel voyager subagents to map current behavior dependencies blast radius and codebase style. Then either outputs 3 ranked implementation approaches or an analysis-only verdict report with evidence.
---

# Gather Context

Research a codebase before touching it. Parallel research -> synthesis -> task-mode output.

**Primary goal for open source:** Changes must look like the maintainer wrote them. Minimal diff. Maximum style alignment.

## Trigger Rules

- If the user explicitly asks to "gather context", you MUST invoke this skill.
- Use this skill for implementation tasks and analysis-only tasks:
  - Implement/fix/refactor requests
  - Code review comment validation
  - "Is this claim true?" investigation
  - Architecture/blast-radius assessment before coding
- If evidence is missing or inconclusive, return `Unclear` with exactly what context is missing.

---

## Phase 0 — Issue Intake

Before research, frame the task from the issue/request itself.

- Restate the issue in plain language
- Extract explicit acceptance criteria
- Mark assumptions and missing product decisions
- Classify the task: `bug` | `feature` | `refactor` | `claim-check`

If the issue is underspecified in a way that would materially change the implementation, stop here and ask 1-3 targeted questions instead of forcing options.

---

## Phase 1 — Launch 3 Voyager Agents in Parallel

Spawn all three simultaneously using the Task tool with `subagent_type: voyager`.

Default: always launch all 3. Only skip an agent if the task is truly trivial; if skipped, explain why.

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

## Decision Heuristics (Apply to every proposal)

Use these as hard filters before presenting options:

1. **Reuse first (DRY):** prefer existing modules/components/patterns over new ones.
2. **KISS:** choose the least complex approach that meets requirements.
3. **YAGNI:** do not add extensibility/abstractions unless current requirement needs it.
4. **Single source of truth:** avoid duplicated state/data paths.
5. **User trust/safety:** no risky shortcuts that could create silent bad outcomes.

If an option violates any filter, either fix it or explicitly mark why the tradeoff is unavoidable.

---

## Phase 3 — Present 3 Approaches

Choose output mode by task type:

- Implementation requested -> use `references/approach-template.md`.
- Analysis-only requested (review/validation/investigation) -> use `references/review-verdict-template.md`.

Rank by: **minimal diff + style alignment + reuse/simplicity first** → more involved last.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

Reason from first principles: work backwards from the goal — what is the simplest change that satisfies the requirement without introducing concepts the codebase doesn't already use?

For each option, include one line in this format: `Why this option: reuses <existing thing>, adds <nothing/new X only if needed now>, expected effort <Low/Med/High>.`

After the user selects an option, emit a workflow handoff packet with:

- Chosen approach
- Implementation steps
- Verification steps
- PR summary bullets
- Files likely to change
- Tests to add/update
- Risks / rollback notes
- Commit/PR summary draft

---

## Phase 4 — Hard Stop

Implementation mode: present the 3 options and **wait for explicit user selection**.

Analysis-only mode: stop after verdict report. Do not propose implementation unless user asks.

## Analysis-Only Verdict Standard

When the task is validation/review (no code edits requested), each claim must include:

1. Verdict: `Valid` | `Invalid` | `Unclear`
2. Evidence: direct citation(s) with file path and line number
3. Blast radius: who/what is affected if claim is true
4. Confidence: high/medium/low with one-sentence rationale

No verdict without direct code evidence.
