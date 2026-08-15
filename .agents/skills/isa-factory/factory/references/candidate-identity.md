# Candidate Identity

Freeze this transient identity before Review and carry it unchanged through
Accept and Close:

```text
candidate_id: [stable candidate label]
candidate_ref: [immutable commit, snapshot, or explicit worktree subject]
candidate_digest: [immutable candidate digest or tree identity]
base_head: [base commit]
declared_paths: [complete candidate path set]
build_identity: [immutable build/run artifact and environment identity]
runtime_subject: [selected device, app, data lineage, permissions, and external identity; redact secrets]
```

Rules:

- Canonical identity is a committed no-change candidate's commit plus tree
  identity. A worktree candidate uses its base commit, complete declared path
  set, and one exact diff/digest command with its result recorded before
  Review. Carry that same recipe through Accept and Close; never mix digest
  recipes.
- A branch name, path, timestamp, app name, simulator, or `current` checkout
  alone is not identity.
- For an explicit no-implementation route, use the current immutable committed
  `HEAD` and its tree identity, with `declared_paths: []`; the route must be
  stated by the locked slice and must not be inferred from missing changes.
- Review checks the candidate against the locked slice; it does not prove
  runtime behavior.
- Accept must match all identity fields to trustworthy build/runtime evidence.
  Mismatch is `VOID/BLOCKED`, with no leaf PASS.
- Close must detect an identical already-applied packet/candidate/provenance
  set before mutation. Otherwise, for changed candidates it must reproduce and
  commit the declared tree first, verify `HEAD^{tree}`, and only then update
  the ISA/JOURNAL in a separate local commit; for no-change candidates it must
  reuse the matching committed `HEAD` and never create an empty commit.
