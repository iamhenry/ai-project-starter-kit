---
name: bb-swarm
description: Launch a team of equal peer agents as BB child threads on any task (code, research, writing, analysis) from the user's problem and definition of done, word for word. The team self-organizes over a shared board; scripts keep the clock, deliver messages, keep the record and show the team's state. Use when the user asks for a swarm, a peer team, bb swarm, or multiple agents collaborating on one outcome.
---

# bb-swarm

A team of equal peers works one outcome together. You set it up, keep the clock, and watch. **You never plan, split, or assign the work.** The team decides.

Scripts are plumbing, not policy: they keep time, keep writes safe, deliver messages, keep the record, and *show* state. Peers make every judgment call. Every team-tool reply ends with a snapshot of what's open, waiting, stale, idle and known-limited, so good decisions are cheap.

## 1. Frame
Get from the user, in their words:
- **Problem**
- **Definition of done** — ask only if it can't be checked by anyone.
- **Boundaries** — what peers may touch or must not do (installs, git, publishing, remote access default to no).
- Optional: team size (default 5), models, minutes (default 90).

Write each to a file verbatim. Do not rewrite, decompose, or add a plan.

## 2. Launch
```sh
S=<this skill dir>/scripts
python3 $S/launch.py preflight --model <provider/model> [--model ...]   # real one-line message per model
python3 $S/launch.py start --run <fresh dir> --problem problem.md --done done.md \
  [--boundaries boundaries.md] --model <provider/model[:reasoning]> [--count 5] [--minutes 90]
# mixed team: --peer Ava=provider-a/model:medium --peer Ben=provider-b/model:high ...
# check briefs first in a separate fresh directory: add --dry-run --run <preview dir>
```
`start` resolves parent/project/environment from the current BB thread, writes the run folder and one brief per peer from [peer-brief.md](references/peer-brief.md), starts peers as visible child threads, and schedules a warning and a stop. Must run from a root thread.

## 3. Watch
Read-only. Follow [observer.md](references/observer.md): `launch.py status --run <dir>` on a schedule or when a peer finishes; report working / needs attention / done / remaining. No nudges. If the user asks you to message a peer, use `launch.py tell` so it's logged.

## 4. Close
Peers run `coord.py close <Peer> DONE|PARTIAL|BLOCKED "why"` once themselves. After the deadline: `launch.py confirm-stop --run <dir>`. Report the team's outcome from `RESULTS.md`, what isn't done and why, and where the output is.

## Hard rules
- Never plan, split, or assign the work.
- Pass the problem and done text word for word.
- Don't message peers except through `launch.py tell` at the user's request.
- The deadline is fixed.
- Peers never create sub-agents.

## Files
- [scripts/launch.py](scripts/launch.py) — preflight, start, status, confirm-stop, tell.
- [scripts/coord.py](scripts/coord.py) — the team's tool: board, notify, claim/take/release, handoff, verdict, lock, limit, away, open, close.
- [references/how-we-work.md](references/how-we-work.md) — what good looks like for peers. Every peer reads it first.
- [references/peer-brief.md](references/peer-brief.md) — brief template filled at launch.
- [references/observer.md](references/observer.md) — how to watch without steering.
- [references/lessons.md](references/lessons.md) — why each rule exists. Read before changing a rule.
