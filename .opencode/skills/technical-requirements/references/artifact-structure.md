# Artifact Structure: tech-adr.md

Verbatim tech-adr.md artifact skeleton from technical-requirements Phase 2.

---

## ARTIFACT STRUCTURE: tech-adr.md

```markdown
# Technical Specification: [Project Name]

Generated: [YYYY-MM-DD]
Status: [In Progress | Complete]
Source: product-adr.md.md

---

## Foundational Decision: Technical Approach Selection

**Date:** [YYYY-MM-DD]
**Status:** Accepted

**Context:**
[Summary of product requirements and constraints: indie dev, cost-conscious, validation phase]

**Research Conducted:**
- Product teardown: [summary]
- Open source scan: [summary]
- Framework comparison: [summary]
- Cost projection: [summary]
- Architecture patterns: [summary]
- Boilerplate options: [summary]

**Approaches Considered:**
| #   | Approach | Stack | Est. Cost | Complexity | Time-to-MVP |
| --- | -------- | ----- | --------- | ---------- | ----------- |
| 1   | [Name]   | [...] | $X/mo     | [L/M/H]    | X weeks     |
| 2   | [Name]   | [...] | $X/mo     | [L/M/H]    | X weeks     |
| ... | ...      | ...   | ...       | ...        | ...         |

**Decision:**
[Selected approach and why it was chosen]

**Rejected Approaches:**
| Approach | Why Rejected                                                |
| -------- | ----------------------------------------------------------- |
| [Name]   | [Reason: cost too high, complexity, missing features, etc.] |
| [Name]   | [Reason]                                                    |
| [Name]   | [Reason]                                                    |
| [Name]   | [Reason]                                                    |

**Consequences:**
- Positive: [benefits of selected approach]
- Negative: [tradeoffs accepted]
- Neutral: [implementation notes]

---

## 1. Boundaries (Out of Scope)

**NOT implementing technically:**
- [Item 1] - [Why excluded]
- [Item 2] - [Why excluded]

**Technical debt accepted:**
- [Item] - [Will address in future phase]

**Future technical considerations:**
- [Item for later phases]

---

## 2. Key Components

### Architecture Overview

~~~
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│      API        │────▶│    Database     │
│   (Component)   │     │   (Component)   │     │   (Component)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌─────────────────┐
│   [Component]   │     │ External Service│
└─────────────────┘     └─────────────────┘
~~~

### Component Descriptions
| Component | Responsibility | Technology | Notes         |
| --------- | -------------- | ---------- | ------------- |
| [Name]    | [What it does] | [Stack]    | [Constraints] |

### Layer Boundaries & Responsibilities

| Layer                | Responsibility                              | What Belongs Here                          | What Does NOT Belong                            |
| -------------------- | ------------------------------------------- | ------------------------------------------ | ----------------------------------------------- |
| UI Layer             | Render, user input, local UI state          | Components, event handlers, display logic  | Business rules, API calls, data transformations |
| State Layer          | Client-side data, cache, sync               | Query hooks, stores, optimistic updates    | UI rendering, business validation               |
| Domain Logic         | Business rules, validation, transformations | Services, validators, calculators          | UI concerns, persistence details                |
| Persistence          | Data storage, queries, migrations           | DB operations, schema definitions          | Business logic, UI state                        |
| Integration Adapters | External API communication                  | API clients, response mappers, retry logic | Business rules, UI concerns                     |

### Data Flow (Request Lifecycle)
~~~
[User Action] 
    │
    ▼
[UI Layer] ─── captures input, triggers action
    │
    ▼
[State Layer] ─── optimistic update (if applicable)
    │
    ▼
[Domain Logic] ─── validates, transforms
    │
    ▼
[API/Persistence] ─── executes operation
    │
    ▼
[State Layer] ─── syncs response, invalidates cache
    │
    ▼
[UI Layer] ─── re-renders with new state
~~~

---

## 3. Data Models

### Entity: [EntityName]
~~~typescript
interface EntityName {
  id: string;                    // Primary key, UUID
  field1: string;                // Description
  field2: number;                // Description
  createdAt: Date;               // Auto-generated
  updatedAt: Date;               // Auto-updated
}
~~~

### Relationships
~~~
[Entity A] ──1:N──▶ [Entity B]
[Entity B] ──N:1──▶ [Entity C]
~~~

### Constraints
- [Constraint 1]: [Description]
- [Constraint 2]: [Description]

### Type Contracts Between Layers

| Type Location     | Purpose                         | Derives From |
| ----------------- | ------------------------------- | ------------ |
| `schema.ts` (DB)  | Source of truth for persistence | -            |
| `api/types.ts`    | API request/response shapes     | DB schema    |
| `client/types.ts` | Client-side representations     | API types    |

**Type Flow:**
~~~
[DB Schema] ──generates──▶ [API Types] ──maps to──▶ [Client Types]
~~~

**Rules:**
- DB schema is the source of truth
- API types may omit internal fields (e.g., `passwordHash`)
- Client types may add computed/derived fields
- Shared validation schemas live in `/shared/validators`

### Validation Rules Per Entity

| Entity   | Field   | Validation                             | Layer Enforced |
| -------- | ------- | -------------------------------------- | -------------- |
| [Entity] | [field] | [rule: required, min/max, regex, etc.] | [UI, API, DB]  |

---

## 4. Storage

**Database Choice:** [Database name]
**Rationale:** [Why this database]

### Tables/Collections
| Name    | Purpose   | Indexes   | Notes   |
| ------- | --------- | --------- | ------- |
| [table] | [purpose] | [indexes] | [notes] |

### Migration Strategy
- [How schema changes will be handled]

---

## 5. APIs

### Endpoint: [METHOD] /api/[path]
**Purpose:** [What this endpoint does]
**Auth:** [Required/Optional/None]

**Request:**
~~~typescript
interface RequestBody {
  field1: string;
  field2?: number;
}
~~~

**Response (200):**
~~~typescript
interface ResponseBody {
  data: EntityName[];
  meta?: { total: number };
}
~~~

**Errors:**
| Code | Condition     | Response               |
| ---- | ------------- | ---------------------- |
| 400  | Invalid input | `{ error: "message" }` |
| 404  | Not found     | `{ error: "message" }` |

### Data Flow Diagram (Per Feature)

For each key feature, document the request lifecycle:

~~~
[Feature: Create Item]

[UI] ─── user clicks "Create" ───▶ [State] ─── optimistic insert ───▶ [API]
                                                                         │
                                     [UI] ◀─── invalidate query ◀─── [DB write]

Logging Points:
  • [API Entry]: Log request id, user id, action
  • [Validation]: Log validation failures (no PII)
  • [DB Write]: Log success/failure, duration
  • [Response]: Log status code, duration
~~~

### Request Lifecycle

| Phase      | What Happens                  | Logs To Emit                      |
| ---------- | ----------------------------- | --------------------------------- |
| Entry      | Parse request, extract auth   | `request_id`, `user_id`, `action` |
| Validation | Schema + business rule checks | Validation errors (sanitized)     |
| Execution  | DB/external calls             | Operation type, duration          |
| Response   | Format and return             | Status code, total duration       |

---

## 6. Integrations

### Integration Swappability Check

Before finalizing an integration, ask:
- Is the implementation certain, or might we pivot?
- If uncertain: Does the OUTPUT type exist independent of the fetching logic?
- Swap test: Could a jr dev change the data source by editing ONE file?

### [Service Name]
**Purpose:** [Why we integrate]
**Auth Method:** [API Key/OAuth/etc]
**Rate Limits:** [X requests per Y]
**Documentation:** [Link]

**Key Endpoints Used:**
| Endpoint   | Purpose   | Notes         |
| ---------- | --------- | ------------- |
| [endpoint] | [purpose] | [constraints] |

**Error Handling:**
- [How we handle failures]
- [Retry strategy]

### Side Effects & Domain Events

When an action triggers secondary operations, document the chain:

| Trigger Action       | Side Effects                                  | Failure Handling                       |
| -------------------- | --------------------------------------------- | -------------------------------------- |
| [User upgrades plan] | Update permissions, send email, log analytics | [Each independent; partial success OK] |
| [Item deleted]       | Clean up references, notify subscribers       | [Queue for retry on failure]           |

**Event Flow:**
~~~
[Primary Action] 
    │
    ├──▶ [Side Effect 1] ─── sync/async? ─── failure: [retry/ignore/rollback]
    ├──▶ [Side Effect 2] ─── sync/async? ─── failure: [retry/ignore/rollback]
    └──▶ [Side Effect 3] ─── sync/async? ─── failure: [retry/ignore/rollback]
~~~

### Idempotency Patterns

| Operation            | Idempotency Strategy   | Key Generation             |
| -------------------- | ---------------------- | -------------------------- |
| [Webhook receipt]    | Dedupe by event ID     | `event.id`                 |
| [Payment processing] | Idempotency key header | `user_id:action:timestamp` |
| [Batch sync]         | Upsert pattern         | Entity natural key         |

### Circuit Breaker / Graceful Degradation

| Service        | Fallback Behavior                                         | Circuit Trigger     |
| -------------- | --------------------------------------------------------- | ------------------- |
| [External API] | [Return cached data / Show degraded UI / Queue for retry] | [3 failures in 60s] |

---

## 7. Auth & Security

**Auth Type:** [JWT/Session/OAuth/etc]
**Provider:** [Self-hosted/Auth0/Clerk/etc]

### Flow
~~~
[User] ──login──▶ [Auth Provider] ──token──▶ [App] ──validate──▶ [API]
~~~

### Token Handling
- Storage: [Where tokens stored]
- Refresh: [How tokens refreshed]
- Expiry: [Token lifetime]

### Input Validation Strategy

| Layer | Validation Type                      | Tools/Libraries          |
| ----- | ------------------------------------ | ------------------------ |
| UI    | Format, required fields, UX feedback | [Zod, React Hook Form]   |
| API   | Schema validation, sanitization      | [Zod, express-validator] |
| DB    | Constraints, foreign keys, triggers  | [DB-native constraints]  |

**Validation Flow:**
~~~
[User Input] ──▶ [UI Validation] ──▶ [API Validation] ──▶ [DB Constraints]
                      │                    │                    │
                 Quick feedback      Security gate         Last defense
~~~

### Security Measures

| Concern            | Approach                           | Implementation                    |
| ------------------ | ---------------------------------- | --------------------------------- |
| CORS               | [Restrict to known origins]        | [cors middleware config]          |
| Rate Limiting      | [X requests per user per minute]   | [express-rate-limit / Cloudflare] |
| Input Sanitization | [Escape HTML, validate types]      | [DOMPurify, Zod]                  |
| Sensitive Data     | [Never log tokens, PII, passwords] | [Log sanitizer middleware]        |
| API Keys           | [Server-side only, env vars]       | [.env, secret manager]            |

### What NEVER Gets Logged

- Auth tokens, API keys, secrets
- Passwords (even hashed)
- Full email addresses (OK: `j***@domain.com`)
- Credit card numbers, SSN, PII
- Request/response bodies containing user data

---

## 8. State Management

**Approach:** [Library/Pattern]
**Rationale:** [Why this approach]

### State Structure
~~~typescript
interface AppState {
  [slice]: {
    data: EntityName[];
    loading: boolean;
    error: string | null;
  };
}
~~~

### Sync Strategy
- [How state syncs with server]
- [Caching approach]
- [Invalidation rules]

### Caching Strategy (Detailed)

| Data Type       | Cache Location          | TTL     | Invalidation Trigger      |
| --------------- | ----------------------- | ------- | ------------------------- |
| [User profile]  | [React Query / Zustand] | [5 min] | [On mutation, on focus]   |
| [List data]     | [React Query]           | [1 min] | [On create/update/delete] |
| [Static config] | [localStorage]          | [24h]   | [On app version change]   |

### Derived/Computed Values

| Computed Value | Derived From               | Recompute Trigger   |
| -------------- | -------------------------- | ------------------- |
| [Total count]  | [Individual item statuses] | [Any status change] |
| [Progress %]   | [Completed / Total]        | [Item completion]   |

**Rule:** Compute on read, do NOT store derived values.

### Optimistic Updates

| Action        | Optimistic Behavior          | Rollback On Failure            |
| ------------- | ---------------------------- | ------------------------------ |
| [Create item] | Append to list with temp ID  | Remove from list, show error   |
| [Delete item] | Remove from list immediately | Restore item, show error       |
| [Update item] | Update in place              | Revert to previous, show error |

### Offline Support (if applicable)

| Scenario        | Behavior                                    |
| --------------- | ------------------------------------------- |
| [Offline read]  | [Serve from cache / Show offline indicator] |
| [Offline write] | [Queue locally / Block with message]        |
| [Reconnect]     | [Sync queue / Refresh queries]              |

---

## 9. Async Workflows

### Background Jobs

| Job                  | Trigger                   | Frequency     | Timeout        | Failure Handling       |
| -------------------- | ------------------------- | ------------- | -------------- | ---------------------- |
| [Sync external data] | [Cron / Webhook / Manual] | [Every 5 min] | [30s]          | [Retry 3x, then alert] |
| [Process queue]      | [Queue not empty]         | [Continuous]  | [60s per item] | [Dead letter queue]    |

### Rate Limit Handling

| Service        | Rate Limit          | Strategy                            |
| -------------- | ------------------- | ----------------------------------- |
| [External API] | [100/min]           | [Queue + exponential backoff]       |
| [Own API]      | [1000/min per user] | [429 response + retry-after header] |

**Backoff Pattern:**
~~~
Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 2s
Attempt 4: wait 4s
Attempt 5: fail, queue for manual retry
~~~

### Retry Logic

| Operation Type     | Max Retries | Backoff     | Idempotent   |
| ------------------ | ----------- | ----------- | ------------ |
| [Read operations]  | 3           | Exponential | Yes          |
| [Write operations] | 2           | Linear      | Must be      |
| [Webhooks]         | 5           | Exponential | Yes (dedupe) |

### Agent Loop Pattern (if applicable)

For AI-assisted automation or long-running workflows:

~~~
[Task Queue] 
    │
    ▼
[Agent Loop Start] ─── fresh context per task
    │
    ├──▶ [Load task context]
    ├──▶ [Execute task steps]
    ├──▶ [Checkpoint progress]
    └──▶ [Complete or requeue]
    │
    ▼
[Context Reset] ─── prevents context drift
~~~

**Context Management:**
- Each task starts with clean state
- Progress checkpointed after each step
- Failed tasks requeue with last checkpoint
- Long tasks split into subtasks

---

## 10. Concurrency

### Optimistic Locking

| Entity            | Lock Strategy                     | Conflict Resolution                |
| ----------------- | --------------------------------- | ---------------------------------- |
| [Shared resource] | [Version field / updatedAt check] | [Last write wins / Merge / Reject] |

**Pattern:**
~~~typescript
// Optimistic lock check
if (entity.version !== expectedVersion) {
  throw new ConflictError('Entity was modified by another request');
}
entity.version++;
await save(entity);
~~~

### Race Condition Mitigations

| Scenario            | Risk              | Mitigation                         |
| ------------------- | ----------------- | ---------------------------------- |
| [Double submit]     | Duplicate records | [Disable button + idempotency key] |
| [Concurrent edits]  | Lost updates      | [Optimistic locking + conflict UI] |
| [Counter increment] | Wrong total       | [Atomic DB operation]              |

### Conflict Resolution UI

When conflicts occur, present user with options:
- "Your changes" vs "Their changes"
- Merge option (if applicable)
- Force overwrite (with warning)

---

## 11. Resilience

### Error Handling Strategy

| Layer      | Error Type | Handling             | User Feedback              |
| ---------- | ---------- | -------------------- | -------------------------- |
| UI         | Validation | Inline field errors  | Immediate, specific        |
| UI         | Network    | Toast + retry option | "Connection issue, retry?" |
| API        | Validation | 400 + error details  | Passed to UI               |
| API        | Auth       | 401/403 + redirect   | "Please log in"            |
| API        | Server     | 500 + logged         | "Something went wrong"     |
| Background | Any        | Retry + dead letter  | None (admin alert)         |

### Error Propagation

~~~
[Error Origin]
    │
    ▼
[Catch at boundary] ─── log with context
    │
    ▼
[Transform to user-friendly] ─── strip internal details
    │
    ▼
[Surface to UI] ─── actionable message
~~~

**Rules:**
- Catch at layer boundaries, not everywhere
- Log original error with stack trace
- Transform to user-safe message before surfacing
- Include recovery action when possible ("Retry", "Contact support")

### Graceful Degradation

| Failure             | Degraded Behavior               | User Communication                       |
| ------------------- | ------------------------------- | ---------------------------------------- |
| [External API down] | [Serve cached data, mark stale] | [Banner: "Data may be outdated"]         |
| [Auth service down] | [Allow read-only, block writes] | [Toast: "Login temporarily unavailable"] |
| [Database slow]     | [Extend timeouts, show loading] | [Spinner + "Taking longer than usual"]   |

### Recovery Patterns

| Scenario                | Recovery Action                                 |
| ----------------------- | ----------------------------------------------- |
| Partial failure (batch) | Continue with successful items, report failures |
| Transient error         | Auto-retry with backoff                         |
| Persistent error        | Circuit breaker, alert, manual intervention     |
| Data inconsistency      | Reconciliation job, admin tools                 |

---

## 12. Logging & Observability

**Log Aggregation:** [Console / CloudWatch / Axiom / etc.]
**Error Tracking:** [Sentry / Bugsnag / None]

### Log Levels

| Level | When to Use                          | Example                                 |
| ----- | ------------------------------------ | --------------------------------------- |
| ERROR | Unexpected failures, needs attention | API call failed after retries           |
| WARN  | Recoverable issues, degraded state   | Rate limit approaching, fallback used   |
| INFO  | Key business events, audit trail     | User created, payment processed         |
| DEBUG | Development troubleshooting          | Request/response details, state changes |

### Debug Logging for Implementation

When writing implementation code, emit logs at these points:

| Code Location            | What to Log                 | Level      |
| ------------------------ | --------------------------- | ---------- |
| Function entry (complex) | Input params (sanitized)    | DEBUG      |
| External API call        | Service, endpoint, duration | INFO/DEBUG |
| State mutation           | Before/after (summarized)   | DEBUG      |
| Error caught             | Error type, context, stack  | ERROR      |
| Retry attempt            | Attempt #, delay, reason    | WARN       |
| Background job start/end | Job ID, duration, result    | INFO       |

**Log Format:**
~~~typescript
// Structured logging pattern
logger.info('action_completed', {
  action: 'create_item',
  userId: user.id,
  itemId: item.id,
  durationMs: 145
});
~~~

### Key Events to Track

| Event                   | Purpose                | Data Points                         |
| ----------------------- | ---------------------- | ----------------------------------- |
| [User signup]           | Funnel tracking        | Source, timestamp                   |
| [Core action completed] | Usage metrics          | User, action, duration              |
| [Error occurred]        | Debugging              | Error type, stack, context          |
| [External API call]     | Performance, debugging | Service, endpoint, status, duration |

---

## 13. Infrastructure

**Hosting:** [Vercel/AWS/etc]
**Environments:** [dev, staging, prod]

### Environment Variables
| Variable   | Purpose   | Required |
| ---------- | --------- | -------- |
| [VAR_NAME] | [purpose] | [yes/no] |

### Deployment
- [How deployments happen]
- [CI/CD approach]

### Agent-Native Quality Gates

**PHILOSOPHY:** Quality gates provide FAST, DETERMINISTIC feedback for agent SELF-CORRECTION. "Lint green" is the definition of DONE. Iterate against automated gates until clean, minimizing human review cycles.

**GATE CRITERIA:** Effective gates are:
- FAST: Runs in seconds, not minutes
- DETERMINISTIC: Same input = same output, no flakiness
- ACTIONABLE: Tells you exactly what to fix and where

**STANDARD GATES (ordered cheapest/fastest first):**

| Priority | Gate       | Command     | Purpose                       |
| -------- | ---------- | ----------- | ----------------------------- |
| 1        | Type Check | `[command]` | Structural errors (fastest)   |
| 2        | Lint       | `[command]` | Style + convention violations |
| 3        | Test       | `[command]` | Behavior verification         |
| 4        | Build      | `[command]` | Production build (pre-deploy) |

**SELF-CORRECTION LOOP:**
~~~
[Make change] → [Run gates] ─── PASS ──▶ [Done]
                    │
                  FAIL
                    │
                    ▼
              [Read error] → [Fix violation] → [Run gates again]
~~~

**RULES:**
1. Run gates after every significant change - don't batch
2. Fix before proceeding - never mark complete if failing
3. Read error output carefully - don't guess
4. One fix at a time - tight loop
5. Don't skip gates - even if confident

**WHAT GATES ARE NOT FOR:**
- Slow operations (full builds, E2E tests, deployments)
- Flaky checks (network-dependent validation)
- Subjective quality (design review, UX evaluation)

**ON FAILURE:** If you cannot self-correct after 3 attempts, STOP and report the specific error to the user.

**IMPLEMENTATION PLANNING:** When generating the implementation roadmap, embed this self-correction loop as the completion criteria for each task. A task is not complete until gates pass.

### Performance Considerations

| Area          | Strategy                         | Threshold         |
| ------------- | -------------------------------- | ----------------- |
| Bundle Size   | [Code splitting, tree shaking]   | [< 200KB initial] |
| API Response  | [Pagination, field selection]    | [< 200ms p95]     |
| DB Queries    | [Indexes, query optimization]    | [< 50ms p95]      |
| Images/Assets | [Lazy loading, CDN, compression] | [LCP < 2.5s]      |

### Feature Flags

**Approach:** [Env vars / Config service / Feature flag service]

| Flag                | Purpose               | Default | Environments                 |
| ------------------- | --------------------- | ------- | ---------------------------- |
| [FEATURE_X_ENABLED] | [Gates new feature X] | [false] | [true in dev, false in prod] |

**Implementation:**
~~~typescript
// Feature flag check pattern
if (flags.isEnabled('feature_x')) {
  // New behavior
} else {
  // Existing behavior
}
~~~

---

## 14. Dependencies

### Runtime Dependencies
| Package | Version  | Purpose   | Rationale    |
| ------- | -------- | --------- | ------------ |
| [name]  | [^x.y.z] | [purpose] | [why chosen] |

### Dev Dependencies
| Package | Version  | Purpose   |
| ------- | -------- | --------- |
| [name]  | [^x.y.z] | [purpose] |

### Dependency Tree (Key Relationships)
~~~
[main-lib]
  └── [sub-dependency]
      └── [transitive-dep]
~~~

---

## 15. Testing Strategy

### Test Types Per Layer

| Layer         | Test Type   | Coverage Goal        | Tools                     |
| ------------- | ----------- | -------------------- | ------------------------- |
| UI Components | Unit        | Critical components  | [Vitest, Testing Library] |
| State/Hooks   | Unit        | Business logic hooks | [Vitest]                  |
| API Endpoints | Integration | All endpoints        | [Supertest, Vitest]       |
| Full Flows    | E2E         | Critical user paths  | [Playwright]              |

### What to Test

| Priority | What                                       | Why                      |
| -------- | ------------------------------------------ | ------------------------ |
| HIGH     | Critical user flows (auth, core action)    | Breaking = users blocked |
| HIGH     | Business logic (calculations, validations) | Breaking = wrong data    |
| MEDIUM   | Error handling paths                       | Breaking = bad UX        |
| LOW      | Edge cases, rare scenarios                 | Defer until stable       |

### Mocking Strategy

| Dependency    | Mock Approach                       |
| ------------- | ----------------------------------- |
| External APIs | [MSW handlers / fixture responses]  |
| Database      | [In-memory DB / Test DB with reset] |
| Auth          | [Mock user context / Test tokens]   |
| Time/Date     | [Fake timers / Inject clock]        |

### Test Data

| Approach     | Use Case                                      |
| ------------ | --------------------------------------------- |
| Factories    | Generate valid entities with overrides        |
| Fixtures     | Static known-good data for specific scenarios |
| Seed scripts | Populate test DB with realistic data          |

### Coverage Expectations (by phase)

| Phase         | Coverage Target | Focus                     |
| ------------- | --------------- | ------------------------- |
| Tracer bullet | ~20%            | Critical path only        |
| Build out     | ~50%            | All happy paths           |
| Polish        | ~70%            | + Error paths, edge cases |
~~~
```

---
