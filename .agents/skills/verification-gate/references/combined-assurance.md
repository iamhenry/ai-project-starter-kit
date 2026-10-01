# Verification Gate: Combined Low-Risk Assurance

This skill owns the eligibility contract for `assurance: combined-low-risk`. Use the combined route only when it is explicitly selected and every condition holds:

- The change is narrow and limited to docs or instructions, comments or copy, non-executable metadata, or a truly mechanical edit with no new behavior.
- A decisive existing check can establish the requested outcome.
- Generic configuration is not treated as low risk automatically.
- The change does not involve auth, security, privacy, data or schema changes, migrations, dependencies, public interfaces, new or changed runtime behavior, build/release/deploy infrastructure, destructive operations, or broad/coupled changes.

## How the run differs

One fresh `qa` agent, separate from implementation, performs a quality precheck first and then decisive verification, and emits one result. No prior `APPROVE_CODE` and no separate reviewer is required, and no separate code-quality result is created.

Before proof, the agent inspects the exact diff for scope, correctness, simplicity, style and maintainability, sensitive content and security, and continued eligibility.

- A concrete defect returns `FAIL`.
- Uncertainty, a need for deeper judgment, or any unmet or uncertain eligibility condition returns `BLOCKED` before proof, and the caller uses the standard separate `code-quality-gate` then `verification-gate` route.
- Record the precheck and the verification evidence in the single result.

If fresh separation from implementation is unavailable, return `BLOCKED`.
