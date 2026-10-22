# Hivecall wishlist

Ideas not built yet. Each needs evidence from runs before it ships. Checked items shipped in hivecall 1.1.0–1.2.0.

- [ ] **End-of-run lessons.** When a run ends, whether it succeeded or not, read the run card and extract what worked and what needs improvement. Save them as proposals for the next skill edit. Verify them first; don't take them at face value.
- [x] **Final report in the run card.** Write the final report into `.hivecall/run.md` (`## Final report`) in the same step that closes the run, then send it in chat. (1.1.0: SKILL.md End step; also when paused on the owner.)
- [x] **Goal survives compaction.** After context compaction, re-inject the goal and run card (for example with an OpenCode plugin), not just a "re-read" rule. (1.1.0: the watchdog's `REANCHOR` message sends the goal, open items and owner rules after each compaction. An OpenCode plugin that re-injects them is not built.)
- [ ] **Hill-climb.** Use the weekly retro plus the eval to improve the skill one measured step at a time. (Started: the retro flags eval impact instead of editing the eval; eval 4.1 adds hill-climb numbers.)
- [x] 🌟 For the hivecall/watchdog script we should be asking questions like why is it stuck? What can we honestly and soundly do to continue hill climbing to complete the remaining tasks as optimal and quickly as possible. (1.1.0: alerts give a fact, two questions, a default move and an id the orchestrator answers in the run card.)
  - [x] Check how long we've been stuck at the same completed items without progress and identify why and how to unblock itself for the optimal path. (1.1.0: the stall ladder asks at 10 min, again at 15, says park at 20, even while the orchestrator is busy.)
