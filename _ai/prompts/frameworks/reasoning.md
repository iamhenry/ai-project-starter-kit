---
description: Structured reasoning tool with software development triggers for problem-solving
alwaysApply: false
---

<reasoning>
# LLM Structured Reasoning Tool with Software Development Triggers

This tool enables Large Language Models (LLMs) to solve software development problems using a structured, step-by-step approach based on a JSON schema, limited to 5 thought steps. It includes rule—specific events or conditions in software development that activate the reasoning process. Each step involves a topic, detailed thinking, reflection, a quality score (reward), and a decision on the next step, concluding with a summary and reflection.

## Problem
[Insert the user-provided problem and specify the trigger, e.g., "Failing unit test in login feature (Trigger: Failing Test in TDD)"]

## Instructions for LLMs
- Purpose: Use this template to address software development problems triggered by specific events.
- Triggers: Initiate reasoning when a trigger condition is met (see below). Identify the trigger in the "Problem" section.
- Steps: Follow the 5-step process, filling out each section as described.
- Scoring: Assign a reward score (0.0 to 1.0) to evaluate each step's quality:
  - 0.8+: CONTINUE with the current approach.
  - 0.5–0.7: ADJUST with minor changes.
  - Below 0.5: BACKTRACK and try a different approach.
- Output: Provide the completed template in Markdown, ensuring all sections are filled.
- Tone: Be clear, precise, and reflective, exploring multiple angles and questioning assumptions.

## Analysis

### Step 1
- Topic: [High-level idea, question, or approach, e.g., "Identify the cause of the failing test"]
- Thinking: [Detailed reasoning, e.g., review test output, check code logic, analyze error messages. Explore all angles, be thorough.]
- Reflection: [Evaluate the approach, e.g., "Did I miss a dependency? Should I check logs or try a different test case?"]
- Reward: [Score between 0.0 and 1.0]
- Next Step: [CONTINUE, ADJUST, or BACKTRACK]

### Step 2
- Topic: [High-level idea, question, or approach]
- Thinking: [Detailed reasoning, calculations, or considerations. Explore all angles, be thorough.]
- Reflection: [Evaluate the approach. Is it working? Should you adjust or try something else?]
- Reward: [Score between 0.0 and 1.0]
- Next Step: [CONTINUE, ADJUST, or BACKTRACK]

### Step 3
- Topic: [High-level idea, question, or approach]
- Thinking: [Detailed reasoning, calculations, or considerations. Explore all angles, be thorough.]
- Reflection: [Evaluate the approach. Is it working? Should you adjust or try something else?]
- Reward: [Score between 0.0 and 1.0]
- Next Step: [CONTINUE, ADJUST, or BACKTRACK]

### Step 4
- Topic: [High-level idea, question, or approach]
- Thinking: [Detailed reasoning, calculations, or considerations. Explore all angles, be thorough.]
- Reflection: [Evaluate the approach. Is it working? Should you adjust or try something else?]
- Reward: [Score between 0.0 and 1.0]
- Next Step: [CONTINUE, ADJUST, or BACKTRACK]

### Step 5
- Topic: [High-level idea, question, or approach]
- Thinking: [Detailed reasoning, calculations, or considerations. Explore all angles, be thorough.]
- Reflection: [Evaluate the approach. Is it working? Should you adjust or try something else?]
- Reward: [Score between 0.0 and 1.0]
- Next Step: [CONTINUE, ADJUST, or BACKTRACK]

## Final Thought
[Clear, concise summary of the solution, e.g., "Fixed the failing test by correcting the login validation logic"]

## Final Reflection
[Clear, concise reflection on the thinking process, e.g., "The systematic approach helped identify a hidden assumption in the code"]

## Conclusion
[Final answer to the problem, formatted as needed, e.g., updated code, test fix, or architectural proposal]
</reasoning>