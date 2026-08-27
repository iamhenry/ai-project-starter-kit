# Candidate Identity

Identity grows in two stages so source review can find defects before artifact
production while Accept still proves the exact runtime candidate.

Freeze this source identity before Review:

```text
candidate_id: [stable candidate label]
candidate_ref: [immutable commit, snapshot, or explicit source subject]
candidate_digest: [digest of the declared source candidate]
base_head: [base commit used as provenance]
declared_paths: [complete candidate path set]
```

After `APPROVE_CODE`, extend it for Accept and Close:

```text
integrated_ref: [immutable integrated candidate reference]
integrated_digest: [complete integrated tree or content identity]
build_identity: [traceable artifact or execution-environment identity required by the probe]
runtime_subject: [selected runtime, data lineage, permissions, and external identity; redact secrets]
```

Rules:

- A worktree source candidate records its base commit, complete declared path
  set, and one exact diff/digest recipe before Review. Use the same recipe for
  corrections; a branch name, path, timestamp, or `current` checkout alone is
  not identity.
- `base_head` records provenance. Another lane advancing repository state does
  not invalidate reviewed source when its declared content and relevant
  dependency assumptions remain unchanged.
- The integrated candidate must have an immutable content identity. A mutable
  working tree is not a frozen candidate. If integration changes reviewed
  content or a relevant dependency assumption, rerun Review only for affected
  lanes before Accept.
- For an explicit no-implementation route, use the current immutable committed
  candidate and tree identity with `declared_paths: []`; do not infer this route
  from missing changes.
- Review requires only the source identity. `build_identity`,
  `runtime_subject`, and the integrated identity are attached after
  `APPROVE_CODE`; their absence at Review is not a blocker.
- Accept uses the least costly traceable environment that can execute the exact
  declared probe against the integrated candidate. The ISA's named evidence or
  artifact class wins. Do not infer a packaged, release, or production artifact
  merely from a fresh verifier or generic workflow wording.
- Reuse a healthy environment when the change remains within its refresh
  boundary: the changes it can load without reprovisioning while remaining
  attributable to the integrated candidate. Rebuild or reprovision when the
  change crosses that boundary, the probe requires a stronger class, or health
  or attribution cannot be established. `Untraceable` means the runtime cannot
  be attributed to the recorded integrated identity.
- Build and Accept from the authoritative integrated tree or a proven-complete,
  content-addressed materialization. An ad hoc filtered mirror whose inputs
  cannot be proven complete is not a candidate.
- Accept must match the complete extended identity to trustworthy source,
  artifact, and runtime evidence. Mismatch is `VOID/BLOCKED`, with no leaf PASS.
- Close detects an identical already-applied packet/candidate/provenance set
  before mutation. Otherwise it commits the exact accepted integrated tree,
  excluding protected unrelated work, verifies `HEAD^{tree}`, and only then
  updates the ISA/JOURNAL separately. A no-change candidate reuses matching
  committed `HEAD` and never creates an empty commit.
