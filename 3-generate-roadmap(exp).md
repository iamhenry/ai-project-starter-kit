// My Notes
- think about how the roadmap steps will be affected by TDD (writing tests first) and if it makes sense to me
- if it doesnt, restructure the milestone slices to focus on logic first → implementation (follow unit → integration tdd flow)
- this new  Tracer Bullet Vertical Slice Method focuses on one core journey or user story that's chord to the MVP
`(ex. # Core Flow Home: (Conversation List) → FAB → Capture/Gallery → Image Processing → New Conversation View (with Receipt Component showing parsed items)`

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

## Principles
- Each phase builds on the previous WITHOUT major rewrites.
- End-to-end slice: Ship a minimal, working thread through the system—UI → API → data—so you can test reality, not theory. Even if it’s rough, it proves integration, deploys, logs, and latency.

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

#### 2. Table of Contents Section
Add after the Parallel Execution Guide section:
```markdown
## Table of Contents

**Phase 1 - [Phase Name]**:
[Brief description summarizing what the entire phase accomplishes - the overall acceptance criteria for the phase]

- M1: [Milestone Name] - [Single-line description of what this milestone delivers]
- M2: [Milestone Name] - [Single-line description of what this milestone delivers]

**Phase 2 - [Phase Name]**:
[Brief description summarizing what the entire phase accomplishes - the overall acceptance criteria for the phase]

- M3: [Milestone Name] - [Single-line description of what this milestone delivers]
- M4: [Milestone Name] - [Single-line description of what this milestone delivers]

**Phase 3 - [Phase Name]**:
[Brief description summarizing what the entire phase accomplishes - the overall acceptance criteria for the phase]

- M5: [Milestone Name] - [Single-line description of what this milestone delivers]
- M6: [Milestone Name] - [Single-line description of what this milestone delivers]
```

#### 3. Task Execution Plans
For each milestone, include execution syntax directly in the milestone header showing parallel opportunities:
```markdown
### Milestone X: [Milestone Name]
**Task Execution Plan: Task 1 ⚠️ → Task 2,3 🔄 (parallel after Task 1)**

Objective: [Brief description]
```

---

## Phase-Specific Guidance

### Guiding Principle: Build in Vertical Slices, Not Horizontal Layers

The roadmap must be structured around delivering thin, end-to-end user functionality in each phase. We will de-risk the project by building and testing the most critical, interactive user journey first.

### Phase 1: The Tracer Bullet (Core Functional Slice)
- **Objective:** Build the thinnest possible, functional slice of the project's **single most critical user journey**. This slice must connect all necessary architectural layers (e.g., UI -> API -> Service) to prove the concept works end-to-end.
- **Method:** To achieve speed, this phase should aggressively use in-memory state, mocked API responses, and hardcoded data *within* the functional pipeline. The goal is interactivity, not feature completeness or data persistence.
- **Outcome:** A developer can use a primitive but complete version of the core feature, validating the riskiest architectural and user-experience assumptions immediately.
- **Handling Multiple Core Flows:** If the application has more than one critical user journey, the planner must force a prioritization to select a **single** journey for the Phase 1 Tracer Bullet. The remaining core flows become the top-priority milestones for Phase 2. Use the following criteria to decide:
    1.  **Dependency:** Does one flow require the output or existence of another? (e.g., A "view item" flow must precede a "purchase item" flow). Choose the prerequisite flow first.
    2.  **Risk:** Which flow contains the most significant technical or usability unknowns? Build the riskiest one first.
    3.  **Core Value:** Which flow is most central to the app's unique value proposition? Build that one first.

### Phase 2: Service Integration & Feature Expansion
- **Objective:** To evolve the Phase 1 Tracer Bullet into a robust, production-ready feature and then systematically build out the remaining critical user journeys of the application.
- **Prioritization Hierarchy (MUST be followed in this order):**
    1.  **Stabilize the Core Slice:** Replace all mocks from Phase 1 with real services and add necessary persistence (e.g., database storage). This makes the initial feature complete.
    2.  **Implement Subsequent Core Flows:** Build out any other critical user journeys that were deferred from Phase 1. These should be tackled in a logical, dependency-first order.
    3.  **Expand with Secondary Features:** Once all core journeys are functional, build out supporting features (e.g., settings screens, ancillary content feeds, user profiles).

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
- Potentially: Deepwiki MCP URL to github repo of the codebase/boilerplate i plan to use
- `ARCHITECTURE.MD` (if available)
- `TECHNICAL-REQUIREMENTS.md`

---

# Style Guide

### Structure & Formatting
- Use headers for section titles.
- Keep milestone descriptions concise and action-oriented.
- Use relevant mermaid diagrams for Data Flow.
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

