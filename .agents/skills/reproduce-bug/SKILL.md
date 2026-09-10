---
name: reproduce-bug
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
- conditions under which it occurs (environment, data, timing, account), if known
- starting URL, screen, command, or environment
- known repro steps, if any
- account, auth, test data, or feature flag prerequisites

If the bug report is vague, reduce it to one testable repro target before proceeding.

Treat the original report and its attached media as the authority on the symptom (what was seen and when), not as proof of the cause. This skill does not own root cause: cause statements in the report are hypotheses for the owner, never findings to accept. Reuse the report's existing details and media; do not re-interview the reporter for what the report already contains.

## Modes

Choose exactly one primary mode:

1. `browser-interactive`
   - Use when the bug requires clicks, typing, navigation, async state changes, or a multi-step user journey.
2. `browser-static`
   - Use when the bug is visible on load and a screenshot is enough to prove it.
3. `non-browser`
   - Use when the bug is reproduced more directly through a command, API call, file output, log, or data check.
   - iOS user journeys count here: load the `argent` skill and replay the reported entry point as a flow on a simulator or connected iPhone. Save the flow ONLY at `_ai/task/{SLUG}/reproduction/flows/<safe-name>.yaml` (safe name: letters, numbers, `_`, `-`) so `verification-gate` can replay the exact file on the candidate.
   - The flow must assert the initial screen state and the expected behavior (not just that the actions ran) — the reproduction contract in the `argent` skill. Establish that the installed app matches the exact candidate before replay; missing/stale app means build/install via `xcodebuildmcp-cli` first, or `BLOCKED` if provenance cannot be established.
   - The flow result plus `--json` report is the observable proof; mechanical proof (build, logs) stays with `xcodebuildmcp-cli`.

Prefer the smallest repro path that still proves the bug clearly.
## Workflow

1. Define the repro target.
   - State the exact behavior you are trying to trigger.
   - State the falsifier: the observation that distinguishes the reported bug
     from expected behavior.
   - Keep it to one bug at a time.

2. Map the shortest repro flow.
   - Start from the first meaningful action.
   - End at the exact failing state or at proof that the bug did not occur.
   - Avoid extra setup steps unless they are required to trigger the issue.
   - Keep the flow rerunnable as the cheapest faithful before/after check: after a fix, the same entry point should flip the expected/actual contrast without rework.
   - Record that exact command or flow as the reusable smoke check for verification; do not make verification rediscover or broaden it.

3. Run the smallest faithful reproduction.

   - Reproduce through the reported entry point: the screen, command, or flow the reporter actually used. A unit test, a different code path, or a mocked dependency can support a finding but never confirms a real user-flow bug by itself.
   - Prefer user-visible proof first: show what the user actually sees going wrong, then add mechanical proof (logs, command output, file state) to pin the failure. Observable alone can be ambiguous; mechanical alone can miss the user's actual experience.
   - When the requester explicitly asks for a screenshot (or other specific artifact), capture it or return `BLOCKED` naming the missing prerequisite; do not substitute a different artifact silently.
   - Check for existing faithful evidence (logs, screenshots, reports from the actual flow) before spending on a new reproduction; valid existing evidence that matches the reported entry point can avoid a new expensive repro run.
   - Clearly mark controlled evidence (staging data, seeded fixtures, scripted runs); it supports diagnosis but never proves live user behavior on its own.
   - Record observations separately from hypotheses. "The save button produced no network call" is an observation; "the handler is not wired" is a hypothesis. Report only what was observed; leave cause claims to the fix stage.
   - Instrument only enough to locate the first observed divergence. Prefer
     existing evidence and logs, then existing debug flags or tool-level
     inspectors. This skill must not edit application code to add logging. If
     source instrumentation is the smallest useful next probe, return that
     need to the diagnosis or implementation owner.
   - Reuse the smallest part of the `dogfood` workflow needed to reproduce the reported bug.
   - Capture `📸` when a single static proof state is enough.
   - Capture `🎥` when the bug requires interaction or timing proof; prefer one recording for the full sequence.

   - For `non-browser`, run the shortest direct repro path available.
   - Prefer concrete proof: failing output, wrong response, missing file, broken state, or other observable result.

4. Spend evidence only while it changes the decision.

   - Principle: optimize for the first trustworthy result, not a fixed number
     of attempts.
   - Heuristic: continue only when a specific question remains and the next
     probe adds a new signal that could change the result at proportionate cost
     and risk.
   - Before another probe, be able to state the unresolved question, the new
     signal, and how that signal changes the decision. If any part is missing,
     stop with the result the current evidence supports.
   - Do not repeat an unchanged blocked or failed setup. Repetition is useful
     when repetition is itself the probe, such as a race, timing failure, or
     intermittent report; state the observation window and stopping condition.
   - Example: one failing dark-mode toggle can prove a deterministic bug. A
     reported race can justify repeated runs across its relevant timing window.
     Repeating the same unavailable login adds no information.

5. Decide the result and exit.

   - `REPRODUCED`: the reported bug was triggered and proven.
   - `NOT_REPRODUCED`: the reported bug did not occur within the stated
     conditions and evidence budget; report that coverage without claiming the
     bug cannot occur.
   - `BLOCKED`: required auth, data, environment, or tooling is missing.
   - Exit when the evidence supports a result, no discriminating probe remains,
     a prerequisite is blocked, or further work is disproportionate to the
     unresolved question.

6. Report the result.

## Evidence Rules

- Match the evidence to the bug.
- Prefer cheap user-observable proof (what the user sees) plus mechanical proof (logs, command output, file state) together; observable alone can be ambiguous, mechanical alone can miss the user's actual experience.
- Use screenshots for static visible issues.
- Use a single full-sequence video for interaction-heavy repros.
- Never capture secrets, tokens, private user data, or unnecessary personal information.
- If a task directory exists, store artifacts under `_ai/task/{SLUG}/reproduction/` with `screenshots/` and `videos/` subfolders.
- For iOS flow reproduction, the replayable flow itself is durable evidence: keep it at `_ai/task/{SLUG}/reproduction/flows/<safe-name>.yaml` alongside the other artifacts.
- Always include artifact paths when evidence exists.

## Output

Use this exact structure:

```md
## Reproduction Result

- Mode: `browser-interactive|browser-static|non-browser`
- Bug: [short bug summary]
- Repro target: [exact behavior tested]
- Falsifier: [observation that distinguishes the bug from expected behavior]
- Result: `REPRODUCED|NOT_REPRODUCED|BLOCKED`
- Reusable smoke: [exact command or flow to rerun after a fix, or "Unavailable — [reason]"]
- Checks run: [concise list of probes and any observation window]

### Repro Steps

- [short numbered or ordered steps]

### Evidence

- [artifact path or "No artifacts"]

### Notes

- Observed boundary: [where expected and actual behavior first diverged, or "Unknown"]
- Why another probe was or was not warranted: [unresolved question and new signal, or "Result already decisive"]
- [key proof point or blocker; observations only, kept separate from any cause hypothesis]

### Next Action

- [fix bug / refine bug report / unblock environment / one diagnostic question to owner if cause is unclear]
```

## Examples

- `browser-interactive`: Open settings -> toggle notifications -> save -> page resets and loses the new state.
- `browser-static`: Open pricing page -> CTA text is clipped on mobile.
- `non-browser`: Run import command -> command exits successfully but no output file is created.
- `non-browser` (iOS flow): Launch app -> open settings -> toggle notifications -> save -> toggle reverts instead of persisting.
