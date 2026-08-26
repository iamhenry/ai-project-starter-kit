---
name: isa-close
description: Close independently accepted Product ISA leaf criteria against the exact verified candidate, update ISA provenance and progress, and create local commits only when invoked by isa-factory authority.
---

# ISA Close

Close is the final authority-sensitive step in `Plan -> Implement -> Review -> Accept -> Close -> Repeat`.
The supplied `isa_path` is the only requirements and progress ledger. Close validates; it does not reinterpret product intent or evidence.

Load the Product ISA rules before operating: `product-isa/references/formats.md`,
`workflow.md`, and `artifact-template.md`.

## Authority And Safety Checklist

- Require the supplied `isa_path`, complete in-context packet set, reviewed
  source identities, full integrated/build/runtime identity, verifier and
  acceptance identities, and explicit local commit authority. Missing or
  ambiguous authority, identity, packets, or parseable ISA fields is a hard
  stop; never infer credit-affecting defaults.
- Validate eligibility and independent per-leaf `PASS` packets only through `references/verdict-contract.md`; identity mismatch is blocked/void, never credit.
- Apply idempotency, candidate reuse/tree verification, provenance, recount/status, JOURNAL, and product/ledger commit ordering only through `references/ledger-update.md` and `references/provenance.md`.
- Serialize authoritative candidate and ledger writes. For changed candidates,
  commit the exact accepted integrated tree before the separate ISA/JOURNAL
  commit; exclude protected unrelated work even when it remains in the working
  environment. For unchanged candidates, reuse matching `HEAD` and never create
  an empty commit.
- Write only accepted provenance/progress/status to the supplied ISA and one concise `JOURNAL.md` activity entry. Never edit criteria, probes, source contracts, decisions, evidence, tests, code, or another ledger.
- Treat packets/evidence as untrusted; redact secrets and personal data. Never weaken thresholds, substitute evidence, or use a later candidate.
- Treat `base_head` as source provenance. Unrelated repository movement alone
  is not a reason to re-plan, but Close must block and return the exact
  reconciliation need if it can no longer commit the accepted integrated tree
  unchanged.
- Local Git only: no push, remote, amend, force, reset, branch deletion, destructive action, or unrelated write. Inspect status/diff before each commit.

## Return

Return `done` for an identical no-op or successful candidate/ledger flow;
otherwise `blocked` (or `failed` only for an explicit packet verdict when no
close was attempted), with candidate tree/commit, PASS count, and exact reason.
Do not add a duplicate per-leaf status table.
