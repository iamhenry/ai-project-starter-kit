---
name: subagent-delegation
description: Structured handoff brief for delegating work to subagents. Use whenever spawning subagents for exploration, planning, or coding so they receive one complete task contract.
---

# Subagent Delegation

When delegating to subagents, fill the handoff brief below. One contract for discovery, planning, and implementation — MODE changes how fields fill, not which fields exist.

Delegate when a separate context buys coordination, specialist capability, isolation, useful parallelism, or independent judgment, not just another handoff. An authorized Mission owner may execute a small understood task directly; a root Supervisor remains coordination-only, and implementation never replaces fresh independent quality and verification. Explicitly selected workflows retain their required delegation.

**Key Files format** when known:

- Line ranges: `file.ts:123-145` for precise navigation
- Function refs: `(function: handleAuth - validates token)`
- Interface refs: `(interface: SpotifyTrack - add album field)`
- Pattern refs: `(similar to: spotify.ts:862)`

Pass every relevant file you already know. Token savings from precision outweighs list cost. Discovery may write `discover`.

**Reusing existing reports:** When an authoritative report or plan already exists, verify it exists and read its latest scope before sending the brief, and point the subagent at that path to reuse its facts rather than copying them into the brief; never invent a report artifact as a prerequisite. If findings materially change the task scope, reconcile the change in the owning artifact and continue with a concise delta follow-up rather than restarting or expanding silently.

For durable supervised work, identify the canonical local ticket or existing issue artifact in the brief's Key Files. It holds intent and acceptance independently of the harness; in BB, also retain the required native Task key, Mission attachment, and UI lifecycle tracking under the Supervisor SOP. Other harnesses need no BB IDs. The Supervisor owns scope and lifecycle, the Mission records execution evidence at serialized handoffs, and gates judge the same candidate against that source. Share one verified path across environments, or supply a source excerpt and return findings to its owner if inaccessible; do not create independently edited copies or a second ledger. Research or status questions do not require a new ticket.

**Brief proportionally, not ceremonially.** The brief is a default, not mandatory boilerplate: no fixed lengths, exhaustive checklists, or prose for its own sake. Three heuristics decide how much detail a brief needs — Can the subagent identify the next action and stopping condition without rereading the conversation? Does the stated proof distinguish success from the likely false positive? Is the detail already authoritative in a linked artifact? Add detail only where a heuristic exposes uncertainty. Keep scope, authority, safety, and owning-skill gates explicit; never drop them for brevity.

### Delegate uncertainty deliberately

**Preserve intent through every handoff.** In the existing Problem or Goal field, quote the relevant user wording and latest explicit correction, or link an accessible authoritative source. Distinguish requested behavior from implementation assumptions; do not invent controls, preserve a default the user asked to change, or add flexibility without evidence of need. For example, "make the card 280px wide, width only" does not request adaptive shrinking with the old default. Workers should flag unsupported requirements or contradictory evidence to the assigning owner before dependent work, while continuing independent authorized work. Give review and verification owners the same intent source so they check the requested outcome, not merely a rewritten brief.

State whether the assignment is discovery, planning, implementation, or an explicitly authorized sequence. The heuristic is **does the unknown change what we should build, or only how to carry out the settled change?**

- If it can change the outcome, approach, scope, safety, or proof strategy, make resolving that question the next bounded discovery assignment. Its deliverable is evidence sufficient for the owner to choose the route, not exhaustive knowledge. Stop at the research endpoint even when implementation looks obvious.
- If it is a local detail within the agreed route, let the worker read relevant code, check assumptions, and investigate within the brief's bounds. Prevent repeated discovery, not necessary understanding. Material contradictory evidence stops dependent implementation and returns a concise delta to the owner; independent authorized work may continue.
- For an authorized discovery-to-implementation sequence, the accountable orchestrator resolves findings into the existing brief or plan before handing off dependent implementation. No extra thread, artifact, or human approval is needed for settled, reversible decisions within authority; unresolved intent or permission still goes to the user.

The delegating owner fills every field except Success Criteria Result / Evidence. Implementation workers receive the selected route, relevant files, and criteria — not an invitation to repeat project discovery. Unknown files or exact probes are valid discovery inputs, not reasons to fabricate precision or block research. Existing gates own their procedures; name the check, do not paste `verification-gate`.

## Handoff Brief

Use this brief verbatim, populated with actual context:

```
### Mode
[discovery | planning | implementation | sequence. Heuristic: does the unknown change what we should build, or only how to carry out a settled change?]

### Problem
[Describe what is wrong or missing, who or what it affects, and why resolving it matters.]

### Vision
[1–3 sentences: what the user should experience when this assignment is done. Experiential context, not implementation steps.]

### Goal
[State the smallest exact, measurable outcome that will count as complete, preserving the intent source supplied in Problem or here.]

### Current State
[Describe how it works today. Include baseline evidence such as observed behavior, commands, screenshots, logs, or file references. Include dependencies and blast radius.]

### Ideal State
[Describe what should be true or what the user should experience when the work is complete. Do not describe implementation steps. For discovery, state the understanding needed and remaining uncertainty.]

### Boundaries
[Define what is included, excluded, constrained, or dependent. Identify anything that must not change. Record publish authority (commit, push, PR, merge).]

### Decisions Made
[Record choices already settled that the worker must follow — architecture, pattern, approach, or explicit non-goals. Do not reopen them unless new evidence contradicts them.]

### Key Files
[List known paths as `path:start-end` (name — why). If unknown, write discover. Pass files you already know — do not make the worker rediscover them.]

### Success Criteria

#### C1 — [State one atomic, observable, binary claim about the completed state.]
- Probe: [Specify the exact command, test, file check, query, or browser assertion that directly verifies this claim.]
- Expected: [State the precise output, behavior, value, or threshold required to pass.]
- Falsifier: [State the specific observation that would prove the claim false.]
- Result: [Record PASS, FAIL, or BLOCKED only after executing the probe.]
- Evidence: [Record fresh observed output, screenshot, link, or file reference. Include the tested revision or environment when relevant.]

[Repeat this block for each additional criterion. A probe may be mechanical or user-observable; name the check, do not paste owning-skill procedure. If a falsifiable criterion cannot be written yet, this is discovery — do not invent precision. One criterion can be enough.]

### Deliverable
[Specify exactly what the agent must create, modify, or return, including the expected format or location.]

### Exit Criteria
[Declare the work complete only when every criterion has fresh PASS evidence produced by its declared probe. Do not infer completion from implementation, file existence, or unchecked assumptions. Stop and ask instead of guessing when intent or authority is ambiguous, access is missing, a criterion cannot be verified, or the work requires a change outside Boundaries.]
```

## References

- [Mission Lead reference](references/mission-lead.md) — role SOP for a `🚀` BB Mission Lead. Read it when briefing a Mission Lead (resolve it to an absolute runtime path and include the path in the brief) or when acting as a Mission Lead with a supplied path.
