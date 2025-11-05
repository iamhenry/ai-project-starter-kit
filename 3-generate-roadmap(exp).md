// My Notes
- think about how the roadmap steps will be affected by TDD (writing tests first) and if it makes sense to me
- if it doesnt, restructure the milestone slices to focus on logic first → implementation (follow unit → integration tdd flow)
- this new  Tracer Bullet Vertical Slice Method focuses on one core journey or user story that's chord to the MVP
`(ex. # Core Flow Home: (Conversation List) → FAB → Capture/Gallery → Image Processing → New Conversation View (with Receipt Component showing parsed items)`

# HIGHLY Experimental Roadmap.md Parallel Task Execution

## Purpose
1.  Break down work into granular tasks.
2.  Define clear interfaces (contracts) to enable vertical slice development.
3.  Facilitate parallel development of UI, API, and database logic.
4.  Minimize integration conflicts by building and testing end-to-end from day one.

## When to Use
*   Starting a new software project and needing a comprehensive development plan.
*   Planning projects where tasks will be delegated to multiple developers or AI agents simultaneously.
*   When aiming to reduce merge conflicts through contract-first development and parallelizable task structures.
*   To ensure consistency and clarity in roadmap documentation across different projects.

## Principles (Tracer Bullet & Vertical Slice)
*Consider these principles and questions when structuring the roadmap and tracer bullet.*
*   Each phase builds on the previous WITHOUT major rewrites.
*   **End-to-end slice**: Ship a minimal, working thread through the system—UI → API → Database—so you can test reality, not theory. Even if it’s rough, it proves integration, deploys, logs, and latency.
*   What are our table stakes?
*   **Reduce code churn (it wastes time)**: Building with real components from the start avoids the throwaway work of replacing mocks.
*   How to ship faster? What can be trimmed and why?
*   Keep only the core value proposition.
*   Minor inconvenience that doesn't block core workflow is ok; poor UX is not.
*   The original Pragmatic Programmer definition says tracer bullets should: **"Operate in the same environment and under the same constraints as the real system."**
*   **Use REAL production code, not prototypes.**
*   Be the thinnest slice that **actually works end-to-end**.
*   **The tracer bullet should go THROUGH the high-risk parts, not around them.**
*   **Learn about constraints immediately.**
*   **Each iteration adds real value.**
*   **Use real data and persistence, not mocks.**
*   What tasks can be sacrificed while preserving the core flow and value proposition?

```
- Vertical Slice = Build ONE user action end-to-end:
  - UI (button/form/display)
  - Frontend logic (state management, API calls)
  - Backend (database + external API calls)
- Ex: Connect Apple Music (END-TO-END)
  - Database schema for storing tokens
  - Encryption utilities (backend)
  - Apple Music token storage (backend)
  - "Connect Apple Music" button (UI)
  - Connection status display (UI)
  > What you can TEST: Click button → authenticate → see "Connected" status
  > Components built: AppleMusicConnect.tsx, providerTokens table, encryption utils
```

# Instructions

*   Review and analyze the `Required` documents (e.g., User Stories, Overview).
*   Decompose the project into a step-by-step development plan following the **Vertical Slice Phasing Model** outlined below.
*   **Prioritize breaking down tasks into the smallest, most independent units possible to enable parallel execution by AI agents and support frequent, small integrations/merges.**
*   Break down complex tasks into subtasks with a complexity scale (1-5, where 5 is very complex).
*   **Emphasize 'Interface-First' or 'Contract-First' development.** Define data structures (e.g., TypeScript types), API signatures (e.g., OpenAPI specs for backend), and component prop types *before* dependent tasks are assigned. These contracts are crucial for minimizing merge conflicts when multiple agents work concurrently.
*   Generate a new file in `_ai/docs/ROADMAP.md`.

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

The roadmap must be structured around delivering thin, end-to-end user functionality in each phase. We will de-risk the project by building and testing the most critical, interactive user journey first. Each slice should contain components from every necessary layer—UI, backend logic, and database.

### Phase 1: The Tracer Bullet (Core Functional Slice)
*   **Objective:** Build the thinnest possible, functional slice of the project's **single most critical user journey**. This slice must connect all necessary architectural layers (e.g., UI -> API -> Database) to prove the concept works end-to-end with real data and persistence.
*   **Method:** This phase focuses on creating a working, albeit minimal, piece of functionality. It uses real database schemas, real API logic, and real UI components. The goal is to validate the entire system, from user interaction to data storage, immediately.
*   **Outcome:** A developer can use a primitive but complete version of the core feature, validating the riskiest architectural and user-experience assumptions with production-like code from day one.
*   **Handling Multiple Core Flows:** If the application has more than one critical user journey, the planner must force a prioritization to select a **single** journey for the Phase 1 Tracer Bullet. The remaining core flows become the top-priority milestones for Phase 2. Use the following criteria to decide:
    1.  **Dependency:** Does one flow require the output or existence of another? Choose the prerequisite flow first.
    2.  **Risk:** Which flow contains the most significant technical or usability unknowns? Build the riskiest one first.
    3.  **Core Value:** Which flow is most central to the app's unique value proposition? Build that one first.

