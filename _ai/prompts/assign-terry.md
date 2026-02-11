---
name: assign-terry
description: Assign file reference to Terry CLI with interactive configuration
subtask: false
---

# Assign Terry

Assigns a file reference to Terry CLI for automated work with interactive
configuration options for branch, models, and task parameters.

## Usage

`/assign-terry` - Interactive mode: configure and assign Terry tasks with numbered prompts
`/assign-terry @filename.md` - Assign file reference directly to Terry

The command handles the workflow automatically based on arguments provided.

## Interactive Mode (No Args)

When run without arguments, displays all configuration questions with defaults upfront:

**Questions presented (all at once):**

```
1. Plan file? [_ai/task/{LATEST_DIR}/plan.md]
2. Target Branch? [<current branch via git>]
3. How many tasks? [1]
4. Models? [gpt-5.1-codex-max-xhigh, sonnet]
```

Where `{LATEST_DIR}` is dynamically resolved from the most recent task directory.

**How to answer:**

- User provides all answers at once: "1. plan.md", "2. current branch", "3. 2", "4. sonnet"
- Or press Enter to accept all defaults
- After submission, displays concise summary with exact commands to execute
- Asks "Proceed? [Y/N]" before running `terry create`

**Defaults explained:**

- Plan file: Auto-detected from most recent `_ai/task/` directory (see detection logic below)
- Branch: Run `git rev-parse --abbrev-ref HEAD` to get current branch as default for `--branch` flag
- Models: Comma-separated list; defaults to `gpt-5.2-codex-max-xhigh, sonnet`

## Command Logic

**Check arguments:**

- If no arguments: Run interactive mode workflow
- If argument starts with `@`: Run file reference workflow

**Interactive Mode Workflow:**

1. Run `ls -td _ai/task/20* 2>/dev/null | head -1` to find latest task directory
2. Check if `{LATEST_DIR}/plan.md` exists:
   - If exists: use full path as default for question 1 (e.g., `_ai/task/2025-12-12-floating-bar-connection-counter/plan.md`)
   - If not exists: show `[none - required]` and require user to provide path manually
3. Run `git rev-parse --abbrev-ref HEAD` to get current branch for default
4. Display all 4 numbered questions with resolved defaults upfront
5. User provides answers (or Enter to accept all defaults)
6. Validate plan file exists before proceeding - if not found, display error and ask user to provide valid path
7. Display summary of parsed answers
8. Display exact `terry create` commands that will be executed
9. Confirm "Proceed? [Y/N]"
10. Execute commands only after user approval

**File Reference Workflow:**

1. Check if file exists
2. Create Terry task with natural language instruction to read the file
3. Terry handles file reading and interpretation during execution

Both workflows use the `terry create` command with appropriate context for automated work.

# Docs

- If you are stuck and need more information please read `https://docs.terragonlabs.com/docs/integrations/cli`

## Terry CLI

- IMPORTANT: Always use `--branch` flag to a branch
- `terry create "Refactor code" --model sonnet` command to specify model (ex. `gpt-5.1-codex-high`, `opencode/gemini-2.5-pro`, `gpt-5.1-codex-max-medium` or `gpt-5.2-high`)
- Default to models: `gpt-5.1-codex-max-medium` and `sonnet` when creating multiple tasks

## What This Command Does

**With @filename** (File reference workflow):

1. **Check File** - Verify file exists in current directory
2. **Create Terry Task** - Assign file reference to Terry CLI with instructions to read it
3. **Confirmation** - Returns clear confirmation of task creation

## Step-by-Step Workflow

### Create Terry Task

<!--
CRITICAL: REUSE THIS EXACT PROMPT TEMPLATE VERBATIM
This is the standard prompt for file reference workflow.
Only substitute: @specs.md → @{actual-filename}
DO NOT modify the core instruction text.
-->

```bash
terry create --branch main "Work on the requirements in @specs.md file. Read the file for full context and specifications. Use it as your todo list (Use format: - [x]). As you complete each item actively mark done in the checklist and write down any notes (inline) you may find helpful along the way. Append agent name at the end of the branch name (ex. `m4-[agent-name]/real-transfer-requirements`, ex. "agent name" can be something like claude, codex, etc)."
```

**Prompt Template Requirements:**

- MUST reuse the exact text above for all file reference workflows
- ONLY substitute the filename (e.g., `@specs.md` → `@plan.md`)
- DO NOT modify instructions about checklist format, notes, or branch naming

### Confirmation

Display success message with:

- File reference assigned
- Terry task creation status
- Branch name (if created)

## Error Handling

If file not found:

- Display error message with file path attempted
- Request user to provide valid file path

If Terry CLI fails:

- Display error message with file details
- Provide fallback instructions for manual assignment

## Implementation Details

**File Reference Assignment:**

- Validates file existence before creating task
- Uses standardized prompt template for consistency
- Includes instructions for checklist tracking and branch naming
- Provides full file context to Terry agent

**Terry Task Creation:**

- Automatic branch creation enabled
- File reference with @ syntax for direct assignment
- Agent name appended to branch for traceability