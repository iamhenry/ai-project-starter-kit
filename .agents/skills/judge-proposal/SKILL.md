---
name: judge-proposal
description: Judge proposed approaches from a gather-context task artifact. Use after `{ISSUE_DIR}/issue.md` contains candidate approaches and research artifacts exist. Scores options against hard gates, ETHOS, and evidence; writes the selected decision back into issue.md or returns ASK_USER with one focused question. Does not implement anything.
---

# Judge Proposal

Select the best approach from an existing task artifact. Be lean, rubric-based, evidence-based, and implementation-free.

## Inputs

Required task folder:

- `{ISSUE_DIR}/issue.md`
- `{ISSUE_DIR}/research/*.md`
- `_ai/docs/ETHOS.md`

Artifact contract:

- `issue.md` contains the problem, acceptance criteria, constraints, and candidate approaches.
- `ISSUE_DIR` is the artifact directory created by `gather-context` for the current pipeline run.
- `research/*.md` contains cited codebase/product/external evidence.
- `ETHOS.md` supplies decision principles: tracer bullet first, reuse existing pieces, one fact one place, user trust, fail safely, pragmatic shipping, idiomatic code, simple UX.

## Read Sequence

1. Read `issue.md` first. Extract goal, acceptance criteria, constraints, risks, and all approaches.
2. Read every `research/*.md`. Treat cited findings as evidence; treat uncited claims as weak signal.
3. Read `_ai/docs/ETHOS.md`. Use it to resolve tradeoffs, not to invent new scope.

If any required input is missing or approaches are not present, return `ASK_USER` and ask for the missing artifact or proposal set.

## Hard Gates

Reject an approach before scoring if it:

- Fails explicit acceptance criteria.
- Conflicts with stated constraints or research evidence.
- Adds implementation scope not required by the issue.
- Creates duplicated state/source of truth without a clear need.
- Weakens security, privacy, reversibility, or user trust.
- Depends on unavailable APIs, libraries, credentials, or product decisions.
- Cannot be verified with the available acceptance criteria or a clear regression probe.

## Weighted Rubric

Score each non-rejected approach from 0-100:

- 25: Acceptance fit: satisfies all acceptance criteria with the smallest complete change; no extra product scope.
- 20: Evidence fit: supported by cited `research/*.md`; assumptions are explicit and not contradicted.
- 15: ETHOS fit: aligns with tracer bullet first, reuse, one fact one place, user trust, fail safely, and pragmatic shipping.
- 15: Reuse/style fit: follows repo patterns and avoids new surfaces, state, dependencies, or abstractions unless needed.
- 10: Blast radius: limits touched files, regression paths, migration risk, and downstream coupling.
- 10: Verification clarity: has clear acceptance/regression checks and is easy to rollback.
- 5: Phase fit: matches proof/build/polish quality bar from `ETHOS.md`; does not over- or under-engineer.

Scoring anchors for each category:

- Full credit: clearly satisfies the category with cited evidence.
- Half credit: partially satisfies it, or evidence is plausible but thin.
- Zero credit: missing, contradicted, or unverifiable.

If scores tie or are close, break ties in this order:

1. Meets acceptance criteria with least scope.
2. Lower blast radius.
3. Better repo style fit.
4. Better verification clarity.
5. More reversible.

## Decision Rule

Choose one approach only when:

- All hard gates pass for the selected approach.
- Score is `>= 80`.
- Lead over second place is `>= 8` points.
- No product-sensitive ambiguity remains.

Otherwise return `ASK_USER` with exactly one focused question. Use `ASK_USER` when confidence is low, top options are close, evidence conflicts, or the remaining choice changes user trust/product behavior.

Explicit `ASK_USER` cases:

- Product behavior changes user trust.
- Top two valid approaches differ by `< 8` points.
- Evidence conflicts across issue/research artifacts.
- Selected approach needs an unavailable product decision.
- No approach passes hard gates.

## Writeback

Edit only the `## Judge Decision` section in `issue.md`. If missing, append it to the end of `issue.md`.

Use exactly this section shape:

```md
## Judge Decision

Status: SELECTED | ASK_USER
Selected Approach: <approach name or N/A>
Confidence: High | Medium | Low

Scores:
- <approach>: <score>/100 - <one-line reason>
- <approach>: <score>/100 - <one-line reason>

Decision:
<2-4 bullets explaining why this wins or why selection is blocked. Cite exact evidence from issue.md/research where useful.>

Question:
<one focused question if ASK_USER, otherwise N/A>
```

Return the same decision summary in chat after writeback.

## Constraints

- Do not edit code.
- Do not implement the selected approach.
- Do not create a separate decision file.
- Do not create helper/reference files.
- Do not modify `research/*.md` or `_ai/docs/ETHOS.md`.
- Do not commit changes.
- Do not perform `judge-plan` responsibilities such as implementation steps, task breakdowns, or worker prompts.
