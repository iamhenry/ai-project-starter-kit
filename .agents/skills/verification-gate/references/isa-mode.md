# Verification Gate: ISA Mode

This contract applies only when the caller explicitly supplies `mode: isa`.

## Inputs

All of these are required unless marked optional:

- `mode: isa`.
- `isa_path`: caller-supplied authoritative ISA path, carried unchanged and
  read-only for provenance/context. Any example path is illustrative; a
  missing or unreadable path is `BLOCKED`, never an inferred default.
- `locked_slice`: the same transient locked slice passed to `code-quality-gate`, including `slice_id` and stable leaf records with exact criterion, probe, and pass condition. It is immutable for this invocation. Verify only these leaves; do not discover, split, merge, reorder, or infer additional leaves.
- `source_identity`: the exact frozen identity reviewed by `code-quality-gate`,
  containing `candidate_id`, immutable `candidate_ref`, `candidate_digest`,
  `base_head` as provenance, and `declared_paths`.
- `acceptance_identity`: the extension created after source approval,
  containing immutable `integrated_ref`, `integrated_digest`, traceable
  `build_identity`, and `runtime_subject`.
- `code_quality_result`: the corresponding ISA-mode result, which must be
  `APPROVE_CODE` for the same `slice_id` and source identity when
  implementation changed files. For the no-implementation alternative, this
  field is replaced by an explicit `no_implementation_route: true` plus the
  immutable committed source and integrated identity with no changed paths.
- changed files and/or implementation summary, plus the target URL, command, environment, auth, data, and other prerequisites relevant to the selected platform route.
- Optional: baseline or runtime-subject identity required by a leaf's probe.

If a required input or any source/acceptance identity field is missing, or neither a
matching `APPROVE_CODE` nor the explicit no-implementation route is supplied,
return `BLOCKED` and do not run platform verification. Never infer the
no-implementation route from an absent diff, empty summary, or missing review.

## Candidate Identity Gate

Before evaluating a leaf, establish that the runtime subject actually verifies
the immutable integrated candidate and that every reviewed source digest is
present unchanged. `base_head` is provenance, not a requirement that unrelated
repository state remain frozen. If integration changed reviewed content or a
relevant dependency assumption, return `BLOCKED` for affected lanes until their
source review is renewed.

Use the least costly traceable environment that can execute the exact declared
probe. The ISA's named evidence or artifact class wins; never infer a packaged,
release, or production artifact from a fresh verifier or generic phase wording.
Reuse a healthy environment when the change remains within its refresh
boundary: the changes it can load without reprovisioning while remaining
attributable to `integrated_digest`. Rebuild or reprovision when the change
crosses that boundary, the probe requires a stronger class, or health or
attribution cannot be established. `Untraceable` means the runtime cannot be
attributed to the integrated identity.

Run from the authoritative integrated tree or a proven-complete,
content-addressed materialization. Do not verify an ad hoc filtered mirror whose
required inputs cannot be proven complete. A development, incremental, or
already-running environment may satisfy Accept when it is the declared proof
class and its candidate attribution is trustworthy; convenience alone is not
identity.

If identity cannot be established or any identity field mismatches, the
verification is `VOID/BLOCKED`: return overall `VOID/BLOCKED`, mark every leaf
in the affected slice `BLOCKED` (or `VOID` where the report needs to distinguish
invalidated evidence), and mark none of them `PASS`. Do not accept partial
identity evidence, reuse evidence from another candidate, or award
credit/update the ISA or `JOURNAL`.

## Verification And Routing

Use the existing platform routes, smallest-proof-path rule, evidence hygiene, screenshot hygiene, and artifact cleanup from `SKILL.md`. Execute only the declared probe for each locked leaf. A leaf is `PASS` only when its own consumer-boundary probe and exact pass condition are proven against the matched candidate; source inspection, mocks, fixtures, or another leaf's evidence are not substitutes.

One real end-to-end execution is the default. Add at most two independent
perspectives only when each addresses a distinct named risk such as recovery,
state, runtime, or user context. A count is never a quota, and an automated
persona must still execute the real system rather than a mocked integration.

Before returning overall `PASS`, validate every Close packet field for every
leaf (`isc`, `verdict`, `candidate`, `build`, `probe`, `subject`, `threshold`,
`observed`, `evidence`, `verifier`, `authority`) is complete, non-ellipsized,
and its evidence locator is retained and accessible through Close, not merely
accessible in-session. Missing, placeholder, or inaccessible packet data is
`BLOCKED`, not later packet-repair churn.

Use one complete Close packet record per leaf, with these fields and no inferred
values: `isc`, `verdict`, `candidate`, `build`, `probe`, `subject`, `threshold`,
`observed`, `evidence`, `verifier`, and `authority`. `candidate` carries the
complete source and acceptance identity unchanged. Use per-leaf verdicts
`PASS`, `FAIL`, or `BLOCKED`. `BLOCKED` means the declared proof cannot run or
cannot establish its condition; `FAIL` means it ran and the condition was not
met. Overall `PASS` requires every leaf to be `PASS`; any `FAIL` yields overall
`FAIL`, and any `BLOCKED` yields overall `BLOCKED` unless a higher-priority
identity failure already yields `VOID/BLOCKED`.

- `FAIL`: route the failing leaf evidence to the implementation owner; do not edit code, ISA, or `JOURNAL`.
- `BLOCKED`: route the missing prerequisite or proof gap to the caller. Preserve
  reviewed implementation, park the dependent probe, and block closure without
  forcing re-plan unless the slice or relevant assumptions changed.
- `PASS`: report evidence only. This gate never credits, closes, or updates ISA leaves.

## Output

Use this alternate structure only for ISA mode:

```md
## Verification Result

- Mode: `isa`
- ISA: [isa_path]
- Slice: [slice_id]
- Candidate: [candidate_id, candidate_ref, candidate_digest, base_head,
  declared_paths, integrated_ref, integrated_digest, build_identity,
  runtime_subject]
- Platform: `web|mobile-web|ios|macos|non-ui`
- Overall verdict: `PASS|FAIL|BLOCKED|VOID/BLOCKED`

### Leaf Verdict Packet Set

Each row is one transient packet and must include all fields required by
`isa-factory/close/references/verdict-contract.md`:

| isc | verdict | candidate | build | probe | subject | threshold | observed | evidence | verifier | authority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [leaf_id] | `PASS|FAIL|BLOCKED|VOID` | [complete source and integrated identity] | [traceable proof artifact/environment] | [declared probe] | [runtime subject] | [exact threshold] | [observation] | [retained path or command] | [identity/time] | [identity/packet set] |

### Evidence

- [artifact path or `No artifacts`]

### Next Action

- [commit / fix failing leaves / unblock prerequisites / invalidate and rerun against the frozen candidate]
```

For identity failure, use `Overall verdict: VOID/BLOCKED`, use `VOID` or `BLOCKED` for every matrix row, and include no `PASS` row. Do not emit the issue-mode single `PASS|FAIL|BLOCKED` output in ISA mode. Do not modify any code, ISA, `JOURNAL`, or commit.
