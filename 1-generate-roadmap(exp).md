# HIGHLY Experimental Roadmap.md Parallel Task Execution

## Purpose
1. Break down work into granular tasks
2. Define clear interfaces (contracts)
3. Facilitate parallel development
4. Minimize integration conflicts

## When to Use
- Starting a new software project and needing a comprehensive development plan.
- Planning projects where tasks will be delegated to multiple developers or AI agents simultaneously.
- When aiming to reduce merge conflicts through contract-first development and parallelizable task structures.
- To ensure consistency and clarity in roadmap documentation across different projects.

# Instructions

- Review and analyze the `Required` documents (e.g., User Stories, Overview).
- Decompose the project into a step-by-step development plan following the **Vertical Slice Phasing Model** outlined below.
- **Prioritize breaking down tasks into the smallest, most independent units possible to enable parallel execution by AI agents and support frequent, small integrations/merges.**
- Break down complex tasks into subtasks with a complexity scale (1-5, where 5 is very complex).
- **Emphasize 'Interface-First' or 'Contract-First' development.** Define data structures (e.g., mock data, TypeScript types), API signatures (e.g., OpenAPI specs for backend), and component prop types *before* dependent tasks are assigned. These contracts are crucial for minimizing merge conflicts when multiple agents work concurrently.
- Generate a new file in `_ai/docs/ROADMAP.md`.

## Parallel Execution Documentation

### REQUIRED SECTIONS FOR ROADMAP:
Include these sections in every generated roadmap to enable clear parallel task execution:

#### 1. Parallel Execution Guide Section
Add immediately after the Overview section:
```markdown
## Parallel Execution Guide

### Phase Dependencies
- Phase 1 (Tracer Bullet) → Phase 2 (Expansion) → Phase 3 (Hardening)

### Milestone Parallelization
- **Phase 1**: Milestones are typically sequential as they build the core end-to-end flow.
- **Phase 2**: Milestones for different vertical slices (e.g., M2: Real OCR, M3: Settings UI) can often run in parallel after the core slice is stable.
- **Phase 3**: Milestones (e.g., M4: Animations, M5: Analytics) can almost always run in parallel.

### Task Symbols
- ⚠️ **BLOCKING** - Must complete before other tasks can start
- 🔄 **PARALLEL** - Can run simultaneously with other tasks
- ✅ **DEPENDENT** - Requires specific prior task completion
```

#### 2. Task Execution Plans
For each milestone, include execution syntax directly in the milestone header showing parallel opportunities:
```markdown
### Milestone X: [Milestone Name]
**Task Execution Plan: Task 1 ⚠️ → Task 2,3 🔄 (parallel after Task 1)**

Objective: [Brief description]
```

#### 3. Dependencies & Parallelization Per Milestone
For each milestone, include this subsection:
```markdown
Dependencies & Parallelization:
- **BLOCKS**: What this milestone blocks (or "None")
- **BLOCKED BY**: What blocks this milestone
- **PARALLEL WITHIN**: Which tasks within milestone can run parallel
- **PARALLEL WITH**: Which other milestones can run parallel
```

---

## Phase-Specific Guidance

### Guiding Principle: Build in Vertical Slices, Not Horizontal Layers

The roadmap must be structured around delivering thin, end-to-end user functionality in each phase. We will de-risk the project by building and testing the most critical, interactive user journey first.

### Phase 1: The Tracer Bullet (Core Functional Slice)
- **Objective:** Build the thinnest possible, functional slice of the project's **single most critical user journey**. This slice must connect all necessary architectural layers (e.g., UI -> API -> Service) to prove the concept works end-to-end.
- **Method:** To achieve speed, this phase should aggressively use in-memory state, mocked API responses, and hardcoded data *within* the functional pipeline. The goal is interactivity, not feature completeness or data persistence.
- **Outcome:** A developer can use a primitive but complete version of the core feature, validating the riskiest architectural and user-experience assumptions immediately.

### Phase 2: Service Integration & Feature Expansion
- **Objective:** Systematically replace the mocked/hardcoded parts of the "Tracer Bullet" with real services and begin building out secondary features as their own vertical slices.
- **Prioritization:**
    1.  **Swap out mocks:** Connect the Phase 1 slice to real databases, real 3rd-party APIs, and real backend logic.
    2.  **Build new vertical slices:** Add secondary features (e.g., user profiles, settings pages, content feeds) one by one, ensuring each is a complete, functional slice.
