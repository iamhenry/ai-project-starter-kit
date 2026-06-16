---
name: verification-gate
description: Reusable verification gate for completed work before commit or merge. Use when implementation is done and Claude must prove the task works, verify the main user flow, route verification by platform, and return a PASS/FAIL/BLOCKED verdict with evidence. Web and mobile-web verification uses agent-browser. iOS and macOS verification uses xcodebuildmcp-cli.
---

# Verification Gate

Use this skill after implementation and after `code-quality-gate` returns `APPROVE_CODE`, before commit or merge.

Keep the scope narrow:

- Prove the intended task outcome works.
- Choose the lightest platform route that creates confidence.
- Return a clear verdict with evidence.

Do not use this skill for exploratory QA or bug hunting. Use `dogfood` for that.

## Inputs

Collect the minimum context needed to verify the work:

`ISSUE_DIR` is the artifact directory created by `gather-context` for the current pipeline run.

- `plan.md` Verification Target:
  - Platform: `web|mobile-web|ios|macos|non-ui`
  - Objective: single outcome to prove
  - Primary Flow: shortest realistic proof path
  - Regression Check: one adjacent behavior to protect, or `None`
  - Evidence Required: artifact, command output, API response, file result, or `None`
  - Pass Criteria: concrete success condition
  - Blocked Conditions: known missing auth, data, environment, device, service, or tooling
- changed behavior or files
- target URL, command, or environment
- auth, seed data, or other prerequisites
- code-quality-gate result: `APPROVE_CODE`

If key prerequisites are missing and you cannot verify safely, return `BLOCKED`.

If the code-quality-gate result is missing, `REVISE_CODE`, or `ASK_USER`, return `BLOCKED` and do not run platform QA.

`plan.md` owns what to prove. This skill owns how to prove it by choosing the platform route and smallest proof path.

## Platform Routes

Choose exactly one primary platform route:

1. `web`
   - Use `agent-browser` for desktop browser UI flows, visible states, screenshots, and recordings.
2. `mobile-web`
   - Use `agent-browser` with a mobile viewport/device profile for responsive browser UI flows and visible states.
3. `ios`
   - Use `xcodebuildmcp-cli` for simulator/device build, launch, UI, and test verification.
4. `macos`
   - Use `xcodebuildmcp-cli` for macOS app build, launch, UI, and test verification.
5. `non-ui`
   - Use direct tests, build commands, API calls, CLI checks, data checks, or file assertions.

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

   - For `web` or `mobile-web`, use `agent-browser` instead of re-inventing browser steps.
   - Before browser commands, load `agent-browser` and follow its own CLI-served setup and usage guidance.
   - Follow the `snapshot -> interact -> re-snapshot` cadence.
   - Use named sessions.
   - Use screenshots for static proof points.
   - Use recordings only for multi-step interactions or async transitions that are hard to prove with screenshots alone.

   - For `ios` or `macos`, use `xcodebuildmcp-cli`.
   - First verify the CLI exists.
   - Use help-first discovery before commands: inspect available commands/options instead of relying on stale recipes.
   - Keep execution minimal: choose the smallest build, test, launch, simulator, or UI check that proves the Verification Target.
   - If `xcodebuildmcp-cli` is missing or the required project/device/runtime is unavailable, return `BLOCKED` with the missing prerequisite.

   - For `non-ui`, run the smallest direct proof path available.
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
- If `ISSUE_DIR` exists, store artifacts under `{ISSUE_DIR}/verification/` with `screenshots/` and `videos/` subfolders.
- Always include artifact paths in the final report when evidence exists.

### Screenshot Hygiene

- Capture the smallest app-owned proof area that supports the verdict, not the full desktop.
- For `web` and `mobile-web`, prefer the browser viewport.
- For traditional `macos` apps, prefer the app window or the active sheet/modal bounds.
- For menu bar apps, prefer the opened popover, panel, or menu bounds, and prefer deterministic QA hooks or launch flags over raw status-item clicks when available.
- If bounded capture is unavailable, crop tightly, close unrelated windows first, and retake or delete artifacts that include private desktop content.
- If only full-desktop capture is possible and it would expose private content, return `BLOCKED` instead of saving the artifact.

### Artifact Cleanup

- Treat runtime logs as temporary evidence unless the plan explicitly requires them.
- Before returning `PASS`, remove or leave untracked noisy logs that may include local paths, hostnames, process IDs, or user/system details.
- Preserve durable proof artifacts only: cropped screenshots, sanitized summaries, command pass/fail excerpts, or explicitly required files.
- If logs must be kept, sanitize them first and mention why they are required.

## Output

Use this exact structure:

```md
## Verification Result

- Platform: `web|mobile-web|ios|macos|non-ui`
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

- `web`: Select model -> enter prompt -> submit -> generated images appear.
- `mobile-web`: Open settings on mobile viewport -> verify new card, copy, and CTA render correctly.
- `ios`: Build and launch app -> complete primary flow in simulator -> success state appears.
- `macos`: Build and launch app -> complete primary flow -> success state appears.
- `non-ui`: Run export command -> confirm output file exists and contains expected records.
