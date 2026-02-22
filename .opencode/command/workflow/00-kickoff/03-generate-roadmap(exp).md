---
name: generate-roadmap (03)
description: Generate a brand new Roadmap from technical requirements
subtask: false
---
// My Notes
- think about how the roadmap steps will be affected by TDD (writing tests first) and if it makes sense to me
- if it doesnt, restructure the milestone slices to focus on logic first → implementation (follow unit → integration tdd flow)
- this new  Tracer Bullet Vertical Slice Method focuses on one core journey or user story that's chord to the MVP
`(ex. # Core Flow Home: (Conversation List) → FAB → Capture/Gallery → Image Processing → New Conversation View (with Receipt Component showing parsed items)`

## Inputs
1. output from: `.opencode/command/workflow/00-kickoff/02-technical-requirements.md` as `tech-adr.md`

---

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

### Code Snippets
*   Include **exact code** inline with tasks when relevant—not all tasks require snippets.
*   Use snippets for: schema definitions, type definitions, function signatures, API contracts, component implementations.
*   Place snippets directly after the task checkbox, before subtasks.
*   Keep scope minimal: show only what's being added/modified.
*   Use fenced code blocks with appropriate language tag.

**Example:**
- [ ] 1. ⚠️ Define Database Schema
  ```typescript
  // db/schema.ts
  export const recipes = pgTable('recipes', {
    id: serial('id').primaryKey(),
    name: text('name').notNull(),
    ingredients: jsonb('ingredients').$type<string[]>().notNull(),
  });
  ```
  - [ ] 1.1. Run migration to create table
  - Files: `db/schema.ts`

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
  ```typescript
  // db/schema.ts
  export const recipes = pgTable('recipes', {
    id: serial('id').primaryKey(),
    name: text('name').notNull(),
    ingredients: jsonb('ingredients').$type<string[]>().notNull(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  });
  
  // services/dbService.ts
  export async function createRecipe(ingredients: string[]) {
    return db.insert(recipes).values({
      name: 'New Recipe',
      ingredients,
    }).returning();
  }
  ```
  - [ ] 1.1. Define Drizzle schema for `recipes` table
  - [ ] 1.2. Implement `createRecipe` service function
  - Files: `db/schema.ts`, `services/dbService.ts`
  - Branch Name: `feature/db-recipe-schema`
  - Acceptance Criteria: A `recipes` table schema is defined, and a service function can write a new record to it.
  - Complexity: 2
- [ ] 2. ✅ Build the API Endpoint for Recipe Creation
  ```typescript
  // app/api/recipes/route.ts
  export async function POST(request: Request) {
    const { ingredients } = await request.json();
    const recipe = await createRecipe(ingredients);
    return Response.json(recipe, { status: 201 });
  }
  ```
  - [ ] 2.1. Create API route handler for POST requests
  - [ ] 2.2. Parse request body and call dbService
  - File: `app/api/recipes/route.ts`
  - Branch Name: `feature/api-create-recipe`
  - Acceptance Criteria: The `POST /api/recipes` endpoint saves data and returns the created object.
  - Complexity: 2
- [ ] 3. ✅ Build Minimal UI to Create and Display Recipe
  ```tsx
  // app/page.tsx
  export default function Page() {
    const [ingredients, setIngredients] = useState('');
    const [recipe, setRecipe] = useState(null);
    
    const handleSave = async () => {
      const res = await fetch('/api/recipes', {
        method: 'POST',
        body: JSON.stringify({ ingredients: ingredients.split(',') }),
      });
      setRecipe(await res.json());
    };
    
    return (
      <div>
        <input value={ingredients} onChange={e => setIngredients(e.target.value)} />
        <button onClick={handleSave}>Save</button>
        {recipe && <div>{recipe.name}: {recipe.ingredients.join(', ')}</div>}
      </div>
    );
  }
  ```
  - [ ] 3.1. Create form with input and submit button
  - [ ] 3.2. Call API on submit and store result in state
  - File: `app/page.tsx`
  - Branch Name: `feature/ui-recipe-loop`
  - Acceptance Criteria: User can input ingredients, save, and see the returned data.
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
  ```typescript
  // services/aiService.ts
  export async function generateRecipeName(ingredients: string[]): Promise<string> {
    const response = await aiClient.generate({
      prompt: `Create a recipe name using: ${ingredients.join(', ')}`,
    });
    return response.name;
  }
  
  // app/api/recipes/route.ts (updated)
  export async function POST(request: Request) {
    const { ingredients } = await request.json();
    const name = await generateRecipeName(ingredients);
    const recipe = await createRecipe(ingredients, name);
    return Response.json(recipe, { status: 201 });
  }
  ```
  - [ ] 1.1. Add AI SDK and create `generateRecipeName` function
  - [ ] 1.2. Integrate AI call into POST handler before save
  - [ ] 1.3. Add error handling for AI service failures
  - Files: `services/aiService.ts`, `app/api/recipes/route.ts`
  - Branch Name: `feature/api-real-ai`
  - Acceptance Criteria: API endpoint calls AI service and returns recipe with generated name.
  - Complexity: 3
