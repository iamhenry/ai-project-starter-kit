# Lessons behind bb-swarm

These are practical lessons, not another operating manual. Source labels point to local trial artifacts below; the artifacts and private thread IDs are **not** bundled with this public skill. Change a rule only when new evidence warrants it.

## Before launch

| Observation | Practice | Source |
|---|---|---|
| Unstated scope, limits, or exit conditions invite agents to guess. | Get the full contract approved; offer to draft missing fields, but never infer approval or split the task. | [C8], [D] |
| The proof route and tool limits are often unknown until work begins. | Agree on *what done means*, then let peers find the cheapest consumer path and share any discovered limits. | [D], [B7] |
| A model can appear in a catalog yet fail to answer; credits can run out. | Preflight each selected model with a tiny real request; record interruptions rather than silently changing models. | [CS], [E6] |
| A scheduled cutoff is not an executed cutoff; preparation can consume the budget if timed too early. | Start the clock at dispatch, schedule warn/stop for exact peer IDs, then confirm the stop ran. Recovery does not reset time. A time limit is not a dollar cap. | [C8], [F10] |
| A skill can be advertised to agents even when the user intended manual control. | Keep invocation user-led: v2 disables autoinvoke in metadata; v1 needs a project permission rule plus a manual command. | [OC1], [OC2], [OC3], [OC4] |

## While peers work

| Observation | Practice | Source |
|---|---|---|
| Preassigning files made peers queue on one shared source; permanent planner/worker/judge roles added handoffs. | Equal peers choose small, coherent, provable work themselves. Do not pre-plan or decompose it for them. | [I8], [B7] |
| A working base let others integrate early, but a foundation claim can swallow dependent work. | Agree only the shared interface needed now, get a thin base working, then let peers pick and release adjacent work. | [C8], [H10] |
| Arbitrary claim names can hide overlap; ownership alone does not prevent file collisions. | Describe the actual work, check for existing work first, coordinate shared edits with short locks, and surface stale claims rather than silently stealing them. | [C8], [H10] |
| A relay, broadcast pings, full-board rereads, and acknowledgment loops spent turns without moving the result. | Keep one append-only board with safe writes and per-peer unread cursors; post once, notify one peer only when action is needed. Names are labels, not identity checks. | [CS], [C8], [BB] |
| Manually held locks can stall peers and turn coordination into a queue. | Release edit locks before testing or waiting. The board lock must release automatically. | [C8], [H9] |
| Peers finished their own slice while unowned work remained; idle teammates were not recalled. | Show open/review/stale/idle state in every tool reply. Before leaving, scan it; if you step away, say so. Idle remains reachable. | [H9], [F10] |
| Repeated failed gestures and rediscovered capability limits burned time. | Share attempted path, result, and next hypothesis. After two similar failures, rethink; try one cheap capability route, log a limit, and move on. | [B7], [C8] |
| A parent nudge changed the experiment; late notices revived peers for already-closed work. | Observer stays read-only unless the user intervenes; log any intervention. Mark closed-work notices as stale without discarding the board post. | [F10], [H10] |
| Browser sessions and other shared resources interfered with each other. | Give each peer its own named session/resources. Directory boundaries are instructions, not security isolation; keep secrets and private data off the board. | [B7], [C8] |

## Prove and close

| Observation | Practice | Source |
|---|---|---|
| Work waited until the end for review; duplicate reviews added delay. | Integrate when it first works, name one reviewer, and record built → integrated → peer verdict. Recheck only behavior a later edit affects. | [R9], [H10] |
| Blind testing contradicted many peer and self PASS claims, usually on secondary “and also” requirements. | Check every clause through the consumer's real path; record what was seen. Label self-checks, and never treat code reads, stored state, logs, or a teammate's claim as user-visible proof. | [Q10], [S10] |
| Tool inability was sometimes mistaken for an app defect or promoted to PASS. | Distinguish FAIL, BLOCKED, and UNVERIFIED. Don't fake native permissions or OS gestures. Evidence strength depends on the claim, not screenshot count. | [R9], [Q10] |
| Independent parts worked yet integration failed, including refresh and cross-view behavior. | Check the assembled result and a few meaningful interactions, not just isolated contributions; preserve the simplest solution that meets the whole contract. | [H9], [Q10] |
| Multiple trackers disagreed, and peers repeatedly rehashed the same freeze. | Use one board/state record and one closer. Fingerprint the exact output once; everyone else reuses it. | [F10], [S10] |
| “Active” threads and many screenshots looked like progress without proving outcome. | Report DONE only when the agreed exit criteria are observed; otherwise state PARTIAL/BLOCKED and the remaining gap. Do not infer spend from wall time or agent count. | [B7], [E6], [Q10] |
| A formal QA gate can return BLOCKED for a missing mechanical receipt even after useful user-path findings. | Ask for the cheapest direct observation, keep its receipt, and avoid unrelated verification ceremony. | [Q10] |
| Solo baselines and scorecards answered trial questions, not the team's task. | Keep routine swarm closeout to outcome, evidence, remaining gaps and exact output; do not turn trial scoring into policy. | [S10], [D] |

## Sources used

Local trial notes (source labels only; intentionally not copied into this repo):

- [D] User decisions in the conversation that shaped this skill (not public): manual invocation, complete approval, no decomposition or routine scoring.
- [CS] Shared-room feasibility ticket (`chat-smoke/ticket.md`).
- [E6] Run 6 experiment and trace-review brief (`run6/EXPERIMENT.md`, `run6/TRACE-REVIEW-PLAN.md`).
- [B7] Run 7 contract (`run7/BRIEF.md`).
- [C8] Run 8 charter (`run8/CHARTER.md`).
- [I8] Run 8 intervention log (`run8/evidence/interventions.md`).
- [H9] Run 9 working principles (`run9/HOW-WE-WORK.md`).
- [R9] Run 9 swarm results (`run9/swarm/evidence/RESULTS.md`).
- [H10] Run 10 working principles (`run10/HOW-WE-WORK.md`).
- [F10] Run 10 shared board and freeze (`run10/swarm/board.md`, `run10/evidence/freeze.md`).
- [Q10] Run 10 blind QA reports (`run10/qa/swarm/QA.md`, `run10/qa/solo/QA.md`).
- [S10] Run 10 comparison note (`run10/evidence/SCORE.md`).
- [BB] Local BB thread guide and `bb automation create --help` for directed notices and scheduled work (no public URL used).

Official OpenCode docs used for manual invocation:

- [OC1] [Agent Skills, OpenCode v1](https://opencode.ai/docs/skills/) — skill discovery and permissions.
- [OC2] [Skills, OpenCode v2](https://opencode.ai/v2/docs/skills/) — `metadata.opencode/autoinvoke` and slash visibility.
- [OC3] [Commands](https://opencode.ai/docs/commands/) — user-run command files and file references.
- [OC4] [Permissions](https://opencode.ai/docs/permissions/) — `skill` deny/ask/allow behavior.

Retros happen only when requested. Do not turn this reference into a tracker or a fixed task plan.
