---
name: debug
description: Dual-path bug investigation with triangulated evidence
---
<!-- Purpose: use any time you have a bug and you need more confidence about the root cause -->
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

After both subagents return, you MUST triangulate their outputs before final ranking.

Triangulation protocol (required)
1) Normalize hypotheses into shared buckets (merge duplicates/synonyms).
2) Compare A vs B for each hypothesis:
   - `Agreement`: agree | partial | disagree
   - `Agent A evidence`
   - `Agent B evidence`
   - `Shared evidence`
   - `Conflicts / gaps`
3) Re-rank using this tie-break order:
   - Hard evidence quality (strongest first)
   - Cross-agent agreement level
   - Raw likelihood
4) If A and B disagree on top rank, explain exactly why one is downgraded.
5) Add one fastest falsification check for the #1 hypothesis.

Return format
1) Ranked Findings
   - `Rank | Hypothesis | Likelihood | Agreement(A/B) | Hard Evidence`
2) Triangulation Matrix
   - `Hypothesis | A stance | B stance | Shared evidence | Conflicts | Confidence delta`
3) Brief rationale per rank (1-2 lines each)
4) Convergence (where A/B align) and Disagreements (where A/B diverge)
5) Contradictions or missing evidence (explicit assumptions)
6) Most likely root cause (single best current bet)
7) Fastest falsification check for top hypothesis
