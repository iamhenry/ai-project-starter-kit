---
description: File detailed Beads epics and issues from a plan
argument-hint: <plan-description-or-context>
---

# File Beads Epics and Issues from Plan

You are tasked with converting a plan into a comprehensive set of Beads epics and issues. Follow these steps carefully:

## Step 1: Understand the Plan

First, review the plan context provided: `$ARGUMENTS`

If no specific plan is provided, ask the user to share the plan or point to a planning document.

## Step 2: Analyze and Structure

Before filing any issues, analyze the plan for:

1. **Major workstreams** - These become epics
2. **Individual tasks** - These become issues under epics
3. **Dependencies** - What must complete before other work can start?
4. **Parallelization opportunities** - What can be worked on simultaneously?
5. **Technical risks** - What needs spikes or investigation first?

## Step 3: File Epics First

Create epics for major workstreams using:

```bash
bd create "Epic: <title>" -t epic -p <priority> --json
```

Epics should:

- Have clear, descriptive titles
- Include acceptance criteria in the description
- Be scoped to deliverable milestones
- **Reference the source plan** as single source of truth
- **List relevant ADRs** (architectural decision records)
- **Define out of scope** to prevent scope creep

### Epic Description Template

```bash
bd create "Epic: <title>" -t epic -p <priority> \
  --description "Brief summary of the epic goal.

SOURCE OF TRUTH: <path/to/plan.md> - contains code snippets, ADRs, error handling, and acceptance tests.

KEY ADRs:
- ADR-1: <decision summary>
- ADR-2: <decision summary>

OUT OF SCOPE: <list items explicitly excluded>" \
  --json
```

## Step 4: File Detailed Issues

For each epic, create child issues with FULL CONTEXT using `--description` and `--acceptance` flags:

```bash
bd create "<task title>" -t <type> -p <priority> --deps <parent-epic-id> \
  --description "<what to do, where, and how>" \
  --acceptance "<specific done criteria>" \
  --json
```

### CRITICAL: Verbose, Context-Rich Beads

Sparse beads (title-only) are USELESS for subagents. Each issue MUST be VERBOSE and include:

- **Clear title** - Action-oriented (e.g., "Implement X", "Add Y", "Configure Z")
- **`--description`** - REQUIRED. Include ALL of the following:
  - File path(s) to modify (e.g., "File: src/auth/handler.ts")
  - Line numbers if known (e.g., "lines 59-86")
  - **Current state** - What exists now, how it works before this change
  - **Full code snippet** - Copy the implementation example from the plan
  - Code patterns to follow (e.g., "Pattern: similar to createX at file.ts:100")
  - Relevant ADRs or architectural decisions (e.g., "ADR-1: Stripe as source of truth")
  - **Constraints** - Technical limits, compatibility requirements, performance targets
  - **Error handling notes** - What happens when things fail
  - **Gotchas** - Non-obvious details that could cause bugs
  - User story reference if available (e.g., "US-PAY01")
  - Plan cross-reference (e.g., "CODE EXAMPLE: see plan.md Task 1.2")
- **`--acceptance`** - REQUIRED. Specific, testable criteria:
  - What behavior should exist after completion
  - What should NOT happen (edge cases)
  - How to verify it works
- **`--deps`** - Link to blocking issues with `--deps bd-X,bd-Y`

### Example: Good vs Bad Beads

**BAD (sparse, useless):**

```bash
bd create "Add admin bypass" -t task -p 1 --deps bd-epic --json
```

**GOOD (verbose, actionable with code snippet):**

```bash
bd create "Add ADMIN_EMAILS to environment config" -t task -p 1 --deps bd-epic \
  --description "File: src/config/env.ts. Add ADMIN_EMAILS export and isAdminEmail helper. ADR-3: Admin bypass via environment variable.

IMPLEMENTATION:
\`\`\`typescript
export const ADMIN_EMAILS =
  process.env.ADMIN_EMAILS?.split(',').map((e) => e.trim().toLowerCase()) ?? [];

export function isAdminEmail(email: string): boolean {
  return ADMIN_EMAILS.includes(email.toLowerCase());
}
\`\`\`

PATTERN: Mirror existing env exports in same file.
CODE EXAMPLE: see plan.md Task 1.1" \
  --acceptance "ADMIN_EMAILS exported as string[]. isAdminEmail() helper exists and works case-insensitively. Handles undefined env var gracefully (empty array)." \
  --json
```

**GOOD (with error handling and gotchas):**

