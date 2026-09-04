# Task Tracking

Read this file before creating, attaching, updating, or summarizing a native BB Task.

## Authority And Creation

Native Task status and labels are the durable lifecycle authority. The Supervisor alone creates or reuses Tasks, changes lifecycle state or labels, attaches Missions, and performs Epic roll-up. Mission sections are derived navigation; Mission envelopes are handoff messages.

For a confirmed durable outcome, create or reuse one Task in the Tasks project linked to the BB project. If none is linked, ask once for its name and prefix before creating it. Do not create a Task for a one-turn advisory or status request. Add an Epic parent only when multiple related Tasks genuinely need roll-up.

Before spawning, inspect both Task attachments and the Supervisor's direct children:

```bash
bb tasks threads <task-key> --json
bb thread list --parent-thread <supervisor-thread-id> --project <project-id> --json
```

Ignore archived attachments as history and reuse the one valid non-archived attached direct Mission. If none is attached, inspect non-archived `🚀` children with `bb thread show` and `bb thread log`; a unique orphan is reusable only when its brief carries the exact Task key and its parent, project, outcome, and environment all match. Attach that orphan and reuse it. If candidates conflict or identity is uncertain, stop and report. Spawn only when no attached or verified orphan Mission exists.

After a successful spawn, attach it:

```bash
bb tasks attach <task-key> --thread <mission-thread-id>
```

Only after attachment is confirmed, move the Task to `in_progress`, add its start comment, and place the Mission in the derived Active section. If spawn or attachment fails, do not advance the Task; follow `mission-operations.md`.

## Lifecycle Projection

| Task state | Derived Mission view |
|---|---|
| `backlog` or `todo` | No Mission yet. |
| `in_progress` without `blocked` | `Missions - Active` |
| `in_progress` with `blocked` | `Missions - Blocked` |
| `in_review` | `Missions - Ready for review` |
| `done` or `canceled` | Retire safely, then use archived history. |

Resolve the three native sections once. Archived direct Missions are completed history; do not create a `Done` section.

Update a Task only at start, blocker, review handoff, and completion. At each boundary add at most one concise comment with evidence and next action; include the Workflow run ID when present. Remove the `blocked` label when work resumes. Never create a Task per Worker or Workflow stage, and never mirror Worker events into Task comments.

Emit the standalone native `::task{key="<task-key>"}` card for creation, blocker, review handoff, completion, and explicit `status` responses. The directive must be the only content on its line: never prefix it with a bullet or append arrows, status, or prose; put those on separate lines.

Only the Supervisor moves a direct Mission:

```bash
bb thread update <mission-thread-id> --section <section-id>
```

## Mission Status Envelope

At a blocker, review handoff, completion, or explicit `status` request, the Mission Lead begins its report with:

```text
MISSION_STATUS
TASK: <key|none>
STATE: ACTIVE|BLOCKED|READY_FOR_REVIEW
CURRENT_STEP: <one sentence>
NEXT_ACTION: <one sentence>
RETRYABLE: true|false|n/a
ENVIRONMENT_MODE: SHARED|MANAGED_WORKTREE
ENVIRONMENT_ID: <id>
COMMIT: <sha|none>
PR: <url|none>
WORKFLOW_RUN: <run-id|none>
READY_TO_RETIRE: yes|no
```

The Mission reports evidence or requests a transition. It does not mutate Task lifecycle state.

## Status Requests

1. List open Tasks in the linked Tasks project and resolve attached direct Missions. Include `done` or `canceled` only when history is requested.
2. Read each Task first, then verify its Mission, environment, Git, and PR facts where needed.
3. If an idle Mission has no running Worker, current todo, or valid envelope, mark its Task blocked with reason `missing status report`; do not guess.
4. Reconcile stale sections from Task state, then report `Task | Mission | State | Current step | Workflow | Next action`.
5. Never list provider-native Workers as project work items. Inspect them only when direct Mission state is inconsistent.
