---
name: bb-swarm
description: Launch equal peer agents as BB child threads on a user-approved task contract. Invoke manually with /bb-swarm; never start from an agent's suggestion alone.
slash: true
metadata:
  opencode/autoinvoke: false
---

# bb-swarm

A team of equal peers works one outcome together. You set it up, keep the clock, and watch. **You never plan, split, or assign the work.** The team decides.

**Manual entry only.** OpenCode v2 honors `metadata.opencode/autoinvoke: false`, so the user can invoke `/bb-swarm` without advertising it to agents. For OpenCode v1, this repository hides the skill with `permission.skill.bb-swarm: deny` and exposes the user-run `.opencode/commands/bb-swarm.md` command instead. When copying the skill to another v1 project, copy that permission and command too; frontmatter alone does not disable v1 discovery. Restart OpenCode after changing skill or config files.

Scripts are plumbing, not policy: they keep time, keep writes safe, deliver messages, keep the record, and *show* state. Peers make every judgment call. Every team-tool reply ends with a snapshot of what's open, waiting, stale, idle and known-limited, so good decisions are cheap.

## 1. Frame and approve
Before starting a swarm, get an explicit user-approved contract containing **all** of:

- Problem statement and scope (what is included and excluded).
- Definition of done and exit criteria (when to report DONE, PARTIAL or BLOCKED).
- Team size and model choice for the peers.
- Budget: time limit (`--minutes`) and either a spend cap or an explicit choice of no spend cap (`budget.md`). The script enforces time, **not** a dollar cap; if a hard dollar cap is required, resolve how to enforce it before launch.
- Boundaries and permissions (work area, installs, git, publishing, remote access). Default to none of those side effects unless approved.

If anything is missing, **offer to fill it in** from context. Show one compact proposed contract, ask the user to approve or correct it, and wait. Do not infer approval from silence, silently apply defaults, or launch with blanks. Already supplied requirements stay as the user stated them; only proposed fields need approval. This is intake, **not** a task plan or decomposition for the peers.

After approval, write the text fields to files without changing the user's wording or the approved proposal. The launcher checks that every field is nonempty and requires `--approved` for a live start; the approval itself comes from the user, not from the flag.

## 2. Launch
```sh
S=<this skill dir>/scripts
python3 $S/launch.py preflight --model <provider/model> [--model ...]   # real one-line message per model
python3 $S/launch.py start --run <fresh dir> --problem problem.md --scope scope.md \
  --done done.md --exit exit.md --budget budget.md --boundaries boundaries.md \
  --model <provider/model[:reasoning]> --count <approved count> --minutes <approved time> --approved
# mixed team: --peer Ava=provider-a/model:medium --peer Ben=provider-b/model:high ...
# check briefs first in a separate fresh directory: add --dry-run --run <preview dir> (no --approved needed)
```
`start` resolves parent/project/environment from the current BB thread, writes the run folder and one brief per peer from [peer-brief.md](references/peer-brief.md), starts peers as visible child threads, and schedules a warning and a stop. Must run from a root thread.

## 3. Watch
Read-only. Follow [observer.md](references/observer.md): `launch.py status --run <dir>` on a schedule or when a peer finishes; report working / needs attention / done / remaining. No nudges. If the user asks you to message a peer, use `launch.py tell` so it's logged.

## 4. Close
Peers run `coord.py close <Peer> DONE|PARTIAL|BLOCKED "why"` once themselves. After the deadline: `launch.py confirm-stop --run <dir>`. Report the team's outcome from `RESULTS.md`, what isn't done and why, and where the output is.

## Hard rules
- Only a user invocation and an approved, complete contract authorize launch.
- Never plan, split, or assign the work.
- Pass user-provided text word for word; pass assistant-proposed text only after the user approves it.
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
