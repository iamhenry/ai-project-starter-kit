# Product ISA Artifact Template

Canonical output: `_ai/docs/ISA.md`.

The template shows final order. Generated artifacts omit empty conditional sections. During the interview, insert newly populated sections into this order rather than creating placeholders.

```markdown
---
artifact: product-isa
format: lifeos-inspired
title: "[Whole app name]"
status: drafting
clarification_progress: 0/8
principal_stated_goal: "[Exact user statement]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
# Add progress: 0/N only after Criteria synthesis.
---

# Product ISA: [Whole app name]

## Problem

[What is broken or missing now and why it matters.]

## Vision

[One to five sentences describing the intended user experience and end state.]

## Out of Scope

[Explicit anti-vision and current non-goals.]

## Principles

[Optional product-relevant truths. Do not copy ETHOS wholesale.]

## Constraints

[Immovable product, trust, platform, privacy, or user-stated mandates.]

## Goal

[One to three hard-to-vary sentences defining observable done.]

## Criteria

- [ ] ISC-001: [Atomic observable claim]
- [ ] ISC-002: Anti: [Atomic prohibited outcome]

## Not yet specified

[Conditional drafting fog. Must contain no material current-scope behavior at ready.]

## Test Strategy

| ISC | Anchors to | Source contracts | Probe type | Check | Pass threshold | Tool |
| --- | --- | --- | --- | --- | --- | --- |
| ISC-001 | literal | FTR-001, FLOW-001 | behavioral | [Consumer-boundary probe] | [Binary threshold] | [Tool] |

## Features

This section is the detailed product contract for this `product-isa` dialect. It is not LifeOS's implementation work-breakdown table.

### Feature Catalog

#### FTR-001: [Feature]
[Contract fields from formats.md]

### Screen Contracts

#### SCR-001: [Screen]
[Contract fields from formats.md]

### User Flow Contracts

#### FLOW-001: [Flow]
[Contract fields from formats.md]

### Action Contracts

#### ACT-001: [Action]
[Contract fields from formats.md]

### Data Display Contracts

#### DATA-001: [Data element]
[Contract fields from formats.md]

### Edge-State Contracts

#### EDGE-001: [Edge state]
[Contract fields from formats.md]

## Decisions

### DEC-001: [Decision]
[Decision Ledger fields from formats.md]

## Learning

[Conditional, only after actual refutation changes understanding.]

## Verification

[Conditional, one provenance line per evidence-closed ISC.]
```

## Frontmatter Lifecycle

| Field | Rule |
| --- | --- |
| `artifact` | Always `product-isa` |
| `format` | Always `lifeos-inspired` |
| `status` | Normal climb is `drafting` -> `ready` -> `building` -> `verified`; accepted revisions return to `drafting` until invalidation and readiness gates complete |
| `clarification_progress` | Completed interview categories out of eight |
| `principal_stated_goal` | Exact user statement; change only on explicit revision recorded in Decisions |
| `created` | Set once |
| `updated` | Update on every artifact edit |
| `progress` | Closed leaf ISCs over total; absent before synthesis, `0/N` at ready, `N/N` at verified |

`ready` means the behavior contract can be implemented. It does not mean the app works. `verified` requires every in-scope leaf ISC to close on evidence.
