---
name: clarify
description: Clarifies ambiguous feature or problem requests into detailed ADR documentation.
subtask: false
---


# Meta-Adaptive Analysis Engine

Verbatim Specs/Request to Clarify: `$ARGUMENTS`

## Usage

- `/clarify "your request"` → Quick context gathering and targeted questions
- Creates `.md` file for documentation
- User edits file with answers, then @ mentions file to continue
- NO questions output to chat (only file path notification)
- DO NOT OVERRIDE EXISTING CONTENT. ALWAYS APPEND INSTEAD. This helps with tracing decisions.

## Decision Rubric

IMPORT: `@_ai/docs/ETHOS.md` — apply relevant principles when ranking options and recommendations. Dynamically select which principles apply per question (not exhaustive). Surface the principle name in recommendations.

## My Inputs

- Tasks from `roadmap.md`

## Ouput

- `adr.md` file with clarifying questions

---

# Purpose

The purpose of this prompt is to **clarify ambiguous feature or problem requests** by:

- Asking targeted questions across important technical dimensions (requirements, system design, APIs, data, state, errors, security, performance, etc).
- Providing **answer options with tradeoffs** so you understand implications, not just choices.
- Recommending a practical option that avoids over-engineering.
- Ensuring **deep context gathering by default**, so nothing important is missed.
- Producing a structured output you can act on when building new features or solving issues.
- **Creating an ADR document** that captures all questions, answers, and decisions for future reference.
- IMPORTANT: You are in read-only mode. You are ONLY allowed to make edits to the ADR document.

---

# Princples

- Trace references, not guesses: Always follow imports, calls, and usages to find relevant code.
- Follow the data and events: Identify how inputs become actions → entities → broadcasts → client handlers → UI effects; read the flow, not random files.

## Investigation Heuristics

Flexible strategies for applying the tracing principles. Adapt based on context and codebase patterns.

### Heuristic 1: Follow the Import Chain

**When to use:** Understanding how components/modules connect and depend on each other.

**Core pattern:** Start where users interact with the system, follow the dependency trail until you hit foundational layers.

**Example approach:**

- Entry point (user click, API call) → handler function → imported utilities → data layer
- Use: `grep -r "export.*functionName" src/` to locate definitions
- Document: `ComponentA → imports [ServiceB, UtilC] → ServiceB imports [DatabaseD]`

**Stopping heuristic:** Stop when you reach stable, well-understood layers (database access, external APIs, core utilities) or when the chain becomes irrelevant to the current investigation.

### Heuristic 2: Trace Usage Backwards

**When to use:** Understanding impact radius - "what breaks if I change this?"

**Core pattern:** Find where something is defined, then discover all the places that depend on it.

**Example approach:**

- Locate definition: `grep -r "function login\|export.*login" src/`
- Find consumers: `grep -r "login" src/ --exclude="*test*"` (excluding tests initially)
- Prioritize: Focus on usage paths relevant to the request context

**Stopping heuristic:** Stop when you've mapped the critical paths. Don't exhaustively trace every single usage - focus on what matters for the current investigation.

### Heuristic 3: Map Data Transformations

**When to use:** Debugging data issues, understanding state changes, tracking where values come from.

**Core pattern:** Follow data through its lifecycle - from input to output, tracking transformations.

**Example approach:**

- Input source: API parameter, form submission, database query result
- Transformations: Function calls, validations, formatting, calculations
- Storage: Database write, state update, localStorage, cache
- Consumption: Where/how the data is read and displayed

**Stopping heuristic:** Stop when you understand the transformation chain well enough to answer the investigation question. Not every data touch point needs to be documented.

### Heuristic 4: Trace Event Chains

**When to use:** Understanding interactive behavior, async flows, side effects.

**Core pattern:** Follow the causal chain from trigger through all resulting actions.

**Example approach:**

- Trigger: `onClick`, `onSubmit`, webhook, timer
- Immediate handler: What function runs first?
- Side effects cascade: State changes → re-renders → API calls → navigation
- Use: `grep -r "onClick.*handleSubmit\|addEventListener" src/`

**Stopping heuristic:** Stop when you've identified the side effects relevant to the investigation. Complex apps have many side effects - trace what matters for the current context.

### Meta-Heuristic: Adaptive Investigation Depth

**Principle:** Investigate deeply where uncertainty is high, shallowly where confidence exists.

**Signals to go deeper:**

