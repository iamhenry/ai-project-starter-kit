---
name: gather-context
description: Research existing code before changes, or answer a focused codebase question. Calibrates local and external investigation to uncertainty, then presents supported approaches, minimal diff first, without implementing them.
---

# Gather Context

Research a codebase before touching it. Inspect -> synthesize -> present supported approaches -> stop at the authorized endpoint.

## Scope And Effort

Accept the raw request, scope, authority, and any existing evidence. An optional S/M/L/XL estimate with risk rationale is context, not a fixed topology; revise it when evidence warrants. For a known small change, inspect the affected path, callers, adjacent patterns, and checks directly. Expand investigation for uncertain behavior, shared contracts, security, or consequential failure. Do not fabricate alternatives or external research when one supported approach is sufficient.

For a focused research-only/no-edits request, return a cited answer and unresolved gaps, then stop: no task artifacts, proposal selection, or implementation. For delivery intake, use the artifact workflow below. Missing technical facts call for bounded investigation; missing material intent or authority calls for one focused question. Reuse sound evidence; after changes, identify affected findings and necessary rechecks rather than automatically restarting research.

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

When the caller requests **intake only**, stop after Phase 0 and return `ISSUE_DIR`, the task classification, and unresolved intake questions; leave research, approaches, and judge sections pending. On an explicit request to resume research, reuse that directory and the current intake, reconcile any supplied reproduction evidence, and continue at Phase 1 without repeating intake or reproduction. Without an intake-only request, follow the normal full workflow.

## Phase 1 — Define Target Scenarios And Investigate

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

Use the five lenses below, not a mandatory five-agent campaign. Cover applicable lenses directly for small known work; delegate substantial independent local questions to `atlas` and external questions to `voyager` only when needed and permitted. Parallelize independent questions, not overlapping busywork. Record why a lens is inapplicable rather than inventing findings.

Pass both scenarios to every subagent as part of its task context so research stays anchored to the same target behavior.

**Evidence requirement:** Cite local findings with file paths and line numbers; cite external findings with URLs and relevant snippets. For compact research, retain citations inline in `issue.md` and say so in Research Index. For delegated or substantial research, save reports under `{ISSUE_DIR}/research/` using the relevant names below. If results are thin or inconclusive, note gaps explicitly in Phase 2 — do not proceed with assumptions.

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

After the selected investigation completes, combine applicable findings (lens names below identify subject matter, not required agent counts):

1. **Gherkin Happy Path** — the happy path scenario from Phase 1, surfaced verbatim
2. **Gherkin Edge Path** — the edge path scenario from Phase 1, surfaced verbatim
3. **Current UX** — what the user sees and can do today (from Agent 3, surfaced here verbatim)
4. **Post-change UX** — what the user will see after the change (from Agent 3, surfaced here verbatim)
5. **Current behavior** — what the code does today
6. **Constraints** — what must not change (public API, test contracts, style rules)
7. **Style rules** — the extracted cheatsheet from Agent 4
8. **Blast radius** — scope of impact from Agent 2
9. **External signal** — cited implementation-shaping findings from Agent 5
10. **Research Index** — links to reports actually produced, or inline citations for compact research

Update `issue.md` with the synthesized scenario sections and Research Index. Keep substantial evidence in linked research files; concise evidence may remain inline.

## Decision Heuristics (Apply to every proposal)

Use these as hard filters before presenting options:

1. **Reuse first (DRY):** prefer existing modules/components/patterns over new ones.
2. **KISS:** choose the least complex approach that meets requirements.
3. **YAGNI:** do not add extensibility/abstractions unless current requirement needs it.
4. **Single source of truth:** avoid duplicated state/data paths.
5. **User trust/safety:** no risky shortcuts that could create silent bad outcomes.

---

## Phase 3 — Present Supported Approaches

Rank by: **minimal diff + style alignment first** -> more involved last.

Each option must include a relevant regression probe, or explain why no adjacent behavior is affected. Include duplicate trigger/clobber checks when that risk exists.

For each option ask: *"Would a maintainer approve this PR without asking for changes?"*

Reason from first principles: work backwards from the goal — what is the simplest change that satisfies the requirement without introducing concepts the codebase doesn't already use?

Write the supported approaches into the `Approaches` section of `{ISSUE_DIR}/issue.md`; one obvious approach is enough, otherwise compare meaningful alternatives. Do not create `approaches.md`, `decision.md`, `handoff.md`, `plans/`, or `suggestions.md` for this pipeline.

---

## Phase 4 — Hard Stop

Return `ISSUE_DIR`, classification, evidence locations, supported approaches, and unresolved gaps. Stop for explicit user selection unless selection was already authorized to `judge-proposal`; then hand off to that owner, not implementation.

This skill never implements. Existing approval may be reused only while scope and relevant evidence remain valid.
