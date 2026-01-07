---
name: group-chat-brainstorm
description: Never-ending group chat with multiple AI models to ideate and plan projects
---

# Group Chat Brainstorm

## Mental Model

You're in a group chat with N frontier models as your thinking partners. Every message you send fans out to all models simultaneously. The orchestrator synthesizes their responses and presents consensus, divergence, and open questions. This loops indefinitely until you've flushed out your idea into a roadmap-ready plan for execution.

## Purpose

Collaboratively refine a project idea through multi-perspective conversation:
- Surface risks, assumptions, and gaps (technical, UX, product)
- Challenge ambiguity with targeted questions using dynamic frameworks
- Start broad, then narrow with each round toward actionable clarity

## When to Use

- You need multi-perspective planning before committing to a roadmap.
- You want gaps, ambiguities, and assumptions explicitly challenged.

## Usage

`/group-chat-brainstorm` - Start a never-ending group chat with multiple AI models. Every message you send fans out to all models, they respond, and the orchestrator synthesizes. The session continues indefinitely—each follow-up triggers another round of fan-out → capture → synthesis. Models receive the full conversation transcript, so context builds over time.

## Interactive Flow

Present only the essentials. User presses Enter to accept defaults.

```
/group-chat-brainstorm

1. What are we ideating? (problem/goal statement) >

2. Models (comma-separated)? [opus, gemini, gpt]
   (Add as many models as you like; no hard limit)
   >

---
Summary:
- Topic: {topic}
- Models: {models}
- Frameworks: dynamically selected based on conversation needs
- Constraints: concise, ~500 tokens/model

Proceed? [Y/n]
```

## Model Aliases

Expand these aliases to full provider/model format (no hard limit on count):

| Alias    | Full Model Name                   |
| -------- | --------------------------------- |
| `opus`   | `google/gemini-claude-opus-4-5-thinking-low` |
| `gemini` | `google/gemini-3-pro-low`         |
| `gpt`    | `openai/gpt-5.2-low`              |
| `codex`  | `openai/gpt-5.2-codex-medium`     |

Users can also specify full model names directly.

## Execution Steps

### Step 1: Parse Inputs

- Split models by comma, trim whitespace.
- Expand aliases to full model names.
- Keep default outputs/frameworks unless overridden in future prompts.

### Step 2: Create Tmux Session

```bash
tmux kill-session -t ensemble-ideation 2>/dev/null
tmux new-session -d -s ensemble-ideation -n {model1-alias}
tmux new-window -t ensemble-ideation -n {model2-alias}
tmux new-window -t ensemble-ideation -n {model3-alias}
# ... for each model
```

### Step 3: Build Ideation Prompt

Construct the prompt using the inputs:

```markdown
You are in a group chat brainstorm with other frontier models. You all see the full conversation history. Deliver crisp, constructive planning guidance.

## Conversation Transcript
{transcript}

## Current User Message
{user_message}

## Topic
{topic}

## Progression
- Round 1: Broad exploration — surface all considerations
- Round 2+: Narrow based on user direction — deepen on selected threads
- Each round: Challenge remaining ambiguity, don't rehash resolved points
- Goal: Converge toward actionable user stories with clear acceptance criteria

## Desired Outputs
- Solutions and tradeoffs
- Gaps/ambiguities and pointed questions
- Risks + mitigations
- Dependencies/assumptions to validate
- Draft epics → user-story seeds with acceptance hints
- Light metrics/guardrails

## Personas/Frameworks
- Apply PM, Tech Lead, and Researcher lenses by default.
- Dynamically select and apply frameworks from this toolkit based on what the conversation needs:
  - Six Thinking Hats (parallel perspectives)
  - SWOT (strengths, weaknesses, opportunities, threats)
  - 5 Whys (root cause analysis)
  - Socratic Method (probing questions)
  - PACT (purpose, audience, context, task)
  - Riskiest Assumption Test (validate unknowns first)
  - Jobs-To-Be-Done (user motivations)
  - User-story mapping (feature breakdown)
  - Acceptance criteria drafting (definition of done)
  - Pre-mortem (imagine failure, work backwards)
  - Opportunity-solution tree (map options to outcomes)
- Choose frameworks that best surface ambiguity for the current round. Don't force all frameworks—use what fits.

## What to Deliver
- Restate goal + success criteria.
- Solution candidates (with tradeoffs).
- Open questions + assumptions to validate.
- Risks + mitigations (technical, product, ops).
- Dependencies + sequencing considerations.
- Draft epics → user-story seeds with acceptance hints.
- Metrics/guardrails (lightweight).

Tone/constraints: concise, pragmatic, ~500 tokens/model
```

### Step 4: Send Commands to Each Window

For each model/window:

```bash
tmux send-keys -t ensemble-ideation:{alias} 'opencode run --model {full_model_name} --format json "{escaped_prompt}"; echo "###DONE###"' C-m
```

