# Routing And Evidence

Route each selected leaf independently. A slice can contain mixed routes, but
an assignment cannot pretend a blocked route is implementation work.

## Routes

| Route | Use when | Assignment/handoff |
| --- | --- | --- |
| `automated` | Repository tools and a real runtime can exercise the exact ISA probe and threshold. | Fresh implementation or evidence agent may proceed; name the real subject and retained evidence. |
| `human-external` | The probe requires a real authority, permission, device, account, physical condition, or external system unavailable to the environment. | Do not ask for generic help. State the exact authority/access and the minimum evidence the human must return. Interrupt only for this true external need. |
| `contract-gap` | The ISC/probe/threshold is missing, contradictory, non-atomic, or cannot identify an honest evidence boundary. | Stop that leaf. Ask for ISA owner resolution only; never invent or weaken contract text. |
| `dependency-blocked` | A repository or runtime prerequisite is missing, broken, or owned by another capability, but is not an ISA contradiction or true external authority. | Return the prerequisite and owner/dependency edge. Do not interrupt the human; another pipeline slice must resolve it. |

## Evidence Requirements

For every automated assignment, require:

- The source identity needed for Review, plus the proof class, subject/data
  lineage, permissions, and attribution needed to extend it for Accept. Do not
  require a build/runtime identity before that environment is selected.
- The real user or consumer path, including controlled conditions only when
  the ISA explicitly permits them.
- The direct observation channel named by the claim.
- The exact binary threshold copied from the ISA.
- Retained replayable evidence and a clear PASS/FAIL/BLOCKED result.

For human-external routing, require the same fields plus the authority or
condition only the human can supply. Do not request secrets, personal data, or
unbounded screenshots. A static screenshot cannot prove motion, persistence,
audio, absence, or lifecycle unless the ISA's probe explicitly makes it
sufficient.

## Blocker Rules

- Wrong runtime subject, synthetic data, missing source lineage, or a missing
  threshold is a hard blocker, not a reason to substitute a convenient case.
- A code/test dependency is `dependency-blocked` even if the leaf itself is
  well specified.
- A contradiction inside the authoritative ISA is the only ordinary reason to
  interrupt the user or ISA owner. Quote both conflicting passages and their
  locations.
- Lack of current implementation is not a blocker by itself; route
  `automated` with `implementation_required: yes` when the real path is
  available.
- Existing failed or blocked evidence remains context. Never convert it to
  PASS and never hide it from the packet when it affects selection.
