# Close Provenance

## Canonical Line

Write one concise line per newly or repeatedly valid PASS leaf in `## Verification`:

```text
- ISC-001: PASS - candidate [commit/tree]; build [immutable identity]; subject [redacted identifier]; observed [threshold value]; evidence [retained path or replay command]; verifier [identity]; packet [packet-set/packet ID]
```

Use the ISA's existing one-line verification style. Keep the exact observed value and threshold-relevant evidence locator; do not paste logs. Redact tokens, credentials, private paths, email addresses, and unnecessary personal data.

The candidate commit is the first close commit when candidate files changed. For
a no-change candidate, the already verified committed `HEAD` is the candidate
commit and no empty commit is created. The ISA/JOURNAL commit is returned after
creation but is not written into its own JOURNAL entry, because a commit cannot
contain its own SHA. The candidate tree identity remains the binding identity;
a commit SHA alone is insufficient.

## Preservation

- Do not add provenance for `FAIL`, `BLOCKED`, or `VOID`.
- Do not rewrite valid prior PASS provenance unless the same leaf is being revalidated against a new candidate; then replace only that leaf's line with the new exact identity.
- Do not retain stale PASS provenance after a changed claim, superseded probe, or invalidated candidate. Such invalidation belongs to the owning ISA workflow, not Close; block rather than reinterpret it.
- Do not create a second verification line for the same current leaf. Existing
  valid PASS lines are idempotently retained; their packet identity must still
  match the candidate being closed. A repeated Close is a no-op only when the
  packet-set identity, complete candidate/build identity, and existing PASS
  provenance match exactly and the ISA already reflects the resulting
  recount/status.

## Provenance Checks

Before writing, each line must be derivable from one valid packet and the current ISA Test Strategy row. After writing, recount the current leaf lines from the ISA itself and verify each credited line has a corresponding valid PASS packet. A provenance line is proof metadata, not a second requirements or status ledger.
