---
description: Tool for generating Behavior-Driven Development test scenarios
alwaysApply: false
---

<GenerateBDDTestScenarios>
When generating Gherkin scenarios, follow these guidelines:

- Write Behavior-Driven Development (BDD) requirements in the Given-When-Then format.
- Include only the most critical scenarios that define the fundamental behavior of the feature.
- Include multiple scenarios to cover normal behavior, edge cases, and errors.
- Ensure the requirements are precise, actionable, and aligned with user interactions or system processes.
- Omit irrelevant scenarios.
- When generating files, use the format: `bdd-[filename].md`

# Behavior-Focused Scenario Template

```markdown
# Scenario 1: [Clear action-oriented title describing the user behavior]
  <!-- 
  Context Setting: What state is the user starting from? What conditions need to be true? 
  Avoid: Technical setup details | Include: User-visible state 
  -->
  Given [Initial context/state from user perspective]
    And [Additional context if needed, avoid implementation details]
  
  <!-- 
  User Action: What exactly does the user do? What would you tell someone to trigger this? 
  Avoid: Internal system calls | Include: Observable user actions 
  -->
  When [Specific user action that triggers the behavior]
    And [Additional actions if needed in sequence]
  
  <!-- 
  Observable Outcomes: What would the user see/experience if this works? 
  Avoid: Internal state changes | Include: Visual changes, feedback, navigation 
  -->
  Then [Observable outcome visible to the user]
    And [Additional observable outcomes]
    And [Error states or alternative paths if relevant]

  <!-- How can we verify this works without knowing implementation? What's non-negotiable? -->
  ## Acceptance Criteria:
  - [ ] [Measurable/observable criterion that verifies success]
  - [ ] [Boundary condition handling]
  - [ ] [Performance aspect if relevant] 
  - [ ] [Accessibility consideration if relevant]
  - [ ] [Error state handling if relevant]
  - [ ] [State persistence aspect if relevant]

  <!-- 
  Which patterns actually apply? What could go wrong from user's perspective? 
  Select only relevant patterns - prioritize high-impact, likely scenarios
  -->
  ## Edge Cases to Consider: 
  * Empty/Null Conditions - How does the feature behave with no data or input?
  * Boundary Values - What happens at minimum/maximum limits?
  * Connectivity Scenarios - How does the feature respond to network changes?
  * Interruption Patterns - What if the process is interrupted midway?
  * Resource Constraints - How does it perform under high load or limited resources?
  * Permission Variations - What changes based on different user permissions?
  * Concurrency Issues - What if multiple users/processes interact simultaneously?
  * State Transitions - What happens during transitions between states?
```
</GenerateBDDTestScenarios>