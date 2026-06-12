---
name: gather-context
description: Research first SOP before implementing any code change. Use when starting any task that involves modifying an existing codebase features bugs refactors open source contributions. Triggers when I want to work on X help me implement or fix or refactor X gather relevant context for X lets work on this. Launches parallel atlas subagents for local codebase evidence plus voyager external signal research, then presents 3 ranked approaches minimal diff first for user approval before any code is written.
---

# Gather Context

Research a codebase before touching it. Parallel research -> synthesis -> 3 ranked approaches -> wait for approval.

**Primary goal for open source:** Changes must look like the maintainer wrote them. Minimal diff. Maximum style alignment.

---

## Phase 0 — Issue Intake

Before research, frame the task from the issue/request itself.

Artifact directory rule:
- `gather-context` creates `ISSUE_DIR` before research starts.
- `ISSUE_DIR = _ai/task/{YYYY-MM-DD}/{slug}` using the create-issue-compatible nested shape.
- Reuse the same `ISSUE_DIR` for every artifact in this run.

- Restate the issue in plain language
- Extract explicit acceptance criteria
- Mark assumptions and missing product decisions
- Classify the task: `bug` | `feature` | `refactor` | `claim-check`
- Create or update `{ISSUE_DIR}/issue.md` as the proposal source of truth

`issue.md` must contain these sections:
- Original GitHub Issue
- Acceptance Criteria
- Gherkin Happy Path
- Gherkin Edge Path
- Research Index
- Approaches
- Judge Decision placeholder

If the issue is underspecified in a way that would materially change the implementation, stop here and ask 1-3 targeted questions instead of forcing options.

## Phase 1 — Define Target Scenarios, Then Launch Research Agents in Parallel

Before launching subagents, generate two Gherkin scenarios from the original user query: one happy path and one edge path. Keep them minimal and targeted. We are defining the smallest user-visible contract for a simple enhancement, not a full spec.

Use this format:

### Happy Path: [User action and outcome]

Given [user state/precondition]
When [user action]
Then [user-visible outcome with verifiable condition]

### Edge Path: [Boundary/failure case and outcome]

Given [edge precondition]
When [user action]
Then [safe user-visible outcome with verifiable condition]

Acceptance Criteria:

- [Measurable outcome: specific value/threshold/state]

Rules:
- Generate exactly 2 scenarios: happy path + edge path
- Base it on the original user query, not on implementation guesses
- Keep it user-visible, testable, falsifiable, and implementation-agnostic
- Keep it minimal and targeted to the enhancement being requested
- These scenarios are the target goal for all subagents

Spawn all five agents simultaneously using the Task tool:
- Agents 1-4 use `subagent_type: atlas`
- Agent 5 uses `subagent_type: voyager`

Pass both scenarios to every subagent as part of its task context so research stays anchored to the same target behavior.

**Evidence requirement:** Agents 1-4 must cite findings with code snippets, file paths, and line numbers. Agent 5 must cite URLs and quote/snippet the relevant source. No assertions without evidence. Each agent must save its full evidence report under `{ISSUE_DIR}/research/`. If results are thin or inconclusive, note gaps explicitly in Phase 2 — do not proceed with assumptions.

### Agent 1: Code Archaeology
> What does this code do today, and how?

Save full report to `{ISSUE_DIR}/research/code-archaeology.md`.

- Locate entry points, relevant files, core logic
- Trace the current implementation end-to-end
- Identify existing tests covering this area
- Note any TODOs, FIXMEs, or known issues near the target

### Agent 2: Dependency Map
> What breaks if we touch this?

Save full report to `{ISSUE_DIR}/research/dependency-map.md`.

- Map callers and callback/event consumers (what depends on this code, including who reacts to emitted/invoked behavior)
- Map callees and callback/event producers (what this code depends on, including what it emits/invokes)
- Capture invocation cardinality and order for critical interactions (once vs multiple, before vs after)
- Identify public API surface vs internal details
- Assess blast radius: files, modules, tests, and cross-component behavioral side effects at risk
- Flag any breaking change risks

