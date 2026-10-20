# Shape playbook

Input: an idea or problem to build toward. Output: a short spec the main agent implements from.

Never pass a previous synthesis as input. Turn it into the brief below: hard limits stay limits, shared facts stay facts, and everything else, including design choices the user agreed to after an earlier round, becomes an open question.

## Brief template

The brief must be neutral and non-biased, with no leading details: facts and the question only, no hint at a design. Check it against the rule in SKILL.md before sending.

```markdown
ROLE: Terminal worker, read-only advisor. Do not edit files, run writing commands, spawn threads or subagents, or ask other models. You may read the repo and search the web; cite URLs.

## Problem statement
<the user's problem>

## Hard limits (owner; do not reopen)
- <privacy, cost, authority, and similar limits only; never a design choice or a prior round's conclusion>

## Facts
- <what exists, data available, known limits; no opinions>

## Open questions (answer each with a reason)
- <each unresolved choice, phrased neutrally>

## Answer in this order (under ~800 words)
1. Shape: the high-level design in a few sentences and a small diagram (components and data flow).
2. Components: each with its job, inputs, outputs, and what it reuses from the repo.
3. Open questions: your answer and reason for each.
4. Cut list: what existing code or steps to delete or not build.
5. Risks and upkeep: what breaks and how often; how you keep it low maintenance.
6. Proof: the smallest real check that shows it works, readable by a non-expert.
7. Unique angle: one thing the other advisors would likely miss.

Return only your own raw answer. Do not compare, merge, or write a combined spec.
```

## Synthesis into a spec (main agent only)

The advisors return raw shapes only. The agent that invoked this skill, in the parent thread, merges them into the spec after all five answers arrive.

Merge the five shapes. Where they agree, adopt. Where they differ, pick one, give the reason, and list the runner-up. Escalate to the user only choices that change scope, cost, or a hard limit.

Write the spec with these sections:

- **Goal:** the problem in one sentence.
- **Shape:** diagram plus a few sentences.
- **Components:** job, inputs, outputs, files touched.
- **Decisions:** each open question, the choice, and why.
- **Cut:** what is removed or not built.
- **Proof:** the real check that shows it works.
- **Out of scope.**

Show the spec to the user for approval before implementing. After approval, the main agent implements from the spec; the advisors do not.
