# Mission Operations

Read this file before spawning, retrying, stopping, or retiring a Mission.

## Choose The Environment

| Task | Mode |
|---|---|
| Read, inspect, explain, or review current work | `SHARED` |
| Continue existing dirty work with confirmed intent | `SHARED` |
| Make unrelated changes or run parallel write work | `MANAGED_WORKTREE` |
| Writing intent or ownership is unclear | Ask one focused question before spawning. |

For `SHARED`, record the existing environment's Git status and diff as a baseline, then verify its ID:

```bash
bb thread spawn --parent-self --project <project-id> \
  --title "🚀 <outcome>" --environment <existing-environment-id> \
  --visibility visible --prompt "ROLE: Mission Lead. ENVIRONMENT_MODE: SHARED. ..."
```

For `MANAGED_WORKTREE`, create a fresh managed worktree:

```bash
bb thread spawn --parent-self --project <project-id> \
  --title "🚀 <outcome>" --new-environment worktree \
  --visibility visible --prompt "ROLE: Mission Lead. ENVIRONMENT_MODE: MANAGED_WORKTREE. ..."
```

Use an explicit verified parent ID when `--parent-self` is unavailable. Do not silently fall back from `MANAGED_WORKTREE` to `SHARED`. Allow at most one write-capable Mission in a shared environment.

After spawning, follow the attachment and activation sequence in `task-tracking.md`. If attachment fails, do not advance the Task; stop the unattached Mission and report the exact blocker.

## Failure And Retry

When a Mission dies or reports a fatal failure:

- `retryable:false`: preserve the Mission and environment, stop, and report without spawning anything.
- `retryable:true`: inspect Task comments for `MISSION_RETRY: <mission-thread-id> 1/1`. If absent, add that exact comment before running:

  ```bash
  bb thread tell <mission-thread-id> "Retry the failed operation once; keep the same Task and environment."
  ```

  If the marker exists, the retry is consumed and the failure becomes `retryable:false`.

For a silent Mission death, apply the same marker and same-thread operation. Never retry more than once. Any replacement Mission requires explicit user approval and is not a retry.

## Safe Retirement

Cleanup belongs to the Supervisor. Require the Mission Lead's environment mode and `READY_TO_RETIRE` report. Do not mark its Task `done` or `canceled` from the report alone. First verify retained Git and PR evidence and the applicable gate below; then update the Task, add the final evidence comment, and archive the Mission.

### Managed Worktree

Inspect:

```bash
bb environment status <environment-id> --merge-base-branch <branch>
bb environment diff <environment-id>
bb environment pull-request show <environment-id>
```

Archive only when one gate passes:

- **Completed:** the PR is merged and status/diff show no newer local work; or the Mission was read-only and the environment is clean with no commits or changes to retain.
- **Abandoned:** state the exact unmerged commits or changes that cleanup will destroy and obtain explicit informed user approval.

Otherwise preserve the environment and report the blocker. After a gate passes:

```bash
bb environment archive-threads <environment-id>
```

When the final thread is archived, BB removes the managed worktree and branch. Use `bb thread stop <mission-thread-id>` to pause while preserving work. Never use `rm -rf`, raw `git worktree remove`, or `bb thread delete` for routine cleanup. Never treat a merged PR as sufficient when newer local work exists, and never clean the Supervisor's own project environment as Mission retirement.

### Shared Environment

Compare current Git state with the recorded baseline and Mission outcome. If complete with no unexpected changes, archive only the Mission:

```bash
bb thread archive <mission-thread-id>
```

Never run `bb environment archive-threads` for a shared Mission; it would also archive the Supervisor and other threads. If work is incomplete or unclear, run `bb thread stop <mission-thread-id>` and report the blocker.

Archiving preserves conversation history and metadata while releasing runtime; it does not preserve a running agent process.
