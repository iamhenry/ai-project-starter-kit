# Slice Selection Heuristics

## Thin Vertical Slice

Choose one journey from user trigger to observable end state. Prefer a slice
that exercises the same real path named by its probes: UI, persistence, audio,
network, OS boundary, or another consumer boundary. A slice is tightly coupled
when its leaves share the journey, setup subject, behavior owner, and evidence
run, and a leaf cannot be completed honestly without the others. Shared nouns
or nearby screens are not enough.

For greenfield products, choose the smallest journey that proves the first
real user value and include the minimum capability chain to reach its end
state. For existing products, prefer the smallest change through proven
behavior owners and data paths. Preserve behavior that already works; do not
rebuild it merely to create an assignment.

## Candidate Ranking

Consider open leaves first. Rank a candidate slice by:

1. Direct contribution to the ISA goal and one complete user journey.
2. Coherent shared setup and a single honest evidence run.
3. Fewest unresolved dependencies and smallest implementation surface.
4. Ability to produce a binary result at the ISA's exact threshold.
5. Value of the resulting capability to the next slice.

Use judgment, not a score or quota. Select 1-5 leaves. One leaf is correct
when it is independently useful; more than one is justified only when the
coupling makes separate work wasteful or impossible.

## Anti-Easy-Leaf-Farming

Do not fill the slice with cheap leaves just because they are open, already
nearly proven, or easy to assign. Reject a candidate when it has no meaningful
connection to the selected journey, can be closed by a weaker substitute than
the ISA requires, or hides a harder leaf behind unrelated progress. Prefer a
smaller slice with one real unresolved boundary over a broad list of trivial
leaves. A proof-only leaf is valid when its exact evidence is the real next
capability, not as padding.

## Existing Evidence

Use code to locate behavior owners and likely change points, Git to distinguish
current committed behavior from uncommitted or historical attempts, and
JOURNAL entries to preserve failed probes, blockers, and known recovery
constraints. Evidence can explain selection and dependency inference; it does
not close an ISC. If sources disagree, identify whether the disagreement is
historical evidence or an ISA contradiction. Only the latter interrupts.

## Dependency Shape

Trace both prerequisites and dependents:

- Prerequisite: capability, data, runtime subject, tool, or authority needed
  before the leaf can be exercised.
- Dependent: behavior or leaf that would be affected by changing the owner.
- Evidence dependency: exact subject, environment, threshold, recording, or
  external response needed by the probe.

Keep dependencies in the packet even when they are outside the slice. Never
quietly absorb an unrelated prerequisite into a capability assignment.
