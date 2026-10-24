# Live run of the to-do benchmark

How to run hivecall on the frozen to-do task and compare it with the baseline in `../../README.md`. This is the setup from to-do run 1. Follow it as written so runs stay comparable.

Two rules matter most:

- **Nothing in the run folder points at answers.** It gets `TASK.md`, `design.md` and frozen skill copies. Never `QA.md`, the eval, earlier runs, or this file.
- **The plugin's source is not in the run folder.** The run loads a frozen copy from outside, so it can use the skill but has no reason to read or edit the plugin's code. (Run `2026-10-23-YJoOhR` had the bundle inside and the orchestrator read the plugin's source.)
- **Never edit `TASK.md`, `design.md` or `QA.md`.** Change the skill, not the task.

## 1. Build the run folder

Pick a new folder, for example `~/Desktop/Projects/other/hivecall-todo-run<N>`, and a skill version: a commit or tag of this repo (`<REF>`).

```bash
RUN=~/Desktop/Projects/other/hivecall-todo-run<N>; KIT=<path to ai-project-starter-kit>; REF=<commit or tag>
# Frozen plugin, outside the run folder and outside the kit. Absolute path, no eval, read-only.
BUNDLE="$HOME/Desktop/Projects/other/hivecall-bundles/$(git -C "$KIT" rev-parse --short "$REF")/hivecall"
mkdir -p "$(dirname "$BUNDLE")"
git -C "$KIT" archive "$REF" .opencode/plugins/hivecall | tar -x --strip-components=2 -C "$(dirname "$BUNDLE")"
rm -rf "$BUNDLE/eval" && chmod -R a-w "$BUNDLE"
mkdir -p "$RUN" && cd "$RUN" && git init -q
git -C "$KIT" show "$REF:.opencode/plugins/hivecall/eval/bench/todo/TASK.md" > TASK.md
git -C "$KIT" show "$REF:.opencode/plugins/hivecall/eval/bench/todo/design.md" > design.md
mkdir -p .opencode/skills .opencode/agents
for s in subagent-delegation code-quality-gate verification-gate agent-browser git-commits \
         gather-context bugging-out reproduce-bug ponytail animation-principles; do
  git -C "$KIT" archive "$REF" ".agents/skills/$s" | tar -x --strip-components=2 -C .opencode/skills
done
git -C "$KIT" show "$REF:.agents/agents/reviewer.md" > .opencode/agents/reviewer.md
printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "default_agent": "orchestrator",\n  "plugins": ["%s"]\n}\n' "$BUNDLE" > opencode.json
```

- **Plugin path.** The `plugins` entry is the bundle's absolute **folder**, not `index.ts`. The OpenCode docs list a `.ts` file as valid, but v2.1.3 logs `configured plugin path must be a directory` and skips it; the hivecall skill then silently falls back to any global `hivecall-deprecated`. The project `plugins` list adds to the global one. Use an absolute path because BB runs the thread in its own worktree (step 2), and a relative path resolves from the worktree's copy of `opencode.json`, which has no bundle beside it.
- **Paths inside the skill still work.** Loading the skill prints `Base directory for this skill: <BUNDLE>` and absolute file paths, so the links in `SKILL.md` (`HOW-TO-WORK.md`, `references/...`, `watchdog/watch.py`) resolve against the bundle. The plugin writes only to `<run>/.hivecall/`, so a read-only bundle is fine. The watchdog copy step becomes `cp "<Base directory>/watchdog/watch.py" .hivecall/watch.py`. A bare `.opencode/plugins/hivecall/...` path no longer exists in the run folder; if the orchestrator uses one, that is a skill bug to note, not something to fix mid-run. Checked 2026-10-23: absolute folder entry → `loading plugin id=<BUNDLE>`, skill load showed the bundle as base directory, copied `watch.py` from it and ran `--simulate stuck-agent`.
- Skills go in `.opencode/skills/`, not `.agents/skills/`. In this setup a global link sends `.agents/skills` to the main checkout, so project copies there are ignored.
- `ponytail` and `animation-principles` are frozen too. Run 1 loaded the global copies, which made it harder to reproduce.
- Hooks: no remote, and a `pre-push` hook that exits 1. Point `core.hooksPath` at `.git/hooks` and use a `pre-commit` that runs only the kit's `.githooks/checks/secrets.sh staged`. The kit's file-size hook blocks normal app files. Add a `commit-msg` hook that runs the kit's `.githooks/commit-msg`.
- Commit the start state (`chore: start run`) and note its sha.

## 2. Register and start

1. `bb project create --name hivecall-todo-run<N> --root "$RUN" --machine <host id>`.
2. Pin the agent. The BB CLI can't choose an agent, so set it through the OpenCode plugin. Stamp the project with `orchestrator`, spawn, stamp the thread, then reset the project to `build`: `bb plugin rpc call opencode stampAgent --input-file <json>`, where the JSON is `{"projectId"|"threadId": ..., "agent": "orchestrator", "queued": false}`.
3. Spawn a **top-level** thread, not a child of your chat, so your chat can't leak in: `bb thread spawn --project <id> --provider opencode --title "hivecall to-do run <N>" --model anthropic/claude-opus-5-5 --reasoning-level medium --permission-mode full --visibility visible --prompt-file prompt.md`. Always pass `--provider opencode`: without it BB uses the project's remembered provider, and in run `2026-10-23-YJoOhR` the first ~10 helpers ran on Codex, outside the OpenCode trace the eval reads. Keep `prompt.md` outside the run folder. It holds exactly:

   ```text
   /hivecall

   Goal: build the app in @TASK.md until every feature is proven or parked as BLOCKED with a reason. TASK.md is the spec; design.md is the style guide.

   Watchdog: yes. PR: no. You have my go-ahead to start: I won't be answering during this run, so make your best call on anything unclear, note it in the run card, and keep going.
   ```

   The `@TASK.md` mention must resolve to the file.
4. **Record the real run folder.** BB starts the thread in its own git worktree, not in `$RUN`. Read it with `bb thread show <thread> --json` → `environment.path` (run hooks1 ran in `~/.bb/plugins/environment-git-worktree/host-data/worktrees/<thread>-1/<folder name>`). Use that path as `RUN_DIR` for the outside check, blind QA, and the cheat audit; the run card, commits and `.hivecall/` live there. Because the worktree is cut from the start commit, `opencode.json` must be committed in it.
5. Check the first turns. The BB OpenCode plugin log (`~/.bb/plugins/opencode/logs/plugin.log`) must show `agent.derive thread=<run thread> ... agent=orchestrator`. The first hivecall skill load must print `Base directory for this skill: <BUNDLE>` (not a `hivecall-deprecated` path and not a path inside the run folder). If either is wrong, stop the thread, archive it, clean the folder (`git clean -fdx && git checkout .`) and start again.
6. **Helpers must run as the agent their brief names.** On a native subagent call that is the `agent=` argument. On the BB route the CLI can't choose an agent, so each helper spawn needs `--provider opencode` and a `stampAgent` pin with the briefed role (as in step 2, per thread). In run `2026-10-23-YJoOhR` 35 of 37 helpers briefed as `reviewer` or `qa` ran as `build`. Spot-check the first helper in `plugin.log`; afterwards the eval's context row 25 counts it for every helper.

## 3. Watch from outside

Create the outside check as a script automation in a project other than the run's. It re-pins the agent every 5 min, scans tool calls for answer paths, and stops everything at the cap. It only messages you; the run never sees it.

```bash
bb automation create --project <your project> --name "hivecall-todo-run<N> check" --cron "*/5 * * * *" \
  --timezone <tz> --script-file liverun_check.py --working-directory automation-storage \
  --env-json '{"RUN_THREAD":"<thread>","RUN_DIR":"<environment.path from step 2.4>","RUN_PROJECT":"<run project>","PARENT_THREAD":"<your thread>","SELF_PROJECT":"<your project>","SELF_NAME":"hivecall-todo-run<N> check","START_EPOCH":"<unix seconds>"}'
```

Don't answer the run and don't steer it. Your only reasons to step in are BROKEN, POSSIBLE LEAK or CAP. Whatever the run's own watchdog does is part of the test.

## 4. After it ends

1. **Blind QA.** Follow `QA.md`. Copy the app at the closing commit to a folder outside the run, save file hashes, and run the 3 testers on that copy. Check the hashes are unchanged afterwards.
2. **Grade.** From `../..`, run `python3 eval.py --run <run id>`. Use `HIVECALL_EVAL_DIR=<temp dir>` first if you only want a look.
3. **Cheat audit**, on the run's sessions and the testers': no reads outside the run folder (system files and `$BUNDLE` aside), no reads of plugin source through a run-folder path, every thread in the run project and on provider `opencode`, no web tools or package installs, no push, `TASK.md`/`design.md`/`.opencode` unchanged, every PASS evidence file present, testers never touched the run folder.
4. **Archive** like earlier runs. Keep `~/.evals/hivecall/runs/<run id>/` (the grade writes `run.json`, `sessions/`, `ledger-at-end.html`) and add `run.md` (the run card) and `blind-qa/` (tester notes, hashes, HEAD; no app code).
5. **Clean up**, only after the grade in step 2 (it saves the agent tree the BB project holds). Delete the run folder and its BB worktree, its BB project and threads, its automations, the QA app copy, and the outside check if it hasn't deleted itself.
6. Compare with the baseline in `../../README.md`: time to close, proven items, owner messages, blind QA working and confirmed. Read the run next to its dashboard column before trusting the score.
