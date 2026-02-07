---
name: multi-council
description: Fan out any prompt to multiple AI models in parallel and display responses inline
subtask: false
---

# Multi-Council

Sends the same prompt to multiple AI models in parallel, displays each agent working in tmux panes (stacked vertically on the right), and returns all responses inline in the main pane. Useful for getting diverse perspectives on any question without saving to files.

## Usage

`/multi-council` - Interactive mode: prompts for inputs before execution

## Interactive Flow

When run, display configuration questions with defaults:

```
/multi-council

1. Prompt/question for models? [required]
   > What are the tradeoffs between REST and GraphQL?

2. Models (comma-separated)? [opus, gemini, gpt]
   > opus, gemini

---
Summary:
- Prompt: "What are the tradeoffs between REST and GraphQL?"
- Models: opus, gemini (2 consultations)

Proceed? [Y/n]
```

**How to answer:**

- User provides answers inline
- Press Enter on question 2 to accept default models
- After submission, display summary and ask "Proceed? [Y/n]"

## Model Aliases

Expand these aliases to full provider/model format:

| Alias    | Full Model Name                 |
| -------- | ------------------------------- |
| `opus`   | `firmware/claude-opus-4-6`      |
| `sonnet` | `firmware/claude-sonnet-4-5`    |
| `gemini` | `firmware/gemini-3-pro-preview` |
| `gpt`    | `openai/gpt-5.3-codex`          |

Users can also specify full model names directly.

## Execution Steps

### Step 1: Parse Inputs

- Validate prompt is provided (required)
- Split models by comma, trim whitespace
- Expand aliases to full model names
- Validate at least 1 model specified

### Step 2: Display Summary and Confirm

Show parsed configuration and wait for "Proceed? [Y/n]" confirmation.

### Step 3: Spawn Panes (60/40 Layout)

Spawn each model in a tmux pane for visibility. Panes stack vertically on the right.

**First model** (establishes 60/40 layout — main pane left, agents right):

```bash
tmux split-window -h -d -t 0 -l 40% 'opencode run --model {full_model1} "{escaped_prompt}"; echo "###DONE###"; exec $SHELL' && tmux select-pane -t 1 -T "{model1-alias}"
```

**Remaining models** (spawn in parallel using batch tool, stack vertically in right column):

```bash
tmux split-window -v -d -t 1 'opencode run --model {full_model2} "{escaped_prompt}"; echo "###DONE###"; exec $SHELL'
tmux split-window -v -d -t 1 'opencode run --model {full_model3} "{escaped_prompt}"; echo "###DONE###"; exec $SHELL'
```

**Name panes** (after all spawns complete):

```bash
tmux select-pane -t 2 -T "{model2-alias}"
tmux select-pane -t 3 -T "{model3-alias}"
```

Notes:

- Use the batch tool to spawn remaining models in parallel
- Panes stay open after completion (`exec $SHELL`) for review
- Use model alias for pane title (e.g., "opus" not "firmware/claude-opus-4-6")

### Step 4: Patient Polling

Poll each pane until `###DONE###` marker appears:

**IMPORTANT: Poll every 10 seconds. Do NOT use longer intervals.**

```
LOOP:
  - For each pane (1, 2, 3...):
    - Capture: tmux capture-pane -p -S - -t {pane_index}
    - If output contains "###DONE###" → mark complete
    - If output grew since last check → reset stagnant timer
    - If stagnant for 3 minutes with no growth → mark as timeout
  - Sleep 10 seconds
  - Repeat until all panes complete or timeout
```

Consultations typically take 1-5 minutes depending on prompt complexity.

### Step 5: Capture Results

For each completed pane, capture the human-readable output directly:

```bash
tmux capture-pane -p -S - -t {pane_index}
```

The output uses default format (no `--format json`), so panes display human-readable formatted text that can be captured directly without parsing.

### Step 6: Display Results Inline

Present results from all models in the main pane. Do NOT kill the tmux panes — leave them open for user reference.

## Results Template

```markdown
# Multi-Council Results

**Prompt:** "{user_prompt}"
**Models:** {count} ({alias_list})

---

## {model1_alias}

**Status:** {Complete | Timeout | Error}

{extracted_response}

---

## {model2_alias}

**Status:** {Complete | Timeout | Error}

{extracted_response}

---

Panes visible on the right side. Close manually when done (Ctrl+B, x).
```

## Defaults

| Input  | Default Value     |
| ------ | ----------------- |
| Prompt | required          |
| Models | opus, gemini, gpt |

## Error Handling

**If a model fails:**

- Capture the error output
- Report status as "Error" with the error message
- Continue with other models

**If a model times out:**

- Report status as "Timeout"
- Include any partial output captured

**If not running in tmux:**

- Display warning: "Warning: Not running in tmux. Panes will not be visible."
- Fall back to sequential execution: run each `opencode run` directly without panes
- Display each response as it completes

## Example Session

```
/multi-council

1. Prompt/question for models? [required]
   > Explain the CAP theorem in distributed systems

2. Models (comma-separated)? [opus, gemini, gpt]
   > (enter for default)

---
Summary:
- Prompt: "Explain the CAP theorem in distributed systems"
- Models: opus, gemini, gpt (3 consultations)

Proceed? [Y/n]
> y

Spawning opus in tmux pane...
Spawning gemini in tmux pane...
Spawning gpt in tmux pane...

Polling for completion...
[opus] Running... (30s elapsed)
[gemini] Running... (30s elapsed)
[gpt] Running... (30s elapsed)
[opus] Complete!
[gemini] Complete!
[gpt] Complete!

Capturing results...

# Multi-Council Results

**Prompt:** "Explain the CAP theorem in distributed systems"
**Models:** 3 (opus, gemini, gpt)

---

## opus

**Status:** Complete

The CAP theorem states that in a distributed system...

---

## gemini

**Status:** Complete

CAP theorem, also known as Brewer's theorem...

---

## gpt

**Status:** Complete

The CAP theorem is a fundamental principle...

---

Panes visible on the right side. Close manually when done (Ctrl+B, x).
```

## Dependencies

- `tmux` - for parallel pane management
- `opencode run` - for running models with `--model` flag (uses default human-readable format)
