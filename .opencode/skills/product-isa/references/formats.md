# Product ISA Formats

## Session Tracking

Show a compact status before each question batch:

```text
PRODUCT ISA | Category [N]/8: [Name] | [resolved]/[total] gaps resolved
Known: [short list]
Open: [short list]
Artifact: _ai/docs/ISA.md
```

## Questions

Use OpenCode's `question` tool for choices when available. If it is unavailable or declined, show the same numbered options in chat and ask for a number or freeform answer; never block the interview on tooling.

```markdown
### [Plain-language decision]

**User impact:** [Why this changes the experience or trust]

1. **[Outcome title]** (Recommended)
   Why: [Fit with the Core Job and ETHOS]
   Product behavior: [What the user experiences]
   Tradeoff: [Main downside]

2. **[Outcome title]**
   Why: ...
   Product behavior: ...
   Tradeoff: ...

Recommendation: [Short evidence-based recommendation]
```

Rules:

- Use 2-4 options when a real choice exists; freeform is always allowed.
- Recommend exactly one option only when evidence supports it.
- Do not include implementation mechanisms, architecture, or time estimates.
- If rationale is not stated, record `Not stated`; never invent it.

## Stable IDs

| Kind | Format | Example |
| --- | --- | --- |
| Feature | `FTR-NNN` | `FTR-001` |
| Screen | `SCR-NNN` | `SCR-002` |
| Flow | `FLOW-NNN` | `FLOW-003` |
| Action | `ACT-NNN` | `ACT-004` |
| Data display | `DATA-NNN` | `DATA-005` |
| Edge state | `EDGE-NNN` | `EDGE-006` |
| Decision | `DEC-NNN` | `DEC-007` |
| Criterion | `ISC-NNN` | `ISC-008` |

IDs never renumber. A split keeps the parent (`ISC-008.1`, `ISC-008.2`). A removed criterion remains as `[DROPPED - see DEC-NNN]`. Superseded contracts remain present and point to their replacement.

`Satisfies` is a semantic proof relationship, not a topic tag. Only list an ISC when that ISC's decisive probe verifies the behavior being claimed by the contract. Add another ISC for a distinct behavior that the existing probe cannot prove.

## Source Contracts

Use prose fields rather than compressed summary tables when detail would be lost.

### Feature

```markdown
#### FTR-001: [Name]
Status: Active
Purpose: [User outcome and Core Job necessity]
Required behavior:
- [Observable rule]
Inputs and outputs: [Product-level only]
Related surfaces: SCR-001
Related flows: FLOW-001
Satisfies: [Backfill ISC IDs after synthesis]
```

### Screen

```markdown
#### SCR-001: [Name or state]
Status: Active
Purpose: [Why it exists]
Entry and exit: [User-visible navigation]
Required elements:
- [Element, label, information, or control]
States: [Empty/loading/success/error/denied as applicable]
Serves: FTR-001
Satisfies: [Backfill ISC IDs]
```

### User Flow

```markdown
#### FLOW-001: [Name]
Status: Active
Trigger: [What starts it]
Path: [Surface -> action -> visible state -> end state]
Branches and recovery: [Cancel/error/permission/offline as applicable]
End state: [Observable completion]
Uses: FTR-001, SCR-001, ACT-001
Satisfies: [Backfill ISC IDs]
```

### Action

```markdown
#### ACT-001: [Name]
Status: Active
Surface and trigger: [Where and how]
Prerequisites: [Product rules]
Result: [Immediate and durable outcomes]
Validation: [Enabled state and correction]
Failure and repetition: [Retry/duplicate/partial behavior]
Side effects: [External or destructive effects]
Satisfies: [Backfill ISC IDs]
```

### Data Display

```markdown
#### DATA-001: [Name]
Status: Active
Surface: SCR-001
Source and meaning: [Canonical product fact]
Presentation: [Label/format/order/grouping]
Freshness and persistence: [When it changes and survives]
Privacy and unavailable states: [Visibility/empty/error behavior]
Satisfies: [Backfill ISC IDs]
```

### Edge State

```markdown
#### EDGE-001: [Name]
Status: Active
Trigger: [Failure or unusual state]
Impact: [What is at risk]
Required behavior: [What happens]
User signal: [Message or visible state]
Recovery: [Retry/undo/resume/escalation]
Must remain unchanged: [Protected state or side effect]
Satisfies: [Backfill ISC IDs]
```

## Decision Ledger

Capture material forks only: behavior, scope, trust, privacy, control, failure or recovery policy, recommendation overrides, and revisions. Do not target a quota; roughly 8-15 decisions is common for a whole app but not required.

```markdown
### DEC-007: [Decision title]
Date: YYYY-MM-DD
Category: [One of the eight categories]
Status: Active | Superseded
Chosen: [Exact option title or freeform choice]
User words:
> [One to three exact sentences, redacted when necessary]
Rationale: [Exact stated rationale, or `Not stated`]
Rejected alternatives:
- [Option title] - [Key tradeoff]
Locks:
- Source contracts: FTR-001, FLOW-002
- Criteria: ISC-003, ISC-004
Supersedes: [DEC-NNN, only when applicable]
```

Only Active decisions lock current behavior. Preserve Superseded entries. Rejected alternatives are not dead ends unless attempted and refuted.

## Criteria

```markdown
- [ ] ISC-001: [One observable end-state claim]
- [ ] ISC-002: Anti: [One prohibited outcome]
```

A leaf ISC:

- Describes state, not implementation work.
- Contains one independently falsifiable concern.
- Avoids compound `and`, `all`, `every`, or `complete` unless enumerated by child ISCs.
- Is hard to vary because a named probe catches weakening.
- Never closes from agent assertion or document review alone.

## Test Strategy

```markdown
| ISC | Anchors to | Source contracts | Probe type | Check | Pass threshold | Tool |
| --- | --- | --- | --- | --- | --- | --- |
| ISC-001 | literal | FLOW-001, SCR-002 | behavioral | Complete the flow through the user surface | End state appears and persisted result is visible | Real app UI automation |
```

`Anchors to` is `literal` or `derived: [named product sub-claim]`. One row closes one leaf ISC. The result must be binary even when the probe is manual or evaluation-based.

## Fog, Learning, And Verification

```markdown
## Not yet specified

- Fog: [Precisely stated in-scope question] - resolves when [needed evidence or decision]
```

```markdown
## Learning

### YYYY-MM-DD: [Title]
Conjectured: [What was believed]
Refuted by: [Actual evidence]
Learned: [Durable correction]
Criterion now: [ISC added, split, tightened, or dropped]
```

```markdown
## Verification

- ISC-001: [Test name, command reference, screenshot path, CI run, or commit]
```

Omit each section when empty. Verification stores provenance, not copied logs or evidence paragraphs.
