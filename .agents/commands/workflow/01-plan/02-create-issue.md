---
name: create-issue
description: Create local Plan file.
allowed-tools: [Bash(mkdir:*), Bash(cat:*), Bash(date:*), Task]
---

# Create Issue Command

Owns the local implementation plan, not implementation or publication. Accept approved intent, selected approach, boundaries, and cited evidence from the caller or existing `issue.md`; do not infer a new task from repository activity. Create or revise `{ISSUE_DIR}/plan.md`, then return its path, scope, verification target, and unresolved gaps. Missing material intent or authority requires one focused question; missing owned artifacts need bounded repair from approved context, not invented requirements.

## ⚠️ CRITICAL REQUIREMENTS

**BEFORE PROCEEDING - VERIFY:**

- [ ] Include the required behavioral contract: acceptance criteria, user story/scenarios, scope, relevant code orientation/dependencies, deliverables/error risks, actionable checklist, and Verification Target. For small known work, short sections and explicit inapplicability suffice; use the fuller template below only where it resolves real uncertainty. Diagrams, models, ADR prose, and multiple phases are not mandatory for a mechanical change.
- [ ] Local file created in `_ai/task/` directory

## Usage

/create-issue [task-title] [task-description]

### Auto-Generation

- When no arguments are provided, reuse explicit approved intent from current context; ask if it is absent.
- Use git status and recent commits to ground technical context, not invent user intent.

### My Manual Inputs

- adr.md (ex. `_ai/task/2025-11-26-m6-fuzzy-matching/adr.md`)

---

## Implementation

Translate the selected approach into proportionate executable steps, reusing supplied research. Inspect only missing details needed for an actionable plan; do not automatically restart research or shaping. If a gap changes the approach or promised outcome, return that specific gap to its owner before planning dependent work. This command does not file GitHub issues, implement, commit, or publish.

### Input Processing

The task details are provided as: $ARGUMENTS

Parse the arguments to extract:

1. Task title (first argument or auto-generate if empty)
2. Task description and context (remaining arguments or auto-generate if empty)

### Auto-Generation Logic

When no title/description provided:

1. Analyze current context (git status, recent commits, branch name)
2. Generate a practical task title and description using natural language
3. Focus on immediate development needs and current work
4. If approved intent is absent, stop with the missing decision rather than defaulting to a generic task.

---

### Task Template

Use this expanded local template as reference; keep only the required contract above and applicable detail. An optional size estimate is advisory: calibrate planning to risk and uncertainty. After a correction, reconcile affected criteria and identify needed downstream rechecks; do not require a whole-plan rewrite for an isolated change.

````markdown
## [PARSED TASK TITLE]

<!--
- THIS IS YOUR SOURCE OF TRUTH.
- USE IT TO TAKE ANY NOTES YOU MAY FIND HELPFUL.
- AS YOU COMPLETE THE TASK, UPDATE THIS CHECKLIST TO REFLECT PROGRESS. (- [x] for done, - [ ] for pending)
-->

### Executive Summary

#### What's broken?

[One line: current problem/annoyance]

#### What's the fix?

[One line: core solution]

#### What happens after the fix?

- [User type 1]: [behavior]
- [User type 2]: [behavior]
- [User type 3]: [behavior]

#### What changes?

- `file/path.tsx`: [the new behavior this enables]
- `file/path.tsx`: [the new behavior this enables]
- `file/path.tsx`: [the new behavior this enables]

#### What's the risk?