### Task Symbols
- ⚠️ **BLOCKING** - Must complete before other tasks can start
- 🔄 **PARALLEL** - Can run simultaneously with other tasks
- ✅ **DEPENDENT** - Requires specific prior task completion

---

## Table of Contents

**Phase 1 - Tracer Bullet (Core Functional Slice)**:
Build the thinnest functional end-to-end flow where a user can enter an ingredient, receive a recipe name from a dumb API, proving the entire UI-to-API-to-UI communication loop works.

- M1: End-to-End Recipe Generation Loop - User can input ingredients and receive a hardcoded recipe name, validating the complete interaction flow

**Phase 2 - Service Integration & Feature Expansion**:
Replace mocked parts with real AI service and database persistence, then build out the remaining critical user journey for viewing recipe history.

- M2: Stabilize Core Feature with Real AI & Persistence - Core loop uses real AI service and saves generated recipes to database
- M3: Implement Core Flow: Recipe History - Users can view a list of their previously generated and saved recipes

**Phase 3 - Production Hardening & Polish**:
Enhance user experience with smooth animations, clear loading states, immediate feedback, and consistent design system across all screens.

- M4: UI Polish and Interaction Feedback - Enhanced UX with loading skeletons, toast notifications, animations, and refined design system

---

## Phase 1: The Tracer Bullet (Core Functional Slice)
Focus on building the thinnest possible, functional slice of the project's single most critical user journey.

---

### Milestone 1: [Milestone Name - e.g., "End-to-End Recipe Generation Loop"]
**Task Execution Plan: ⚠️ Task 1 → ⚠️ Task 2 → ✅ Task 3**

Objective: Enable a user to enter an ingredient and receive a recipe name from a 'dumb' API, proving the entire UI-to-API-to-UI communication loop works.

Data Flow:
- User input from a single screen triggers an API call to a 'dumb' endpoint that returns a hardcoded, structured response. The UI then displays this response.
- API contract defined for `/api/generate-recipe` (request: `{ ingredients: string[] }`, response: `{ recipeName: string }`).

**Tasks**:
- [ ] 1. ⚠️ Define API contract and create the 'dumb' API endpoint
  - [ ] 1.1. Create the API route file `app/api/generate-recipe+api.ts`.
  - [ ] 1.2. Implement the endpoint to accept a POST request with an `ingredients` body.
  - [ ] 1.3. Return a hardcoded JSON object that matches the response contract.
  - File: `app/api/generate-recipe+api.ts`
  - Contract Definition: `POST /api/generate-recipe`, request: `{ ingredients: string[] }`, response: `{ recipeName: string }`
  - Branch Name: `feature/api-recipe-scaffold`
  - Acceptance Criteria: The API endpoint accepts a POST request and returns a hardcoded JSON object matching the defined contract.
  - Complexity: 2
- [ ] 2. ⚠️ Build the minimal UI for the core interaction
  - [ ] 2.1. Create a single-screen UI with a text input, a "Generate" button, and a text area for the result.
  - [ ] 2.2. Implement the client-side logic to call the API endpoint when the button is clicked.
  - [ ] 2.3. Add a basic loading state (e.g., disable the button) while waiting for the response.
  - File: `app/index.tsx`
  - Consumes Contract: API contract for `/api/generate-recipe`.
  - Branch Name: `feature/ui-recipe-generator`
  - Acceptance Criteria: User can input text and click a button, triggering a POST request to the `/api/generate-recipe` endpoint.
  - Complexity: 2
- [ ] 3. ✅ Connect the UI to the API response
  - [ ] 3.1. In the API call's success handler, extract the `recipeName` from the response.
  - [ ] 3.2. Use state management (e.g., `useState`) to store the received recipe name.
  - [ ] 3.3. Render the recipe name in the designated text area on the UI.
  - File: `app/index.tsx`
  - Branch Name: `feature/wire-up-recipe-loop`
  - Acceptance Criteria: The recipe name from the API response is successfully stored in state and rendered on the UI.
  - Complexity: 1

---

## Phase 2: Service Integration & Feature Expansion
Focus on replacing mocked parts of the core loop with real services and building out the remaining critical user journeys.

---

### Milestone 2: [Milestone Name - e.g., "Stabilize Core Feature with Real AI & Persistence"]
**Task Execution Plan: ⚠️ Task 1 → ✅ Task 2**

Objective: Upgrade the core loop by replacing the 'dumb' API with a real AI service and adding database persistence to save generated recipes.

Data Flow:
- The `/api/generate-recipe` endpoint now calls a real AI service. The response is then saved to a new `recipes` table in the database.

