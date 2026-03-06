---
name: verification-gate
description: Reusable verification gate for completed work before commit or merge. Use when implementation is done and Claude must prove the task works, verify the main user flow, choose between browser-flow, browser-static, or non-browser validation, and return a PASS/FAIL/BLOCKED verdict with evidence. When browser verification is needed, rely on the agent-browser skill for browser actions, screenshots, and recordings.
---

# Verification Gate

Use this skill after implementation and before commit or merge.

Keep the scope narrow:

- Prove the intended task outcome works.
- Choose the lightest verification mode that creates confidence.
- Return a clear verdict with evidence.

Do not use this skill for exploratory QA or bug hunting. Use `dogfood` for that.

## Inputs

Collect the minimum context needed to verify the work:

- task goal
- acceptance criteria or success definition
- changed behavior or files
- target URL, command, or environment
- auth, seed data, or other prerequisites

If key prerequisites are missing and you cannot verify safely, return `BLOCKED`.

## Modes

Choose exactly one primary mode:

1. `browser-flow`
   - Use for multi-step UI flows, async state transitions, persisted state, uploads, or other behavior that must be proven end to end in the browser.
2. `browser-static`
   - Use for simple render, layout, copy, or visible-state checks where screenshots are enough.
3. `non-browser`
   - Use for backend, CLI, API, data, or other tasks where browser proof adds no value.

Prefer the smallest proof path that still demonstrates real user value.

## Workflow

1. Define the verification objective.
   - State the single main user outcome that must work.
   - Add one lightweight regression check when adjacent behavior could easily break.

2. Map the proof flow.
   - Start from the first meaningful user or system action.
   - End at the success state the user cares about.
   - Avoid padding the flow with irrelevant steps.

3. Execute verification.

   - For `browser-flow` or `browser-static`, use the `agent-browser` skill instead of re-inventing browser steps.
   - Follow the `snapshot -> interact -> re-snapshot` cadence.
   - Use named sessions.
   - When needed, read:
     - `.opencode/skills/agent-browser/references/snapshot-refs.md`
     - `.opencode/skills/agent-browser/references/session-management.md`
     - `.opencode/skills/agent-browser/references/video-recording.md`
   - Use `📸` screenshots for static proof points.
   - Use `🎥` recordings only for multi-step interactions or async transitions that are hard to prove with screenshots alone.

   - For `non-browser`, run the smallest direct proof path available.
   - Prefer assertions tied to user-visible outcomes: command success, API response shape, file creation, persisted data, or other concrete results.

4. Decide the verdict.

   - `PASS`: the main flow completes and the success state is proven.
   - `FAIL`: the flow breaks, the result is wrong, or the outcome cannot be proven.
   - `BLOCKED`: required auth, data, environment, or tooling is missing.

5. Report the result.

## Evidence Rules

- Prove the whole flow, not just the final screen.
- Capture only the evidence needed to support the verdict.
- Never record secrets, tokens, private user data, or unnecessary personal information.
- If a task directory exists, store artifacts under `_ai/task/{SLUG}/verification/` with `screenshots/` and `videos/` subfolders.
- Always include artifact paths in the final report when evidence exists.

## Output

Use this exact structure:

```md
## Verification Result

- Mode: `browser-flow|browser-static|non-browser`
- Objective: [single outcome verified]
- Primary flow: [short description]
- Regression check: [short description or "None"]
- Verdict: `PASS|FAIL|BLOCKED`

### Evidence

- [artifact path or "No artifacts"]

### Notes

- [key proof point, failure point, or blocker]

### Next Action

- [commit / fix issue / unblock environment]
```

## Examples

- `browser-flow`: Select model -> enter prompt -> submit -> generated images appear.
- `browser-static`: Open settings page -> verify new card, copy, and CTA render correctly.
- `non-browser`: Run export command -> confirm output file exists and contains expected records.