### Phase 2: Feature Expansion & Core Journeys
*   **Objective:** To build upon the foundation of the Phase 1 Tracer Bullet by adding more depth to the existing feature or by systematically building out the remaining critical user journeys of the application.
*   **Prioritization Hierarchy (MUST be followed in this order):**
    1.  **Enhance the Core Slice:** Add more complex logic, integrate external services (e.g., a real AI model), or enrich the UI of the initial feature.
    2.  **Implement Subsequent Core Flows:** Build out any other critical user journeys that were deferred from Phase 1. These should be tackled as new, complete vertical slices.
    3.  **Expand with Secondary Features:** Once all core journeys are functional, build out supporting features (e.g., settings screens, ancillary content feeds, user profiles).

### Phase 3: Production Hardening & Polish
*   **Objective:** Focus on non-functional requirements, user experience enhancements, and business-logic integrations now that the core features are validated.
*   **Tasks Include (Examples):**
    *   **UI/UX Polish:** Animations, advanced styling, accessibility improvements.
    *   **Performance & Security:** Optimization, error monitoring, rate limiting, security audits.
    *   **Business Logic:** Subscription/monetization integration, analytics, user onboarding tours.
*   **Outcome:** A feature-complete, robust, and delightful application ready for launch.

---

# Requirements

*   `USER-STORIES.md`
*   Potentially: Deepwiki MCP URL to github repo of the codebase/boilerplate i plan to use
*   `ARCHITECTURE.MD` (if available)
*   `TECHNICAL-REQUIREMENTS.md`

---

# Style Guide

### Structure & Formatting
*   Use headers for section titles.
*   Keep milestone descriptions concise and action-oriented.
*   Use relevant mermaid diagrams for Data Flow.
*   Use step numbering for Step-by-Step Tasks.
*   Reference file paths and contract documents explicitly to ensure clarity.

### Naming Conventions
*   Use `Phase X: [Phase Name]` for broader project stages (e.g., Phase 1: The Tracer Bullet).
*   Use `Milestone X: [Milestone Name]` to segment major goals.
*   Milestone Naming Rule: Name milestones after the functional outcome they achieve (e.g., "Minimal End-to-End Chat Loop" or "Real-Time OCR Integration"). **Consider grouping parallelizable feature sets or component groups into distinct milestones within the same phase to facilitate concurrent development.**
*   Keep file names and paths consistent across projects (e.g., `db/schema.ts`, `contracts/api.yaml`).

### Task Complexity Ratings
*   1-2: Simple UI tasks, minor adjustments, implementing against a well-defined contract.
*   3: Mid-level complexity such as basic API integrations (consuming or implementing a defined endpoint).
*   4-5: High-complexity tasks like complex state management, defining new core data structures/API contracts, performance optimization.
*   Ensure tasks are broken down at least 3 levels deep. **Even tasks with higher overall complexity (4-5) should be decomposed into smaller, independent sub-tasks (ideally 1-2 complexity each) suitable for individual assignment by an agent and frequent integration.**

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
Build the thinnest functional end-to-end flow where a user can enter an ingredient, have it saved to a database, and see it displayed, proving the entire UI-to-API-to-Database loop works.

- M1: End-to-End Recipe Creation & Display - User can input ingredients, which are saved to the database via an API, and see the result.

**Phase 2 - Feature Expansion & Core Journeys**:
Integrate a real AI service to generate recipes from ingredients and build out the critical user journey for viewing recipe history.

- M2: Integrate Real AI for Recipe Generation - The core loop uses a real AI service to generate a recipe from the saved ingredients.
- M3: Implement Core Flow: Recipe History - Users can view a list of their previously generated and saved recipes.

**Phase 3 - Production Hardening & Polish**:
Enhance user experience with smooth animations, clear loading states, immediate feedback, and a consistent design system across all screens.

- M4: UI Polish and Interaction Feedback - Enhanced UX with loading skeletons, toast notifications, animations, and a refined design system.

---

## Phase 1: The Tracer Bullet (Core Functional Slice)
Focus on building the thinnest possible, functional slice of the project's single most critical user journey with real data and persistence.

---

### Milestone 1: End-to-End Recipe Creation & Display
**Task Execution Plan: ⚠️ Task 1 → ✅ Task 2 → ✅ Task 3**

Objective: Enable a user to enter ingredients, have them persisted to the database, and see the saved record, proving the entire UI → API → DB → UI loop works.

Data Flow:
- User input from a single screen triggers an API call. The API service saves the data to a `recipes` table and returns the created record. The UI then displays the result.
- API contract defined for `POST /api/recipes` (request: `{ ingredients: string[] }`, response: `{ id: string, name: string, ingredients: string[] }`).

