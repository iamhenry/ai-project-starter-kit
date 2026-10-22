# Live run of the to-do benchmark

How to run hivecall on the frozen to-do task and compare it with the baseline in `../../README.md`. This is the setup from to-do run 1. Follow it as written so runs stay comparable.

Two rules matter most:

- **Nothing in the run folder points at answers.** It gets `TASK.md`, `design.md` and frozen skill copies. Never `QA.md`, the eval, earlier runs, or this file.
- **Never edit `TASK.md`, `design.md` or `QA.md`.** Change the skill, not the task.

## 1. Build the run folder

Pick a new folder, for example `~/Desktop/Projects/other/hivecall-todo-run<N>`, and a skill version: a commit or tag of this repo (`<REF>`).

```bash
RUN=~/Desktop/Projects/other/hivecall-todo-run<N>; KIT=<path to ai-project-starter-kit>; REF=<commit or tag>
mkdir -p "$RUN" && cd "$RUN" && git init -q
git -C "$KIT" show "$REF:.agents/skills/hivecall/eval/bench/todo/TASK.md" > TASK.md
git -C "$KIT" show "$REF:.agents/skills/hivecall/eval/bench/todo/design.md" > design.md
mkdir -p .opencode/skills .opencode/agents
for s in hivecall subagent-delegation code-quality-gate verification-gate agent-browser git-commits \
         gather-context bugging-out reproduce-bug ponytail animation-principles; do
  git -C "$KIT" archive "$REF" ".agents/skills/$s" | tar -x --strip-components=2 -C .opencode/skills
done
rm -rf .opencode/skills/hivecall/eval
git -C "$KIT" show "$REF:.agents/agents/reviewer.md" > .opencode/agents/reviewer.md
printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "default_agent": "orchestrator"\n}\n' > opencode.json
```

- Skills go in `.opencode/skills/`, not `.agents/skills/`. In this setup a global link sends `.agents/skills` to the main checkout, so project copies there are ignored.
- `ponytail` and `animation-principles` are frozen too. Run 1 loaded the global copies, which made it harder to reproduce.
- Hooks: no remote, and a `pre-push` hook that exits 1. Point `core.hooksPath` at `.git/hooks` and use a `pre-commit` that runs only the kit's `.githooks/checks/secrets.sh staged`. The kit's file-size hook blocks normal app files. Add a `commit-msg` hook that runs the kit's `.githooks/commit-msg`.
- Commit the start state (`chore: start run`) and note its sha.

## 2. Register and start

1. `bb project create --name hivecall-todo-run<N> --root "$RUN" --machine <host id>`.
2. Pin the agent. The BB CLI can't choose an agent, so set it through the OpenCode plugin. Stamp the project with `orchestrator`, spawn, stamp the thread, then reset the project to `build`: `bb plugin rpc call opencode stampAgent --input-file <json>`, where the JSON is `{"projectId"|"threadId": ..., "agent": "orchestrator", "queued": false}`.
3. Spawn a **top-level** thread, not a child of your chat, so your chat can't leak in: `bb thread spawn --project <id> --title "hivecall to-do run <N>" --model anthropic/claude-opus-5-5 --reasoning-level medium --permission-mode full --visibility visible --prompt-file prompt.md`. Keep `prompt.md` outside the run folder. It holds exactly:

   ```text
   /hivecall

   Goal: build the app in @TASK.md until every feature is proven or parked as BLOCKED with a reason. TASK.md is the spec; design.md is the style guide.

   Watchdog: yes. PR: no. You have my go-ahead to start: I won't be answering during this run, so make your best call on anything unclear, note it in the run card, and keep going.
   ```

   The `@TASK.md` mention must resolve to the file.
4. Check the first turns. The plugin log (`~/.bb/plugins/opencode/logs/plugin.log`) must show `agent.derive thread=<run thread> ... agent=orchestrator`. The hivecall skill must load from `$RUN/.opencode/skills/`. If either is wrong, stop the thread, archive it, clean the folder (`git clean -fdx && git checkout .`) and start again.

## 3. Watch from outside

Create the outside check as a script automation in a project other than the run's. It re-pins the agent every 5 min, scans tool calls for answer paths, and stops everything at the cap. It only messages you; the run never sees it.

```bash
bb automation create --project <your project> --name "hivecall-todo-run<N> check" --cron "*/5 * * * *" \
  --timezone <tz> --script-file liverun_check.py --working-directory automation-storage \
  --env-json '{"RUN_THREAD":"<thread>","RUN_DIR":"<RUN>","RUN_PROJECT":"<run project>","PARENT_THREAD":"<your thread>","SELF_PROJECT":"<your project>","SELF_NAME":"hivecall-todo-run<N> check","START_EPOCH":"<unix seconds>"}'
```

Don't answer the run and don't steer it. Your only reasons to step in are BROKEN, POSSIBLE LEAK or CAP. Whatever the run's own watchdog does is part of the test.

## 4. After it ends

1. **Blind QA.** Follow `QA.md`. Copy the app at the closing commit to a folder outside the run, save file hashes, and run the 3 testers on that copy. Check the hashes are unchanged afterwards.
2. **Grade.** From `../..`, run `python3 eval.py --run <run id>`. Use `HIVECALL_EVAL_DIR=<temp dir>` first if you only want a look.
3. **Cheat audit**, on the run's sessions and the testers': no reads outside the run folder (system files aside), every thread in the run project, no web tools or package installs, no push, `TASK.md`/`design.md`/`.opencode` unchanged, every PASS evidence file present, testers never touched the run folder.
4. **Archive** like earlier runs. Keep `~/.evals/hivecall/runs/<run id>/` (the grade writes `run.json`, `sessions/`, `ledger-at-end.html`) and add `run.md` (the run card) and `blind-qa/` (tester notes, hashes, HEAD; no app code).
5. **Clean up**, only after the grade in step 2 (it saves the agent tree the BB project holds). Delete the run folder, its BB project and threads, its automations, the QA app copy, and the outside check if it hasn't deleted itself.
6. Compare with the baseline in `../../README.md`: time to close, proven items, owner messages, blind QA working and confirmed. Read the run next to its dashboard column before trusting the score.
