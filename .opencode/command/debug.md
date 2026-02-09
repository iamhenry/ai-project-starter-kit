---
name: debug
description: Dual-path bug investigation with ranked evidence
---

Investigate this bug: $ARGUMENTS

You are the main orchestrator. Spawn two `general` subagents in parallel via the Task tool.

Subagent A (5 Whys)
- Use `@.claude/skills/5-whys/SKILL.md` for the method.
- Ask one why at a time, investigate, then continue.
- Every conclusion must include hard evidence.

Subagent B (Debug Error)
- Use `@_ai/tools/analysis/debug_error.md` for the method.
- Generate 5-7 plausible causes, reduce to top 1-2 most likely.
- Add targeted checks/log statements to validate assumptions.
- Every conclusion must include hard evidence.

Hard evidence requirements for both subagents
- File evidence with exact ranges: `path/file.ts:lineStart-lineEnd`.
- Log evidence with command/query used and key output lines.
- If evidence is missing, explicitly mark as assumption.

After both subagents return, synthesize into a brief report ranked by likelihood.

Return format
1) Ranked Findings
   - `Rank | Hypothesis | Likelihood | Hard Evidence`
2) Brief rationale per rank (1-2 lines each)
3) Contradictions or missing evidence
4) Most likely root cause (single best current bet)