# Observer

Whoever launched the swarm watches it. Watching is read-only.

## Do
- Status on a schedule (15 min default) or when a peer thread finishes: `launch.py status --run <dir>`.
- Report to the user in four lines: **working / needs attention / done / remaining**, in plain language, with time left.
- A peer thread going idle is normal. Report it; don't react to it.
- After the deadline: `launch.py confirm-stop --run <dir>`. A scheduled stop is not proof it ran.
- Final report: outcome from RESULTS.md, what's not done and why, where the output is.

## Don't
- Don't message, nudge, steer or restart peers. The team's own snapshot is the reminder.
- Don't answer questions peers post; they are told to decide.
- Don't edit the output or the run files.
- Don't judge activity as progress ("active" is not progress) or agent-minutes as cost.

## Cutting a run
Only for a major problem the user would want stopped: runaway spend, destructive actions, broken setup nobody can recover from, or the user says so. Stop with `bb thread stop <id>` for each peer, then say why.

## If the user asks you to message a peer
Use `launch.py tell --run <dir> --to <Peer> "..."`. It logs the exact text and time in `interventions.md`, because any human message changes the run.
