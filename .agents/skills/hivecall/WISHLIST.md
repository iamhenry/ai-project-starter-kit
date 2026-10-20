# Hivecall wishlist

Ideas not built yet. Each needs evidence from runs before it ships.

- **End-of-run lessons.** When a run ends, whether it succeeded or not, read the run card and extract what worked and what needs improvement. Save them as proposals for the next skill edit. Verify them first; don't take them at face value.
- **Final report in the run card.** Write the final report into `.hivecall/run.md` (`## Final report`) in the same step that closes the run, then send it in chat.
- **Goal survives compaction.** After context compaction, re-inject the goal and run card (for example with an OpenCode plugin), not just a "re-read" rule.
- **Run stays with the orchestrator.** Flag it when another agent, such as `build`, ends up driving most of a run.
- **Watchdog: fewer false alarms, same real catches.**
  - Before calling a process orphaned, check whether its parent or owning agent is still working. This is a guideline, not a rigid rule.
  - Work in a separate thread the watchdog can't see shouldn't look unclaimed. Make that work visible instead.
  - Skip finished or leftover sessions before calling an agent stuck, ghost or not visible.
  - Use the newest ledger verdict per item. Don't re-send alerts about things already handled.
  - Measure machine load when evidence is captured, not when the ledger is written.
  - Only blame an agent for files in its own lane.
- **Every alert gets an answer.** The orchestrator acts on each alert, or records why it was a false alarm.
- **Talk-back stays clean.** Workers send only BUG / BLOCKED / QUESTION / STOP, to the right parent. Final results go back the normal way, not as messages.
- **Orchestrator stays hands-off.** No screenshot reads and no code edits in the orchestrator.
- **No full app build on every change.** Build once per checkpoint, not per edit.
- **Check push authority.** Never push without the kickoff's PR authority, and make that checkable.
- **Record the watchdog version per run.** Today only the SKILL.md version is visible.
- **Smaller skill.** Text an edit adds has to pay for itself.
- **Hill-climb.** Use the weekly retro plus the eval to improve the skill one measured step at a time.