- **Outcome:** The core feature becomes robust and production-ready, and the application's surface area grows with fully functional, testable features.

### Phase 3: Production Hardening & Polish
- **Objective:** Focus on non-functional requirements, user experience enhancements, and business-logic integrations now that the core features are validated.
- **Tasks Include (Examples):**
    - **UI/UX Polish:** Animations, advanced styling, accessibility improvements.
    - **Performance & Security:** Optimization, error monitoring, rate limiting, security audits.
    - **Business Logic:** Subscription/monetization integration, analytics, user onboarding tours.
- **Outcome:** A feature-complete, robust, and delightful application ready for launch.

---

# Requirements

- `USER-STORIES.md`
- (Potentially: `API-CONTRACTS.yaml` or `DATA-MODELS.md` if available upfront for later phases)

---

# Style Guide

### Structure & Formatting
- Use headers for section titles.
- Keep milestone descriptions concise and action-oriented.
- Use bullet points for Data Flow and Acceptance Criteria.
- Use step numbering for Step-by-Step Tasks.
- Reference file paths and contract documents explicitly to ensure clarity.

### Naming Conventions
- Use `Phase X: [Phase Name]` for broader project stages (e.g., Phase 1: The Tracer Bullet).
- Use `Milestone X: [Milestone Name]` to segment major goals.
- Milestone Naming Rule: Name milestones after the functional outcome they achieve (e.g., "Minimal End-to-End Chat Loop" or "Real-Time OCR Integration"). **Consider grouping parallelizable feature sets or component groups into distinct milestones within the same phase to facilitate concurrent development.**
- Keep file names and paths consistent across projects (e.g., `mocks/[feature].js`, `contracts/api.yaml`).

### Task Complexity Ratings
- 1-2: Simple UI tasks, minor adjustments, implementing against a well-defined contract.
- 3: Mid-level complexity such as basic API integrations (consuming or implementing a defined endpoint).
- 4-5: High-complexity tasks like complex state management, defining new core data structures/API contracts, performance optimization.
- Ensure tasks are broken down at least 3 levels deep. **Even tasks with higher overall complexity (4-5) should be decomposed into smaller, independent sub-tasks (ideally 1-2 complexity each) suitable for individual assignment by an agent and frequent integration.**

---

# Template

