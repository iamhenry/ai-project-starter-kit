---
name: review-plan
description: Review implementation documents against core principles to prevent over-engineering
subtask: false
# model: github-copilot/claude-opus-4.5
---

# Implementation Document Simplification Review

Purpose: Review implementation documents against core principles to prevent over-engineering and ensure pragmatic, maintainable solutions. You're not allowed to edit the original document. You're simply providing suggestions on how to simplify it.

## Usage

`/review-plan` - Interactive mode: collect inputs then run review

## Interactive Mode

When run, display all configuration questions with defaults upfront:

**Questions presented (all at once):**

```
1. Plan file path? [required]
2. ADR doc path? [none]
3. Include SYSTEM-ARCHITECTURE.md? [N]
```

**How to answer:**

- Provide all answers at once: `1. _ai/task/2025-12-11/plan.md 2. none 3. N`
- Or press Enter to accept defaults (except #1 which is required)
- After submission, proceed directly with PRE-REVIEW phase

**Defaults explained:**

- Plan file: Required, no default - user must provide path (ex. `_ai/task/some-task/plan.md`)
- ADR doc: Optional, defaults to none - skip if not provided
- SYSTEM-ARCHITECTURE.md: Optional, defaults to N - skip if not provided

---

# Philosophy

Start with the simplest solution that delivers current value. Add complexity only when measurable need proves it necessary. Trust that refactoring is easier than
maintaining unused complexity.

---

# PRE-REVIEW: Ground in Reality (MANDATORY)

⚠️ THIS PHASE IS NOT OPTIONAL - DO NOT SKIP

The entire value of this command is evidence-based recommendations. Suggestions without research are speculation, not simplification. You MUST complete research delegation before applying review criteria.

---

## Research Delegation

**Primary Method - Custom Agents (if available):**

- `atlas` → Codebase patterns, similar implementations, reusable components
- `voyager` → Official docs, framework built-ins, best practices

**Fallback - Task Tool Subagents:**
If custom agents unavailable, use `task` tool:

- `subagent: "general"` → General exploration, Codebase research, Official docs, etc.

**Execution:**

- Both needed? Use `batch` for parallel execution
- Single scope? Spawn only the relevant agent
- Consolidate results into main context before applying review criteria

**Decision Matrix:**
| Plan Contains | Atlas | Voyager |
| -------------------------- | ----- | ------- |
| Custom abstraction/pattern | ✓ | - |
| New library/dependency | ✓ | ✓ |
| Framework feature usage | - | ✓ |
| Both patterns + docs | ✓ | ✓ |

---

## Research Execution

AFTER delegation completes, use agent outputs to gather sufficient evidence. DO NOT restrict your research - gather as much context as needed to confidently justify scope cuts.

NOTE: The proposed feature likely doesn't exist yet - you're researching similar patterns, related implementations, and whether simpler alternatives exist.

1. Codebase Research

   - Search for SIMILAR implementations (not exact feature - it's probably new)
   - Identify established patterns for RELATED functionality
   - Find reusable components, utilities, or abstractions that could apply
   - Check how ANALOGOUS problems are currently solved
   - Verify what framework/library features are already integrated
   - Look for existing code that solves parts of the problem

2. Official Documentation Research (USE WEB SEARCH)

   - Search web for official docs: "[framework/library name] [feature] official documentation"
   - When plan proposes new dependencies: verify if framework built-ins can do it
   - When plan uses libraries: check official docs for recommended patterns
   - When plan implements features: search for framework-native solutions
   - Look for official best practices and anti-patterns
   - Verify current API recommendations and latest approaches

3. Build Evidence for Simplification
   - Document specific file paths, code snippets, and patterns found (filepath/line numbers)
   - Quote relevant official documentation with URLs
   - Provide concrete alternatives from codebase or docs
   - Show why existing patterns/solutions are better than proposed custom code (brief tradeoff analysis)
   - Reference specific examples from codebase

Your simplification recommendations MUST be backed by evidence:
"Plan proposes custom [X] in [file], but similar pattern exists in [path] for [related feature]" or "Plan adds [library], but [framework] docs recommend built-in [feature] instead - see [URL]"

---

# Review Criteria

Apply these filters to every section of the implementation document:

1. YAGNI Check (Primary Filter)

Question: "Is this needed NOW for the current requirement?"

- Remove features built "just in case"
- Eliminate abstract layers with only one implementation
- Cut configuration systems without actual configurability needs
- Delete premature optimizations without measured performance issues
- Strip hypothetical future scenarios from scope

Red Flags:

- "This will allow us to..." (future tense)
- "We might need to..." (speculation)
- "For flexibility..." (without specific use case)
- Multiple abstraction layers for simple operations

2. KISS Application

Question: "What's the simplest solution that works?"

- Prefer built-in framework features over custom solutions
- Replace complex patterns with straightforward approaches
- Break down over-engineered components into simple pieces
- Remove unnecessary dependencies
- Simplify data flows with fewer transformation steps

Red Flags:

- Custom implementations of framework-provided functionality
- Factory patterns for single implementations
- Complex state management for simple data
- Multiple nested abstractions

3. SOLID Alignment

Question: "Does each component have ONE clear purpose?"

- SRP: One file/class = one responsibility (split if doing too much)
- OCP: Extend via interfaces, not modification (but only if extension is actually needed NOW)
- LSP: Subclasses work interchangeably (avoid if unnecessary inheritance)
- ISP: Small focused interfaces (combine if artificially split)
- DIP: Inject dependencies (but don't create unnecessary abstraction layers)

Red Flags:

- God classes doing multiple unrelated things
- Modifying shared code for new features
- Abstract interfaces with no current need for multiple implementations

4. DRY Evaluation

Question: "Is duplication actually a problem here, or acceptable?"

- Extract patterns repeated 3+ times (not 2)
- Allow intentional duplication for decoupling
- Share logic only when changes truly need to propagate
- Avoid premature abstraction of similar-but-different code

Red Flags:

- Abstracting two slightly different implementations
- Creating utilities for one-off operations
- Premature extraction before pattern is clear

---

# Simplification Actions

For each document section, apply:

Architecture Diagram:

- Remove hypothetical components not built in this task
- Simplify data flows to essential paths only
- Cut "future extension points" without current use cases

Data Models:

- Remove fields not used in current scope
- Defer optional features to separate tasks
- Avoid over-normalized structures without query justification

Implementation Checklist:

- Delete "nice to have" items
- Remove infrastructure tasks for unused features
- Consolidate granular steps that don't need separation
- Cut tasks building for "what if" scenarios

Dependencies:

- Challenge each new dependency: "Can built-in features do this?"
- Remove libraries added for convenience without clear value
- Prefer standard library over external packages

Error Handling:

- Keep error scenarios that will actually occur
- Remove defensive code for impossible states
- Defer edge case handling until it happens

Deliverables:

- Remove files not needed for current functionality
- Consolidate related concerns into fewer files
- Defer abstractions until second implementation

---

# Output Format

Output MUST begin with a brief summary, followed by actionable recommendations only.

## What to Exclude

Do NOT include "KEEP" or "no change" recommendations in the artifact:

- If a section was reviewed and found optimal → exclude from file
- If previous suggestions were reversed → exclude (don't document "KEEP")
- Only document recommendations requiring ACTION from the user

The summary section captures that the plan was reviewed thoroughly. Individual recommendation sections should only appear if they need modification.

## Format Structure

```
# Review Summary

**Plan reviewed**: [filename]
**Research performed**: [Atlas/Voyager/Both/Task subagents] - [brief scope]
**Verdict**: [X actionable suggestions / Plan is optimal]

[1-2 sentence summary of what was reviewed and overall assessment]

---

# Recommendations

<!-- Only include sections below if they require ACTION. Omit sections that are optimal. -->

## Section: [Document section being reviewed]

**Recommendation**: [Specific action to simplify]

**Reason**: [YAGNI/KISS/SOLID/DRY - which principle is violated]

**Evidence**:

- Current plan: [what the plan proposes]
- Codebase findings: [specific file paths, line numbers, patterns found]
- Web search: [Performed/Not performed]
  - If performed: [URLs, official docs, framework recommendations]
  - If not performed: [Justification - why existing codebase evidence is sufficient]
- Justification: [brief tradeoff analysis]

<!--
Repeat this format for each section/recommendation.
All recommendations MUST be grounded in verifiable evidence from codebase or official documentation.
-->
```

---

# Documentation Requirements

AFTER completing the review and providing recommendations:

1. Decision Recording
   - List `_ai/task/` directory to find most recent subdirectory starting with `20`
   - Use that directory (will have format: `YYYY-MM-DD-brief-slug/` from create-issue)
   - Write file as: `suggestions.md`
   - Full path: `_ai/task/{LATEST_DIR}/suggestions.md`
   - Quick check: `ls -td _ai/task/20* 2>/dev/null | head -1`
2. File Format
   - Reuse the same output format from "Output Format" section above
   - Include all recommendations with evidence
   - Preserve the structured format: Recommendation → Reason → Evidence → Alternative → Justification
3. Quality Standards
   - DO NOT make suggestions for the sake of making suggestions
   - If there are no valid simplifications needed, that's acceptable
   - MUST provide valid justifications with evidence for each suggestion
   - Empty suggestions file is better than unfounded recommendations
   - If no suggestions: Document "No simplifications recommended" with brief reasoning why the plan is already optimal
4. Valid "No Suggestions" Scenarios
   - Plan already follows YAGNI/KISS/SOLID/DRY principles
   - Implementation matches established codebase patterns
   - Scope is minimal and justified by current requirements
   - No simpler alternatives exist based on codebase/docs research

---

# Guiding Questions for Reviewer

- "If we removed this, would current requirements still work?"
- "Is this solving a problem we actually have?"
- "Can we defer this until we need it?"
- "What's the dumbest solution that could possibly work?"
- "Are we building for imaginary future users?"
