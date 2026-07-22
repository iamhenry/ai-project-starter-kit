# Categories

Verbatim category order and thinking framework from technical-requirements Phase 2.

---

## CATEGORIES (Sequential Order)

Work through these categories IN ORDER. Each must reach 90% clarity before proceeding to the next.

| Phase | #   | Category                | Focus                                                                 |
| ----- | --- | ----------------------- | --------------------------------------------------------------------- |
| 1     | 1   | Boundaries              | Define what's OUT before spending time on IN                          |
|       | 2   | Key Components          | Architectural skeleton, layer boundaries, component diagram           |
| ----- | --- | ----------------------- | ------------------------------------------------------------          |
| 2     | 3   | Data Models             | Entities, relationships, types, validation rules, type contracts      |
|       | 4   | Storage                 | Persistence approach, database choice                                 |
|       | 5   | APIs                    | Endpoints, contracts, data flow diagrams, request lifecycle           |
| ----- | --- | ----------------------- | ------------------------------------------------------------          |
| 3     | 6   | Integrations            | External services, side effects, idempotency, circuit breakers        |
|       | 7   | Auth & Security         | Authentication flow, input validation, CORS, rate limits              |
| ----- | --- | ----------------------- | ------------------------------------------------------------          |
| 4     | 8   | State Management        | Client-side state, caching strategy, invalidation, optimistic updates |
|       | 9   | Async Workflows         | Background jobs, rate-limit handling, retries, agent loops            |
|       | 10  | Concurrency             | Optimistic locking, conflict resolution, race conditions              |
| ----- | --- | ----------------------- | ------------------------------------------------------------          |
| 5     | 11  | Resilience              | Error handling, graceful degradation, recovery patterns               |
|       | 12  | Logging & Observability | Log levels, debug guidance, error tracking, key events                |
| ----- | --- | ----------------------- | ------------------------------------------------------------          |
| 6     | 13  | Infrastructure          | Hosting, deployment, performance, feature flags                       |
|       | 14  | Dependencies            | Libraries with versions, rationale for each                           |
|       | 15  | Testing Strategy        | Test types per layer, mocking approach, coverage expectations         |

---

## CATEGORY THINKING FRAMEWORK

For each category, explore relevant dimensions. Not all dimensions apply to every category or project — use judgment.

### Thinking Dimensions

| Dimension  | Clarifies                                                      |
| ---------- | -------------------------------------------------------------- |
| What       | The choice itself (packages, services, architecture, patterns) |
| Why        | Rationale, alternatives considered, what was rejected          |
| How        | Usage pattern, integration approach, entry points              |
| When       | Lifecycle, timing, upgrade/migration path                      |
| Trade-offs | Cost, risk, constraints, complexity                            |
| Boundaries | What's explicitly NOT included, deferred                       |
| Impact     | Downstream effects, dependencies, what breaks if this changes  |

Apply these dimensions to generate context-appropriate questions for each category.

### Category Boundaries

Stay on-topic per category. Don't ask about concerns that belong elsewhere.

| Category                    | Don't Ask About                                                                                    |
| --------------------------- | -------------------------------------------------------------------------------------------------- |
| 1. Boundaries               | Implementation details (see Key Components, Dependencies)                                          |
| 2. Key Components           | Specific technologies (see Dependencies)                                                           |
| 3. Data Models              | Storage mechanism (see Storage)                                                                    |
| 4. Storage                  | Caching strategy (see State Management)                                                            |
| 5. APIs                     | Retry logic, circuit breakers (see Async Workflows, Resilience)                                    |
| 6. Integrations             | Retry logic, circuit breakers (see Async Workflows, Resilience); runtime failures (see Resilience) |
| 7. Auth & Security          | —                                                                                                  |
| 8. State Management         | Server state persistence (see Storage)                                                             |
| 9. Async Workflows          | —                                                                                                  |
| 10. Concurrency             | —                                                                                                  |
| 11. Resilience              | —                                                                                                  |
| 12. Logging & Observability | —                                                                                                  |
| 13. Infrastructure          | Detailed failure handling (see Resilience)                                                         |
| 14. Dependencies            | Runtime failures (see Resilience); API behavior details (see Integrations)                         |
| 15. Testing Strategy        | —                                                                                                  |

---