**Tasks**:
- [ ] 1. ⚠️ Upgrade API endpoint to be 'smart' and implement Database Schema
  - [ ] 1.1. Add the necessary SDK to call a real AI recipe generation service.
  - [ ] 1.2. Replace the hardcoded response in the API with the real AI call.
  - [ ] 1.3. Define a Drizzle/Prisma schema for a `recipes` table (e.g., `id`, `name`, `ingredients`, `createdAt`).
  - [ ] 1.4. Implement a database service layer to save a recipe.
  - Files: `app/api/generate-recipe+api.ts`, `db/schema.ts`, `services/dbService.ts`
  - Branch Name: `feature/api-real-ai-and-db`
  - Acceptance Criteria: The API endpoint successfully calls a real AI service, and a database schema for `recipes` is defined and functional.
  - Complexity: 4
- [ ] 2. ✅ Integrate database saving into the API flow
  - [ ] 2.1. After receiving a successful response from the AI service, call the `dbService` to save the new recipe.
  - [ ] 2.2. Add error handling for both the AI call and the database write operation.
  - File: `app/api/generate-recipe+api.ts`
  - Branch Name: `feature/api-save-recipe`
  - Acceptance Criteria: After a successful AI response, the generated recipe data is persisted to the database.
  - Complexity: 2

---

### Milestone 3: [Milestone Name - e.g., "Implement Core Flow: Recipe History"]
**Task Execution Plan: ✅ Task 1 → ✅ Task 2**

Objective: Build the next most critical user journey, which allows users to view a list of their previously generated and saved recipes.

Data Flow:
- A new UI screen (`/history`) fetches a list of recipes from the database service. Users can navigate from this list back to a recipe detail view.

**Tasks**:
- [ ] 1. ✅ Create an API endpoint to fetch recipe history
  - [ ] 1.1. Create a new API route `app/api/recipes+api.ts`.
  - [ ] 1.2. Implement a `GET` handler that uses the `dbService` to retrieve all saved recipes.
  - File: `app/api/recipes+api.ts`
  - Branch Name: `feature/api-get-recipes`
  - Acceptance Criteria: A new GET endpoint `/api/recipes` is created that returns all recipe records from the database.
  - Complexity: 2
- [ ] 2. ✅ Build the Recipe History UI
  - [ ] 2.1. Create a new screen/page component for the recipe history list.
  - [ ] 2.2. On page load, call the `/api/recipes` endpoint to fetch the data.
  - [ ] 2.3. Render the list of recipe names, handling loading and empty states.
  - File: `app/history.tsx`
  - Branch Name: `feature/ui-recipe-history`
  - Acceptance Criteria: The history UI page fetches from `/api/recipes` on load and displays the list of recipe names.
  - Complexity: 2

---

## Phase 3: Production Hardening & Polish
Focus on non-functional requirements, UI/UX polish, and business logic.

---

### Milestone 4: [Milestone Name - e.g., "UI Polish and Interaction Feedback"]
**Task Execution Plan: 🔄 Task 1, 2, 3 (all parallel)**

Objective: Enhance the user experience with smooth animations, clear loading states, and immediate feedback for user actions.

**Tasks**:
- [ ] 1. 🔄 Implement loading skeletons
  - [ ] 1.1. While the recipe history list is fetching, display placeholder skeleton components instead of a blank screen.
  - File: `app/history.tsx`, `components/RecipeSkeleton.tsx`
  - Branch Name: `feature/ui-loading-skeletons`
  - Acceptance Criteria: Skeleton loaders are displayed on the history page before the recipe data is rendered.
  - Complexity: 2
- [ ] 2. 🔄 Add interaction feedback
  - [ ] 2.1. After a recipe is successfully generated and saved, show a "Recipe Saved!" toast notification.
  - [ ] 2.2. Animate list items appearing on the history page.
  - Files: `app/index.tsx`, `app/history.tsx`
  - Branch Name: `feature/ui-interaction-feedback`
  - Acceptance Criteria: A toast notification is displayed on successful recipe generation; list items on the history page animate in.
  - Complexity: 2
- [ ] 3. 🔄 Refine the Design System
  - [ ] 3.1. Ensure consistent typography, spacing, and color usage across all screens.
  - [ ] 3.2. Create reusable button and input components with variants.
  - Files: `styles/global.css`, `components/ui/Button.tsx`
  - Branch Name: `feature/ui-design-system-refinement`
  - Acceptance Criteria: Reusable, styled components for Button and Input are created and used; app-wide styles (color, typography) are consistent.
  - Complexity: 3
```
