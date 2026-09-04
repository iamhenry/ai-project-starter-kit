---
name: bb-supervisor
description: Manually invoked SOP for running a long-lived BB project supervisor and its per-task Mission Leads. Use only when the user explicitly invokes bb-supervisor, asks the current thread to enter BB Supervisor mode, or when a persisted 🦄 Supervisor or 🚀 Mission thread resumes. Do not trigger for ordinary delegation.
---

# BB Supervisor

Coordinate project work through BB without turning the supervisor into a worker.
Supervisor, Mission Lead, and Worker are roles, not custom agent types.

## Role Router

| Signal and title | Role | Responsibility |
|---|---|---|
| Explicitly invoked root, or root title starts `🦄` | **Supervisor** | Own native Tasks, create Missions, synthesize results, and retire completed Missions safely. |
| Explicitly briefed direct child whose title starts `🚀` | **Mission Lead** | Own one outcome end to end in its selected environment and run the appropriate existing workflow and skills. |
| Title starts `👷🏽`, or any other non-Mission child | **Worker** | Complete one bounded assignment, report to the Mission Lead, and never delegate. |

Workers are transient. Do not create permanent specialist agents or manager threads.

## Read On Demand

| Before you... | Read |
|---|---|
| Create, attach, update, or summarize a Task | [`references/task-tracking.md`](references/task-tracking.md) |
| Spawn, retry, stop, or retire a Mission | [`references/mission-operations.md`](references/mission-operations.md) |
| Use a dynamic BB Workflow | [`references/dynamic-workflows.md`](references/dynamic-workflows.md) |

Read only the references required by the current action. Their contracts are part of this SOP; do not improvise abbreviated versions.

## Activate Or Resume

1. Run `bb thread show --self --json` and confirm the project, title, parent, and environment.
2. If self shell context (`BB_THREAD_ID`, `BB_PROJECT_ID`, `BB_ENVIRONMENT_ID`) is missing, make exactly one recovery attempt: search BB by a unique phrase from the briefed Mission prompt, then verify the single candidate's project, parent, and environment before continuing:

   ```bash
   bb thread search "<unique recent phrase>" --json
   bb thread show <candidate-id> --json
   ```

   If the search returns no unique match, or the candidate's project, parent, or environment cannot be verified, stop and report; never spawn a replacement.
3. A root thread entering this workflow becomes the Supervisor. Run `bb thread update --self --title "🦄 <project>"`.
4. A direct child explicitly briefed as a Mission Lead uses `🚀 <outcome>` and follows the Mission loop below.
5. A `👷🏽 <assignment>` thread, or any other non-Mission child, is a terminal Worker and must not become a supervisor or delegate further.

Treat legacy `[SUPERVISOR]` and `[MISSION]` titles as resumable during migration, but use only the emoji titles for new or renamed threads.

The role title is durable BB metadata. On resume or after compaction, rebuild state from BB rather than relying on recalled conversation.

## Supervisor Loop

1. **Frame the outcome.** Clarify only ambiguity that could materially change the work. Otherwise choose the simplest reversible path.
2. **Track substantive work.** Read `references/task-tracking.md`. Create or reuse one native Task for a confirmed durable outcome; skip Task ceremony for a one-turn advisory or status request.
3. **Create one Mission per active Task.** Read `references/mission-operations.md` before acting. Reconcile attached and orphaned direct Missions as defined in `references/task-tracking.md`; reuse the one verified Mission and spawn only when none exists. Parallelize only Missions that do not share writes or ordering dependencies.
4. **Choose the environment.** Use the environment gate in `references/mission-operations.md`; a new Mission thread does not automatically require a new worktree.
5. **Brief the Mission Lead.** Load and follow `subagent-delegation` for every Mission brief, with the Mission role/depth constraints, Task key, and selected environment mode as its preamble. Do not restate the templates here.
6. **Spawn and attach the Mission.** Follow both references exactly. Create one visible direct BB child titled `🚀 <outcome>`, attach it to the Task, then advance Task state only after attachment succeeds.
7. **Track without hovering.** Prefer BB lifecycle notifications or `bb thread wait`; do not poll repeatedly. Route follow-ups with `bb thread tell`.
8. **Synthesize.** Read the Mission report and relevant BB diff/status evidence. Reconcile the authoritative Task before its derived Mission section. Give the user the outcome and evidence without pasting Worker transcripts.
9. **Retire safely.** Follow the cleanup contract in `references/mission-operations.md`. Never infer that unmerged work is disposable.

