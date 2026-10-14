---
name: bugging-out
description: Find and fix a bug through cheap, evidence-backed rounds, picking a playbook that fits the bug. Use when a bug is hard to pin down, a fix did not hold, a check keeps failing, progress has plateaued, or someone says "use bugging-out", "we can't find this bug", or "squash this bug".
---

# Bugging Out

Climb toward the cause in small rounds. Each round tests one guess with the cheapest check that could prove it wrong. Pick the playbook that fits what you see, and switch when it stops teaching you anything.

## A round

1. State the failure in one line: what the user does, what they expect, what they get.
2. Make one guess. Pick the cheapest, most direct check that could prove it wrong: one command, one screen, one input, one log line.
3. Change one thing. Run the check. Write down: guess, check, result, what is now ruled out.
4. A round that rules nothing out is a stall.

A check only counts if it fails on the broken code. Checks are throwaway probes (a command, script, log, screen action), not new unit or integration tests.

## Playbooks

Use judgment. Start with whichever fits; combine or switch freely.

| Playbook | Fits when |
|---|---|
| [tight-loop](playbooks/tight-loop.md) | The cause seems near and checks are fast. Log, tweak, rerun. |
| [hypothesis-funnel](playbooks/hypothesis-funnel.md) | Several suspects, no clear lead. Goes wide. |
| [trace-boundaries](playbooks/trace-boundaries.md) | It breaks somewhere along a path, or only sometimes. |
| [compare-good-bad](playbooks/compare-good-bad.md) | A working version exists: a commit, device, input, or setting. |
| [five-whys](playbooks/five-whys.md) | The failing spot is known; the fix would only treat a symptom. Goes deep. |

## Evidence

- Cite `file:line`, or the command run plus its key output.
- Anything without evidence is a guess. Say "probable, not proven" until a check confirms it.
- What the user would see outranks logs, source reading, or an agent's report.

## Tools

Load the tool's skill before use. Use what the project already has first.

| Need | Use |
|---|---|
| Reproduce a full user flow | `reproduce-bug` skill |
| Web or Electron: drive, console, network, screenshot | `agent-browser` |
| iOS or Android: drive, replayable flows, record, screenshot diff | `argent` (`argent-metro-debugger` for JS logs, `argent-native-profiler` for hangs) |
| Apple build, run, test, device logs | `xcodebuildmcp-cli` |
| Native Mac app UI | `agent-device`; `cua-driver` as fallback |
| Long-running server or log stream | `tmux` |
| Find the change | `git log -p`, `git blame`, `git bisect`, `git diff good..bad` |
| Read code, including dependencies | `rg`; read the library source in `node_modules` or vendored code |
| A fresh outside view | `second-opinion` skill |
| Final proof of the fix | `verification-gate` skill |

## When it plateaus

- About 2 stalled rounds: switch playbooks or look somewhere new.
- About 2 playbooks with nothing new ruled out: run parallel agents, if you are allowed to delegate.

**Parallel agents (expensive, at most 3).** Launch fresh agents in parallel, each with a different playbook. Give each the one-line failure, the cheap repro, and the round notes so far. They may run safe probes only: no production edits, no further agents. Merge their findings. Rank by evidence strength first, then by how many agree. Run the one fastest check that could prove the top answer wrong.

## Stop

- **Fixed:** the cause is confirmed and the same check now passes on a fresh run. Hand off to `verification-gate` for final proof.
- **Blocked:** name what is missing and who can unblock it.
- **Parked:** list what was ruled out and the next check worth running.

Report in five lines: Observed / Cause / Change / Proof / Risk.

## Anti-patterns

- Avoid thorough checks that can't change your mind; pick the cheapest one that could.
- Avoid acting on a guess no check could have proved wrong. Once one could and didn't, act, even on a first guess.
- Avoid several changes in one round; you won't know which one worked.
- Avoid digging harder at the same spot after a round taught nothing; look somewhere different.
- Avoid refactors and nearby cleanups while on the bug.
- Avoid leaving temporary logs or throwaway copies behind.
- Avoid parallel agents that look from the same angle; they add cost, not insight.
- Avoid a confident story when the cause isn't found; report what's ruled out instead.
