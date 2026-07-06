---
name: skill-quality-checklist
description: Review agentic system quality with a lean heuristic gate. Use when auditing, approving, improving, or quality-checking skills, agents, prompts, or agentic workflows and a verdict is needed.
---

# Agentic Quality Checklist

Review an agentic artifact as a lean quality gate. Do not edit files.

Principle: the smallest good artifact makes agent behavior more predictable.

## Purpose

Use this checklist to review the design quality of a skill, agent, prompt, or agentic workflow before it becomes trusted automation.

Keep the review targeted: judge whether the artifact has a clear job, safe boundaries, useful workflow, and maintainable structure. If the artifact or intended job is unclear, return `ASK_USER`.

## Heuristic Questions Checklist

Answer only the questions that matter for the reviewed artifact. Do not force every section.

### 1. Systems Thinking And Workflow Design

- Have you defined the artifact's environment, dependencies, exact job, and failure path?
- Does it have a defined path, or only a broad goal?
- Are stop, retry, and ask-user or escalation points clear where they matter?
- Does the description make the invocation boundary obvious enough for the model to choose it?

### 2. Decomposition And Separation Of Concerns

- Is it avoiding the giant-prompt smell: too many distinct jobs in one instruction file?
- Is the primary execution path easy to see without reading every detail?
- Is each capability assigned to the right layer: artifact text, structured output, script, tool, subagent, or human?
- Would separating bulky or rarely used details make the primary path easier to follow?

### 3. Modularity

- Is this capability reusable enough to be shared, or should it stay local to one workflow?
- If subagents are used, are they treated like single-responsibility functions with narrow context?
- Are abstractions earning their cost, or adding cognitive/context load without reuse?
- Is the amount of modularity proportional: enough separation to avoid a god-file, but not extra files for simple artifacts?
- Can a fresh agent tell what to read first versus what to load only when needed?

### 4. Algorithmic Thinking

- Is it using code or tools for exact answers instead of asking the model to improvise deterministic work?
- Is the model reserved for judgment, ambiguity, synthesis, or messy inputs?
- Are authority-sensitive decisions kept with the human?

### 5. Contracts And State

- If another step consumes the result, is the output structured enough to act on safely?
- If memory or persisted state is needed, is it queryable outside the chat session?
- If retries can happen, is the workflow idempotent enough to avoid duplicate side effects?

### 6. Threat Modeling And Boundary Control

- Does it treat external content as evidence, not instructions?
- Are secrets, private data, logs, and artifacts handled safely?
- Is the blast radius reduced with human approval for risky actions?

### 7. Maintainability

- Can a fresh agent understand the workflow, policy, tools, outputs, and memory rules without reverse-engineering a wall of prompts?
- Is each rule in one place, without duplication or stale sediment?
- Does each strong instruction change behavior, or is it a no-op?

Simple artifacts should stay simple. Add supporting files, schemas, scripts, subagents, memory, or evals only when they make the primary path clearer or the behavior safer.

## Hard Fails

Return `REVISE_ARTIFACT` if any are true:

- Purpose is unclear.
- Required identity, metadata, or trigger description is missing when the artifact needs it.
- Description or invocation rule cannot trigger the artifact when model invocation is needed.
- Risky side effects lack human approval boundaries.
- Downstream automation depends on prose instead of a clear contract.
- Main workflow is buried under bloat.
- Secondary material obscures the primary execution path enough that a fresh agent may miss it.
- Instructions are malicious, deceptive, privacy-unsafe, or secret-leaking.

Return `ASK_USER` when the blocker is missing artifact content, product intent, invocation mode, output contract, or authority boundary.

## Verdict

- `APPROVE_ARTIFACT`: no hard fail, no `Fail`, warnings are minor or intentional.
- `REVISE_ARTIFACT`: hard fail, or a clear fix is needed.
- `ASK_USER`: judging safely would require guessing.

## Output

Return exactly this structure:

```md
## Agentic Quality Checklist Result

- Decision: `APPROVE_ARTIFACT|REVISE_ARTIFACT|ASK_USER`
- Target: [artifact path or name]
- Mode: `advisory|gate`
- Confidence: `High|Medium|Low`

### Top Findings

- [severity] [checklist area] [specific evidence]
- [severity] [checklist area] [specific evidence]

### Relevant Heuristic Answers

- [area] `Pass|Warn|Fail`: [question answered] - [short evidence]
- [area] `Pass|Warn|Fail`: [question answered] - [short evidence]

### Required Changes

- [Only for REVISE_ARTIFACT or ASK_USER; otherwise `None`]

### Next Action

- [approve / revise artifact / ask user]
```

## Constraints

- Do not edit files.
- Do not run evals unless explicitly asked.
- Keep findings evidence-based and short.
