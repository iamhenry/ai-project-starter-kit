---
name: gather-context
description: Research first SOP before implementing any code change. Use when starting any task that involves modifying an existing codebase features bugs refactors open source contributions. Triggers when I want to work on X help me implement or fix or refactor X gather relevant context for X lets work on this. Launches 4 parallel voyager subagents to map current behavior dependencies blast radius and codebase style then presents 3 ranked approaches minimal diff first for user approval before any code is written.
---

# Gather Context

Research a codebase before touching it. Parallel research -> synthesis -> 3 ranked approaches -> wait for approval.

**Primary goal for open source:** Changes must look like the maintainer wrote them. Minimal diff. Maximum style alignment.

---

## Phase 0 — Issue Intake

Before research, frame the task from the issue/request itself.

- Restate the issue in plain language
- Extract explicit acceptance criteria
- Mark assumptions and missing product decisions
- Classify the task: `bug` | `feature` | `refactor` | `claim-check`

If the issue is underspecified in a way that would materially change the implementation, stop here and ask 1-3 targeted questions instead of forcing options.

---

## Phase 1 — Define Target Scenario, Then Launch 4 Voyager Agents in Parallel

Before launching subagents, generate exactly 1 Gherkin scenario from the original user query. Keep it minimal and targeted. We are defining the smallest user-visible contract for a simple enhancement, not a full spec.

Use this format:

### Scenario: [User action and outcome]

Given [user state/precondition]
When [user action]
Then [user-visible outcome with verifiable condition]

Acceptance Criteria:

- [Measurable outcome: specific value/threshold/state]

Rules:
- Generate exactly 1 scenario
- Base it on the original user query, not on implementation guesses
- Keep it user-visible, testable, falsifiable, and implementation-agnostic
- Keep it minimal and targeted to the enhancement being requested
- This scenario is the target goal for all subagents

Spawn all four simultaneously using the Task tool with `subagent_type: voyager`.

Pass the scenario to every subagent as part of its task context so research stays anchored to the same target behavior.

**Evidence requirement:** All agents must cite findings with code snippets, file paths, and line numbers. No assertions without evidence. If results are thin or inconclusive, note gaps explicitly in Phase 2 — do not proceed with assumptions.

### Agent 1: Code Archaeology
> What does this code do today, and how?

- Locate entry points, relevant files, core logic
- Trace the current implementation end-to-end
- Identify existing tests covering this area
- Note any TODOs, FIXMEs, or known issues near the target

### Agent 2: Dependency Map
> What breaks if we touch this?

- Map callers and callback/event consumers (what depends on this code, including who reacts to emitted/invoked behavior)
- Map callees and callback/event producers (what this code depends on, including what it emits/invokes)
- Capture invocation cardinality and order for critical interactions (once vs multiple, before vs after)
- Identify public API surface vs internal details
- Assess blast radius: files, modules, tests, and cross-component behavioral side effects at risk
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

1. **Original scenario** — the single target scenario from Phase 1, surfaced verbatim
2. **Current UX** — what the user sees and can do today (from Agent 3, surfaced here verbatim)
3. **Post-change UX** — what the user will see after the change (from Agent 3, surfaced here verbatim)
4. **Current behavior** — what the code does today
5. **Constraints** — what must not change (public API, test contracts, style rules)
6. **Style rules** — the extracted cheatsheet from Agent 4
7. **Blast radius** — scope of impact from Agent 2

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

Use `references/approach-template.md` for consistent output format.

Rank by: **minimal diff + style alignment first** -> more involved last.

Each option must include one regression probe describing how to verify no duplicate trigger/clobber regressions were introduced.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

Reason from first principles: work backwards from the goal — what is the simplest change that satisfies the requirement without introducing concepts the codebase doesn't already use?

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

Present the 3 options and **wait for explicit user selection**.

Do not begin implementation until the user picks an approach.
