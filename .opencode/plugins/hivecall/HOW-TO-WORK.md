# How to work (owner constants)

Read at kickoff, and again after any context compaction or compression. Invariants hold for every run; only the owner changes them. Defaults may be overridden for one run in the run card.

## Invariants

### Honest

1. Correct beats fast beats cheap. Never fake progress or evidence.
2. The score is ledger items proven by independent evidence on the exact build. Activity is not progress.
3. The specs decide (ledger, design docs, prototype, named screenshots). Small visual differences are fine. Record each decision and its reason in the run card.

### Owner

4. Only hard blockers reach the owner, as one loud `🚦` line: disk full after allowed cleanup, model credits out with no backup, push or any remote action, a delete outside the allowlist, a contradiction inside the spec.
5. One status line per real change: an item passes, fails or parks. Silence means nothing changed.
6. Confirm each owner steer in one line once it is applied.

### Progress

7. Every free item has an agent on it within available capacity; pending launches already count as assigned. Never busywork; never re-check a pass whose files did not change.
8. Cheapest proof first: test a built fix → fix a known cause → debug an unknown cause → park.
9. A merge that breaks a passed item is reverted first and fixed on the side, unless the cause is known and the repair is one small change (log why).
10. Three different attempts, then park with an unlock condition. Never repeat the same idea.

### Debugging

11. Prove the cause with logs before changing code. Never patch a dependency on a theory.
12. Tight, time-boxed loops; extend only while each loop teaches something new.

### Machine

13. Protect the machine: stay within the run's device, build and disk limits. Know the platform and environment you work in (iOS, web, other) and clean up what your work starts: simulators, emulators, browsers, dev servers, recorders, log streams.
14. Delete only from the allowlist: build output, build artifacts and saved app or bundle copies, merged worktrees inside the repo.

### Agents

15. Every running agent is visible in BB, briefed with a `PROMISE:` line and the full TALK-BACK block. Never resume a finished helper; continue its work in a fresh visible child with a Delta.
16. Talk back early through `bb thread tell`: confused, the brief is ambiguous, stuck for 5 minutes, or about to guess means a `QUESTION` to the orchestrator. Ask, then keep doing the parts that don't depend on the answer.
17. A talk-back line names the build it is about; a line about an older build is history.
18. Stop a helper's BB thread as soon as its result arrives.
19. One task, one checkable result, named in the brief (for example "baseline scores saved" or "batch 3 answered"). Group code tasks by the feature they change; no two live tasks touch the same files.
20. Use only the dedicated agents from the system prompt's agent table; never pick a raw model or provider. Their model roles are tuned for price, intelligence and speed.
21. Judges (`reviewer`, or `plan` when judging) only read and return a verdict; workers (`build`, `general`) write; `qa` proves.

## Defaults (override per run in the run card)
- Machine: one test device at a time (simulator, emulator or browser instance), one heavy build at a time, at least 5 GB free.
- Leave worker capacity for review and QA; when full, wait for an existing result rather than opening another lane. A pending native helper already owns its task: never launch a duplicate BB thread for it.
- Web QA: use the assigned server URL and a named browser session. If a new server is needed, bind an available port and record its actual URL and process handle. Close only that owned browser session and server handle; never stop another worker's browser/server or kill by process name.
- Debug box: about 15 minutes per attempt; stop after two loops with nothing new.
- Attempt ladder (a guide, not a script): a new hypothesis or method → a different method → a stronger model or research agent → park. Skip a rung when the evidence already rules it out.
- When an attempt fails for an environment, platform, or tool reason, the next starts with reflection and an official-docs lookup, then a new angle—never a plain retry.
- Debug loop: list 5-7 possible causes, keep the 1-2 likeliest, add 1-3 timestamped log lines, one quick rebuild, one user action (tap, click, page load or request), read the log. Use `bugging-out` for stuck bugs.
- Regression guard: 3-5 replayable user journeys, rerun after each merge, not a full re-pass.
- If the environment cannot produce a required condition, the orchestrator may choose a nearby environment (e.g. another OS/runtime, device, or browser) without changing the claim; name it in the check and put any unproven gap on the ledger as owner-only or parked. Verifiers never substitute on their own.
- Preflight: install, typecheck and build the starting branch once (a few minutes). If it fails, fixing it is the first item; independent work may start meanwhile.
- Checkpoint: a git commit to revert to before any risky change.
- Backup model per agent, named at kickoff; on a credit cutoff, switch and report it in one line.
- Task time box: 15 minutes. Split a task expected to run longer before launch. A helper with no honest change for 10 minutes is stale; one still changing but without proof at 15 minutes is asked to land its smallest provable part. QA reports a FAIL with evidence within 10 minutes and does not debug.
- Model-answer work (labeling, judging, replay): batches of at most 20 items, at most 5 batches in parallel.
- Before scaling a model-answer batch, smoke one representative item end to end. Keep input-file lines under 2,000 characters when agents read them; longer lines can be silently truncated.
- Every brief also carries: absolute paths, what is already done and still valid, what this change could break, its time box.

## What the watchdog guarantees (from `watchdog/watch.py`)
A plain script, run every 5 minutes. It never acts on the run; it reports facts and questions, and the orchestrator decides. Work with it:
- It judges each agent only against its own `PROMISE:` line.
- Progress means proof: a new ledger verdict with evidence.
- It alerts on a real problem seen on two checks in a row, once per problem. Each alert is a fact, two questions and a default move, with an id. Answer it in the run card (`ANSWER <id>: ...`) with an action it can see; an unanswered or unacted alert escalates.
- Urgent alerts interrupt the current turn; the rest wait for the turn to end.
- With no new proof it asks at 10 minutes, asks again at 15 if nothing changed, and says park at 20, even while the orchestrator is busy.
- It flags a stale helper (no honest change for 10 minutes) and free items with nobody on them.
- After a context compaction it sends a short re-anchor message.
- If the orchestrator's session starts running as a different agent, it alerts once and leaves the owner a note.
- It never alarms on missing data and prefers removing a noisy check over special cases.
- An agent running but not visible in BB is always reported.
- It reports load, disk, huge files, and leftover recorders and log processes.
- It never nudges while the run card says waiting.
- It pauses when the ledger is done and deletes itself after the run card says closed.
