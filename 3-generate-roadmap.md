# Instructions

- Review and analyze the `Required` documents
- Then decompose and suggest a step by step plan to development
- Break down complex tasks into subtasks (scale of 1-5, 5 being very complex)
- Ensure the plan is outlined in Milestones
- Phases: Static UI (UI scaffold, no functionality yet) -> Frontend -> Backend -> UI Polish (e.g. animations)
- Generate a new file in `_ai/docs/ROADMAP.md`

# Requirements

- BOM document
- User Stories document

---

# Style Guide

### Structure & Formatting
- Use headers for section titles.
- Keep milestone descriptions concise and action-oriented.
- Use bullet points for Data Flow and Acceptance Criteria.
- Use step numbering for Step-by-Step Tasks.
- Reference file paths explicitly to ensure clarity.

### Naming Conventions
- Use Phase X for broader project stages.
- Use Milestone X: [Milestone Name] to segment major goals.
- Keep file names and paths consistent across projects.

### Task Complexity Ratings
- 1-2: Simple UI tasks, minor adjustments.
- 3: Mid-level complexity such as API integrations.
- 4-5: High-complexity tasks like state management, performance optimization.
- Ensure tasks are broken down at least 3 levels deep.

This template ensures each development roadmap follows a structured and repeatable format.

---

# Template

```markdown
# [Project Name] Development Roadmap

## Overview
This roadmap outlines the development plan for [Project Name], broken down into clear milestones and phases. Each task includes a complexity rating (1-5, where 5 is most complex).

IMPORTANT: Breakup Phases in this order: Static UI (UI scaffold, no functionality yet) -> Frontend -> Backend -> UI Polish (e.g. animations)

## Phase 1: [Phase Name]
Focus on [general phase objective].

### Milestone 1: [Milestone Name]
Objective: [Brief description of milestone goal].

Data Flow:
- [Describe data interactions relevant to this milestone]

Acceptance Criteria:
- [List clear criteria to mark milestone completion]

Step-by-Step Tasks:
- [ ] 1. [Task description: include enough details so that a junior dev can be assigned to it]  
  - File: `[file/path.tsx]`  
  - [ ] 1.1. [Sub-task description: detailed enough for clear implementation]  
  - [ ] 1.2. [Sub-task description: detailed enough for clear implementation]
  - [ ] 1.3. [Sub-task description: detailed enough for clear implementation]   
- [ ] 2. [Task description: include enough details so that a junior dev can be assigned to it]  
  - File: `[file/path.tsx]`  
  - [ ] 2.1. [Sub-task description: detailed enough for clear implementation]  
  - [ ] 2.2. [Sub-task description: detailed enough for clear implementation]  
  - [ ] 2.3. [Sub-task description: detailed enough for clear implementation]

### Milestone 2: [Milestone Name]
Objective: [Brief description of milestone goal].

Data Flow:
- [Describe data interactions relevant to this milestone]

Acceptance Criteria:
- [List clear criteria to mark milestone completion]

Step-by-Step Tasks:
- [ ] 3. [Task description: include enough details so that a junior dev can be assigned to it]  
  - File: `[file/path.tsx]`  
  - [ ] 3.1. [Sub-task description: detailed enough for clear implementation]  
  - [ ] 3.2. [Sub-task description: detailed enough for clear implementation]  

(Continue for additional phases and milestones as needed)
```