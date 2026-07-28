# Product ISA Evals

**Status:** Defined, but not run yet.

The scenarios in `evals.json` check whether Product ISA changes preserve important behavior. Run them after meaningful edits to detect regressions and compare whether the new version is actually better.

## Future Workflow

1. Before editing, preserve the current skill as the baseline. Ask the agent to snapshot it or use the last committed version.
2. Make the proposed Product ISA edits.
3. Run the evals with the `skill-creator` skill, comparing the edited skill against the baseline.
4. Review both the generated artifacts and benchmark results.
5. Keep the change only when expected behavior does not regress and the qualitative result is meaningfully better.

Copyable request:

```text
Use the skill-creator workflow to evaluate `.opencode/skills/product-isa` with `.opencode/skills/product-isa/evals/evals.json`. Compare the edited skill against the preserved baseline, run every scenario for both versions, grade objective assertions, and open the eval viewer so I can review the outputs and benchmark. Do not revise the skill until I provide feedback.
```

## First Formal Run

The current scenarios have empty `files` arrays. Before the first reproducible benchmark, create small fixture inputs such as sample user stories, a partial ISA, and conflicting product briefs, then reference them from `evals.json`.

Until fixtures exist, the prompts can still be used as manual smoke tests in disposable sessions, but results may depend on the current workspace.

## What To Check

- Only `_ai/docs/ISA.md` is written.
- Missing inputs and source conflicts stop safely.
- Existing IDs and superseded history are preserved.
- Detailed contracts remain first-class and trace to atomic ISCs.
- Every ISC has one decisive probe.
- Technical implementation choices do not leak into the ISA.
- The user confirms before `status: ready`.

Formal results should live in a sibling workspace such as `product-isa-workspace/iteration-1/`; they are evaluation output, not part of the skill itself.
