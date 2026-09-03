---
name: subagent-delegation
description: Structured context templates for delegating work to subagents. Use whenever spawning subagents for exploration, planning, or coding tasks so they receive complete structured context.
---

# Subagent Delegation

When delegating to subagents, ALWAYS provide structured context to help the subagent understand the current situation. Use the delegation templates below.

**When to provide KEY FILES with line numbers:**

- Planning/coding phase: YES (provide files discovered from exploration)
- Refactoring/debugging: YES (provide specific files to modify)
- Exploration phase: NO (let subagent discover through search)
- Building on existing patterns: YES (provide reference implementations)

**Format:**

- Line ranges: `file.ts:123-145` for precise navigation
- Function refs: `(function: handleAuth - validates token)`
- Interface refs: `(interface: SpotifyTrack - add album field)`
- Pattern refs: `(similar to: spotify.ts:862)`

## Pattern: Exploration (NO files)

```
TASK: [Describe what to find/understand]

CURRENT STATE: [What we know now, current understanding]
DEPENDENCIES: [What depends on this code? What does this code depend on? Assess blast radius.]
TARGET STATE: [What understanding we need to achieve]
CONSTRAINTS: [Scope limits, areas to avoid, time constraints]
DECISIONS MADE: [Relevant decisions that affect exploration]
FOCUS: [Specific patterns, concepts, or areas to investigate]
RECENT CONTEXT: [Why this exploration matters now, user preferences]
OUT OF SCOPE: [What to explicitly ignore or avoid]

KEY FILES: [Omitted - subagent discovers]
APPROACH: [Search keywords, directories to focus on, patterns to identify]
```

## Pattern: Planning/Coding (Files from exploration)

```
TASK: [Describe what to design/implement]

CURRENT STATE: [Existing behavior, what code does now]
TARGET STATE: [Desired behavior, expected outcome]
CONSTRAINTS: [Tech requirements, compatibility, performance limits]
DECISIONS MADE: [Architecture choices, patterns to follow]
FOCUS: [Priority areas, critical paths, what to get right first]
RECENT CONTEXT: [Recent discoveries, user preferences, session context]
OUT OF SCOPE: [What to explicitly ignore or avoid]

KEY FILES:
- path/to/file.ts:start-end (identifier: name - relevance note)
- path/to/file.ts:start-end (identifier: name - relevance note)
- path/to/file.ts:start-end (identifier: name - relevance note)
[List all relevant files with line numbers - no limit]

DEPENDENCY ANALYSIS:
- Dependents: [files/modules that depend on these]
- Dependencies: [what these files depend on]
- Blast radius: [estimated scope of impact]
- Breaking risks: [potential breaking changes]

APPROACH: [Implementation guidance, patterns to follow, what to prioritize]
```

**No file limit** - List all relevant files with line numbers when known. Token savings from precision outweighs file list cost.