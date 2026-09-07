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

EXECUTION BOUNDS: [Source-change scope boundary, first proof of the riskiest behavior on an appropriate real or disposable surface, and correction budget and escalation from the owning workflow, including BB Supervisor policy when applicable.]
PROOF CONTRACT: [Observable claim, concrete check on the appropriate surface, likely false positive, and evidence to retain; reference the owning skill contract rather than duplicate it. For planning-only assignments, describe intended verification rather than require implementation.]
RETURN REQUIREMENTS: [Result, environment and exact candidate identity, checks actually run, evidence location, and blockers; implementation self-checks do not replace independent acceptance.]
APPROACH: [Implementation guidance, patterns to follow, what to prioritize]
```

**No file limit** - List all relevant files with line numbers when known. Token savings from precision outweighs file list cost.

## References

- [Mission Lead reference](references/mission-lead.md) — role SOP for a `🚀` BB Mission Lead. Read it when briefing a Mission Lead (resolve it to an absolute runtime path and include the path in the brief) or when acting as a Mission Lead with a supplied path.
