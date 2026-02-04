---
name: multi-perspective-ensemble
description: Fan out a task to multiple AI models and collect diverse perspectives
subtask: false
---

# Multi-Perspective

Sends the same task to multiple AI models in parallel, displays each agent working in tmux panes, and saves each response to a separate markdown file. Useful for getting diverse analytical perspectives on plans, code, or documents.

## Usage

`/multi-perspective` - Interactive mode: prompts for all inputs before execution

## Interactive Flow

When run, display all configuration questions with defaults upfront:

**Questions presented (all at once):**

```
1. Target file to review? [required]
2. Prompt/task for models? [Analyze this file and provide insights, critiques, and suggestions]
3. Models (comma-separated)? [claude-sonnet-4-5, claude-opus-4-5, gemini-3-pro-high]
4. Output directory? [_ai/task/]
```

**How to answer:**

- User provides answers: "1. plan.md", "2. Review for security issues", "3. sonnet, opus", "4. \_ai/task/"
- Press Enter on any question to accept its default
- After submission, display concise summary with exact commands to execute
- Ask "Proceed? [Y/N]" before running

## Command Logic

**Step 1: Collect Inputs**

Display all 4 numbered questions with defaults and wait for user input.

**Step 2: Parse Models**

Split the models string by comma and trim whitespace. The number of models determines how many tasks to fan out.

**Step 3: Display Summary**

Show parsed configuration:

```
Summary:
- Target: @{target-file}
- Prompt: "{user-prompt}"
- Models: {model1}, {model2} ({count} tasks)
- Output files:
  • {output-dir}/{target-name}-{model1}.md
  • {output-dir}/{target-name}-{model2}.md
```

**Step 4: Confirm**

Ask "Proceed? [Y/N]" and wait for user approval.

**Step 5: Execute**

Spawn each model in a tmux pane for visibility. Output is saved to files AND displayed in panes.

**First model** (establishes 60/40 layout — main pane left, agents right):

```bash
!tmux split-window -h -d -t 0 -l 40% 'opencode run --model {model1} --file {target-file} "{prompt}" > {output-dir}/{target-name}-{model1}.md 2>&1; exec $SHELL' && tmux select-pane -t 1 -T "{model1-alias}"
```

**Remaining models** (spawn in parallel using batch tool, stack vertically in right column):

```bash
!tmux split-window -v -d -t 1 'opencode run --model {model2} --file {target-file} "{prompt}" > {output-dir}/{target-name}-{model2}.md 2>&1; exec $SHELL'
!tmux split-window -v -d -t 1 'opencode run --model {model3} --file {target-file} "{prompt}" > {output-dir}/{target-name}-{model3}.md 2>&1; exec $SHELL'
```

**Name panes** (after all spawns complete):

```bash
!tmux select-pane -t 2 -T "{model2-alias}"
!tmux select-pane -t 3 -T "{model3-alias}"
```

Notes:
- Use the batch tool to spawn remaining models in parallel
- Panes stay open after completion (`exec $SHELL`) for review
- Use model alias for pane title (e.g., "opus" not "firmware/claude-opus-4-5")

**Step 6: Report Results**

After all commands complete, display:

```
✓ Complete! {count} perspectives saved:
  • {output-dir}/{target-name}-{model1}.md
  • {output-dir}/{target-name}-{model2}.md

Agents visible in tmux panes (right side). Close panes manually when done (Ctrl+B, x).
```

## Output File Naming

Files are named: `{target-filename-without-extension}-{model}.md`

Example with target `plan.md` and models `sonnet, opus`:

- `_ai/task/plan-sonnet.md`
- `_ai/task/plan-opus.md`

## Defaults

| Input      | Default Value                                                      |
| ---------- | ------------------------------------------------------------------ |
| Target     | required (no default)                                              |
| Prompt     | Analyze this file and provide insights, critiques, and suggestions |
| Models     | claude-sonnet-4-5, claude-opus-4-5, gemini-3-pro-high              |
| Output dir | \_ai/task/                                                         |

## Available Models Reference

Use these exact model names when specifying models. Grouped by provider for easy reference.


**OpenAI (GPT)**

- openai/gpt-5.2-extra-high
- openai/gpt-5.2-high

**LLM Proxy (Alternative Access)**

- firmware/claude-opus-4-5
- firmware/gemini-3-pro-preview

**Quick Aliases**
For convenience, these shorthand aliases map to full model names:

- `opus` → `claude-opus-4-5`
- `gemini` → `gemini-3-pro-high`
- `gpt` → `gpt-5.2-high`

## Error Handling

**If target file doesn't exist:**

- Display error: "Target file not found: {path}"
- Do not proceed with execution

**If output directory doesn't exist:**

- Create it before writing files

**If a model fails:**

- Display error for that specific model
- Continue with remaining models
- Report partial success at the end

**If not running in tmux:**

- Display warning: "Warning: Not running in tmux. Panes will not be visible, but files will still be saved."
- Fall back to original headless execution: `!opencode run --model {model} --file {target-file} "{prompt}" > {output-dir}/{target-name}-{model}.md`

## Example Session

```
/multi-perspective

1. Target file to review? [required]
> _ai/docs/SOME-DOC.md

2. Prompt/task for models? [Analyze this file and provide insights, critiques, and suggestions]
> Review this some-doc for feasibility and suggest improvements

3. Models (comma-separated)? [sonnet, opus, gemini-2.5-pro]
> sonnet, opus

4. Output directory? [_ai/task/]
> (enter for default)

Summary:
- Target: _ai/docs/SOME-DOC.md
- Prompt: "Review this some-doc for feasibility and suggest improvements"
- Models: sonnet, opus (2 tasks)
- Output files:
  • _ai/task/SOME-DOC-sonnet.md
  • _ai/task/SOME-DOC-opus.md

Proceed? [Y/n]
> y

Spawning sonnet in tmux pane...
Spawning opus in tmux pane...

✓ Complete! 2 perspectives saved:
  • _ai/task/SOME-DOC-sonnet.md
  • _ai/task/SOME-DOC-opus.md
```