---
name: bb-supervisor
description: Manually invoked SOP for running a long-lived BB project supervisor and its per-task Mission Leads. Use only when the user explicitly invokes bb-supervisor, asks the current thread to enter BB Supervisor mode, or when a persisted [SUPERVISOR] or [MISSION] thread resumes. Do not trigger for ordinary delegation.
---

# BB Supervisor

Coordinate project work through BB without turning the supervisor into a worker.
Supervisor, Mission Lead, and Worker are roles, not custom agent types.

## Roles

| Role | BB shape | Responsibility |
|---|---|---|
| **Supervisor** | One long-lived root thread titled `[SUPERVISOR] <project>` | Understand requests, create Missions, track them, synthesize results, and retire completed Missions safely. |
| **Mission Lead** | One direct child titled `[MISSION] <outcome>` in an explicitly selected environment | Own one outcome end to end and run the appropriate existing workflow and skills. |
| **Worker** | A fresh subagent used by an existing skill | Research, implement, review, or verify one bounded assignment, then report to the Mission Lead. |

Workers are transient. Do not create permanent specialist agents or manager threads.

## Activate Or Resume

1. Run `bb thread show --self --json` and confirm the project, title, parent, and environment.
2. If self shell context (`BB_THREAD_ID`, `BB_PROJECT_ID`, `BB_ENVIRONMENT_ID`) is missing, make exactly one recovery attempt: search BB by a unique phrase from the briefed Mission prompt, then verify the single candidate's project, parent, and environment before continuing:

   ```bash
   bb thread search "<unique recent phrase>" --json
   bb thread show <candidate-id> --json
   ```

   If the search returns no unique match, or the candidate's project, parent, or environment cannot be verified, stop and report; never spawn a replacement.
3. A root thread entering this workflow becomes the Supervisor. Run `bb thread update --self --title "[SUPERVISOR] <project>"`.
4. A direct child explicitly briefed as a Mission Lead uses `[MISSION] <outcome>` and follows the Mission loop below.
5. Any other child is a terminal Worker and must not become a supervisor or delegate further.

The role title is durable BB metadata. On resume or after compaction, rebuild state from BB rather than relying on recalled conversation.

## Supervisor Loop

1. **Frame the outcome.** Clarify only ambiguity that could materially change the work. Otherwise choose the simplest reversible path.
2. **Create one Mission per independent outcome.** Parallelize only Missions that do not share writes or ordering dependencies.
3. **Choose the environment.** Apply the gate below before spawning; a new Mission thread does not automatically require a new worktree.
4. **Brief the Mission Lead.** Load and follow `subagent-delegation` for every Mission brief, with the Mission role/depth constraints and selected environment mode as its preamble. Do not restate the templates here.
5. **Spawn the Mission.** Create one visible direct BB child in the selected environment. Pass the project explicitly and identify the child as a Mission Lead in both its title and prompt.
6. **Track without hovering.** Prefer BB lifecycle notifications or `bb thread wait`; do not poll repeatedly. Route follow-ups with `bb thread tell`.
7. **Synthesize.** Read the Mission report and relevant BB diff/status evidence. Give the user the outcome, evidence, blockers, decisions, and thread link without pasting transcripts.
8. **Retire safely.** Follow the cleanup gate below and the Mission failure contract in the Mission Spawn Shape section. Never infer that unmerged work is disposable.

The Supervisor may inspect BB metadata, reports, diffs, and PR state and may perform BB housekeeping. It does not research deeply, edit project files, implement, review code, run product verification, commit, or merge.

### Mission Spawn Shape

Choose the environment with this small gate:

| Task | Mode |
|---|---|
| Read, inspect, explain, or review current work | `SHARED` |
| Continue existing dirty work with confirmed intent | `SHARED` |
| Make unrelated changes or run parallel write work | `MANAGED_WORKTREE` |
| Writing intent or ownership is unclear | Ask one focused question before spawning. |

For `SHARED`, record the existing environment's Git status/diff as a baseline, verify its ID, and attach the new Mission thread to it:

```bash
bb thread spawn --parent-self --project <project-id> \
  --title "[MISSION] <outcome>" --environment <existing-environment-id> \
  --visibility visible --prompt "ROLE: Mission Lead. ENVIRONMENT_MODE: SHARED. ..."
```

For `MANAGED_WORKTREE`, create a fresh managed worktree:

```bash
bb thread spawn --parent-self --project <project-id> \
  --title "[MISSION] <outcome>" --new-environment worktree \
  --visibility visible --prompt "ROLE: Mission Lead. ENVIRONMENT_MODE: MANAGED_WORKTREE. ..."
```

Use an explicit verified parent ID when `--parent-self` is unavailable. Do not silently fall back from `MANAGED_WORKTREE` to `SHARED`. Allow at most one write-capable Mission in a shared environment.