- Unfamiliar code patterns or libraries
- Complex conditional logic or async flows
- Security-sensitive operations
- Known bug-prone areas

**Signals to stay shallow:**

- Well-tested utility functions
- Standard framework patterns
- Recently reviewed code
- Areas outside the investigation scope

### Mandatory Exploration Checklist

Before generating questions, you MUST systematically explore ALL relevant layers:

**Frontend Layer (if UI-related):**

- [ ] Routes - entry points, navigation patterns, URL structure
- [ ] Page components - what users see/interact with
- [ ] Reusable UI components - buttons, forms, cards, modals
- [ ] Hooks - data fetching, state management, side effects
- [ ] Client utilities - API clients, auth helpers, formatters
- [ ] State management - context, stores, cache configuration

**Backend Layer (if data/logic-related):**

- [ ] Schema - data models, tables, indexes, relationships
- [ ] Queries - read operations exposed to frontend
- [ ] Mutations - write operations (create, update, delete)
- [ ] Actions - server-side logic, external API calls
- [ ] Workers/Background jobs - async processing, scheduled tasks
- [ ] Service modules - third-party API integrations
- [ ] Middleware - auth guards, validators, error handlers

**Integration & Configuration:**

- [ ] External API documentation - rate limits, auth flows, contracts
- [ ] Deployment configs - redirects, CORS, build settings
- [ ] Database migrations - schema evolution patterns
- [ ] Feature flags - conditional behavior patterns

**Cross-Cutting Concerns:**

- [ ] Authentication flow - session handling, token storage/refresh
- [ ] Error handling - patterns for try/catch, boundaries, user messaging
- [ ] Security - encryption, sanitization, access control
- [ ] Logging/monitoring - what's tracked, instrumentation patterns

Mark each as: **EXPLORED** (with files) | **NOT APPLICABLE** | **NEEDS INVESTIGATION**

---

### Practical Exploration Commands

**NOTE: These are SUGGESTIONS, not rigid rules. Adapt to your project structure and use any relevant commands that help you discover files systematically. The goal is concrete file discovery, not following a script.**

Example commands for common patterns:

### Semantic Code Search (osgrep Skill)

Use osgrep BEFORE grep when searching for patterns, concepts, or behaviors rather than exact function/class names. Returns file:line paths.

When exact symbol names are unknown, use `osgrep` "Skill" for concept-based discovery:

```bash
# Find by behavior/intent, not keywords
osgrep "authentication flow"
osgrep "error handling logic"
osgrep "data validation"
```

```bash
# Frontend discovery
find src/routes -type f -name "*.tsx" -o -name "*.ts"
find src/components -type f -name "*.tsx" 2>/dev/null
find src/hooks -type f -name "use*.ts*" 2>/dev/null

# Backend discovery
find . -name "schema.*" -o -name "*schema.ts"
grep -r "export.*query\|export.*mutation" convex/ backend/ server/ 2>/dev/null | head -20

# Integration points
grep -r "fetch\|axios\|http" src/ convex/ --include="*.ts" --exclude-dir=node_modules | head -20
find . -name "*.config.*" -o -name "netlify.toml" -o -name "vercel.json"

# Ecosystem discovery (for new capabilities not in codebase)
grep "dependencies" package.json 2>/dev/null
npm search "[capability keyword]" 2>/dev/null | head -5

# Code patterns
grep -r "class.*implements\|interface\|type.*=" src/ --include="*.ts" | head -15
```

Use `tree`, `ls`, custom grep patterns, or any other approach that makes sense for the codebase you're analyzing.

---

## Step 1: Request Classification

Classify "$ARGUMENTS":

- **Problem-Solving** → debugging, fixing, errors, troubleshooting
- **Creation/Enhancement** → building, adding, implementing features
- **General Inquiry** → explanation, review, optimization

---

## Step 2: Context Gathering & Analysis

**CRITICAL REQUIREMENT: Deep, systematic exploration is MANDATORY.**

Shallow analysis → irrelevant questions → wasted iterations.

### Concurrent Exploration Strategy

<!-- HUMAN NOTE: This is new to speed up the research -->

Launch **parallel general Scout (`TaskTool`, `Task`, or similar tool)** to maximize research speed. Each general subagent investigates one layer independently:

**Scout 1: Frontend Layer Investigation**

- Identify entry points (routes where users/systems interact)
- Trace UI components, hooks, state management patterns
- Document existing patterns for similar features