```markdown
# [Project Name] Development Roadmap

## Overview
This roadmap outlines the development plan for [Project Name], broken down into clear milestones and phases following a vertical slice methodology. Each task includes a complexity rating (1-5, where 5 is most complex) and is designed to support parallel work where possible by defining clear interfaces.

## Parallel Execution Guide
### Phase Dependencies
- Phase 1 (Tracer Bullet) → Phase 2 (Expansion) → Phase 3 (Hardening)

### Milestone Parallelization
- **Phase 1**: Milestones are typically sequential as they build the core end-to-end flow.
- **Phase 2**: Milestones for different vertical slices (e.g., M2: Real OCR, M3: Settings UI) can often run in parallel after the core slice is stable.
- **Phase 3**: Milestones (e.g., M4: Animations, M5: Analytics) can almost always run in parallel.

### Task Symbols
- ⚠️ **BLOCKING** - Must complete before other tasks can start
- 🔄 **PARALLEL** - Can run simultaneously with other tasks
- ✅ **DEPENDENT** - Requires specific prior task completion

## Phase 1: The Tracer Bullet (Core Functional Slice)
Focus on building the thinnest possible, functional slice of the project's single most critical user journey.

### Milestone 1: [Milestone Name - e.g., "End-to-End Core Interaction Loop"]
**Task Execution Plan: ⚠️ Task 1 → ⚠️ Task 2 → ✅ Task 3**

Objective: [Brief description of the core loop, e.g., "Enable a user to perform the core action and see a result from a real API call, using mocked data within the API to start."].

Dependencies & Parallelization:
- **BLOCKS**: All other milestones (this proves the core concept).
- **BLOCKED BY**: None (starting milestone).
- **PARALLEL WITHIN**: None (this is a sequential build of the core slice).
- **PARALLEL WITH**: None.

Data Flow:
- [Describe the end-to-end flow, e.g., "User input from a single screen triggers an API call to a 'dumb' endpoint that returns a hardcoded, structured response. The UI then displays this response."].
- [e.g., "API contract defined for `/api/core-action` (request: `{ input: string }`, response: `{ id, result: string }`)."]

Acceptance Criteria:
- [List criteria, e.g., "User can interact with the core UI element (e.g., a button)."]
- [e.g., "A network request is successfully sent to the defined API endpoint."]
- [e.g., "The API endpoint returns a successful, hardcoded response adhering to the defined contract."]
- [e.g., "The UI updates to display the result from the API call."]

**Tasks**:
- [ ] 1. ⚠️ Define the API contract and create the 'dumb' API endpoint
  - [ ] 1.1. Create the API route file.
  - [ ] 1.2. Implement the endpoint to accept a POST request.
  - [ ] 1.3. Return a hardcoded JSON object that matches the defined response contract.
  - File: `app/api/core-action+api.ts`
  - Contract Definition: [e.g., `POST /api/core-action`: request/response schema]
  - Branch Name: `feature/api-core-action-scaffold`
  - Complexity: 2
- [ ] 2. ⚠️ Build the minimal UI for the core interaction
  - [ ] 2.1. Create the simplest possible UI (e.g., one button and a text display area).
  - [ ] 2.2. Implement the logic to call the API endpoint when the button is clicked.
  - [ ] 2.3. Add basic loading state handling (e.g., disable the button while waiting for the response).
  - File: `app/index.tsx` (or a single component file)
  - Consumes Contract: API contract for `/api/core-action`.
  - Branch Name: `feature/ui-core-interaction`
  - Complexity: 2
- [ ] 3. ✅ Connect the UI to the API response
  - [ ] 3.1. Take the response from the API call.
  - [ ] 3.2. Update the application's state with the result.
  - [ ] 3.3. Render the result in the text display area.
  - File: `app/index.tsx`
  - Branch Name: `feature/wire-up-core-loop`
  - Complexity: 1

## Phase 2: Service Integration & Feature Expansion
Focus on replacing mocked parts of the core loop with real services and building out secondary features as new vertical slices.

### Milestone 2: [Milestone Name - e.g., "Real Service Integration for Core Loop"]
**Task Execution Plan: Task 1 ✅**

Objective: [e.g., "Replace the hardcoded API response with a call to a real 3rd-party service or real business logic."].

Dependencies & Parallelization:
- **BLOCKS**: Full feature testing.
- **BLOCKED BY**: Milestone 1 complete.
- **PARALLEL WITH**: Milestone 3 (if it's an independent feature).

Data Flow:
- [e.g., "The `/api/core-action` endpoint now forwards the request to a real 3rd-party API, transforms the response, and returns it to the client, maintaining the same contract."]

**Tasks**:
- [ ] 1. ✅ Upgrade API endpoint to be 'smart'
  - [ ] 1.1. Add the necessary SDK or fetch logic to call the real external service.
  - [ ] 1.2. Replace the hardcoded response with the logic to call the service.
  - [ ] 1.3. Add error handling for when the external service call fails.
  - File: `app/api/core-action+api.ts`
  - Branch Name: `feature/api-real-service-integration`
  - Complexity: 3

(Continue with other milestones for Phase 2, such as adding database persistence or building new vertical slices like a settings page.)

## Phase 3: Production Hardening & Polish
Focus on non-functional requirements, UI/UX polish, and business logic.

### Milestone X: [Milestone Name - e.g., "UI Polish and Animations"]
**Task Execution Plan: Task 1,2,3 🔄 (all parallel)**

Objective: [e.g., "Enhance the user experience with smooth animations and a polished design system."].

Dependencies & Parallelization:
- **BLOCKS**: None.
- **BLOCKED BY**: Relevant features from Phase 2 must be complete.
- **PARALLEL WITHIN**: All UI polish tasks can run in parallel.
- **PARALLEL WITH**: Other Phase 3 milestones (e.g., Analytics).

**Tasks**:
- [ ] 1. 🔄 Implement screen transition animations
  - ...
- [ ] 2. 🔄 Add loading state animations
  - ...
```