# Close Verdict Contract

## Packet Set

The authority supplies a complete in-context set of independent JSON or Markdown packets. The format may vary, but each packet must expose these fields without inference. Packet records are transient; any durable evidence locator belongs in that record's `evidence` field.

| Field | Requirement |
| --- | --- |
| `isc` | One current leaf ID from ISA `## Criteria`; no group ID |
| `verdict` | Exactly `PASS`, `FAIL`, `BLOCKED`, or `VOID` |
| `candidate` | Complete source plus acceptance identity: `candidate_id`, immutable `candidate_ref`, `candidate_digest`, provenance `base_head`, `declared_paths`, `integrated_ref`, and `integrated_digest` |
| `build` | Traceable `build_identity` plus the artifact/environment channel needed to distinguish the verified execution |
| `probe` | The ISA Test Strategy row or exact predeclared probe identity |
| `subject` | Runtime-selected subject, redacted as needed; not a synthetic stand-in |
| `threshold` | Exact predeclared binary pass threshold |
| `observed` | What the verifier actually observed, including units/counts/timing where relevant |
| `evidence` | Replayable retained evidence path or command and observation channel |
| `verifier` | Independent verifier/session identity and completion time |
| `authority` | Acceptance authority identity and packet-set identity |

Extra fields are ignored unless they contradict a required field. Missing, malformed, duplicated, or contradictory required fields invalidate that packet.

## Validity

A `PASS` is valid only when the packet's ISC, probe, threshold, subject, evidence, candidate tree, build identity, and verifier are mutually consistent and match the current ISA. The observation must directly establish the threshold at the claim's boundary. A packet cannot pass because the implementation exists, a test was asserted, or another packet passed.

`FAIL` means the declared probe ran and did not meet its threshold. `BLOCKED`
means the probe or required evidence channel was unavailable or not honestly
sufficient; it parks proof and cannot earn closure, but does not invalidate
reviewed implementation. `VOID` means the packet is not eligible for credit,
including candidate/build identity mismatch, stale or superseded ISA/probe,
duplicate authority, tampering, or unreconciled contradiction.

All non-PASS verdicts have zero credit. Preserve them in the packet set; do not convert, repair, or summarize them as PASS.

## Reconciliation

Before mutation, Close must establish:

- exactly one packet-set authority and one packet per targeted leaf;
- packet-set coverage of the target leaves, with no unaccounted duplicate;
- current ISA leaf IDs and Test Strategy rows still match the packet claims;
- packets closed together reference the same immutable integrated identity;
  each source identity matches its reviewed lane and each proof environment is
  traceable to that candidate. Shared identity fields must agree, while a
  provenance-only `base_head` difference does not invalidate otherwise
  identical accepted content;
- independent verifier identities are not the implementation author or acceptance authority unless the authority explicitly permits that role;
- evidence is retained and accessible without requiring a destructive or remote action.

If these checks fail, do not credit any affected leaf. If the conflict cannot be resolved without changing ISA intent, return `blocked` and request human authority only under the skill's interruption rules.