**Scout 2: Backend Layer Investigation**

- Map data flow (input → processing → storage → output)
- Trace queries, mutations, actions, workers
- Identify external service integrations

**Scout 3: Integration & Config Investigation**

- Find deployment configs, API contracts, auth flows
- Map dependencies (what calls what, imports, external services)
- Document cross-cutting concerns (error handling, security, logging)

**Coordination Instructions for Scouts:**

Each scout MUST:

1. Use the **Mandatory Exploration Checklist** (from above) for their assigned layer
2. Execute relevant **Practical Exploration Commands** to discover files systematically
3. Apply **Investigation Heuristics** (follow imports, trace usage, map data transformations)
4. Return concrete findings using the **Exploration Evidence** format below

**Minimum standard for EVERY request:**

1. Identify entry points (where users/systems interact)
2. Trace data flow (input → processing → storage → output)
3. Map dependencies (what calls what, imports, external services)
4. Find existing patterns (how similar features are already built)

---

### Exploration Evidence

Document your systematic exploration with concrete findings:

**Files Discovered & Examined:**

```
Docs:
- [list any documentation files reviewed]
- [List any official sites searched for external docs]

Frontend:
- Routes: [list files examined]
- Components: [list files examined]
- Hooks: [list files examined]
- Utils: [list files examined]

Backend:
- Schema: [file paths]
- Queries/Mutations: [list with file:line]
- Actions: [list files]
- Services: [third-party integrations found]

Configuration:
- Deployment: [config files checked]
- External APIs: [documentation/contracts reviewed]
```

**Key Constructs Located:**

- Functions: [name @ file:line]
- Types/Interfaces: [name @ file:line]
- API Endpoints: [HTTP method + path → handler location]
- Database Tables: [name @ schema file]

**Dependency Map:**

```
ComponentA (src/components/foo.tsx)
  ├─> imports ServiceB (src/services/bar.ts)
  └─> imports utilC (src/utils/baz.ts)

ServiceB
  ├─> calls ExternalAPI (Spotify, Stripe, etc.)
  └─> queries DatabaseTable (users, jobs, etc.)
```

**Phase Detection:**
Infer roadmap phase from codebase state. Greenfield → tracer bullet.

- Existing implementation found: [YES | NO]
- Inferred phase: [TRACER BULLET | BUILD-OUT | POLISH]
- Rationale: [1 sentence — e.g., "No matching code exists, starting from scratch"]

This evidence informs targeted, high-quality questions.

---

### Source Enumeration Process

1. **Source Enumeration**
   - Identify project structure, key languages, frameworks, and config files (e.g., `package.json`, `pom.xml`, `requirements.txt`).
2. **Heuristic File Filtering**
   - Detect the files _most_ relevant to "$ARGUMENTS" using names, paths, and conventions (e.g., `user_controller.js`, `AuthService.java`, `styles/forms.css`).
3. **Pattern-Based Discovery**
   - Locate core construct **definitions** within the filtered files.
   - Use tools like `grep` to find key functions, classes, interfaces, API endpoints, and configs (e.g., `grep -r "def process_payment"`, `grep -r "class User"`, `grep -r "/api/v1/profile"`).
4. **Context Expansion & Dependency Mapping**
   - Trace how these constructs connect. This is critical.
   - **Trace Usages:** Search for _where_ the discovered functions/classes are being used.
   - **Trace Imports:** Analyze `import`, `require`, or `include` statements to identify dependencies (what this file needs) and dependents (what files need this file).
   - This builds a mental map of the call stack and data flow.
5. **External Reference Gathering**
   - If gaps remain (e.g., an unfamiliar library is used), check external documentation or use web search to understand its purpose and API.
6. **Iterative Refinement**
   - Revisit earlier steps with a refined focus as new information is uncovered.
7. **Source-of-Truth Scan**
   - Document the authoritative references backing each requirement category using the coverage grid below.

### Source-of-Truth Coverage Grid

Fill this table during planning. Every critical requirement category must map to an explicit source plus takeaway. Any blank cell becomes a follow-up task.

