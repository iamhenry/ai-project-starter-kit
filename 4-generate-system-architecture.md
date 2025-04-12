# Generating System Architecture


# Requirements

- roadmap.md
- Defined Overview / User Stories document

#### Instructions
Create a detailed system architecture document:
- based on the [Requirements]
- create a new file `SYSTEM-ARCHITECTURE.md` in `_ai/docs`
- generate the document using the [output_format]



<output_format>
Use the following example structure:

```markdown
# System Architecture Document (SAD) Template

## 1. Overview
### Purpose
[Provide a brief description of the system, its objectives, and its intended users.]

### Scope
[Define the scope of the system, including what is included and what is out of scope.]

### Context
[Describe the environment in which the system operates, including key business and technical constraints.]

---

## 2. Architectural Goals
[Specify key design principles and trade-offs, such as performance, scalability, maintainability, security, and simplicity.]

---

## 3. System Context Diagram
[Provide a high-level mermaid diagram illustrating how the system interacts with external entities, such as APIs, databases, and user interfaces.]

### Description
[Explain the key components and their roles in the system context diagram.]

---

## 4. Component Diagrams
[Break down the system into its major modules or services, describing their responsibilities and interactions.]

### High-Level Architecture
[Provide a diagram showcasing system components and their relationships.]

### Subsystems & Modules
[List the major subsystems or modules, along with their descriptions.]

---

## 5. Data Models
[Define the structure of data used by the system, including schemas, entity-relationship diagrams, and data flow descriptions.]

### Database Schema
[Outline the database schema with tables, fields, and relationships.]

### Data Flow
[Explain how data moves through the system, including transformations and storage.]

---

## 6. Interface Definitions
[Define how system components communicate, including API specifications, protocols, and message formats.]

### APIs
[List key APIs with request/response structures and authentication mechanisms.]

### Data Contracts
[Describe expected data formats, payload structures, and validation rules.]

---

## 7. Technology Stack
[Specify technologies, frameworks, and tools chosen for the project, along with justifications for their selection.]

### Programming Languages & Frameworks
[List chosen languages, frameworks, and libraries, and explain why they were selected.]

### Infrastructure & Deployment
[Describe hosting environments, cloud services, CI/CD pipelines, and deployment strategies.]

---

## 8. Risk & Mitigation
[Identify potential risks associated with the system and provide contingency plans.]

### Risk Assessment
[List possible risks, their impact, and probability of occurrence.]

### Mitigation Strategies
[Describe strategies to mitigate each identified risk, including monitoring, backups, and alternative solutions.]

---

## 9. Appendix (Optional)
[Include any additional references, glossaries, or supporting documentation.]

---

**Notes:**
- Ensure diagrams are clear and labeled appropriately.
- Keep descriptions concise but informative.
- Update the document as the system evolves.
```
</output_format>


[No code blocks in the final task list]
