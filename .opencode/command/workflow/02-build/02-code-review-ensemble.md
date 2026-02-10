---
name: code-review-ensemble
description: Fan out code review to multiple AI models in parallel and synthesize results
purpose: Use when I want to merge the feature branch into main and need confidence
---

# Code Review Ensemble

Spawns parallel code reviews across multiple AI models using tmux, then synthesizes the results. This is used when I'm about to merge the branch (different than the "best-pr' flow)

## Usage

`/code-review-ensemble` - Interactive mode with defaults

## Interactive Flow

Present all questions with defaults. User presses Enter to accept defaults.

```
/code-review-ensemble

1. What to review? [staged]
   Options: staged | unstaged | latest-commit | branch
   >

2. Base branch? [main]
   (Only asked if "branch" selected above)
   >

3. Models (comma-separated)? [opus, gemini, gpt]
   >

4. Additional context/focus? [none]
   Example: "focus on security" or "check async handling"
   >

---
Summary:
- Scope: staged changes
- Models: opus, gemini, gpt, codex (4 reviews)
- Focus: none

Proceed? [Y/n]
```

## Model Aliases

Expand these aliases to full provider/model format:

<!-- Only heavy-hitter frontier models -->
<!-- model list can be seen at `opencode models` in a terminal -->

| Alias    | Full Model Name                               |
| -------- | --------------------------------------------- |
| `opus`   | `google/antigravity-claude-opus-4-6-thinking` |
| `gemini` | `google/antigravity-gemini-3-pro`             |
| `gpt`    | `openai/gpt-5.2`                              |
| `codex`  | `openai/gpt-5.3-codex`                        |

Users can also specify full model names directly.

## Execution Steps

### Step 1: Parse Inputs

- Split models by comma, trim whitespace
- Expand aliases to full model names
- Validate scope is one of: staged, unstaged, latest-commit, branch

### Step 2: Create Tmux Session

```bash
tmux kill-session -t ensemble-review 2>/dev/null
tmux new-session -d -s ensemble-review -n {model1-alias}
tmux new-window -t ensemble-review -n {model2-alias}
tmux new-window -t ensemble-review -n {model3-alias}
# ... for each model
```

### Step 3: Build Review Prompt

Read the code review instructions from `_ai/tools/quality/code-review.md` and construct the prompt:

```markdown
You are performing a code review.

## Scope

Review: {scope}
{if scope is "branch": Compare against: {base_branch}}

## Additional Focus

{additional_context or "None specified"}

## Instructions

{contents of \_ai/tools/quality/code-review.md}

---

IMPORTANT: First, run the appropriate git command to get the changes:

- If scope is "staged": run `git diff --cached`
- If scope is "unstaged": run `git diff`
- If scope is "latest-commit": run `git show HEAD`
- If scope is "branch": run `git diff {base_branch}...HEAD`

Then perform the code review following the instructions above.

After completing the review, write the final output as markdown to the repository root using this exact filename pattern:

- `review-{alias}.md` (examples: `review-opus.md`, `review-gemini.md`)

If file write fails, print the final review between markers:

- `###REVIEW_START###`
- `###REVIEW_END###`
```

### Step 4: Send Commands to Each Window

For each model/window:

```bash
tmux send-keys -t ensemble-review:{alias} 'opencode run --model {full_model_name} "{escaped_prompt}"; echo "###DONE###"' C-m
```

### Step 5: Patient Polling

Poll each window until `###DONE###` marker appears:

**IMPORTANT: Poll every 10 seconds. Do NOT use longer intervals.**

```
LOOP:
  - Capture: tmux capture-pane -p -S - -t ensemble-review:{alias}
  - If output contains "###DONE###" → mark complete
  - If output grew since last check → reset stagnant timer
  - If stagnant for 3 minutes with no growth → mark as timeout
  - Sleep 10 seconds  ← DO NOT CHANGE THIS
  - Repeat until all windows complete or timeout
```

Reviews can take 10-15 minutes - keep waiting as long as output grows.

### Step 6: Capture Results

For each completed window, capture results in this order:

1. **File-first (default):** Read markdown file from repo root:

```bash
cat review-{alias}.md
```

2. **Fallback (if file missing):** Extract marker-delimited review text from tmux pane:

```bash
tmux capture-pane -p -S - -t ensemble-review:{alias}
```

Capture content between `###REVIEW_START###` and `###REVIEW_END###`.

3. **If neither exists:** mark model status as `Error` (or `Timeout` if stagnant timeout triggered) and continue.

### Step 7: Cleanup

```bash
tmux kill-session -t ensemble-review
```

### Step 8: Hold Results

Hold raw outputs from each model. Do not synthesize yet - wait for verification.