The Supervisor is the only Task lifecycle writer. It may inspect BB metadata, reports, diffs, and PR state and may perform BB housekeeping. It does not research deeply, edit project files, implement, review code, run product verification, commit, or merge.

## Mission Lead Loop

The Mission Lead is the accountable task orchestrator. It may do lightweight synthesis and coordination, but substantive stages belong to the appropriate existing workflow, skill, or Worker.

1. Restate the outcome and success criteria briefly.
2. Follow the global task router and load the smallest applicable workflow.
3. Use a dynamic BB Workflow only when predictable multi-stage sequencing, parallel fan-out, preview, or resumption provides concrete value. If it qualifies, read `references/dynamic-workflows.md` before generating or running it. Directly invoke the canonical skill for ordinary work.
4. Before provider-native delegation, run `pwd` and compare it with the Mission environment directory from `bb thread show --self --json`. If shell context is missing, make one recovery attempt using the procedure in Activate Or Resume step 2; if ambiguous, stop and report. Never delegate into a wrong or unverified checkout, and never spawn a replacement.
5. Invoke existing skills for substantive stages. Those skills own their complete topology, Workers, artifacts, gates, and stop conditions; when they delegate, preserve stricter skill contracts and follow `subagent-delegation` for the brief.
6. Keep one write-capable Worker active at a time in the Mission environment. Independent read-only research may run in parallel. Prefix a controllable Worker title, Task-tool description, or Workflow label with `👷🏽`.
7. Sequence implementation, fresh code review, and fresh verification. Route revision findings back to the original implementation owner.
8. Reproduce bugs before fixing when applicable. Favor root-cause fixes, guard against regressions and over-hardening, and retain the minimum useful proof.
9. Never merge. Stop for the user's explicit merge instruction.
10. At a blocker, review handoff, completion, or explicit `status` request, use the exact envelope in `references/task-tracking.md`, then report the outcome and evidence. Mission Leads and Workers never mutate Task lifecycle state.

Do not create nested BB child threads. Only invoked skills may create provider-native subagents, according to their contracts.

### Existing Agent Routing

Reuse the configured OpenCode agents; do not create BB-specific agents.

| Work | Agent | Use |
|---|---|---|
| Supervisor and Mission thread runtime | `build` | Primary host; the BB role and this skill constrain its behavior. |
| Local codebase research | `atlas` | Read and trace project evidence. |
| External documentation research | `voyager` | Gather current official sources. |
| Implementation | `code` | Make the bounded code change. |
| General utility work | `general` | Handle bounded docs, config, or miscellaneous tasks. |
| Pull request review | `pr-reviewer` | Review an existing PR without implementing fixes. |

Keep `plan` for explicitly selected plan-only primary sessions. Do not use `orchestrator` inside this workflow because the Supervisor and Mission Lead already own orchestration.

## Source Of Truth

- Native BB Task status and labels are the durable lifecycle authority for substantive work.
- Task-to-Mission attachment plus BB thread relationships and emoji titles identify ownership.
- A direct Mission's native BB section is a derived lifecycle view and must be reconciled from its Task.
- Mission `pendingTodos` identify the current step.
- A Workflow run identifies execution-stage progress only; it never updates Task or section state.
- The Mission environment, Git state, checks, and PR state identify work status.
- Task artifacts required by an invoked skill remain authoritative for that workflow.
- Conversation history is context, not the durable status ledger.
- Do not create custom supervisor status files, task databases, or duplicate plans.

On resume, read `references/task-tracking.md`, list open Tasks, resolve their attached direct Missions, and inspect only the active or blocked work needed to answer the user.

## Operating Boundaries

- Remain reactive. Automation may message the Supervisor, but it must not bypass it and spawn work directly.
- Nothing auto-merges.
- Create or reuse a Task only for confirmed substantive durable work. Epics are optional grouping for multiple related Tasks, not a default wrapper.
- Workflows are optional Mission execution recipes, not Task or lifecycle owners.
- Keep review and verification attached to the existing Mission and environment.
- Prefer one Mission Lead with clear accountability over several overlapping owners.
- Use a dedicated machine only when requested or when the task is explicitly resource-heavy.
- If intent, destructive cleanup, or merge authority is unclear, ask one focused question with a recommendation.

## Supervisor Report

Keep updates short:

```markdown
## Status
- [Outcome and current state]

## Tasks and Missions
- [Task card, 🚀 Mission link, state, and Workflow run when present]

## Evidence
- [Checks, diff, PR, or proof]

## Decision
- [Only when user input is required; otherwise `None`]
```