- [ ] 2. ✅ Save AI-generated name to Database
  ```typescript
  // services/dbService.ts (updated)
  export async function createRecipe(ingredients: string[], name: string) {
    return db.insert(recipes).values({
      name,
      ingredients,
    }).returning();
  }
  ```
  - [ ] 2.1. Update `createRecipe` to accept name parameter
  - [ ] 2.2. Return full recipe object with AI-generated name to client
  - File: `services/dbService.ts`
  - Branch Name: `feature/api-save-ai-recipe`
  - Acceptance Criteria: AI-generated name is persisted and returned in response.
  - Complexity: 2

---

### Milestone 3: Implement Core Flow: Recipe History
**Task Execution Plan: ⚠️ Task 1 → ✅ Task 2**

Objective: Build the next most critical user journey, which allows users to view a list of their previously generated and saved recipes.

Data Flow:
- A new UI screen (`/history`) fetches a list of all recipes from the database via a new GET endpoint.

**Tasks**:
- [ ] 1. ⚠️ Create an API endpoint to fetch recipe history
  ```typescript
  // app/api/recipes/route.ts (add GET handler)
  export async function GET() {
    const allRecipes = await db.select().from(recipes).orderBy(desc(recipes.createdAt));
    return Response.json(allRecipes);
  }
  ```
  - [ ] 1.1. Implement GET handler to query all recipes
  - [ ] 1.2. Return recipes ordered by most recent first
  - File: `app/api/recipes/route.ts`
  - Branch Name: `feature/api-get-recipes`
  - Acceptance Criteria: `GET /api/recipes` returns all recipe records from database.
  - Complexity: 2
- [ ] 2. ✅ Build the Recipe History UI
  ```tsx
  // app/history/page.tsx
  export default function HistoryPage() {
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
      fetch('/api/recipes')
        .then(res => res.json())
        .then(data => { setRecipes(data); setLoading(false); });
    }, []);
    
    if (loading) return <div>Loading...</div>;
    if (recipes.length === 0) return <div>No recipes yet</div>;
    
    return (
      <ul>
        {recipes.map(r => <li key={r.id}>{r.name}</li>)}
      </ul>
    );
  }
  ```
  - [ ] 2.1. Create history page component with fetch on mount
  - [ ] 2.2. Handle loading and empty states
  - [ ] 2.3. Render list of recipe names
  - File: `app/history/page.tsx`
  - Branch Name: `feature/ui-recipe-history`
  - Acceptance Criteria: History page fetches `/api/recipes` and displays list of recipe names.
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
  ```tsx
  // components/RecipeSkeleton.tsx
  export function RecipeSkeleton() {
    return (
      <div className="animate-pulse flex space-x-4">
        <div className="rounded-full bg-gray-200 h-10 w-10"></div>
        <div className="flex-1 space-y-2 py-1">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }
  
  // app/history/page.tsx (updated)
  if (loading) return <RecipeSkeleton />;
  ```
  - [ ] 1.1. Create `RecipeSkeleton` component with placeholder styling
  - [ ] 1.2. Replace "Loading..." text with skeleton in history page
  - Files: `components/RecipeSkeleton.tsx`, `app/history/page.tsx`
  - Branch Name: `feature/ui-loading-skeletons`
  - Acceptance Criteria: Skeleton loaders display on history page before data renders.
  - Complexity: 2
- [ ] 2. 🔄 Add interaction feedback
  ```tsx
  // app/page.tsx (updated)
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  
  const handleSave = async () => {
    setSaving(true);
    const res = await fetch('/api/recipes', { /* ... */ });
    setRecipe(await res.json());
    setToast('Recipe saved!');
    setSaving(false);
    setTimeout(() => setToast(''), 3000);
  };
  
  return (
    <>
      {toast && <div className="toast">{toast}</div>}
      <button disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
    </>
  );
  ```
  - [ ] 2.1. Add toast notification on successful recipe save
  - [ ] 2.2. Add loading state to save button during submission
  - Files: `app/page.tsx`
  - Branch Name: `feature/ui-interaction-feedback`
  - Acceptance Criteria: Toast shows on save; button shows loading state.
  - Complexity: 2
- [ ] 3. 🔄 Refine the Design System
  ```tsx
  // components/ui/Button.tsx
  interface ButtonProps {
    variant?: 'primary' | 'secondary';
    children: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }
  
  export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
    const base = 'px-4 py-2 rounded font-medium';
    const variants = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700',
      secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    };
    return <button className={`${base} ${variants[variant]}`} {...props}>{children}</button>;
  }
  ```
  - [ ] 3.1. Create reusable `Button` component with variants
  - [ ] 3.2. Ensure consistent typography/spacing across screens
  - Files: `components/ui/Button.tsx`, `app/globals.css`
  - Branch Name: `feature/ui-design-system-refinement`
  - Acceptance Criteria: Reusable Button component created and used across app; styles consistent.
  - Complexity: 3
```
