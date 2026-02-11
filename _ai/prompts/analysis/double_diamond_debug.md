---
description: Double Diamond workflow adapted for root-cause debugging
alwaysApply: false
---

<DoubleDiamondDebug>
Use a four-stage debugging workflow focused on root-cause isolation. Keep it evidence-first and non-interactive.

1) Discover
- Capture repro context, scope, environment, recent changes, and initial evidence inventory.
- Separate confirmed facts from unknowns.

2) Define
- Write a precise failure statement.
- Set clear boundaries (what is affected, what is not).
- List falsifiable assumptions.

3) Develop
- Generate 5-7 plausible hypotheses.
- Narrow to top 1-2 using discriminating checks that can rule causes in/out.
- Propose exact logs/queries/inspections needed to validate assumptions.

4) Deliver
- Provide a ranked root-cause bet.
- Include confidence, contradictions or missing evidence, and the fastest falsification check.

Evidence rules
- Every conclusion must cite hard evidence.
- File evidence format: `path/file.ts:lineStart-lineEnd`.
- Runtime evidence format: command/query + key output lines.
- If evidence is missing, mark the claim as an assumption.

Do not ask the user to confirm stage progression.
</DoubleDiamondDebug>