---
name: verify-cells-ensemble
description: Fan out cells correctness to multiple AI models in parallel and synthesize results
---

---

# Cells Verification Ensemble

Spawns parallel verification tasks across multiple AI models using tmux, then synthesizes the results. Each model verifies that cells created from ROADMAP.md are complete, accurate, and well-structured.

## Inputs

- Roadmap.md

## Interactive Flow

Present all questions with defaults. User presses Enter to accept defaults.

```
/verify-cells-ensemble

1. Models (comma-separated)? [opus, gemini, gpt]
   >

2. Additional focus? [none]
   Example: "focus on dependency graph" or "check code snippets"
   >

---
Summary:
- Roadmap: _ai/docs/ROADMAP.md
- Cells: hive_cells()
- Models: opus, gemini, gpt (3 verifications)
- Focus: none

Proceed? [Y/n]
```

## Model Aliases

| Alias    | Full Model Name                 | Provider |
| -------- | ------------------------------- | -------- |
| `opus`   | `firmware/claude-opus-4-5`      | Firmware |
| `gemini` | `firmware/gemini-3-pro-preview` | Google   |
| `gpt`    | `openai/gpt-5.2`                | OpenAI   |

Users can also specify full model names directly.

## Execution Steps

### Step 1: Parse Inputs

- Split models by comma, trim whitespace
- Expand aliases to full model names
- Validate at least 1 model specified

### Step 2: Create Tmux Session

```bash
tmux kill-session -t cells-verify 2>/dev/null
tmux new-session -d -s cells-verify -n {model1-alias}
tmux new-window -t cells-verify -n {model2-alias}
tmux new-window -t cells-verify -n {model3-alias}
# ... for each model
```

### Step 3: Build Verification Prompt

```markdown
You are verifying the correctness of a hive cells (issue tracking) mapping.

## Task

Verify that the cells created from the ROADMAP.md plan are:
1. **Complete** - All milestones have epic cells AND all tasks have task cells
2. **Accurate** - Cell descriptions match the roadmap details (objectives, time estimates, ADRs)
3. **Well-structured** - Dependencies form a valid DAG; tasks link to parent epics
4. **Verbose** - Cells contain sufficient context (file paths, code snippets, acceptance criteria)

## Additional Focus

{additional_context or "None specified"}

## Instructions

1. First, read the roadmap: `cat _ai/docs/ROADMAP.md`
2. Get the cells list using the `hive_cells()` MCP tool
3. Compare each milestone/phase against created cells

## Verification Checklist

### For Epics (Milestones):
- [ ] All milestones (M0, M1, M2...) have a corresponding epic cell
- [ ] Epic titles match milestone names
- [ ] Epic descriptions include: objective, time estimate, execution order, key ADRs, out of scope
- [ ] Epic acceptance criteria match milestone acceptance criteria

### For Tasks:
- [ ] All tasks within each milestone have a corresponding task cell
- [ ] Task titles match roadmap task titles
- [ ] Task descriptions include: file paths, code snippets, patterns, gotchas
- [ ] Acceptance criteria are **measurable** (specific values/thresholds) AND **testable** (verifiable conditions)
- [ ] Each AC answers "How would I verify this passes?" with concrete method
- [ ] Dependencies match execution plan (BLOCKING, PARALLEL, DEPENDENT)

### For Structure:
- [ ] Tasks link to their parent epic via parent_id
- [ ] No orphaned tasks (every task relates to an epic)
- [ ] Dependency graph forms valid DAG (no cycles)

## Output Format

Return a structured report:

### Summary
- Milestones in ROADMAP: {X}
- Epics found: {Y}
- Tasks in ROADMAP: {A}
- Task cells found: {B}
- Epic coverage: {percentage}
- Task coverage: {percentage}

### Missing Cells
| Milestone | Task | Expected |
| --------- | ---- | -------- |

### Incorrect Mappings
| Cell ID | Issue | Recommendation |
| ------- | ----- | -------------- |

### Dependency Issues
| Cell ID | Expected Deps | Actual Deps | Issue |
| ------- | ------------- | ----------- | ----- |

### Quality Assessment
- Description completeness: {score}/10
- Code snippet inclusion: {score}/10
- Acceptance criteria clarity: {score}/10

### Verdict
**{PASS | PASS WITH NOTES | FAIL}** - {brief reasoning}
```

### Step 4: Send Commands to Each Window

For each model/window:

```bash
tmux send-keys -t cells-verify:{alias} 'opencode run --model {full_model_name} --format json "{escaped_prompt}"; echo "###DONE###"' C-m
```

### Step 5: Patient Polling

Poll each window until `###DONE###` marker appears:

**IMPORTANT: Poll every 10 seconds. Do NOT use longer intervals.**

```
LOOP:
  - Capture: tmux capture-pane -p -S - -t cells-verify:{alias}
  - If output contains "###DONE###" → mark complete
  - If output grew since last check → reset stagnant timer
  - If stagnant for 3 minutes with no growth → mark as timeout
  - Sleep 10 seconds
  - Repeat until all windows complete or timeout
```

Verifications can take 10-15 minutes - keep waiting as long as output grows.

### Step 6: Capture Results

For each completed window, extract the verification report using Python (handles escaped newlines):

```bash
tmux capture-pane -p -S - -t cells-verify:{alias} | python3 -c "
import sys, re
content = sys.stdin.read()
texts = re.findall(r'\"text\":\"([^\"]+)\"', content)
if texts:
    longest = max(texts, key=len)
    print(longest.replace('\\\\n', '\n').replace('\\n', '\n'))
"
```

### Step 7: Cleanup

```bash
tmux kill-session -t cells-verify
```

### Step 8: Synthesize Results

Present results from all models with consensus analysis.

## Results Template

```markdown
# Cells Verification Ensemble Results

## Scope

**Roadmap:** _ai/docs/ROADMAP.md
**Cells:** hive_cells() (45 cells)
**Focus:** {additional_context or "General verification"}
**Models:** {count} ({model_list})

---

## Results by Model

{For each model:}

### {model_name}

**Status:** {Complete | Timeout | Error}
**Verdict:** {PASS | PASS WITH NOTES | FAIL}
**Coverage:** {X}%

{extracted verification content}

---

## Synthesis

### Consensus Points
_Issues identified by 2+ models:_
- {issue 1}
- {issue 2}

### Divergent Opinions
_Where models disagreed:_
- {Model A said X, Model B said Y}

### Critical Issues (MUST FIX)
| Issue | Cell ID | Recommendation |
| ----- | ------- | -------------- |

### Recommended Improvements
1. **[HIGH]** {action}
2. **[MEDIUM]** {action}
3. **[LOW]** {action}

### Final Verdict
**{PASS | PASS WITH NOTES | FAIL}** - {reasoning based on model consensus}
```

## Error Handling

**If a model fails:**
- Capture the error output
- Report status as "Error" with the error message
- Continue with other models

**If a model times out:**
- Report status as "Timeout"
- Include any partial output captured

## Dependencies

- `tmux` - for parallel session management
- `opencode run` - for running models with `--model` and `--format json` flags
- `hive_cells()` - MCP tool for listing cells (available to spawned models)
