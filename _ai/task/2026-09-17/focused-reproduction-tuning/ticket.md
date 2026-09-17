# Focused reproduction tuning

## Outcome

Known-bug reproduction should return the first trustworthy structured result without drifting into exploratory QA or collecting redundant evidence.

## Scope

- Route browser reproduction directly through `agent-browser` without changing that skill.
- Add a small default probe budget and a result-first exit rule to `reproduce-bug`.
- Add one bounded recovery instruction to `issue-to-pr` when evidence exists but the reproduction result is missing.
- Add a generic return-before-enrichment rule to `subagent-delegation`.
- Set QA to OpenAI Luna with extra-high reasoning.
- Preserve `dogfood` unchanged.
- Preserve Atlas and Voyager on GLM 5.3 Flash with high reasoning, and Build and General on OpenAI Luna with extra-high reasoning; those settings already match the request.

## Acceptance

- A deterministic reproduction defaults to one faithful attempt and at most one discriminating probe.
- A decisive result is reported before optional evidence or cleanup.
- Pipeline recovery requests a structured result from existing evidence without rerunning or independently judging the reproduction.
- Agent configuration uses the requested model assignments.
- Commit and PR publication happen only after review approval.
