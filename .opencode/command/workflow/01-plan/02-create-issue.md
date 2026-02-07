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

[Generate specific, measurable outcomes that define task completion based on the task description. Format as checkboxes.]

### User Story

[Generate one high-impact user story in the format: "As a [user type], I want [functionality] so that [benefit/value]". Include 1-2 specific acceptance criteria that focus on the most critical user-facing behaviors or outcomes.]

### Gherkin BDD Scenarios

[Generate primary (happy path) and secondary (edge case) scenarios in Given-When-Then format, user-focused with 1-2 acceptance criteria each:]

```md
### Scenario: [User action and outcome]

Given [user state/precondition]
When [user action]
Then [user-visible outcome]

Acceptance Criteria:

- [Observable outcome]
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

#### Phase 2: Quality Gates

Once implementation is complete, verify code quality by running these checks in order:

- [ ] **Type Safety**: Run type checking to verify no type errors exist
- [ ] **Code Linting**: Run linting to ensure code follows project standards
- [ ] **Build Verification**: Run build process to confirm no compilation errors
- [ ] **Regression Testing**: Run existing test suite to ensure no functionality broke (DO NOT create new tests unless explicitly requested)

**NOTE**: These quality gates are SEPARATE from implementation. Run them AFTER completing all implementation tasks. Use the project's configured commands (check package.json scripts or project documentation for specific commands).

---

### Browser Verification Plan

<!-- Only include when the task has UI changes. Delete this section if not applicable. -->

Verify the implementation visually in the browser. The agent uses the `chrome-devtools` skill (Puppeteer) to automate these steps and capture screenshots as evidence.

**Guidelines:**
- 3-5 checkpoints covering the core happy-path flow
- Mark 2-3 key moments with `📸` for screenshot capture
- Screenshots saved to `_ai/task/{SLUG}/screenshots/{step}.png`

**Example:**
1. Navigate to `http://localhost:3000/settings`
2. 📸 Verify the new "Notifications" tab renders (screenshot: initial state)
3. Toggle notification preference — verify toggle animates and state persists
4. 📸 Verify success toast appears (screenshot: confirmation)
5. Refresh page — verify preference persisted

---

[Generate 3-5 verification checkpoints for the core flow. Mark 2-3 moments with 📸.]

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
- **Quality gates** (typecheck, lint, build, test) should be listed SEPARATELY in Phase 2 after implementation tasks
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