# ISA Ledger Update

## Mutation Rules

The ISA is canonical. In one in-memory transaction, then one file write:

1. Identify current leaf ISCs and their valid existing `## Verification` PASS lines.
2. Union existing valid PASS leaves with newly valid PASS packet leaves, keyed by ISC ID. Never count a parent/group row.
3. For a repeated leaf, retain the existing line when it proves the same candidate identity; otherwise replace that leaf's line with the new provenance only after the new packet passes all checks.
4. Set `progress: N/T`, where `N` is the number of unique current leaf ISCs with valid PASS provenance and `T` is the total current leaf count. Recount; never increment a stored number.
5. Derive `status` only from current progress: `ready` when `N=0`, `building` when `0<N<T`, and `verified` when `N=T`. Preserve `drafting` when the ISA is not a ready implementation contract; Close must not make a drafting or contradictory ISA verified.
6. Update `updated` once. Do not edit criteria text, Test Strategy, source contracts, decisions, non-PASS records, or unrelated frontmatter.

`FAIL`, `BLOCKED`, and `VOID` do not change `N`, `progress`, or status. A candidate identity mismatch blocks the entire close before any mutation; it is not a failed leaf.

## Idempotency And Recount

Running Close twice with the same packet-set identity, complete candidate
identity, and existing PASS provenance must return a successful no-op: no
candidate or ledger commit, verification line, progress change, or duplicate
JOURNAL event. A new candidate may replace the provenance for a leaf only when
it is a valid PASS for the current leaf; the unique-leaf count remains bounded
by `T`.

After the ISA write, assert all of these before the second commit:

- every credited ID is a current leaf;
- each credited ID has one valid provenance line and one valid PASS packet;
- `progress` equals the recount, not a prior value;
- `N <= T` and status equals the lifecycle rule;
- no non-PASS packet received credit;
- no duplicate verification line exists for a leaf.

If any assertion fails, do not commit ISA/JOURNAL and return `blocked`.

## JOURNAL Entry

Append one concise entry to `JOURNAL.md`, for example:

```text
YYYY-MM-DD | isa-close | candidate [commit/tree] | PASS [N/T] | non-PASS [count] | packets [packet-set]
```

The entry records the operation and candidate pointer only. It must not become a competing per-leaf status list or claim that non-PASS leaves were closed. Return the ISA/JOURNAL commit SHA after it exists; do not write that SHA into this same commit. If the candidate commit succeeded but the ISA/JOURNAL commit fails, leave the entry/update uncommitted as appropriate, do not reset the candidate, and return `blocked` with the failure.

## Commit Ordering

1. Candidate commit: exact verified candidate tree only. For a no-change
   candidate whose committed `HEAD` already has the packet tree identity, reuse
   `HEAD`; otherwise verify `HEAD^{tree}` equals the packet tree identity after
   creating the candidate commit. Never create an empty commit.
2. ISA/JOURNAL commit: the provenance, recount, derived status, and concise journal entry, including the candidate commit/tree identity.

Never combine these commits, because the second commit cannot contain its own SHA. Never write ISA/JOURNAL before the first tree verification succeeds.
