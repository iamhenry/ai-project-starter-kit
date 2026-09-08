---
name: subagent-delegation
description: Structured context templates for delegating work to subagents. Use whenever spawning subagents for exploration, planning, or coding tasks so they receive complete structured context.
---

# Subagent Delegation

When delegating to subagents, ALWAYS provide structured context to help the subagent understand the current situation. Use the delegation templates below.

**When to provide KEY FILES with line numbers:**

- Planning/coding phase: YES (provide files discovered from exploration)
- Refactoring/debugging: YES (provide specific files to modify)
- Exploration phase: optional (supply known evidence; let subagent discover missing entry points)
- Building on existing patterns: YES (provide reference implementations)

**Format:**

- Line ranges: `file.ts:123-145` for precise navigation
- Function refs: `(function: handleAuth - validates token)`
- Interface refs: `(interface: SpotifyTrack - add album field)`
- Pattern refs: `(similar to: spotify.ts:862)`

**Reusing existing reports:** When an authoritative report or plan already exists, verify it exists and read its latest scope before sending the brief, and point the subagent at that path to reuse its facts rather than copying them into the brief; never invent a report artifact as a prerequisite. If findings materially change the task scope, reconcile the change in the owning artifact and continue with a concise delta follow-up rather than restarting or expanding silently.

**Brief proportionally, not ceremonially.** The templates above are defaults, not mandatory boilerplate: no fixed lengths, exhaustive checklists, or prose for its own sake. Three heuristics decide how much detail a brief needs — Can the subagent identify the next action and stopping condition without rereading the conversation? Does the stated proof distinguish success from the likely false positive? Is the detail already authoritative in a linked artifact? Add detail only where a heuristic exposes uncertainty. Keep scope, authority, safety, and owning-skill gates explicit; never drop them for brevity.

## Shared Handoff Contract

Every brief answers these five questions, in the fields below or a verified authoritative reference—not a second checklist to fill out:

- **Scope:** What is included, excluded, and authorized to change or publish?
- **Direct route:** What is the next action, supplied context, and approach? For discovery, give the question, known evidence, and search boundaries rather than inventing an implementation route.
- **Definition of done:** What observable result completes this assignment? Research may end with a cited answer and explicit remaining uncertainty; implementation ends at its assigned acceptance target.
- **Verification:** How will each result be checked, what evidence must return, and who accepts it? Return expected versus observed results and evidence references; implementation receipts identify the exact candidate. Existing gates own their procedures and technical verdicts; worker completion is not independent acceptance.
- **Exit criteria:** Stop at the requested endpoint, a blocker that invalidates the route, or the effective investigation/correction limit. Name the limit, what counts against it, and the escalation owner in the brief; use the owning workflow's stricter limits. If none applies, the delegating owner sets a finite task-sized timebox or attempt limit before starting. Report the result or blocker without expanding scope; replanning or replacement does not reset consumed budgets.

### Delegate uncertainty deliberately

State whether the assignment is discovery, planning, implementation, or an explicitly authorized sequence. The heuristic is **does the unknown change what we should build, or only how to carry out the settled change?**

- If it can change the outcome, approach, scope, safety, or proof strategy, make resolving that question the next bounded discovery assignment. Its deliverable is evidence sufficient for the owner to choose the route, not exhaustive knowledge. Stop at the research endpoint even when implementation looks obvious.
- If it is a local detail within the agreed route, let the worker read relevant code, check assumptions, and investigate within the brief's bounds. Prevent repeated discovery, not necessary understanding. Material contradictory evidence stops dependent implementation and returns a concise delta to the owner; independent authorized work may continue.
- For an authorized discovery-to-implementation sequence, the accountable orchestrator resolves findings into the existing brief or plan before handing off dependent implementation. No extra thread, artifact, or human approval is needed for settled, reversible decisions within authority; unresolved intent or permission still goes to the user.