**Tasks**:
- [ ] 1. ⚠️ Define Database Schema and Backend Service
  - [ ] 1.1. Define a Drizzle/Prisma schema for a `recipes` table (e.g., `id`, `name`, `ingredients`, `createdAt`).
  - [ ] 1.2. Implement a database service layer to create a new recipe record. For now, the `name` can be hardcoded (e.g., "New Recipe").
  - Files: `db/schema.ts`, `services/dbService.ts`
  - Branch Name: `feature/db-recipe-schema`
  - Acceptance Criteria: A `recipes` table schema is defined, and a service function can write a new record to it.
  - Complexity: 2
- [ ] 2. ✅ Build the API Endpoint for Recipe Creation
  - [ ] 2.1. Create the API route `app/api/recipes/+api.ts`.
  - [ ] 2.2. Implement a `POST` handler that takes `ingredients` from the request body.
  - [ ] 2.3. Use the `dbService` to save the new recipe and return the newly created record.
  - File: `app/api/recipes/+api.ts`
  - Branch Name: `feature/api-create-recipe`
  - Acceptance Criteria: The `POST /api/recipes` endpoint successfully saves data to the database and returns the created object.
  - Complexity: 2
- [ ] 3. ✅ Build Minimal UI to Create and Display Recipe
  - [ ] 3.1. Create a UI with a text input, a "Save" button, and a display area for the result.
  - [ ] 3.2. Implement client-side logic to call the `POST /api/recipes` endpoint.
  - [ ] 3.3. On a successful response, use state management to store the returned recipe object and render its name/ingredients.
  - File: `app/index.tsx`
  - Branch Name: `feature/ui-recipe-loop`
  - Acceptance Criteria: A user can input ingredients, click save, and see the data returned from the live API displayed on the screen.
  - Complexity: 2

---

## Phase 2: Feature Expansion & Core Journeys
Focus on enhancing the core feature with external services and building out the remaining critical user journeys.

---

### Milestone 2: Integrate Real AI for Recipe Generation
**Task Execution Plan: ⚠️ Task 1 → ✅ Task 2**

Objective: Upgrade the recipe creation endpoint to call a real AI service to generate a recipe name based on the provided ingredients.

Data Flow:
- The `POST /api/recipes` endpoint first calls an AI service with the ingredients. It then uses the AI-generated name to save the new recipe to the database.

**Tasks**:
- [ ] 1. ⚠️ Enhance API to call AI service
  - [ ] 1.1. Add the necessary SDK to call a real AI recipe generation service.
  - [ ] 1.2. In the `POST /api/recipes` handler, before saving to the DB, call the AI service to get a recipe name.
  - [ ] 1.3. Add error handling for the AI service call.
  - File: `app/api/recipes/+api.ts`
  - Branch Name: `feature/api-real-ai`
  - Acceptance Criteria: The API endpoint successfully calls the AI service to get a recipe name.
  - Complexity: 3
- [ ] 2. ✅ Save AI-generated name to Database
  - [ ] 2.1. Use the name from the AI response when calling the `dbService` to create the recipe record.
  - [ ] 2.2. Ensure the full recipe object (with the AI-generated name) is returned to the client.
  - File: `app/api/recipes/+api.ts`
  - Branch Name: `feature/api-save-ai-recipe`
  - Acceptance Criteria: After a successful AI response, the generated recipe name is persisted to the database.
  - Complexity: 2

---

### Milestone 3: Implement Core Flow: Recipe History
**Task Execution Plan: ⚠️ Task 1 → ✅ Task 2**

Objective: Build the next most critical user journey, which allows users to view a list of their previously generated and saved recipes.

Data Flow:
- A new UI screen (`/history`) fetches a list of all recipes from the database via a new GET endpoint.

**Tasks**:
- [ ] 1. ⚠️ Create an API endpoint to fetch recipe history
  - [ ] 1.1. In `app/api/recipes/+api.ts`, implement a `GET` handler.
  - [ ] 1.2. Use the `dbService` to retrieve all saved recipes from the database.
  - File: `app/api/recipes/+api.ts`
  - Branch Name: `feature/api-get-recipes`
  - Acceptance Criteria: A `GET /api/recipes` endpoint is created that returns all recipe records from the database.
  - Complexity: 2
- [ ] 2. ✅ Build the Recipe History UI
  - [ ] 2.1. Create a new screen/page component for the recipe history list.
  - [ ] 2.2. On page load, call the `GET /api/recipes` endpoint to fetch the data.
  - [ ] 2.3. Render the list of recipe names, handling loading and empty states.
  - File: `app/history.tsx`
  - Branch Name: `feature/ui-recipe-history`
  - Acceptance Criteria: The history UI page fetches from `/api/recipes` on load and displays the list of recipe names.
  - Complexity: 2

---

## Phase 3: Production Hardening & Polish
Focus on non-functional requirements, UI/UX polish, and business logic.

---

### Milestone 4: UI Polish and Interaction Feedback
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
