---
name: reproduce
description: Lightweight SOP for reproducing bugs and proving whether a reported issue can be triggered. Use when Claude needs to reproduce a bug, validate a bug report, capture a repro video or screenshot, and return a clear REPRODUCED/NOT_REPRODUCED/BLOCKED result. When browser-based reproduction is needed, rely on the dogfood skill for browser setup, navigation, and evidence capture.
---

# Reproduce Bug

Use this skill when the goal is to reproduce a reported bug quickly and with low friction.

Keep the scope narrow:

- Prove whether the reported bug can be reproduced.
- Capture the lightest evidence that makes the result clear.
- Return a clear result with repro steps and artifact paths.

Do not use this skill for broad QA, new bug discovery, or root-cause analysis.

## Preflight

Before starting any browser-based reproduction:

- Confirm the `dogfood` skill is available and read it first for browser setup and evidence capture.
- If browser reproduction is needed but `dogfood` is not ready, do not loop on failing browser steps. Return `BLOCKED` with the missing setup or prerequisite.

## Inputs

Collect only the context needed to attempt reproduction:

- bug summary
- expected behavior
- actual behavior
- starting URL, screen, command, or environment
- known repro steps, if any
- account, auth, test data, or feature flag prerequisites

If the bug report is vague, reduce it to one testable repro target before proceeding.

## Modes

Choose exactly one primary mode:

1. `browser-interactive`
   - Use when the bug requires clicks, typing, navigation, async state changes, or a multi-step user journey.
2. `browser-static`
   - Use when the bug is visible on load and a screenshot is enough to prove it.
3. `non-browser`
   - Use when the bug is reproduced more directly through a command, API call, file output, log, or data check.

Prefer the smallest repro path that still proves the bug clearly.

## Workflow

1. Define the repro target.
   - State the exact behavior you are trying to trigger.
   - Keep it to one bug at a time.

2. Map the shortest repro flow.
   - Start from the first meaningful action.
   - End at the exact failing state or at proof that the bug did not occur.
   - Avoid extra setup steps unless they are required to trigger the issue.

3. Attempt reproduction.

   - For `browser-interactive` or `browser-static`, use the `dogfood` skill instead of rebuilding browser repro instructions here.
   - Reuse the smallest part of the `dogfood` workflow needed to reproduce the reported bug.
   - Capture `📸` when a single static proof state is enough.
   - Capture `🎥` when the bug requires interaction or timing proof; prefer one recording for the full sequence.

   - For `non-browser`, run the shortest direct repro path available.
   - Prefer concrete proof: failing output, wrong response, missing file, broken state, or other observable result.

4. Decide the result.

   - `REPRODUCED`: the reported bug was triggered and proven.
   - `NOT_REPRODUCED`: the reported bug did not occur after a reasonable attempt.
   - `BLOCKED`: required auth, data, environment, or tooling is missing.

5. Report the result.

## Evidence Rules

- Match the evidence to the bug.
- Use screenshots for static visible issues.
- Use a single full-sequence video for interaction-heavy repros.
- Never capture secrets, tokens, private user data, or unnecessary personal information.
- If a task directory exists, store artifacts under `_ai/task/{SLUG}/reproduction/` with `screenshots/` and `videos/` subfolders.
- Always include artifact paths when evidence exists.

## Output

Use this exact structure:

```md
## Reproduction Result

- Mode: `browser-interactive|browser-static|non-browser`
- Bug: [short bug summary]
- Repro target: [exact behavior tested]
- Result: `REPRODUCED|NOT_REPRODUCED|BLOCKED`

### Repro Steps

- [short numbered or ordered steps]

### Evidence

- [artifact path or "No artifacts"]

### Notes

- [key failure point, proof point, or blocker]

### Next Action

- [fix bug / refine bug report / unblock environment]
```

## Examples

- `browser-interactive`: Open settings -> toggle notifications -> save -> page resets and loses the new state.
- `browser-static`: Open pricing page -> CTA text is clipped on mobile.
- `non-browser`: Run import command -> command exits successfully but no output file is created.
