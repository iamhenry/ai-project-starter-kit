# Research Phase

Verbatim pre-category research phase from technical-requirements Phase 2.

---

## RESEARCH PHASE (Pre-Categories)

Before diving into the 15 categories, spawn 6 parallel research subagents to explore technical approaches. This ensures decisions are grounded in real-world implementations, not assumptions.

### Subagent Missions

| Agent             | Mission                                                       |
| ----------------- | ------------------------------------------------------------- |
| Product Teardown  | Find 2-3 similar products, identify their tech stacks         |
| Open Source Scan  | GitHub repos solving similar problems (stars, activity, arch) |
| Framework Compare | Compare frameworks for this use case (DX, ecosystem, docs)    |
| Cost Projection   | Estimate hosting + services costs at 0/100/1000 users         |
| Architecture      | Recommend patterns suitable for solo-dev/indie context        |
| SaaS Boilerplate  | Find TypeScript starters with auth/payments/billing built-in  |

### Subagent Prompts

Each subagent receives the product requirements summary and executes independently.

**AGENT 1: Product Teardown**
Find 2-3 similar products. Identify tech stack, key arch decisions, what works/doesn't.
Output: Concise bullets with sources.

**AGENT 2: Open Source Scan**
Search GitHub for similar projects. Filter: TypeScript, active (6mo), 100+ stars.
Output: 2-3 repos with arch pattern, dependencies, strengths/limitations. Include links.

**AGENT 3: Framework Compare**
Compare relevant frameworks on: DX, ecosystem, docs, learning curve, community.
Output: Comparison matrix with version numbers.

**AGENT 4: Cost Projection**
Estimate monthly costs at 0/100/1000 users. Include: hosting, database, auth, services.
Output: Cost table per approach. Flag free tiers and limits.

**AGENT 5: Architecture Patterns**
Recommend patterns for solo indie dev context (monolith vs modular, serverless vs traditional, build vs buy).
Output: 2-3 patterns with trade-offs.

**AGENT 6: SaaS Boilerplate**
Detect platform from requirements: [web | mobile | both]
- Web → Find Next.js/React TypeScript starters
- Mobile → Find Expo/React Native TypeScript starters
- Both → Find monorepo starters or compatible pairs
Constraints: Free/OSS only, must have auth + payments.
Output: 2-3 boilerplates with feature checklist + GitHub links.

### Synthesis Format

After all 6 agents return, synthesize findings into this format:

```
═══════════════════════════════════════════════════════════════════════
RESEARCH PHASE COMPLETE
═══════════════════════════════════════════════════════════════════════

RAW FINDINGS SUMMARY:

Product Teardown:
  • [Product 1]: [stack] - [key insight]
  • [Product 2]: [stack] - [key insight]

Open Source:
  • [Repo 1]: [pattern] - [insight]
  • [Repo 2]: [pattern] - [insight]

Frameworks:
  • [Framework comparison summary - 1-2 lines]

Cost Analysis:
  • Cheapest path: [approach] at $X/mo
  • Most expensive: [approach] at $X/mo

Architecture:
  • Recommended pattern: [pattern] - [why]

Boilerplates:
  • [Boilerplate 1]: [features covered] - [link]
  • [Boilerplate 2]: [features covered] - [link]

───────────────────────────────────────────────────────────────────────

5 DISTINCT APPROACHES:

───────────────────────────────────────────────────────────────────────
APPROACH [N]: [Name]
Stack: [Frontend] + [Backend] + [Database] + [Hosting]
Boilerplate: [Name + link] or "None"

✓ Benefits:
  • [Benefit 1]
  • [Benefit 2]

✗ Trade-offs:
  • [Trade-off 1]
  • [Trade-off 2]

Cost: $X/mo at 100 users | Complexity: [Low/Med/High] | Time-to-MVP: X weeks
───────────────────────────────────────────────────────────────────────

(Repeat format for approaches 1-5)

───────────────────────────────────────────────────────────────────────

RECOMMENDATION:

Approach: [Approach X - Name]

Rationale:
[2-3 sentences explaining why this approach fits the user's constraints:
indie dev, cost-conscious, validation phase, TypeScript preference]

Concerns:
[Any trade-offs or risks to be aware of]

───────────────────────────────────────────────────────────────────────

Which approach would you like to proceed with? (Enter 1-5 or describe your own)
```

### After User Selects Approach

1. Create ADR-000 documenting the decision (see ADR template below)
2. Proceed to Category 1: Key Components
3. All subsequent category decisions should align with the selected approach

---