[What could go wrong, what's protected, fallback plan]

#### What's on me?

[Any manual steps, reviews, deploys, commands]

---

### Description

[Use the parsed task description and expand with clear, concise explanation of what needs to be done. Include the goal or purpose to give context.]

### Current vs Target State Comparison

| Scenario            | Current                                  | Target                              |
| ------------------- | ---------------------------------------- | ----------------------------------- |
| **User Experience** | [Current user behavior/pain points]      | [Desired user experience]           |
| **Code Structure**  | [Existing files/components/architecture] | [New/modified files/components]     |
| **Data Flow**       | [How data currently moves]               | [How data should move]              |
| **Performance**     | [Current performance characteristics]    | [Expected performance improvements] |
| **Dependencies**    | [Current dependencies/libraries]         | [New dependencies required]         |
| **Error Handling**  | [Current error states]                   | [Improved error handling]           |

### Acceptance Criteria

[Carry forward the approved acceptance criteria and their identifiers unchanged, with a reference to the original request or issue.md. If none are supplied, derive measurable, testable criteria from approved intent without inventing behavior; surface unresolved product decisions. Keep implementation choices separate. Format as checkboxes.]

**MEASURABLE Format Examples:**
- ✅ `API endpoint returns 200 status code with valid response schema` (testable via automated test)
- ✅ `Button click triggers navigation to /dashboard within 100ms` (measurable latency)
- ❌ `User has a good experience` (subjective, not measurable)

**TESTABLE Requirements:**
Each AC must answer: "How would I verify this passes?" 
- Include expected outputs, states, or side effects
- Specify exact values, ranges, or conditions when possible
- Reference specific files, functions, or endpoints affected

### User Story

[Reuse the approved user story, or express the same intent as: "As a [user type], I want [functionality] so that [benefit/value]". Reference the relevant acceptance criteria above rather than creating another set.]

### Gherkin BDD Scenarios

[Reuse approved happy-path and edge-path scenarios. If absent, derive them from the acceptance criteria above, with expected outputs/states and references to those criteria:]

```md
### Scenario: [User action and outcome]

Given [user state/precondition]
When [user action]
Then [user-visible outcome with verifiable condition]

Acceptance Criteria References:

- [Relevant criterion identifier or exact text from Acceptance Criteria above]
```
````

[Repeat this template for both primary and secondary scenarios with different contexts.]

### Scope & Boundaries

<!-- Reference the project's tech stack from CLAUDE.md context. -->

#### In Scope

- [ ] [What MUST be done to complete this issue]

#### Out of Scope

- [What should NOT be done (prevents scope creep)]

### Codebase Orientation

- Entry points
- Key patterns to follow
- Where to find examples
- Dev commands

### Dependencies

[List any prerequisites, files or dependencies that may be needed.]

### Data Flow

[Describe how data moves through the system for this task using Mermaid diagrams. Include input sources, processing steps, transformations, and output destinations. This helps understand the complete data journey.]

### Data Models

#### [Model Name]

[Define the structure of Model in your language]

- [Add properties as needed]
- [Provide code snippets]

Add more models if necessary

### Architecture Diagram

[Create a Mermaid diagram showing the key components and their relationships for this task. Illustrate the system structure.]

### Architecture Decision Records

[One paragraph per decision: context, options, decision, consequences. This is where you explicitly write the secondary/tertiary effects.]

### Resources and References

[Link or point to relevant documentation, code, or files from the current project.]

### Deliverables

[List all deliverable files that need to be created or modified based on the task.]

### Error Handling

#### Error Scenarios

1. **Scenario 1:** [Description]

   - **Handling:** [How to handle]
   - **User Impact:** [What user sees]

2. **Scenario 2:** [Description]
   - **Handling:** [How to handle]
   - **User Impact:** [What user sees]

---

### 🧩 Implementation Checklist (Step-by-Step To-Do)

#### Phase 1: Implementation Tasks

<!-- A detailed and thorough decomposed checklist (with tasks and subtasks) that's broken up into logical phases/milestones for a junior developer to accomplish this task. -->

**FORMAT GUIDE** (Use this structure for first phase, then repeat pattern for subsequent phases):

**Phase N: [Descriptive Phase Name] ([Time Estimate])**

**Task N.X: [Clear Task Objective]**

- [ ] ACTION: [Description of task] [specific file/location]
- [ ] ACTION: [Description] [what is being added/changed]
- [ ] ACTION: [Implementation step with technical detail]
  - [ ] SUBTASK: [Nested substep if needed]
- [ ] NOTE: [Reference similar patterns, file locations, line numbers if helpful]

**ACTION PREFIXES:**
Start every checklist item with an **ALL CAPS** Action Verb followed by a colon. This makes the step immediately actionable.

*Suggested prefixes (use these or similar specific verbs):*

- CREATE: / ADD: (New files/features)
- UPDATE: / MODIFY: (Existing code)
- IMPLEMENT: (Core logic)
- RESEARCH: / ANALYZE: (Investigation tasks)
- REFACTOR: (Cleanup)
- VERIFY: / TEST: (Validation steps)
- CONFIG: (Settings/Env)

**CODE SNIPPET GUIDELINES:**

- Include code snippets for complex implementations or non-obvious patterns
- Reference existing code: "Mirror pattern from `file.ts:line-number`" or copy small snippets
- Provide inline code examples for new functions, types, or configurations
- Use markdown code blocks with language syntax highlighting (e.g., `tsx, `ts, ```bash)
- Show before/after code for modifications to existing files
- Keep snippets concise and focused on the specific task

**STYLE RULES:**

- **Use Action Prefixes**: Ensure checklist items start with an ALL CAPS verb (e.g., CREATE:, RESEARCH:).
- Include file paths in backticks: `path/to/file.ts`
- Reference code patterns: "Clone X from `file.ts:20-65`" or "Mirror pattern in `file.ts`"
- Nest substeps when task has multiple parts (use 2-space indentation)
- Add "Implementation notes:" as last item to guide junior developers to examples
- Keep tasks atomic: one clear outcome per task

**REPEAT THIS STRUCTURE** for each subsequent phase/milestone.

**IMPORTANT NOTES:**

- Focus on code implementation. Do not add a test suite. Prefer an existing check as Mechanical. A new test is in-scope only as that oracle, and must assert the user-visible Objective, not compilation.
- Each task should specify the files to create/modify
- Break down into atomic tasks following the guidelines above

---

[Generate the actual implementation checklist following the format above]

#### Phase 2: Verification Gate

Once implementation is complete, obtain `code-quality-gate` approval, then `verification-gate` acceptance before any authorized commit. Dispatch them as separate sessions; neither gate is performed by the implementer. These skills own review depth, proof-route selection, recovery, and completion. Define what must be proven:

- [ ] **web / mobile-web**: Browser verification targets for desktop or responsive/mobile browser UI
- [ ] **desktop / ios / android / macos**: App verification targets
- [ ] **non-ui**: Real CLI/API consumer flow, or internal-only checks when no user or consumer behavior changes

**NOTE**: This phase is SEPARATE from implementation and from commit. Prove the intended task behavior with a named Mechanical command and Observable evidence whenever user or consumer behavior changes. Let `verification-gate` run the cheapest decisive lane first. Do not treat lint/typecheck alone as the user flow.

---

### Verification Target

<!-- Include when the task needs explicit post-implementation validation. State what to prove; verification-gate owns how to prove it. Pick the smallest target and evidence that can prove the task works. -->

Use the `verification-gate` skill's platform routes and evidence rules to prove the task works before any authorized commit.

**Required fields:**
- **Platform**: `web | mobile-web | desktop | ios | android | macos | non-ui`
- **Objective**: The single main outcome that must be proven
- **Falsifier**: The observation that would prove the Objective false
- **Primary Flow**: Shortest realistic path covering the core outcome; identify the target runtime and how the exact candidate will be loaded and identified. State required activation permission and restoration, if applicable; planning grants no shared-runtime mutation authority.
- **Regression Check**: 1 lightweight adjacent behavior check when relevant
- **Mechanical**: Named command(s) plus expected exit/output asserting a relevant machine-checkable condition of the Objective. Prefer an existing check or focused content/asset assertion; together with Observable it must distinguish success, not require new end-to-end infrastructure. Lint/typecheck/format may be extra, never the only command when Platform is UI. "tests pass" is not enough.
- **Observable**: Retained evidence path under `{ISSUE_DIR}/verification/`, using `screenshots/` or `videos/` for UI media and the real consumer result for CLI/API work. Use `n/a` only for genuinely internal `non-ui` changes with no changed user or consumer-observable behavior.
- **Pass Criteria**: Exact condition that counts as success. Must be checkable from Mechanical output and, when not `n/a`, the Observable artifact.
- **Blocked Conditions**: Missing auth, data, runtime access, activation permission, or tooling that would prevent reliable verification; name the prerequisite owner and unlock condition.

**Evidence rules:**
- Mechanical is a command the verifier re-runs and quotes. It is not a paragraph.
- Use `screenshot` when a static state is enough to prove the outcome
- Use `recording` only when motion or lifecycle cannot be proven by screenshots; prefer one recording for the sequence instead of multiple short clips
- Use `test output` or `logs` as Mechanical proof; they do not replace Observable on UI platforms
- For UI work, Observable must show the app-owned result produced by the Primary Flow. A terminal, test runner, CI page, log viewer, or source file is Mechanical evidence, not Observable evidence.
- Start with the cheapest faithful probe. Add another check only when it targets a named unresolved question, provides a new signal that could change the verdict, and remains proportionate to the task. Repetition is appropriate when it tests timing or intermittency and has a stated observation window and stopping condition.
- Save browser artifacts to `{ISSUE_DIR}/verification/videos/{step}.webm`
- Save browser artifacts to `{ISSUE_DIR}/verification/screenshots/{step}.png`

**Example (`web`):**
- Falsifier: Generated images do not appear after submission
- Mechanical: `pnpm test -- generate-cancel` exits 0
- Observable: `{ISSUE_DIR}/verification/screenshots/cancel.png`
1. Open `http://localhost:3000/create`
2. Decide the lightest proof: use screenshots for static proof states, or a recording when motion or lifecycle cannot be shown otherwise
3. If using `recording`, record one full sequence: select model -> enter prompt -> submit -> wait for completion -> verify generated images render
4. If using `screenshot`, capture the one or two proof states that clearly show success

---

[Generate a verification target with an Objective and Falsifier, Mechanical command(s), Observable path or `n/a`, the shortest primary flow, and a relevant regression check. Named oracle tests only; do not add a suite. Let verification-gate challenge a costly or weak proof route rather than mandate replica infrastructure.]

#### Phase 3: Commit Changes

Only when the user authorized a commit, after required gates pass, use the repo's normal commit conventions. Planning alone grants no commit, push, PR, or merge authority.

- [ ] **Create Commit**: Attempt the commit after Phase 2 passes
- [ ] **Handle Hook Failures**: If commit hooks fail, inspect the output, fix the issues, and retry the commit

**NOTE**: Do not bypass commit hooks. Treat hook failures as feedback that must be resolved before the task is considered complete.

### Manual QA Checklist

<!-- Steps that require human action and cannot be automated by the agent. -->

[Checklist of manual steps the developer must perform — environment configuration, third-party dashboard settings, deploy verification, access control checks, etc.]

**Example:**
- [ ] Enable webhook endpoint in Stripe dashboard
- [ ] Verify CloudFlare DNS records propagated

```

---

## Atomic Task Requirements

(for reference only, not to be included in the final document)

**Each task must meet these criteria for optimal agent execution:**

- **File Scope**: Touches 1-4 related files maximum
- **Single Purpose**: One testable outcome per task
- **Specific Files**: Specify files to create/modify
- **Agent-Friendly**: Clear input/output with minimal context switching

## Task Format Guidelines

(for reference only, not to be included in the final document)

- Use checkbox format: `- [ ] Task number. Task description`
- **Use subtasks**: Group related work under parent tasks (e.g., 4, 4.1, 4.2, 4.3)
- **Specify implementation details** as bullet points under each subtask
- **Avoid broad terms**: No "system", "integration", "complete" in task titles
- **DO NOT include a test suite** in implementation tasks. Prefer an existing check as Mechanical. A new test is allowed only as that oracle, and must assert the Objective.
- **Verification gate** should be listed in Phase 2 after implementation tasks; **commit + hook remediation** should be listed separately in Phase 3
- Distinguish between "writing code" and "running validation commands"

## Good vs Bad Task Examples

(for reference only, not to be included in the final document)

❌ **Bad Examples (Too Broad)**:

- "Implement authentication system" (affects too many files, multiple purposes)
- "Add user management features" (vague scope, no files specification)
- "Build complete dashboard" (too large, multiple components)

✅ **Good Examples (Atomic with Subtasks)**:

- 4. Develop API endpoints and routing
  - 4.1 Set up routing configuration and middleware
  - 4.2 IMPLEMENT: Add CRUD API endpoints
  - 4.3 UPDATE: Add API documentation
  - 4.4 RESEARCH: Compare library X vs Y for validation

---

### Local File Creation

When creating local files:

1. Generate slug from task title:
   - Extract 3-5 key words from parsed task title
   - Convert to lowercase, replace spaces/special chars with dashes
   - Remove articles (a, an, the) and filler words (for, with, using)
   - Example: "Implement Spotify Preflight Token Validation" → `spotify-preflight-validation`
2. Create timestamp using `date +%Y-%m-%d`
3. Reuse caller-supplied `ISSUE_DIR`; otherwise create `_ai/task/{TIMESTAMP}/{SLUG}/`.
4. Write file as: `plan.md`
5. Full path: `{ISSUE_DIR}/plan.md`.

Example: `_ai/task/2025-11-20/spotify-preflight-validation/plan.md`

---

### Error Handling

**For Local Files:**

- Check write permissions for `_ai/task/` directory
- Handle directory creation if it doesn't exist
- Provide clear feedback on file location

### Implementation Steps

1. **Parse Arguments**: Extract content, auto-generate if needed
2. **Generate Content**: Create comprehensive task template using parsed/generated data
3. **Create Local File**: Write to `{ISSUE_DIR}/plan.md`; verify it exists before reporting completion. On a write failure, return the path, owner, and unlock condition; do not redirect silently or retry indefinitely.
4. **Report Results**: Provide clear feedback on file location

Start by processing $ARGUMENTS, auto-generating content if needed, and creating the local file.
```
