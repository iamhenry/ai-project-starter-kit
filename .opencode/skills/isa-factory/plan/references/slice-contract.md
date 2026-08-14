# Locked Slice Contract

The packet is transient. It is not a file, progress record, issue, plan, or
replacement for the ISA. Keep exact contract text intact; add context around
it rather than rewriting it.

```text
LOCKED ISA SLICE
Status: ready | blocked
ISA path: [resolved path]
ISA identity: [artifact/title, revision or updated identity, current progress]

Journey: [one user trigger -> observable end state]
Why this slice: [one concise evidence-backed reason]

Leaves:
- ID: [ISC-ID]
  Exact text: [verbatim ISA leaf text]
  Exact probe: [verbatim prescribed probe/check]
  Exact threshold: [verbatim prescribed pass threshold]
  Current state: open | failed | blocked
  Implementation required: yes | no | uncertain
  Evidence basis: [code/Git/JOURNAL/ISA path and lines]
  Route: automated | human-external | contract-gap | dependency-blocked

Capabilities:
- [CAP-ID] Owner/outcome: [one narrow capability]
  Covers: [ISC IDs or "enables evidence only"]
  Dependencies: [prerequisites]
  Evidence obligation: [exact consumer-boundary evidence]
  Non-overlap boundary: [what this assignment does not own]

Dependencies:
- [prerequisite or dependent] -> [affected leaf/capability]; [reason and evidence]

Candidate identity expectation: [fresh agent identity plus exact runtime/data/
subject identity it must preserve or select; no synthetic substitution]
Evidence requirements: [subject lineage, live boundary, retained result, and
the exact ISA threshold]
Hard blockers: [ISA contradiction, unavailable true external authority/access,
missing prerequisite, wrong subject, unavailable evidence channel]
Out of scope: [all other leaves, contract edits, implementation outside the
journey, verification/accept/close/commit/push]
```

## Locking Rules

- Lock only open leaves. A leaf is still open when its code exists but its
  exact probe has not passed in the ISA's required evidence class.
- Copy IDs, wording, probe steps, thresholds, and evidence modality exactly.
  If an ISC is compound or malformed, route `contract-gap`; do not repair it.
- `Implementation required: no` means the selected capability already exists
  enough to support the prescribed probe. It does not mean the ISC is closed.
- `uncertain` requires a specific unknown and a capability that resolves it;
  it is not a license to guess.
- A capability may cover several selected leaves only when it has one coherent
  behavior owner and one clear boundary. Otherwise split the assignment.
- A capability can enable a proof-only leaf, but must not claim PASS or mutate
  ISA progress.
- Candidate identity is the exact subject expectation for fresh work: build,
  device/runtime, input/data lineage, account/permissions, and any external
  identity needed by the probe. Redact secrets and personal data.
- If the probe requires a world-state this lane cannot produce with allowed
  tools and existing subjects, route `dependency-blocked`. Do not lock
  "acquire a better subject" as implementation. The factory then selects
  other startable open work.