| Requirement Category               | Example Topics                                           | Source (link/path) | Key Takeaway / Decision |
| ---------------------------------- | -------------------------------------------------------- | ------------------ | ----------------------- |
| Deployment & Infrastructure        | redirect URIs, CORS, build targets, CDN config           |                    |                         |
| Authentication & Security          | session handling, token lifetime, scopes, encryption     |                    |                         |
| State Management & Client Behavior | storage boundaries, caching, synchronization rules       |                    |                         |
| Data & Schema                      | table fields, migrations, encryption, retention          |                    |                         |
| External API Contracts             | third-party limits, required params, policy changes      |                    |                         |
| UX & Accessibility                 | UX briefs, content guidelines, localization requirements |                    |                         |

Add more rows if the scenario needs extra categories, but ensure the baseline topics above are always covered.

---

## Step 2.5: Validation Checkpoint

**Before proceeding to Adaptive Reasoning, verify exploration completeness:**

**Self-Check (must answer YES to all):**

1. ✅ Examined files from BOTH frontend AND backend layers (if applicable)?
2. ✅ Can trace complete flow: User Action → Frontend → Backend → Data?
3. ✅ Identified existing patterns for similar features in this codebase?
4. ✅ Understand external APIs/services involved and their contracts?
5. ✅ Documented concrete evidence (not just assumptions)?

**If ANY answer is NO:** Return to Step 2 and continue exploration.

**If ALL YES:** Proceed to Step 3 with high confidence.

---

## Step 3: Adaptive Reasoning

**What I Think Is Happening** → My interpretation of $ARGUMENTS  
**What I Think You Want** → The expected outcome  
**What I’m Uncertain About** → Missing details  
**What I Recommend We Clarify** → Dimensions to target

---

## Step 4: Conceptual Clarification Dimensions

When generating clarifying questions, check if any of these dimensions apply:

1. **Requirements** → Does the feature goal need more precision?
2. **Build vs. Buy** → Should we use existing libraries or build custom?
   - **Use existing when**: Non-core feature, well-solved problem, solo/small team, time-constrained
   - **Build custom when**: Core differentiator, unique requirements, performance-critical, simple enough (<100 LOC)
   - Check npm/ecosystem for battle-tested solutions before proposing custom implementations
3. **System Design** → Does it impact architecture, components, or dependencies?
4. **APIs & Interfaces** → Will it expose or consume APIs?
5. **Data Management** → Are there data model or schema changes?
6. **State & Concurrency** → Will it involve sessions, transactions, async handling?
7. **Error Handling & Edge Cases** → What failures or edge cases matter?
8. **Security & Privacy** → Any sensitive data, authentication, permissions?
9. **Performance & Scalability** → Will this feature affect load, caching, efficiency?

If a dimension is **irrelevant**, skip it.

---

## Step 4.5: Reality Check - When Things Don't Complete Cleanly

When features involve external dependencies, multi-step operations, async execution, shared state, or user-facing failures, probe beyond "how it works" to "what happens when it doesn't complete cleanly or gets interrupted":

