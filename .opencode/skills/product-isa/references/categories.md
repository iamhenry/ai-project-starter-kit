# Interview Categories

Work backwards from the Core Job. Ask gaps only; the lists below are coverage prompts, not a script or quota.

## Category Map

| # | Category | Canonical destination | IDs produced |
| --- | --- | --- | --- |
| 1 | Core Job | Problem, Vision, Goal, Constraints | none |
| 2 | Features | Features > Feature Catalog | `FTR-*` |
| 3 | Screens | Features > Screen Contracts | `SCR-*` |
| 4 | User Flows | Features > User Flow Contracts | `FLOW-*` |
| 5 | Actions | Features > Action Contracts | `ACT-*` |
| 6 | Data Display | Features > Data Display Contracts | `DATA-*` |
| 7 | Edge Cases | Features > Edge-State Contracts | `EDGE-*` |
| 8 | Boundaries | Out of Scope and product Constraints | none |

## 1. Core Job

Clarify:

- The current problem and who experiences it.
- The observable end state that means the app did its job.
- The smallest coherent whole-app promise.
- How the user recognizes success and why it matters.
- Product-level trust, platform, privacy, cost, or control constraints already stated by the user.
- The user's exact goal language for `principal_stated_goal`.

Do not ask for architecture, stack, database, or implementation strategy.

## 2. Features

For every required capability, clarify:

- What it lets the user accomplish and why the Core Job requires it.
- Required inputs, outputs, rules, and relationships to other capabilities.
- What is required now versus explicitly excluded.
- Access or permission behavior when relevant.
- External side effects the user expects or must control.
- Whether actions are reversible and what persists.

Avoid speculative convenience features. A feature exists only when removing it would change the selected ideal state.

## 3. Screens

For every user-visible or system-provided surface, clarify:

- Purpose and linked features.
- Required content, controls, labels, navigation, and primary action.
- Entry and exit paths.
- Empty, loading, success, error, denied, and unavailable states where relevant.
- Differences between create, edit, read-only, or permission-blocked modes.
- Existing mock authority and any intentional differences.

Mocks seed known layout and flows; they do not silently override explicit product decisions.

## 4. User Flows

For every core and recovery journey, clarify:

- Trigger, ordered user-visible steps, and terminal state.
- What the user can cancel, reverse, retry, or resume.
- What happens when the app is backgrounded, interrupted, force-quit, or offline where relevant.
- Permission, authentication, payment, or external-service branches where relevant.
- Partial-success and return-later behavior.
- What must remain unchanged on abandon or failure.

## 5. Actions

For each meaningful action, clarify:

- Surface, trigger, prerequisites, and enabled or disabled rules.
- Immediate visible result and durable result.
- Validation and user-facing correction.
- Duplicate taps, repeated execution, stale state, and conflicting actions where relevant.
- Confirmation, undo, destructive impact, and external side effects.
- What happens when the action fails before or after a partial side effect.

## 6. Data Display

For every decision-relevant data element, clarify:

- Canonical source and meaning.
- Surface, label, format, ordering, grouping, truncation, and accessibility meaning.
- Empty, hidden, unavailable, stale, and error representation.
- Refresh or freshness expectations.
- Persistence across navigation, relaunch, devices, or sessions where relevant.
- Privacy and visibility rules.

Do not defer user-visible ordering or freshness to technical planning.

## 7. Edge Cases

Cover relevant failure families without inventing irrelevant states:

- Invalid, missing, malformed, or unsupported input.
- Empty, loading, slow, unavailable, and timed-out dependencies.
- Permission denied, revoked, or dismissed.
- Offline, interrupted, backgrounded, and force-quit work.
- Partial success across multiple side effects.
- Duplicate submissions, retries, stale responses, and conflicts.
- Persistence failure, recovery, rollback, and data loss expectations.
- Destructive actions, trust failures, privacy exposure, and misleading success.

For each edge state, capture trigger, impact, required behavior, user message or signal, recovery, and facts that must remain unchanged.

## 8. Boundaries

Clarify:

- Explicit non-goals for the current whole-app ideal state.
- Features, platforms, users, integrations, and guarantees that are not included.
- Actions the app must never take silently.
- Future considerations that are not current commitments.
- Product constraints that truly bind behavior or user trust.

Do not turn repository implementation choices into product boundaries. If the user explicitly declares a technical mandate, record it as a Constraint in their words rather than expanding it into a design.
