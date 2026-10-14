---
name: bugging-out
description: Pick the right playbook to find and fix a bug, sized to how hard it is. Use when a bug is hard to pin down, a fix did not hold, a check keeps failing, or someone says "use bugging-out", "we can't find this bug", or "squash this bug". Thin router over playbooks; reproduce-bug owns reproduction and verification-gate owns final proof.
---

# Bugging Out

Find the cause from evidence, then fix it once. Pick a playbook by the bug's shape; step up when it stalls.

## Pick a playbook

| Bug shape | Run |
|---|---|
| Error or stack trace names the line | Fast lane: read it, fix it, prove it. No playbook. |
| Cause unclear, several suspects | [hypothesis-funnel](playbooks/hypothesis-funnel.md) |
| Fails somewhere between layers, or only sometimes | [trace-boundaries](playbooks/trace-boundaries.md) |
| "It used to work" or "it works over there" | [compare-good-bad](playbooks/compare-good-bad.md) |
| Failing spot found; fix keeps treating symptoms | [five-whys](playbooks/five-whys.md) |
| Before any fix that is not the fast lane | [failing-check-first](playbooks/failing-check-first.md) |

Usual order: see the bug (`reproduce-bug`) → funnel or compare → trace → five whys → failing check → fix → prove (`verification-gate`).

## Rules

- Keep a short bug note: each hypothesis, the probe, what it showed, and `confirmed`, `refuted`, or `guess`.
- Never call a guess a cause. Say "probable, not proven" until a probe confirms it.
- Change one thing per probe. Remove temporary logs when done.
- Ask the user before fixing only when the bug is hard or the fix is risky or hard to undo.

## When stuck

After 2-3 rounds with no new evidence, do not repeat the playbook. Switch to the next one. Or explain the code path step by step in writing, get a `second-opinion`, or hand the bug note to a fresh agent. If still stuck, park it with what was ruled out and what would unblock it.
