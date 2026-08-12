# Code Quality Gate: ISA Mode

This contract applies only when the caller explicitly supplies `mode: isa` for
a slice whose implementation changed files. The factory must skip this gate
for an explicit no-implementation route; it must not require an artificial
diff.

## Inputs

All of these are required unless marked optional:

- `mode: isa`.
- `isa_path`: caller-supplied authoritative ISA path, carried unchanged. Any
  example path is illustrative; a missing or unreadable path is `ASK_USER`,
  never an inferred default.
- `locked_slice`: transient, caller-supplied contract containing `slice_id` and one or more leaf records. Each leaf record must contain a stable `leaf_id`, the exact criterion, its falsifiable implementation-relevant requirement, and its declared probe/pass condition. The gate must treat this slice as immutable for this invocation; it must not broaden, split, rewrite, or derive leaves from the ISA.
- `candidate_identity`: the complete frozen identity of the implementation under review, forwarded unchanged: `candidate_id`, immutable `candidate_ref`, `candidate_digest` or tree identity, `base_head`, `declared_paths`, `build_identity`, and `runtime_subject`. A branch name, path, timestamp, or `current` checkout alone is not an identity.
- changed files and/or the candidate diff, required only when implementation
  changed files; never create an artificial diff for a no-implementation slice.
- implementation summary.
- Relevant test, build, lint, and typecheck output when available.
- Optional: quality standards referenced by the issue-mode contract.

Missing `isa_path`, `locked_slice`, any required candidate identity field, or
changed code/diff for an implementation slice is `ASK_USER`. Missing output
that is needed to judge safely is also `ASK_USER`; inapplicable output is not a
failure.

## Review Boundary

Review only the candidate against the supplied locked slice and normal quality standards. This gate may assess whether the implementation is plausible and complete enough for later proof, but it must not run runtime/platform verification, claim that a leaf is proven, credit or update any leaf, edit the ISA or `JOURNAL`, or create review artifacts. `isa_path` is provenance/context only, not a write target.

Check that the diff and summary identify the frozen candidate, and that the implementation addresses each locked leaf without adding unrequested scope. Do not treat source presence, mocks, fixtures, or supplied assertions as runtime proof.

## Decisions And Revision Routing

Return the existing decisions exactly: `APPROVE_CODE`, `REVISE_CODE`, or `ASK_USER`. Apply the existing hard-fail and score rules, using the locked slice instead of `plan.md` for intended scope. `APPROVE_CODE` means only that code quality passed; it does not mean any ISA leaf passed.

- `REVISE_CODE`: route the findings to the implementation owner. After revision, rerun this gate with a newly frozen candidate identity and the applicable locked slice; never silently reuse an identity for changed code.
- `ASK_USER`: route missing, conflicting, or ambiguous ISA inputs to the caller.
- `APPROVE_CODE`: route the same locked slice and complete frozen candidate identity, unchanged, to `verification-gate`.

## Output

Use the existing `## Code Quality Gate Result` structure from `SKILL.md`. Keep its decision, score, findings, required changes, and next-action fields unchanged. In `Reviewed`, name `isa_path`, `locked_slice`, every field of `candidate_identity`, the diff/changed files, summary, and supplied checks instead of `plan.md`/`issue.md`. Forward the complete candidate identity unchanged; do not add leaf verdicts.