### Step 5: Patient Polling

Poll each window until `###DONE###` marker appears:

```
LOOP:
  - Capture: tmux capture-pane -p -S - -t ensemble-ideation:{alias}
  - If output contains "###DONE###" → mark complete
  - If output contains error (API error, connection failed, rate limit) → mark as FAILED
  - If output grew since last check → reset stagnant timer
  - If stagnant for 60 seconds with no growth → mark as FAILED
  - Sleep 10 seconds
  - Repeat until all windows complete or failed
```

### Step 5.5: Retry Failed Models + Human Fallback

For each FAILED model:

1. **Retry once** — recreate window, resend same command, poll with same logic
2. **If still fails** — prompt user:
   ```
   {model} failed after retry.
   Enter a response to substitute (or press Enter to skip):
   >
   ```
   - If user provides text → use as that model's output
   - If user presses Enter → exclude model from this round's synthesis

### Step 6: Capture Results

For each completed window:

```bash
tmux capture-pane -p -S - -t ensemble-ideation:{alias} | grep '"type":"text"' | sed 's/.*"text":"\([^"]*\)".*/\1/'
```

Extract the clean text response from JSON output.

### Step 7: Cleanup

```bash
tmux kill-session -t ensemble-ideation
```

### Step 8: Synthesis + Transcript Update

After capturing all results:

1. **Update transcript file** (`.opencode/group-chat/{topic-slug}-{timestamp}.md`):

```markdown
## Round {n} — {timestamp}

**USER:**
{verbatim user message for this round, unmodified}

<!-- Repeat **{MODEL}:** for each participating model in every section below -->

### Goal Restatement
**{MODEL}:** {response}

### Solution Candidates
**{MODEL}:**
| Solution | Approach | Tradeoff |
| -------- | -------- | -------- |
| ...      | ...      | ...      |

### Open Questions
**{MODEL}:**
- {question}

### Risks + Mitigations
**{MODEL}:**
- {risk} → {mitigation}

### Epics → Story Seeds
**{MODEL}:**
- Epic: {name}
  - Story: As a <user>, I want <behavior> so that <value>. Acceptance hints: {criteria}

### Suggested Next Steps
**{MODEL}:**
- {next step}

### SYNTHESIS
{synthesis below}
```

2. **Synthesize** using this template:

```markdown
# Group Chat Brainstorm — Round {n}

## Summary
- Goal: {topic}
- Models: {count} ({list})
- Round: {n}
- Focus: {broad|narrowing|converging}

## Consensus
- {bullets where 2+ models agree}

## Divergence
- {bullets where models disagree, with pros/cons}

## Clarified This Round
- {what became clearer}

## Still Ambiguous / Open Questions
- {remaining questions to resolve}

## Risks & Mitigations
- {risk} → {mitigation/validation step}

## Proposed Plan (Epics → Story Seeds)
- Epic: {name}
  - Story: As a <user>, I want <behavior> so that <value>. Acceptance hints: {criteria/guardrails}
- (repeat)

## Next Action
- Smallest next step to validate or unblock based on synthesis.
```

3. **Present synthesis to user** and wait for next message.

### Step 9: Loop

When user sends a follow-up message:

1. Orchestrator appends user message to transcript
2. Go to Step 2 (create tmux session)
3. Build prompt with FULL transcript (Step 3)
4. Fan out to all models (Step 4-6)
5. Cleanup tmux (Step 7)
6. Synthesize + update transcript (Step 8)
7. Wait for next user message → repeat

The loop never ends. Each round, models receive the complete conversation history so they can build on prior discussions and narrow toward clarity.

## Transcript

Location: `.opencode/group-chat/{topic-slug}-{timestamp}.md`

Format (section-grouped for easy comparison):

```markdown
# Group Chat Brainstorm Transcript
Topic: {initial topic}
Models: opus, gemini, gpt
Started: {timestamp}

---

## Round 1 — {timestamp}

**USER:**
{verbatim initial prompt — exact text from step 1, unmodified}

<!-- Repeat **{MODEL}:** for each participating model in every section below -->

### Goal Restatement
**{MODEL}:** {response}

### Solution Candidates
**{MODEL}:**
| Solution | Approach | Tradeoff |
| -------- | -------- | -------- |
| ...      | ...      | ...      |

### Open Questions
**{MODEL}:** {bullets}

### Risks + Mitigations
**{MODEL}:** {bullets}

### Epics → Story Seeds
**{MODEL}:** {epics}

### Suggested Next Steps
**{MODEL}:** {bullets}

### SYNTHESIS
- Consensus: ...
- Divergence: ...
- Next Action: ...

---

## Round 2 — {timestamp}

**USER:**
{verbatim user message for this round, unmodified}

...
```

The transcript accumulates indefinitely. Models receive the full transcript each round so they have complete context.

## Dependencies

- `tmux` - for parallel session management
- `opencode run` - for running models with `--model` and `--format json` flags
