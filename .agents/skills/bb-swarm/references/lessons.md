# Why the rules exist

Lessons from peer-swarm trials. Change a rule only with new evidence.

| Rule | What happened without it |
|---|---|
| The skill never splits the work | Pre-splitting by file created a queue on one shared file instead of parallel work. |
| Equal peers, no fixed roles | Standing planner/worker/judge roles were rejected: they add hops, and peers picking their own work kept everyone busy. |
| One shared board, one post, notify one peer | A relay agent worked but was pure overhead. Broadcast wake-ups caused ack loops. |
| Read only new posts | Full-board reads wasted turns. |
| Short locks, never while testing | A manually held board lock stalled a peer for many minutes. |
| One named reviewer per handoff | Work piled up unreviewed without a recipient; a named peer made review start early. |
| Shared base early | A working base let peers integrate independently instead of waiting. |
| Check every clause of the done text | Blind checks found that many claimed passes missed secondary requirements. |
| Proof = seen through the real path | Several PASSes rested on stored-data reads or board posts and were wrong. |
| Self-check labelled, not hidden | Both team and single agent overclaimed about equally when checking their own work. |
| Snapshot in every reply | Peers stopped when their own part was done while items were unowned; nobody saw the gap. |
| `away` recorded on the board | Idle peers were never recalled; stepping away was invisible. |
| Tool limits shared once, never pre-declared | Notification permission and OS file drag were rediscovered by several agents. They can't be known ahead of time. |
| Share failed attempts; rethink after two | Agents repeated the same failing gesture. |
| Close once | Several peers re-hashed the same files at the end. |
| Stale notices marked "already closed" | Late notices woke peers for work already finished. |
| Never ask the parent | The single agent stopped at minute 12 to ask whether to continue. |
| Observer is read-only; log interventions | An unrequested observer nudge changed the team's behavior. |
| Confirm the stop | A scheduled stop was assumed, not checked. |
| Preflight models with a real message | A listed model was rejected by the account; another ran out of credits mid-run. |
| Per-peer resources | Agents interfered with each other's browser sessions. |
| Fixed deadline | Soft budgets drifted; recoveries tempted resets. |

Retros happen only when the user asks. Add a row here only with evidence from a run.
