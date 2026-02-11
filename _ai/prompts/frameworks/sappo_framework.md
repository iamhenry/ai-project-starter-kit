---
description: SAPPO framework providing a structured approach to software development problem-solving
alwaysApply: false
---

<sappo_framework>

### Overview
The SAPPO Framework (Sense, Analyze, Plan, Perform, Optimize) is a structured, iterative approach to solving complex problems, rooted in systems theory and inspired by frameworks like the Systems Approach Problem Solver (SAPS). It emphasizes understanding the problem holistically, analyzing root causes, planning actionable solutions, implementing them, and optimizing based on feedback. SAPPO is particularly effective for complex, interdependent problems in business, engineering, or systems management, where clarity, stakeholder alignment, and continuous improvement are critical.

### 1. Sense: Define the Problem
Goal: Create a clear, specific problem statement and understand the context.  
Questions to Ask:
- Who is affected by the problem? (Stakeholders)
- What is the current state vs. desired state?
- When and where does the problem occur?
- Why is solving this problem important?
- What data or evidence is available?

Template:
```markdown
### Problem Statement
Problem: [Describe the issue in 1-2 sentences, focusing on facts, not opinions.]  
Stakeholders: [List affected groups, e.g., customers, employees, IT team.]  
Current State: [Describe what's happening now, with evidence.]  
Desired State: [Define the ideal outcome.]  
Scope: [Specify boundaries, e.g., department, timeframe.]  
Initial Data: [List available data, e.g., metrics, complaints, logs.]  
```

Example:
```markdown
### Problem Statement
Problem: Customer complaints about slow order processing have increased by 30% in Q1 2025.  
Stakeholders: Customers, customer service team, IT department.  
Current State: Average order processing time is 48 hours, compared to an industry standard of 24 hours.  
Desired State: Reduce processing time to 24 hours or less.  
Scope: E-commerce platform, U.S. operations, within 6 months.  
Initial Data: Customer feedback logs, system performance metrics, staff reports.  
```

### 2. Analyze: Identify Root Causes
Goal: Deconstruct the problem into components and pinpoint root causes.  
Tools:
- 5 Whys: Ask "why" repeatedly to drill down to the core issue.
- Fishbone Diagram: Categorize causes (e.g., people, process, technology).
- Logic Tree: Break the problem into mutually exclusive, collectively exhaustive (MECE) parts.
- Data Analysis: Use metrics, logs, or surveys to validate causes.

Template:
```markdown
### Root Cause Analysis
Primary Issue: [Restate the problem.]  
Hypotheses: [List possible causes, e.g., "System lag due to outdated software."]  
Analysis Method: [Specify tool, e.g., 5 Whys, fishbone diagram.]  
Findings: [Summarize data or evidence supporting root causes.]  
Root Cause(s): [State the core issue(s) driving the problem.]  
```

Example:
```markdown
### Root Cause Analysis
Primary Issue: Slow order processing time (48 hours vs. 24-hour goal).  
Hypotheses: 
- Outdated order management system causes delays.  
- Insufficient staff training slows manual processing.  
- High order volume overwhelms system capacity.  
Analysis Method: 5 Whys and system performance data analysis.  
Findings: 
- 5 Whys revealed system lag due to legacy software not scaling with order volume.  
- Data shows 60% of delays occur during peak hours (10 AM–2 PM).  
Root Cause(s): Legacy order management system lacks scalability for peak loads.  
```

### 3. Plan: Develop Solutions
Goal: Create a prioritized, actionable plan to address root causes.  
Steps:
- Brainstorm solutions addressing the root cause(s).
- Evaluate trade-offs (cost, feasibility, impact).
- Prioritize using a framework (e.g., impact-effort matrix).
- Define timelines, responsibilities, and success metrics.

Template:
```markdown
### Action Plan
Root Cause(s): [Restate from Analysis.]  
Proposed Solutions: [List solutions with brief descriptions.]  
Evaluation: [Summarize pros, cons, and feasibility for each solution.]  
Prioritized Solution: [Select the best solution and justify.]  
Plan Details: 
- Tasks: [List specific actions.]  
- Timeline: [Specify deadlines.]  
- Responsibilities: [Assign roles.]  
- Success Metrics: [Define measurable outcomes.]  
```

Example:
```markdown
### Action Plan
Root Cause(s): Legacy order management system lacks scalability.  
Proposed Solutions: 
1. Upgrade to a cloud-based order management system (OMS).  
2. Optimize current system with performance patches.  
3. Hire additional staff to handle peak loads.  
Evaluation: 
- Upgrade OMS: High cost ($100K), high impact, 6-month implementation.  
- Optimize System: Low cost ($20K), moderate impact, 2-month implementation.  
- Hire Staff: Medium cost ($50K/year), low impact, 1-month implementation.  
Prioritized Solution: Upgrade to cloud-based OMS for long-term scalability and performance.  
Plan Details: 
- Tasks: Vendor selection, system migration, staff training.  
- Timeline: Complete by Q3 2025 (6 months).  
- Responsibilities: IT team (migration), HR (training).  
- Success Metrics: Reduce processing time to ≤24 hours, 90% customer satisfaction.  
```

### 4. Perform: Implement the Solution
Goal: Execute the plan with clear communication and monitoring.  
Steps:
- Communicate the plan to stakeholders.
- Execute tasks per the timeline.
- Monitor progress with regular check-ins.
- Document actions and challenges.

Template:
```markdown
### Implementation Log
Solution: [Restate prioritized solution.]  
Progress Updates: 
- [Date]: [Task completed, issues encountered, next steps.]  
Stakeholder Communication: [Summarize updates shared with stakeholders.]  
Challenges: [List any obstacles and mitigation strategies.]  
```

Example:
```markdown
### Implementation Log
Solution: Upgrade to cloud-based OMS.  
Progress Updates: 
- 05/01/2025: Vendor selected (VendorX), contract signed.  
- 06/15/2025: Data migration 50% complete; minor data mapping issues resolved.  
Stakeholder Communication: Biweekly updates to IT, customer service, and leadership.  
Challenges: Data mapping errors; mitigated by adding a data specialist to the team.  
```

### 5. Optimize: Evaluate and Refine
Goal: Assess outcomes, refine the solution, and standardize improvements.  
Steps:
- Measure success metrics against goals.
- Collect stakeholder feedback.
- Adjust the solution if needed.
- Standardize successful changes to prevent recurrence.

Template:
```markdown
### Optimization Report
Solution: [Restate solution.]  
Success Metrics: [Compare actual vs. target outcomes.]  
Feedback: [Summarize stakeholder input.]  
Adjustments: [Describe refinements or additional actions.]  
Standardization: [Outline steps to sustain improvements.]  
```

Example:
```markdown
### Optimization Report
Solution: Cloud-based OMS upgrade.  
Success Metrics: 
- Processing time reduced to 20 hours (target: ≤24 hours).  
- Customer satisfaction at 92% (target: 90%).  
Feedback: Customer service reports fewer complaints; IT notes easier maintenance.  
Adjustments: Added automated alerts for peak load monitoring.  
Standardization: Updated IT protocols to include cloud OMS maintenance; trained staff on new system.  
```
</sappo_framework>