### Agent 3: UX Behavior
> What does the user see today, and what will they see after?

Save full report to `{ISSUE_DIR}/research/ux-behavior.md`.

Given the feature/change being investigated, trace the user-facing path — not the code path.

- **Current UX** — step by step what the user sees and can do today (screens, states, limits, caps, hidden elements)
- **Post-change UX** — same walkthrough after the proposed change; explicitly call out anything that stays blocked, hidden, or broken

The main agent must tell this agent what feature is being added/changed so it can focus the trace. Output must be two clearly labelled sections: **Current UX** and **Post-change UX**. No prose beyond what is needed to describe user-visible behavior. Flag any gap where the post-change UX does not match user expectations.

### Agent 4: Style Fingerprint
> How does this codebase write code?

Save full report to `{ISSUE_DIR}/research/style-fingerprint.md`.

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

### Agent 5: External Signal
> What does the outside world say that should shape this implementation?

Save full report to `{ISSUE_DIR}/research/external-signal.md`.

Research platform conventions, framework behavior, API contracts, ecosystem norms, security/privacy guidance, accessibility rules, and unfamiliar implementation patterns relevant to the target scenarios.

Research priority:
- Official docs, specs, and platform guides
- Upstream repos, changelogs, maintainer issues, and discussions
- Reputable ecosystem examples from known teams or mature libraries
- High-signal articles only when they add concrete implementation guidance

Reject:
- SEO blogs
- Generic tutorials
- Uncited claims
- Stale guidance unless clearly labelled

Output:
- 3-7 bullets max
- URL citation per claim
- Version/date/platform notes where relevant
- **What this changes about our approach**

---

## Phase 2 — Synthesize

After all 5 agents return, combine findings:

1. **Gherkin Happy Path** — the happy path scenario from Phase 1, surfaced verbatim
2. **Gherkin Edge Path** — the edge path scenario from Phase 1, surfaced verbatim
3. **Current UX** — what the user sees and can do today (from Agent 3, surfaced here verbatim)
4. **Post-change UX** — what the user will see after the change (from Agent 3, surfaced here verbatim)
5. **Current behavior** — what the code does today
6. **Constraints** — what must not change (public API, test contracts, style rules)
7. **Style rules** — the extracted cheatsheet from Agent 4
8. **Blast radius** — scope of impact from Agent 2
9. **External signal** — cited implementation-shaping findings from Agent 5
10. **Research Index** — links to all five files in `{ISSUE_DIR}/research/`

Update `issue.md` with the synthesized scenario sections and Research Index. Keep full evidence in the research files, not in `issue.md`.

## Decision Heuristics (Apply to every proposal)

Use these as hard filters before presenting options:

1. **Reuse first (DRY):** prefer existing modules/components/patterns over new ones.
2. **KISS:** choose the least complex approach that meets requirements.
3. **YAGNI:** do not add extensibility/abstractions unless current requirement needs it.
4. **Single source of truth:** avoid duplicated state/data paths.
5. **User trust/safety:** no risky shortcuts that could create silent bad outcomes.

---

## Phase 3 — Present 3 Approaches

Rank by: **minimal diff + style alignment first** -> more involved last.

Each option must include one regression probe describing how to verify no duplicate trigger/clobber regressions were introduced.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

Reason from first principles: work backwards from the goal — what is the simplest change that satisfies the requirement without introducing concepts the codebase doesn't already use?

Write the 3 synthesized approaches into the `Approaches` section of `{ISSUE_DIR}/issue.md`. Do not create `approaches.md`, `decision.md`, `handoff.md`, `plans/`, or `suggestions.md` for this pipeline.

---

## Phase 4 — Hard Stop

Present the 3 options and **wait for explicit user selection**.

Do not begin implementation until the user picks an approach.
