---
name: create-issue
description: Create local Plan file.
allowed-tools: [Bash(mkdir:*), Bash(cat:*), Bash(date:*), Task]
---

# Create Issue Command

Creates detailed task templates using comprehensive templates designed for delegating work to junior developers. Creates local files in `_ai/task/`.

## ⚠️ CRITICAL REQUIREMENTS

**BEFORE PROCEEDING - VERIFY:**

- [ ] ALL 15+ template sections included (no exceptions)
- [ ] Local file created in `_ai/task/` directory

## Usage

/create-issue [task-title] [task-description]

### Auto-Generation

- When no arguments provided: auto-generates title and description using natural language based on current context
- Uses git status, recent commits, and general project state for smart defaults

### My Manual Inputs

- adr.md (ex. `_ai/task/2025-11-26-m6-fuzzy-matching/adr.md`)

---

## Implementation

You are a task template creator that takes user input and creates comprehensive, well-structured templates as GitHub issues and/or local files.

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
4. Default to generic development task if context is minimal

---

### Task Template

Create tasks using this comprehensive template (used for both GitHub issues and local files):

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

[Generate acceptance criteria that are **measurable** and **testable**. Each criterion must include verifiable conditions, not just desired states. Format as checkboxes.]

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

[Generate one high-impact user story in the format: "As a [user type], I want [functionality] so that [benefit/value]". Include 1-2 acceptance criteria following the measurable/testable format above, focusing on the most critical user-facing behaviors or outcomes.]

### Gherkin BDD Scenarios

[Generate primary (happy path) and secondary (edge case) scenarios in Given-When-Then format. Each scenario must include testable acceptance criteria with expected outputs/states:]

```md
### Scenario: [User action and outcome]

Given [user state/precondition]
When [user action]
Then [user-visible outcome with verifiable condition]

Acceptance Criteria:

- [Measurable outcome: specific value/threshold/state]
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

- Focus ONLY on code implementation - NO test creation unless explicitly requested
- Each task should specify the files to create/modify
- Break down into atomic tasks following the guidelines above

---

[Generate the actual implementation checklist following the format above]

#### Phase 2: Verification Gate

Once implementation is complete, verify the task outcome before attempting a commit. Choose the lightest verification mode that can prove the core user flow works:

- [ ] **Browser Flow**: Use when the task depends on multi-step UI behavior, async transitions, or end-to-end interaction in the browser
- [ ] **Browser Static**: Use when screenshots are enough to prove visible UI changes
- [ ] **Non-Browser**: Use when backend, CLI, API, or data checks provide a stronger proof than browser automation

**NOTE**: This phase is SEPARATE from implementation and from commit. The goal is to prove the intended task behavior works end to end, not just to run code quality commands.

---

### Verification Gate Plan

<!-- Include when the task needs explicit post-implementation validation. Pick the smallest mode that can prove the task works. -->

Use the `verification-gate` skill to prove the task works before commit. When browser evidence is needed, the verification-gate skill should rely on the `agent-browser` skill for browser actions, screenshots, and recordings.

**Required fields:**
- **Verification Mode**: `browser-flow`, `browser-static`, or `non-browser`
- **Objective**: The single main outcome that must be proven
- **Primary Flow**: 3-5 checkpoints covering the core happy-path flow
- **Regression Check**: 1 lightweight adjacent behavior check when relevant
- **Evidence Plan**: Mark proof points with `🎥` and/or `📸` only when needed
- **Pass Criteria**: Exact condition that counts as success
- **Blocked Conditions**: Missing auth, data, environment, or tooling that would prevent reliable verification

**Evidence rules:**
- Use `📸` when a static screenshot is enough to prove the outcome
- Use `🎥` when the user journey requires interaction or async state changes; prefer one recording for the full sequence instead of multiple short clips
- Save browser artifacts to `_ai/task/{SLUG}/verification/videos/{step}.webm`
- Save browser artifacts to `_ai/task/{SLUG}/verification/screenshots/{step}.png`

**Example (`browser-flow`):**
1. Open `http://localhost:3000/create`
2. Decide the lightest proof: use `📸` if a static state is enough, or `🎥` if the flow needs interaction proof
3. If using `🎥`, record one full sequence: select model -> enter prompt -> submit -> wait for completion -> verify generated images render
4. If using `📸`, capture the one or two proof states that clearly show success

---

[Generate a verification gate plan with 3-5 checkpoints for the primary flow and 0-1 regression checks. Use the lightest evidence plan that proves success or failure. Prefer a single full-flow video for interactive journeys and screenshots only for static proof states.]

#### Phase 3: Commit Changes

Once verification passes, commit the work using the repo's normal commit conventions.

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
- **DO NOT include test creation** in implementation tasks unless explicitly requested in the task description
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
3. Create directory: `_ai/task/{TIMESTAMP}-{SLUG}/`
4. Write file as: `plan.md`
5. Full path: `_ai/task/{TIMESTAMP}-{SLUG}/plan.md`

Example: `_ai/task/2025-11-20-spotify-preflight-validation/plan.md`

---

### Error Handling

**For Local Files:**

- Check write permissions for `_ai/task/` directory
- Handle directory creation if it doesn't exist
- Provide clear feedback on file location

### Implementation Steps

1. **Parse Arguments**: Extract content, auto-generate if needed
2. **Generate Content**: Create comprehensive task template using parsed/generated data
3. **Create Local File**: Write to `_ai/task/{TIMESTAMP}-{SLUG}/plan.md`
4. **Report Results**: Provide clear feedback on file location

Start by processing $ARGUMENTS, auto-generating content if needed, and creating the local file.
```
