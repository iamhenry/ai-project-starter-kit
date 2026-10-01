# Platform: non-ui

Behavior rules (what good looks like, recovery, bail-out, anti-patterns, verdicts) live in `SKILL.md`; this file only adds non-UI specifics.

Choose the route from the real entry point, not the layer that changed. A backend, bridge, SDK, or service change that a UI depends on is not `non-ui`; route it to the UI platform and prove it through the UI.

## Reach

Run the candidate: the built CLI, the local service started from the candidate commit, or the changed doc or config as its reader will load it. Confirm identity (commit, version, or file hash).

## Mechanical

Tests, builds, data checks, and file assertions. These support the claim; they never replace the consumer path.

## Observable

- User-facing CLI or API: run the real command or request and observe the concrete result.
- Docs, skills, or config: the consumer is the next reader, build step, or agent. The resulting file, loaded the way the consumer loads it, is the receipt.
- Genuinely internal change with no consumer-observable difference: Mechanical is the proof, Observable is `n/a`, and you say why.
- Name the consumer for every claim.
- Good looks like: the consumer gets the output it needs from the real interface.
- Anti-pattern: relying on only unit tests, mocks, or source assertions.

## Recovery

| Symptom | One narrow fix |
|---|---|
| Service not running | Start the candidate once; confirm it answers |
| Missing seed data | Use supplied fixtures; otherwise BLOCKED with the owner |
| Stale artifact | Rebuild once and re-confirm identity |

## Hard blockers

Examples to confirm per project: production endpoints or data no one authorized; destructive operations with no safe target; paid external APIs without budget authority.