### Step 9: Verification

After presenting results, immediately spawn two verification agents in parallel:

**Atlas (codebase validation):**

```
Task: Validate code review findings

For each issue identified:
1. Find and read the actual code
2. Trace the data flow / call path
3. Determine: ACTUAL BUG vs DEFENSIVE IMPROVEMENT vs NON-ISSUE
4. Return summary table with verdicts and merge recommendation
```

**Voyager (external docs validation):**

```
Task: Ground findings in official documentation

For each issue involving external APIs/frameworks (Stripe, MusicKit, Convex, etc.):
1. Check official docs for correct usage patterns
2. Verify if flagged code follows best practices
3. Note any documentation-backed corrections to ensemble findings
```

Present combined verification results after both complete.

### Step 10: Final Report

After verification completes, synthesize ALL findings (3 model reviews + atlas + voyager) into a single authoritative report using the Results Template below.

## Results Template

After capturing all results, present them using this format:

```markdown
# Code Review Ensemble Results

## Summary

**Summary:** {1-2 sentence description of what the code changes do}
**Problem(s) Solved:** {What user/system problem(s) this addresses}

## Scope

**Reviewed:** {scope}
**Base Branch:** {base_branch if applicable}
**Focus:** {additional_context or "General review"}
**Models:** {count} ({model_list})

## Changes

- Scope: {files / areas reviewed}
- Risk: {low | medium | high}
- Key outcomes: {2-3 bullet points}

| Cohort / File(s)         | Summary                | Rationale                                  |
| ------------------------ | ---------------------- | ------------------------------------------ |
| {cohort or path glob(s)} | {one-line description} | {why needed; problem, impact, or decision} |

**Risk Assessment Criteria:**

- LOW: Style/refactor, no behavior change, well-tested area
- MEDIUM: New feature, behavior change, moderate test coverage
- HIGH: Auth/payments, data mutations, external API changes, low test coverage

---

## Results by Model

{For each model used, create a section:}

### {model_name}

**Status:** {Complete | Timeout | Error}
**Overall Rating:** {extract from review or "N/A"}

{extracted review content}

---

{End for each}

## Synthesis

### Consensus Points

_Issues identified by 2+ models:_

- {issue 1}
- {issue 2}

### Divergent Opinions

_Where models disagreed:_

- {Model A said X, Model B said Y}

### Critical Issues (BLOCK MERGE)

_Issues that MUST be fixed before merge:_

| Issue   | Location    | Impact                  |
| ------- | ----------- | ----------------------- |
| {issue} | {file:line} | {what breaks for users} |

**Criteria for CRITICAL:**

- Active bugs in user flow (will break for real users)
- Security vulnerabilities (auth bypass, data exposure, injection)
- Regressions (worked before, broken now)
- Performance degradations (N+1 queries, memory leaks in hot paths)
- Data integrity risks (silent data loss, corruption)

### Recommended Improvements

_Defensive improvements and code quality (can be addressed post-merge):_

1. **[HIGH]** {action} - {file:line}
2. **[MEDIUM]** {action} - {file:line}
3. **[LOW]** {action} - {file:line}

**NOT critical (belongs here):**

- Defensive improvements (fail-fast, extra validation)
- Code quality / maintainability
- Edge cases requiring unusual conditions
- Missing guards for admin/internal flows

### Confidence Level

**{High/Medium/Low}** - {reasoning based on model agreement}
```

## Error Handling

**If a model fails:**

- Capture the error output
- Report status as "Error" with the error message
- Continue with other models
- Include partial results in synthesis

**If a model times out:**

- Report status as "Timeout"
- Include any partial output captured
- Note in synthesis that review was incomplete

## Example Session

```
/code-review-ensemble

1. What to review? [staged]
   > branch

2. Base branch? [main]
   > main

3. Models (comma-separated)? [opus, gemini, gpt]
   > opus, gemini

4. Additional context/focus? [none]
   > focus on async error handling

---
Summary:
- Scope: branch (compared to main)
- Models: opus, gemini (2 reviews)
- Focus: focus on async error handling

Proceed? [Y/n]
> y

Starting ensemble review...
- Spawning tmux session with 2 windows
- Sending review prompts to each model
- Polling for completion (this may take 10-15 minutes)

[opus] Running... (2 min elapsed)
[gemini] Running... (2 min elapsed)
[opus] Complete!
[gemini] Complete!

Capturing results...
Cleaning up tmux session...

# Code Review Ensemble Results
...
```

## Dependencies

- `tmux` - for parallel session management
- `opencode run` - for running models with `--model` and inline prompt
- `_ai/tools/quality/code-review.md` - review instructions template