**Mission failure contract.** When a Mission thread dies or reports a fatal failure: if the failure is marked `retryable:false`, preserve the Mission and its environment, stop, and report the failure upward without spawning anything. If `retryable:true`, retry the same Mission once in the same environment; a second failure is `retryable:false`. Any replacement Mission (different title, environment, or parent) requires the user's explicit approval before spawning.

When the Mission thread dies without reporting, the Supervisor classifies the failure itself: treat it as `retryable:true` once per Mission, and a second silent death as `retryable:false`. Do not retry more than once.

## Mission Lead Loop

The Mission Lead is the accountable task orchestrator. It may do lightweight synthesis and coordination, but substantive stages belong to the appropriate existing workflow, skill, or Worker.

1. Restate the outcome and success criteria briefly.
2. Follow the global task router and load the smallest applicable workflow.
3. Before provider-native delegation, run `pwd` and compare it with the Mission environment directory from `bb thread show --self --json`. If shell context is missing, make one recovery attempt using the procedure in Activate Or Resume step 2; if ambiguous, stop and report. Never delegate into a wrong or unverified checkout, and never spawn a replacement.
4. Invoke existing skills for substantive stages. Those skills own their topology and any fresh-context Workers; when they delegate, preserve stricter skill contracts and follow `subagent-delegation` for the brief.
5. Keep one write-capable Worker active at a time in the Mission environment. Independent read-only research may run in parallel.
6. Sequence implementation, fresh code review, and fresh verification. Route revision findings back to the original implementation owner.
7. Reproduce bugs before fixing when applicable. Favor root-cause fixes, guard against regressions and over-hardening, and retain the minimum useful proof.
8. Never merge. Stop for the user's explicit merge instruction.
9. Report upward with the outcome, changed files, checks and evidence, blockers or risks (a fatal failure is marked `retryable:true` or `retryable:false`), PR state, environment mode (`SHARED` or `MANAGED_WORKTREE`), environment ID, and whether the Mission is `READY_TO_RETIRE`.

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

- BB thread relationships and titles identify ownership.
- The Mission environment, Git state, checks, and PR state identify work status.
- Task artifacts required by an invoked skill remain authoritative for that workflow.
- Conversation history is context, not the durable status ledger.
- Do not create supervisor-specific status files, task databases, or duplicate plans.

On resume, list the Supervisor's direct Mission children and inspect only the active or blocked ones needed to answer the user.

## Safe Mission Cleanup

Cleanup is an orchestration operation owned by the Supervisor.

Before retiring a Mission, require the Mission Lead to report its environment mode and `READY_TO_RETIRE`.

### Managed Worktree

Independently inspect:

```bash
bb environment status <environment-id> --merge-base-branch <branch>
bb environment diff <environment-id>
bb environment pull-request show <environment-id>
```

Archive the environment's threads only after one of these gates passes:

- **Completed work:** its PR is confirmed merged **and** status/diff show no newer local work beyond that merged PR; or the Mission was read-only and the environment is clean with no commits or changes to retain.
- **Abandoned work:** the Supervisor states the exact unmerged commits or changes that cleanup will destroy and the user gives explicit informed approval to discard them.

If neither gate passes, preserve the environment and report the blocker.

After a gate passes, run:

```bash
bb environment archive-threads <environment-id>
```

When the final thread in a managed environment is archived, BB removes that worktree and branch. Therefore:

- use `bb thread stop <mission-thread-id>` to pause while preserving work;
- never use `rm -rf`, raw `git worktree remove`, or `bb thread delete` for routine cleanup;
- never treat a merged PR as sufficient when newer local work exists;
- never clean the Supervisor's own project environment as part of Mission retirement.

### Shared Environment

Compare the current Git state with the recorded baseline and Mission outcome. If the Mission is complete and introduced no unexpected changes, archive only its thread:

```bash
bb thread archive <mission-thread-id>
```

Never run `bb environment archive-threads` for a shared Mission because it would also archive the Supervisor and other threads using that environment. If the Mission is incomplete or its changes are unclear, use `bb thread stop <mission-thread-id>` and report the blocker instead.

Archiving preserves BB conversation history and metadata while releasing the runtime; it does not preserve a running agent process.

## Operating Boundaries

- Remain reactive. Automation may message the Supervisor, but it must not bypass it and spawn work directly.
- Nothing auto-merges.
- Keep review and verification attached to the existing Mission and environment.
- Prefer one Mission Lead with clear accountability over several overlapping owners.
- Use a dedicated machine only when requested or when the task is explicitly resource-heavy.
- If intent, destructive cleanup, or merge authority is unclear, ask one focused question with a recommendation.

## Supervisor Report

Keep updates short:

```markdown
## Status
- [Outcome and current state]

## Missions
- [Mission title, thread link, state]

## Evidence
- [Checks, diff, PR, or proof]

## Decision
- [Only when user input is required; otherwise `None`]
```
