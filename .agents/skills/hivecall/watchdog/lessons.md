# Hivecall lessons (from real runs)

Universal rules learned the hard way. Project-specific traps belong in the run card's Lessons section.

## Agents
1. Every agent must show up in BB within 30 seconds of launch. If one doesn't, stop launching more until it does.
2. Never resume a finished agent session; it runs invisibly. Launch a fresh agent instead.
3. `bb thread tell` to a finished agent restarts it. That can put two writers on the same files.
4. After a crash, old agent sessions may still be running. Check before launching replacements.
5. Stop agents with `bb thread stop` (or the OpenCode interrupt API). Never kill processes by name.
6. Agents read and write only inside the repo. A path outside the repo can hang on a permission prompt for an hour. Temp files go under the repo.
7. The orchestrator never opens images or screenshots. One screenshot in context crashed the Journal orchestrator. Testers describe what they see in text.

## Briefs
8. Every brief has: role, the items, the exact check, a `PROMISE:` line, the TALK-BACK block from the `subagent-delegation` skill (one channel, real parent id), a bare result filename, allowed folders, "do not spawn subagents", and "write results as you go". Without TALK-BACK a blocked worker stays silent until it finishes.
9. Pick the promise kind that fits the work: `timed` for anything that waits, `helper` for reviewers.
10. Before briefing a fix, check how many attempts the item already had. After three failed attempts with different approaches, park it.
11. Work on the difference. Re-verify only what a change could have affected.

## Proof
12. Activity is not progress. Only a new ledger verdict with evidence counts.
13. A new test tool needs one positive-control run (a case that must pass) before its FAILs mean anything.
14. A check for "X must not happen" needs a control that shows the check can see X.

## Machine
15. Recorders and log streams need a hard time cap. Check for orphans after every tester.
16. Watch disk. Evidence folders and build caches filled the disk three times; one forced a reboot.
17. Heavy load makes timing and gesture or animation checks fail. Re-check those under calm load before calling them bugs.
18. Hide evidence and lane folders from Git (`.git/info/exclude`). Thousands of untracked files made BB lag.

## Watchdog
19. `bb automation update` drops any field you don't pass. Re-pass env, interpreter, working directory, and script every time.
20. Watch the watchdog: once an hour, check its alerts matched reality. Note false alarms; loosen the check, never special-case it.
21. Usage limits stop agents silently. Set the run card to `waiting-usage` so the watchdog stops nudging.
22. A paused watchdog still clutters BB; delete its automation on the check after the run card closes.
23. Resumed helpers are hidden from BB: BB binds a child only to its first run, so a resumed or queued-to-finished session can keep working while BB shows `idle`, and it creates duplicate writers. So never resume; start a fresh visible child (lesson 24), and trust the watchdog's hidden-helper alert.
24. Send each new task or follow-up to a fresh visible child with a short Delta (`done`, `remaining`, `continue in`); message only running sessions, verify `active` with `bb thread list --parent-thread <orchestrator> --json`, and interrupt any hidden resumed worker before relaunching.
25. Show each worker talk-back message to the owner as a word-for-word quote, then your response: the owner sees what the worker said (not as their own message) and how you handled it.