The delegating owner supplies the five answers and reuses prior findings. Implementation workers receive the selected route, relevant files/patterns, prerequisites, and acceptance target—not an invitation to repeat project discovery. Unknown files or exact probes are valid discovery inputs, not reasons to fabricate precision or block research.

## Pattern: Exploration (Files optional)

```
TASK: [Describe what to find/understand]
MODE / ENDPOINT: [Discovery or planning; named question/decision and the report that ends this assignment]

CURRENT STATE: [What we know now, current understanding]
DEPENDENCIES: [What depends on this code? What does this code depend on? Assess blast radius.]
TARGET STATE: [What understanding we need to achieve]
DEFINITION OF DONE: [Named questions answered with supporting citations, remaining uncertainty explicit, and the requested report delivered; no implementation or unassigned follow-on work]
CONSTRAINTS: [Scope limits, areas to avoid, time constraints]
EXIT CRITERIA: [Effective investigation limit, counting unit, escalation owner, and stop conditions from the Shared Handoff Contract]
DECISIONS MADE: [Relevant decisions that affect exploration]
FOCUS: [Specific patterns, concepts, or areas to investigate]
RECENT CONTEXT: [Why this exploration matters now, user preferences]
OUT OF SCOPE: [What to explicitly ignore or avoid]
RETURN REQUIREMENTS: [The report or cited answer to return; for a research assignment, state that completion is a cited answer to the named question — with the source citations it must carry — and that the assignment ends at the report: no implementation, then stop. Evidence location and blockers.]
VERIFICATION: [What evidence supports the answer, how unsupported conclusions will be distinguished from findings, and who accepts the report]

KEY FILES: [Known evidence or entry points if available; otherwise subagent discovers]
APPROACH: [Search keywords, directories to focus on, patterns to identify]
```

## Pattern: Planning/Coding (Files from exploration)

```
TASK: [Describe what to design/implement]
MODE / ENDPOINT: [Planning, implementation, or authorized sequence; requested terminal deliverable]

CURRENT STATE: [Existing behavior, what code does now]
TARGET STATE: [Desired behavior, expected outcome]
DEFINITION OF DONE: [Concrete observable acceptance criteria for this assignment and its requested deliverable; planning ends at the approved planning endpoint, while implementation names the required checks/evidence and acceptance owner under PROOF CONTRACT]
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

EXECUTION BOUNDS: [Source-change scope boundary, first proof of the riskiest behavior on an appropriate real or disposable surface, and effective limit, counting unit, stop conditions and escalation owner from the Shared Handoff Contract and owning workflow.]
PROOF CONTRACT: [Observable claim and concrete proof proportionate to task type, surface, and uncertainty, chosen so it distinguishes success from the likely false positive: concrete mechanical proof and, where the surface admits it, meaningful user-observable proof; static semantic scenarios for instruction-only work; for planning-only assignments, describe intended implementation verification, not require implementation. When a modality is genuinely inapplicable to the task, say so in one concise reason instead of performing it. State the evidence to retain in an openable artifact, and that unresolved precise probes about an unknown behavior are resolved during investigation before implementation rather than fabricate probes or treat missing precision alone as a spawn blocker. Reference the owning skill contract rather than duplicating its stages.]
RETURN REQUIREMENTS: [Result, environment and exact candidate identity, checks actually run, evidence location, and blockers; implementation self-checks do not replace independent acceptance. State what counts as done, the requested endpoint, whether this role may publish or finalize anything (commit/push/PR/merge), and that it stops when done — no unassigned follow-on work.]
APPROACH: [Selected route, files/patterns and prerequisites for implementation; bounded questions for planning; handle local uncertainty and contradictory evidence under Delegate uncertainty deliberately]
```

**No file limit** - List all relevant files with line numbers when known. Token savings from precision outweighs file list cost.

## References

- [Mission Lead reference](references/mission-lead.md) — role SOP for a `🚀` BB Mission Lead. Read it when briefing a Mission Lead (resolve it to an absolute runtime path and include the path in the brief) or when acting as a Mission Lead with a supplied path.
