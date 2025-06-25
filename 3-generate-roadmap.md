# Instructions

- Review and analyze the `Required` documents (Bill of Materials, Overview/User Stories).
- Decompose the project into a step-by-step development plan.
- Break down complex tasks into subtasks with a complexity scale (1-5, where 5 is very complex).
- Outline the plan in milestones, supporting multiple milestones per phase as needed.
- Follow these phases in order: Static UI (UI scaffold, no functionality yet) -> Frontend -> Backend -> UI Polish (e.g., animations).
- Generate a new file in `_ai/docs/ROADMAP.md`.
- Important:
  - Exclude tests in the Static UI phase to keep it lightweight.
  - Name milestones with a project-wide focus (e.g., "Initial UI Components" instead of "Task List")—see Style Guide for details.

## Phase-Specific Guidance

### Phase 1: Static UI
- Objective: Create UI scaffolds with no functionality, using centralized mock data to represent future real data structures.
- Mock Data Instructions:
  1. Create Centralized Mock Data Files:
     - For each major feature or component set, create a file in a `mocks/` directory (e.g., `mocks/[feature].js` where `[feature]` is a descriptive name like "tasks" or "users").
     - Define a lightweight function (e.g., `get[Feature]Data`) that returns a simple data structure mirroring the expected real data (e.g., `[{ id: 1, title: "Task 1" }]`).
     - Keep it minimal: include only essential fields (e.g., `id`, `title`) based on User Stories or Overview document assumptions.
     - Use plain JavaScript objects—no third-party libraries.
  2. Integrate Mock Data into Components:
     - In each UI component task, import the mock data function (e.g., `import { get[Feature]Data } from '../mocks/[feature].js'`).
     - Pass the mock data as props to the component (e.g., `<Component data={get[Feature]Data()} />`) to render static UI elements.
  3. Document in Roadmap:
     - In the `Data Flow` section, specify the mock data source and flow (e.g., "Mock data from `mocks/[feature].js` passed as props to components").
     - In `Acceptance Criteria`, ensure components render mock data correctly (e.g., "Components display [field] from mock data").
     - In `Step-by-Step Tasks`, include steps for creating the mock file and using it in components (see template example).
- Goal: Ensure mock data is easy to swap with real API data in the Frontend phase by maintaining consistent structure.

# Requirements

- `USER-STORIES.md`

---

# Style Guide

### Structure & Formatting
- Use headers for section titles.
- Keep milestone descriptions concise and action-oriented.
- Use bullet points for Data Flow and Acceptance Criteria.
- Use step numbering for Step-by-Step Tasks.
- Reference file paths explicitly to ensure clarity.

### Naming Conventions
- Use `Phase X: [Phase Name]` for broader project stages.
- Use `Milestone X: [Milestone Name]` to segment major goals.
- Milestone Naming Rule: Name milestones after broad project goals or feature sets (e.g., "Initial UI Components" or "Core Functionality"), avoiding single-entity focus (e.g., "Task List"), based on the Overview/User Stories document.
- Keep file names and paths consistent across projects (e.g., `mocks/[feature].js` for mock data).

### Task Complexity Ratings
- 1-2: Simple UI tasks, minor adjustments.
- 3: Mid-level complexity such as API integrations.
- 4-5: High-complexity tasks like state management, performance optimization.
- Ensure tasks are broken down at least 3 levels deep.

---

This template ensures each development roadmap follows a structured and repeatable format.


# Template

```markdown
# [Project Name] Development Roadmap

## Overview
This roadmap outlines the development plan for [Project Name], broken down into clear milestones and phases. Each task includes a complexity rating (1-5, where 5 is most complex).

IMPORTANT: Breakup Phases in this order: Static UI (UI scaffold, no functionality yet) -> Frontend -> Backend -> UI Polish (e.g. animations)

## Phase 1: Static UI
Focus on creating UI scaffolds with centralized mock data, no functionality yet.

### Milestone 1: [Milestone Name]
Objective: [Brief description of milestone goal, e.g., "Build initial UI components"].

Data Flow:
- [Describe mock data flow, e.g., "Mock data from `mocks/[feature].js` passed as props to components"]

Acceptance Criteria:
- [List criteria, e.g., "Components render with mock data from `mocks/[feature].js`"]
- [e.g., "UI displays [field] from mock data"]
- [e.g., "Layout matches Bill of Materials"]

Step-by-Step Tasks:
- [ ] 1. Create centralized mock data for [feature]  
  - File: `mocks/[feature].js` [e.g., "tasks.js"]
  - Branch Name: `<type>/<context>-<medium-description>`
  - Complexity: 1  
  - [ ] 1.1. Define `get[Feature]Data()` returning [data shape, e.g., "array: [{ id, title }]"]  
  - [ ] 1.2. Export the function for component use  
- [ ] 2. Create [feature] UI component(s)  
  - File: `components/[Feature].tsx` [e.g., "TaskList.tsx"]
  - Branch Name: `<type>/<context>-<medium-description>`
  - Complexity: 2  
  - [ ] 2.1. Import `get[Feature]Data` from `mocks/[feature].js`  
  - [ ] 2.2. Render [describe output, e.g., "list"] using `get[Feature]Data()`  
  - [ ] 2.3. Apply basic CSS [e.g., "flexbox"] per Overview document  

### Milestone 2: [Milestone Name]
Objective: [Brief description of milestone goal, e.g., "Build secondary UI components"].

Data Flow:
- [Describe mock data flow, e.g., "Mock data from `mocks/[secondary].js` passed as props"]

Acceptance Criteria:
- [List criteria, e.g., "Components render with mock data"]

Step-by-Step Tasks:
- [ ] 1. Create centralized mock data for [secondary]  
  - File: `mocks/[secondary].js` [e.g., "users.js"]
  - Branch Name: `<type>/<context>-<medium-description>`
  - Complexity: 1  
  - [ ] 1.1. Define `get[Secondary]Data()` returning [data shape]  
  - [ ] 1.2. Export the function  
- [ ] 2. Create [secondary] UI component(s)  
  - File: `components/[Secondary].tsx`
  - Branch Name: `<type>/<context>-<medium-description>`
  - Complexity: 2  
  - [ ] 2.1. Import `get[Secondary]Data` from `mocks/[secondary].js`  
  - [ ] 2.2. Render [describe output] using `get[Secondary]Data()`  

(Continue for additional milestones in this phase as needed)

## Phase 2: Frontend
Focus on adding interactivity and real data integration.

### Milestone 3: [Milestone Name]
Objective: [Brief description, e.g., "Add interactivity to [feature]"].

Data Flow:
- [Describe data flow, e.g., "Fetch data from `/api/[feature]` and pass to components"]

Acceptance Criteria:
- [List criteria, e.g., "Components fetch and display real data"]

Step-by-Step Tasks:
- [ ] 1. [Task description: include enough details so that a junior dev can be assigned to it]  
  - File: `[file/path.tsx]`
  - Branch Name: `<type>/<context>-<medium-description>`
  - [ ] 1.1. [Sub-task description: detailed enough for clear implementation]  
  - [ ] 1.2. [Sub-task description: detailed enough for clear implementation]  

(Continue for additional phases and milestones as needed)
```