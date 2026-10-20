# Critique playbook

Input: a problem statement, and optionally an existing solution to judge against it.

## Brief template

The brief must be neutral and non-biased, with no leading details: facts and the question only, no hint at an answer. Check it against the rule in SKILL.md before sending.

```markdown
ROLE: Terminal worker, read-only advisor. Do not edit files, run writing commands, spawn threads or subagents, or ask other models. You may read the repo and search the web; cite URLs.

## Problem statement
<the user's problem, in their words or confirmed by them>

## Owner premises and constraints
- <hard limits only, labeled as the owner's; no design choices or opinions of the options>

## What exists now (facts only)
<the current solution: what it does, size, cost, where it lives; strengths and weaknesses at equal depth>

## Options on the table (if any)
<each option with its strongest case and its costs, same depth; no ranking>

## Answer in this order (under ~700 words)
1. Verdict: does what exists solve the problem? yes / partly / no, one paragraph.
2. Is the problem statement right? What is wrong or missing, from first principles.
3. Risks: what will break, cost, or need upkeep.
4. Recommended next step: the smallest thing that solves the problem under the constraints. Name what to keep, cut, and add.
5. What good looks like: a concrete test a non-expert can use to tell if your recommendation works.
6. Unique angle: one thing the other advisors would likely miss.

Return only your own raw answer. Do not compare, merge, or summarize other advisors' views.
```

With no existing solution, drop "What exists now" and "Options", and answer item 1 as the biggest gap to close; keep the answer order.

## Synthesis (main agent only)

The advisors return raw answers only. The agent that invoked this skill, in the parent thread, writes the synthesis after all five answers arrive.

Open with one sentence: the verdicts and whether they converge.

- **Agree:** points most advisors share, with the count (for example 4 of 5).
- **Disagree:** a table, topic by advisor.
- **Unique angles:** one per advisor, attributed.
- **What it means:** in the user's terms; note any bias you introduced in the brief.
- **Next step:** 2 to 3 options ranked, your pick with one reason.

Link each advisor thread. Do not present agreement as proof when the brief leaned toward one answer.