```bash
bd create "Update webhook to send welcome email" -t task -p 1 --deps bd-email \
  --description "File: src/webhooks/stripe.ts (lines 68-117). ADR-4: Do NOT create user here.

IMPLEMENTATION:
\`\`\`typescript
if (!session.metadata?.userId) {
  const email = session.customer_details?.email;
  if (email) {
    await sendWelcomeEmail({ to: email, loginUrl: '/login' });
  }
}
\`\`\`

GOTCHA: Use session.customer_details.email NOT session.customer_email - the latter may be undefined for guest checkouts.

ERROR HANDLING: If email send fails, log error and continue - user can still request OTP manually.

CODE EXAMPLE: see plan.md Task 1.4" \
  --acceptance "Guest checkout triggers welcome email. Email failure logged but doesn't break flow. Existing auth flow unchanged." \
  --json
```

## Step 5: Map Dependencies Carefully

For each issue, consider:

- Does this depend on another issue completing first?
- Can this be worked on in parallel with siblings?
- Are there cross-epic dependencies?

Use `--deps bd-X,bd-Y` for multiple dependencies.

## Step 6: Set Priorities Thoughtfully

- `0` - Critical path blockers, security issues
- `1` - Core functionality, high business value
- `2` - Standard work items (default)
- `3` - Nice-to-haves, polish
- `4` - Backlog, future considerations

## Step 7: Create Beads Sequentially

**IMPORTANT:** Create beads ONE AT A TIME to avoid database lock errors. Do NOT batch `bd create` calls in parallel.

```bash
# Good: Sequential creation
bd create "Task 1" ... --json
bd create "Task 2" ... --json

# Bad: Parallel batch (causes DB locks)
# batch([bd create "Task 1", bd create "Task 2"])
```

## Step 8: Verify the Graph

After filing all issues, run:

```bash
bd list --json
bd ready --json
```

Verify:

- All epics have child issues
- Dependencies form a valid DAG (no cycles)
- Ready work exists (some issues have no blockers)
- Priorities make sense for execution order

## Step 9: Unblock Child Tasks

Child tasks depend on their parent epic. To make children "ready":

```bash
# Mark epic as completed (preferred) or in_progress
bd update <epic-id> --status completed --json

# Now children with only epic as dependency become ready
bd ready --json
```

## Output Format

After completing, provide:

1. Summary of epics created
2. Summary of issues per epic (with IDs for reference)
3. Dependency graph overview (what unblocks what)
4. Suggested starting points (ready issues)
5. Parallelization opportunities (independent tracks that can run simultaneously)

## Description Content Guidelines

Extract these from the source plan for each bead's `--description`:

| Content Type      | Example                                                 | Required? |
| ----------------- | ------------------------------------------------------- | --------- |
| File path         | `File: src/auth/handler.ts`                             | YES       |
| Line range        | `(lines 59-86)`                                         | If known  |
| Current state     | `Currently webhook only handles authenticated users`    | If exists |
| Code snippet      | Full implementation code block from plan                | YES       |
| Pattern reference | `Pattern: similar to createX at file.ts:100-140`        | YES       |
| ADR/Decision      | `ADR-1: Stripe is source of truth, no temp tables`      | If exists |
| Constraints       | `Must maintain <500ms response, compatible with v2 API` | If exists |
| Gotchas           | `Use session.customer_details.email NOT customer_email` | If exists |
| Error handling    | `If email fails, log and continue - user can retry`     | If exists |
| User story        | `US-PAY01: Guest pays before account creation`          | If exists |
| Plan cross-ref    | `CODE EXAMPLE: see plan.md Task 1.2`                    | YES       |

## Why Verbose Beads Matter

Subagents executing beads have NO access to the original plan context. Everything they need must be IN the bead:

- **Code snippets** prevent subagents from inventing wrong implementations
- **Gotchas** prevent subtle bugs that waste debugging time
- **Error handling notes** ensure graceful degradation is implemented
- **ADR references** ensure architectural decisions are followed
- **Plan cross-references** allow human review of source context

## Common Mistakes to Avoid

- **Sparse beads**: Title-only beads lack context for autonomous execution
- **Missing code snippets**: Subagents will invent wrong implementations without examples
- **Missing file paths**: Subagents waste time searching for where to edit
- **Vague acceptance**: "It works" vs "Returns 401 for invalid tokens"
- **Missing gotchas**: Subtle bugs get introduced (e.g., wrong field name)
- **Missing error handling**: Subagents skip graceful degradation
- **No plan reference**: Loses traceability to source of truth
- **Parallel creation**: Causes DB lock errors - always create sequentially
- **Forgetting to unblock**: Epic must be completed/in_progress for children to be ready