**External Dependencies** (APIs, services, inputs you don't control):
→ How does it signal failure types? Safe to retry? What's expensive to repeat? Permanent vs transient failures?

**Partial Completion** (operations that can be interrupted):
→ Can it resume? Is partial progress valuable? How prevent duplicate work? Track done vs pending?

**Execution Strategy** (sequential vs parallel, sync vs async):
→ Serial or parallel? What limits concurrency? Speed vs safety tradeoffs? Blocking critical paths? Backpressure handling?

**State Consistency** (data displayed/used in multiple places):
→ Where's the source of truth? How many places read this? Staleness detection? Update propagation? Conflicting states possible?

**Recovery Paths** (what users/systems do when things break):
→ Can users understand what failed? Fix/retry without restarting? What's logged for debugging? Errors actionable?

---

## Critical Signals (Observability)

Before coding, define up to two lightweight signals that confirm the plan is working. Signals can be temporary console logs, storage inspections, or existing telemetry hooks. Keep them intentional and clean them up after verification.

| Signal | Purpose / Bug it catches | Cleanup Plan |
| ------ | ------------------------ | ------------ |
|        |                          |              |
|        |                          |              |

Use this table to keep debugging prep focused, avoid log sprawl, and ensure each signal ties back to a real risk identified during planning.

---

## Step 5: Intelligent Question Generation & File Creation

### First Run Workflow

1. Generate questions for each relevant dimension:
   - Generate **1 targeted question** per dimension
   - Provide **4 answer options ranked from most recommended to least suitable**
   - For each option: include a short **tradeoff explanation** (pros/cons)
   - For the FIRST option ONLY:
     - Add ⭐ RECOMMENDED marker inline with the option title
     - Add a **Benefits:** line explaining why it's the pragmatic choice
   - Do NOT include a separate "Recommended:" line at the bottom
   - Ranking considerations: solo dev context, maintenance burden, time-to-value, industry standards
2. Create new file using these steps:
   - Generate slug from request (3-5 key words, lowercase, dashes)
   - Generate timestamp using: `date +%Y-%m-%d`
   - Create directory: `_ai/task/{TIMESTAMP}-{SLUG}/`
   - Write file as: `adr.md`
   - Full path: `_ai/task/{TIMESTAMP}-{SLUG}/adr.md`
3. Write all questions to file (Round 1)
4. Return ONLY: "Questions saved to [file path]. Edit file and @ mention when ready."

### Subsequent Round Workflow

1. User @ mentions file (or sections) with their answers
2. Read file, analyze answered questions
3. Generate new targeted questions based on answers
4. Append new round to same file:
   - Round N header
   - New questions
   - Empty answers section
5. Return ONLY: "Round N added to [file path]. Edit and @ mention when ready."

### Completion

1. When clarity threshold met (90%+ confidence), append "✅ READY TO PROCEED" section
2. File becomes ADR/decision log

### File Template

```markdown
# ADR: [Brief Task Title]

Date: YYYY-MM-DD HH:MM

## REQUEST

[Original user request verbatim from $ARGUMENTS]

## CONTEXT ANALYSIS

### Mandatory Exploration Checklist Status

**Frontend Layer:**

- Routes: [EXPLORED: file1, file2, ... | NOT APPLICABLE]
- Components: [EXPLORED: ... | NOT APPLICABLE]
- Hooks: [EXPLORED: ... | NOT APPLICABLE]
- State: [EXPLORED: ... | NOT APPLICABLE]

**Backend Layer:**

- Schema: [EXPLORED: ... | NOT APPLICABLE]
- Queries/Mutations: [EXPLORED: ... | NOT APPLICABLE]
- Actions: [EXPLORED: ... | NOT APPLICABLE]
- Services: [EXPLORED: ... | NOT APPLICABLE]

**Integration:**

- External APIs: [EXPLORED: docs/contracts | NOT APPLICABLE]
- Config: [EXPLORED: ... | NOT APPLICABLE]

**Cross-Cutting:**

- Auth flow: [EXPLORED: ... | NOT APPLICABLE]
- Error handling: [EXPLORED: ... | NOT APPLICABLE]
- Security: [EXPLORED: ... | NOT APPLICABLE]

---

### Exploration Evidence

**Files Discovered & Examined:**

Frontend:

- Routes: [specific files with line ranges if relevant]
- Components: [specific files]
- Hooks: [specific files]

Backend:

- Schema: [specific files]
- Queries/Mutations: [specific files with key exports]
- Actions: [specific files]

**Key Constructs Located:**

- [FunctionName @ path/to/file.ts:123]
- [TypeName @ path/to/types.ts:45]
- [API endpoint: POST /api/jobs → convex/jobs.ts:createJob]

**Dependency Map:**
[Show 2-3 critical dependency chains relevant to request]

---

### What I Think Is Happening

[Agent's interpretation of the request]

### What I Think You Want

[Expected outcome]

### What I'm Uncertain About

[Missing details that need clarification]

### What I Recommend We Clarify

[Dimensions to target]

---

## ROUND 1 QUESTIONS

Confidence: [X]% ([Low | Medium | High] - [description])

- Requirements: [X]% [🟢|🟡|🔴]
- Architecture: [X]% [🟢|🟡|🔴]
- Data Flow: [X]% [🟢|🟡|🔴]
- Implementation: [X]% [🟢|🟡|🔴]

### Dimension: [Dimension Name]

**Q1: [Question text]**
[Brief context of why this matters]

(a) **[Option 1]**

- Tradeoff: [rational and explanation]
- Benefit: [rational and explanation]

(b) **[Option 2]**

- Tradeoff: [rational and explanation]
- Benefit: [rational and explanation]

(c) **[Option 3]**

- Tradeoff: [rational and explanation]
- Benefit: [rational and explanation]

(d) **[Option 4]**

- Tradeoff: [rational and explanation]
- Benefit: [rational and explanation]

**Recommended:** ([letter]) [Brief rationale] — Aligns with: [PRINCIPLE NAME from ETHOS.md]

============================

**YOUR ANSWER:**

============================

<!-- AGENT REVIEW -->

**PUSHBACK (if needed):**
Status: [✅ OK | ⚠️ CONCERN]

**Issue:** [What's wrong/risky]
**Better approach:** [Alternative with why]
**Tradeoff:** Your way [cost] vs Recommended [benefit + minor cost]
**Evidence:** [codebase pattern/standard]

============================

### Dimension: [Next Dimension]

**Q2: [Question text]**
[Repeat format above]

============================

**YOUR ANSWER:**

============================

---

<!-- Additional rounds will be appended here as needed -->

---

## FINAL DECISION

Status: Complete
Confidence: [X]% 🟢

### Chosen Approach

[Summary of decided solution based on answers]

### Rationale

[Why this approach works given your answers]

### Consequences

- POSITIVE: [benefits of this approach]
- NEGATIVE: [tradeoffs accepted]
- NEUTRAL: [implementation considerations]

### Implementation Notes

[Specific guidance for coding phase]
[File paths, function names, patterns to follow]
```

**Output Format Examples:**

```
### Dimension: Build vs. Buy
**#1. Question:** How should fuzzy string matching be implemented?

- (a) **Use fuse.js (6KB, 20K+ stars)** ⭐ RECOMMENDED
  - Tradeoff: Battle-tested, minimal code, handles edge cases. Adds small dependency (~6KB gzipped).
  - Benefits: Pragmatic for solo dev, proven reliability, minimal maintenance burden.

- (b) **Custom Levenshtein algorithm**
  - Tradeoff: Full control, no dependencies. But requires testing edge cases, ongoing maintenance, not core to business value.

- (c) **Use string-similarity library**
  - Tradeoff: Simpler API than fuse.js. Less feature-rich, smaller community.

- (d) **ML-based similarity (external API)**
  - Tradeoff: Most accurate. But adds latency, cost, external dependency for non-core feature.

### Dimension: Data Management
**#2. Question:** How should profile images be stored?

- (a) **Cloud storage (S3/GCS) with DB reference** ⭐ RECOMMENDED
  - Tradeoff: Scales easily, reduces DB load, highly durable. Slightly more complex integration.
  - Benefits: Balances scalability, durability, and simplicity for growing user base.

- (b) **File system on app server**
  - Tradeoff: Simple for small apps. But doesn't scale well with multiple servers and risks data loss if server crashes.

- (c) **Database BLOB**
  - Tradeoff: Easy to implement, strong consistency. But bloats DB size, hurts performance for large images.

- (d) **Hybrid approach (local cache + cloud)**
  - Tradeoff: Improves performance for frequent access, but adds complexity to sync and cache invalidation.
```

---

## Step 5.5: Confidence Assessment & Gap Closure

After generating initial clarifying questions and analyzing the codebase/docs, evaluate confidence using **evidence-backed scores**. The goal is to reach **90%+ overall confidence** before proposing a final implementation approach.

### Confidence Scoring (100 points total)

Score each dimension from 0–25 based on concrete evidence:

1. **Requirements Clarity (0-25 points)**
   Evidence-based criteria:

   - User story or problem statement identified
   - Acceptance criteria defined
   - Non-goals or exclusions listed
   - Business/UX impact understood

2. **Architecture & System Design (0-25 points)**
   Evidence-based criteria:

   - Relevant services/modules identified
   - Integration points and dependencies mapped
   - Scalability / constraints at least partially understood

3. **Data Flow (0-25 points)**
   Evidence-based criteria:

   - Data inputs & sources identified
   - Key transformations or validations understood
   - Storage targets (DB tables, caches, queues, external systems) known
   - Outputs/consumers of the data identified

4. **Technical Implementation (0-25 points)**
   Evidence-based criteria:
   - Tech stack & framework versions confirmed (from lockfiles/configs)
   - Relevant APIs / interfaces located (with signatures)
   - Error handling patterns and logging conventions found

### Confidence Display Format

Always present confidence with:

- Overall score (%)
- Per-dimension score + emoji
- 1–3 bullets of **explicit evidence** per dimension

**Example**:

```md
CONFIDENCE: 72% (Medium - gaps remain)

- Requirements: 85% 🟢

  - Evidence: Story + ACs in `/docs/checkout.md`
  - Evidence: Non-goals explicitly listed in ticket

- Architecture: 45% 🔴

  - Evidence: Only partial service map in `architecture.md`
  - Evidence: No clear owner for `payments-orchestrator` service

- Data Flow: 60% 🟡

  - Evidence: Reads from `payments.txns` identified
  - Gap: Downstream consumers of new field not confirmed

- Implementation: 95% 🟢
  - Evidence: `POST /payments` contract in `payments/api.go`
  - Evidence: Existing error and logging patterns observed
```

### Gap-Closure Loop

Use the confidence breakdown to drive **targeted follow-ups**:

```md
WHILE overall confidence < 90%:

- Focus ONLY on 🔴 and 🟡 dimensions.
- For each such dimension:
  → Ask 1–2 laser-focused clarifying questions.
  → Each question should: - Be tightly scoped - Reference specific files, endpoints, or decisions where possible
- Incorporate answers into the evidence list.
- Recalculate per-dimension and overall confidence.
```

Guidelines:

- Do **not** ask broad or repetitive questions about 🟢 areas.
- Every new question must aim to upgrade a 🔴 to 🟡 or 🟡 to 🟢.
- Stop the loop once **overall confidence ≥ 90%** with clear evidence for each dimension.

---

## Step 5.6: Final Verification Gate

**Triggered when:** Overall confidence reaches 90%+

Before finalizing the ADR, spawn a verification subagent (using the `Task` tool) to catch missed assumptions. This is a READ-ONLY verification pass.

### Subagent Delegation Template

```
TASK: Verify ADR assumptions before finalizing

CONTEXT: The clarification process has reached 90%+ confidence. Before committing to implementation, verify that all documented decisions align with the actual codebase state and no critical assumptions were missed.

DECISIONS MADE:
[List key decisions from the ADR - copy from FINAL DECISION section]

KEY FILES TO VERIFY:
[List files referenced in the ADR with line numbers]
- path/to/file.ts:start-end (what to check)
- path/to/file.ts:start-end (what to check)

VERIFY THESE ASSUMPTIONS:
1. [Assumption from ADR] → Check: [what to verify in code]
2. [Assumption from ADR] → Check: [what to verify in code]
3. [Data flow assumption] → Check: [trace actual flow]
4. [Integration assumption] → Check: [verify API contracts]

RETURN:
- VALIDATED: [list assumptions confirmed with evidence]
- GAPS FOUND: [list missed assumptions or inaccuracies]
- RECOMMENDED UPDATES: [specific changes to ADR if needed]
```

### Verification Outcome Handling

**If GAPS FOUND is empty:**

1. Append verification summary to ADR bottom
2. Mark ADR as `✅ VERIFIED - READY TO PROCEED`
3. Proceed to Step 6

**If GAPS FOUND has items:**

1. Update confidence score (downgrade affected dimensions)
2. Append new clarifying questions for gaps
3. Return to Step 5.5 gap-closure loop
4. Re-run verification when 90%+ reached again

### ADR Verification Summary Template

Append this section when verification passes:

```markdown
---

## VERIFICATION SUMMARY

Verified: [YYYY-MM-DD]

### Assumptions Validated

- [Assumption 1]: ✅ Confirmed in `path/file.ts:123`
- [Assumption 2]: ✅ Confirmed via [evidence]

### Implementation Ready

All documented decisions verified against codebase. No blocking gaps found.
```

---

## Step 5.7: Answer Validation & Pushback

**Challenge answers that are incorrect, unsuitable, or risky.**

### When to push back:
- Contradicts codebase evidence
- Ignores security/performance best practices
- Over/under-engineered for context
- Misunderstands technical constraints

### Pushback format:

```markdown
⚠️ PUSHBACK: [Question ref]

**Your answer:** [quote]
**Issue:** [what's wrong - 1 sentence]
**Recommended:** [alternative approach]

**Why switch:**
[Tangible benefit - what they GAIN]

**Tradeoff:**
- Your way: [specific risk with evidence]
- Recommended: [what's sacrificed + why acceptable]

**Evidence:** [file:line | standard | existing pattern]

**Your call:** [Explain reasoning if you still prefer original - I'll defer]
```

### Outcome:
- ✅ All valid → proceed to next round/Step 6
- ⚠️ Pushback given → wait for user response (revise/justify/override)

---

## Step 6: Proposed Approach

**Note: Only proceed to this step after Step 5.6 verification passes.**
After clarifying, I’ll outline how I’d tackle the feature given your answers. Then I’ll wait for your confirmation before refining further.