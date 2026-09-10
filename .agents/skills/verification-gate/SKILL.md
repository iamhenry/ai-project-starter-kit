---
name: verification-gate
description: Reusable verification gate for completed work before commit or merge. Use when implementation is done and Claude must prove the task works, verify the main user flow, route verification by platform, and return a PASS/FAIL/BLOCKED verdict with evidence. Web and mobile-web verification uses agent-browser. iOS and macOS verification uses xcodebuildmcp-cli, with argent flow replay for iOS user-flow proof.
---

# Verification Gate

Use this skill for delivery acceptance after implementation and `code-quality-gate` approval, or for an explicitly focused request to verify existing behavior. Focused proof is not delivery approval.

Run acceptance in a fresh verifier session, separate from implementation and code-quality review, including for small changes and standalone calls. Invoking this skill in the implementer's session does not supply independence. If that separation is unavailable, return `BLOCKED`; fresh context reduces self-confirmation bias, not all bias. A focused verification request stops at its verdict and does not authorize fixes, commits, or publication.

## Mode Dispatch

- The default, when `mode` is omitted, is the existing issue mode below. Any mode other than the explicit `mode: isa` request uses the existing issue-mode contract; do not auto-detect ISA inputs.
- When the caller explicitly supplies `mode: isa`, use the alternate contract in `references/isa-mode.md`. Do not require, read, create, or infer `{ISSUE_DIR}/plan.md` for that invocation.
- The two modes have separate inputs and output contracts. Do not mix issue artifacts into ISA verification or ISA inputs into issue verification.
- Mechanical and Observable lanes below apply to issue mode only. ISA mode keeps declared leaf probes in `references/isa-mode.md`.

Keep the scope narrow:

- Prove the intended task outcome works.
- Choose the lightest platform route that creates confidence.
- Return a clear verdict with evidence.
- Optimize for the first trustworthy signal, not the most verification activity.

Do not use this skill for exploratory QA or bug hunting. Use `dogfood` for that.

## Inputs

Collect the minimum context needed to verify the work:

`ISSUE_DIR` is the artifact directory created by `gather-context` for the current pipeline run.

For standalone calls, accept the same Verification Target fields below directly with approved scope, exact candidate identity, and an authorized evidence directory; no pipeline plan is required. References to `plan.md` below mean that supplied target. Distinguish the requested endpoint explicitly: focused verification of existing behavior does not require an unassigned code-quality stage; delivery acceptance, including standalone delivery acceptance, requires `APPROVE_CODE` and both independent gates. Missing pipeline inputs never authorize switching to focused verification; route them to their owners.

- `plan.md` Verification Target:
  - Platform: `web|mobile-web|ios|macos|non-ui`
  - Objective: single outcome to prove
  - Falsifier: observation that would disprove the Objective
  - Primary Flow: shortest realistic proof path
  - Regression Check: one adjacent behavior to protect, or `None`
  - Mechanical: named command(s) plus expected exit code or output
  - Observable: retained evidence path, or `n/a` for `non-ui`
  - Pass Criteria: concrete success condition
  - Blocked Conditions: known missing auth, data, environment, device, service, or tooling
- changed behavior or files
- target URL, command, or environment
- auth, seed data, or other prerequisites
- for bug tasks: the reproduction result and evidence paths from `reproduce-bug`, supplying the faithful smoke to reuse
- for delivery acceptance: code-quality-gate result `APPROVE_CODE`

If key prerequisites are missing, use only the bounded recovery below when safe and authorized; otherwise return `BLOCKED` naming the prerequisite owner and unlock condition, not a code defect or a demand that the user perform routine setup.

If Mechanical is missing from the target, return `BLOCKED` naming the missing command and target owner (plan owner for pipeline calls, supplied-target owner for standalone calls). Do not invent a command or require a standalone caller to create a plan.

For delivery acceptance, if the code-quality-gate result is missing, `REVISE_CODE`, or `ASK_USER`, return `BLOCKED` and do not run final acceptance QA. Exception: when dispatched as a combined small-task gate (SMALL scope, one fresh subagent performing review then verification and returning both verdicts), proceed after the review verdict is `APPROVE_CODE` within the same session. For explicitly focused verification, proceed without that stage only within the supplied target and authority, retaining fresh verifier independence; state in Notes that the verdict proves only the requested behavior and does not imply delivery approval. Neither route authorizes unsafe live installation or mutation.

`plan.md` owns what to prove. This skill owns how to prove it by choosing the platform route and smallest proof path.

This skill must not edit application code, tests, or scorers. Re-run the named Mechanical command; do not rewrite it.

## Platform Routes

Choose exactly one primary platform route:

1. `web`
   - Use `agent-browser` for desktop browser UI flows, visible states, screenshots, and recordings.
2. `mobile-web`
   - Use `agent-browser` with a mobile viewport/device profile for responsive browser UI flows and visible states.
3. `ios`
   - Use `xcodebuildmcp-cli` for build and mechanical proof; it equals mechanical proof for iOS.
   - For user-flow (observable) proof: replay the exact reproduction flow with `argent` when one exists, otherwise the XcodeBuildMCP UI check.
4. `macos`
   - Use `xcodebuildmcp-cli` for macOS app build, launch, UI, and test verification.
5. `non-ui`
   - Use direct tests, build commands, API calls, CLI checks, data checks, or file assertions.

Prefer the smallest proof path that still demonstrates real user value.

Prefer the actual affected surface when safe and authorized. Before building a substitute, compare its setup cost and evidential value with resolving the concrete prerequisite for the real surface. A replica can omit the very integration under test; it cannot silently replace required real-flow proof. If proof infrastructure would exceed the change itself, reconsider the route before adding it: reuse existing checks or a direct preview, or return the precise blocker. Scale depth to risk and uncertainty, not ceremony. A static content/diff check can prove an instruction-only change; it cannot prove a changed UI renders correctly.

## Workflow

1. Define the verification target.
   - State the single main user outcome that must work.
   - State its falsifier: the observation that would show the outcome failed.
   - Add one lightweight regression check when adjacent behavior could easily break.

2. Map the proof flow.
   - Start from the first meaningful user or system action.
   - End at the success state the user cares about.
   - Avoid padding the flow with irrelevant steps.

3. Establish the exact candidate and prerequisites.
   - Confirm that the runtime subject matches the candidate commit, or the base
     commit plus exact uncommitted diff, before accepting evidence.
   - Recover a missing prerequisite only while each recovery step changes the
     available evidence and remains narrow and proportionate. Never repeat an
     unchanged blocked setup. If no useful recovery remains, return `BLOCKED`
     with the prerequisite owner and unlock condition.

4. Execute the tight proof loop.

    - Principle: optimize for the first trustworthy signal, then stop as soon
      as every declared claim is proven.
    - Heuristic: run whichever declared lane can produce the cheapest decisive
      signal first. Mechanical often rejects a broken candidate fastest; an
      already-running actual product can make the Primary Flow faster. A failed
      decisive lane returns `FAIL` without spending on the companion lane. A
      passing first lane does not waive any other lane required for `PASS`.
    - Inline rule: execute the plan-named Mechanical command and quote its raw
      output. Do not paraphrase pass/fail or replace the command.
    - Inline rule: UI and real-integration `PASS` requires operating the actual
      affected product or integration through the Primary Flow on the exact
      candidate. Tests, terminals, CI screens, logs, source inspection, and
      screenshots of those materials are Mechanical evidence only. They never
      satisfy Observable.
    - Use the selected platform route for Observable. `PASS` requires both
      Mechanical and Observable when both are declared.
    - Proof must match the reported flow for the exact candidate being
      accepted: the observed evidence comes from the primary flow on the
      candidate commit (or base commit plus exact uncommitted diff), not a
      different path, an earlier candidate, or implementer claims alone.
    - For bug fixes, the primary flow is the same faithful reproduction smoke
       that triggered the original bug (from the reproduction result), now
       expected to pass on the candidate. Reuse it before/after rather than
       inventing a new flow. If the reproduction evidence does not identify a
       rerunnable faithful smoke, return `BLOCKED` instead of substituting a
       broader flow.
    - When the plan's Regression Check is not `None`, run that one regression.
       Add another counterexample only when it covers a distinct named failure
       mode that remains unresolved; do not expand into unrelated QA.

    - Spend more evidence only while it changes the decision. Before another
      probe, state the unresolved question, the new signal, how it could change
      the verdict, and its added cost or risk. Continue only when all four are
      concrete and proportionate. If no discriminating probe remains, return
      `BLOCKED` with the missing signal rather than accumulating activity.
    - Repetition is valid when repetition is itself the probe, such as timing,
      ordering, or intermittency. State its observation window and stopping
      condition. Otherwise, do not repeat an unchanged check.
    - Instrument with existing evidence and logs first, then existing debug
      flags or tool-level inspectors. This skill must not edit the candidate to
      add logging. If source instrumentation is necessary, return the need to
      diagnosis or implementation and verify the resulting candidate afresh.
    - Example: toggle dark mode once to prove the visible change. Reload only
      when persistence is part of the Objective. For a chunk-ordering bug, add
      a boundary case only when the normal smoke never crosses that boundary.

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

    - `macos` observable proof is always the XcodeBuildMCP UI check.
    - `ios` without a reproduction flow: observable proof is the smallest XcodeBuildMCP UI check that proves the Verification Target. Do not author a flow during verification.
    - `ios` with a reproduction flow from `reproduce-bug` (stored at
      `_ai/task/{SLUG}/reproduction/flows/<safe-name>.yaml`): load `argent`
      and replay that exact file on the exact candidate with `argent flow run
      <path.yaml> --device <id> --platform ios --json`, selecting a device per
      the `argent` skill. Establish candidate provenance for the installed app
      before replay (the `argent` skill's provenance rule); a stale or
      unprovable install is not a valid replay target. A pass on the flow that
      originally triggered the bug is the strongest user-flow proof the fix
      works; a pass from any other path does not substitute for it.
    - A flow replay failing for environment reasons (device missing, runner
      build/signing errors) is `BLOCKED`, not `FAIL`; a flow that runs and
      reports a failed step is `FAIL`.
    - Keep the device selection and report from the replay in the result notes.

    - For `non-ui`, Mechanical is the proof path. Observable is `n/a`.
    - Prefer assertions tied to user-visible outcomes: command success, API response shape, file creation, persisted data, or other concrete results.

5. Decide the verdict and exit.

    - `PASS`: Mechanical passed, and Observable is proven when it is not `n/a`.
    - `FAIL`: under valid prerequisites and a clear target, Mechanical failed, the flow breaks, the result is wrong, cited files are missing, or the evidence does not prove the outcome. Distinguish code defects from evidence gaps in Notes and route to the actual owner.
    - `BLOCKED`: required auth, data, environment, tooling, or a discriminating verification target is missing. A required screenshot or artifact that was explicitly requested but cannot be captured is `BLOCKED` (missing prerequisite), not `PASS`; if the plan declares it Observable and it is absent, that is `FAIL` per the file-existence rule.

    - Exit when the required lanes prove the target, a valid lane disproves it,
      a prerequisite is blocked, no discriminating probe remains, or further
      work is disproportionate to the unresolved risk.

6. Report the result.
    - Write `{ISSUE_DIR}/verification/result.md` first (or `result.md` in the authorized standalone evidence directory).
   - Run `test -f` on that file and every cited Observable path. Missing file = `FAIL`, not `PASS`.
   - Do not return `PASS` from chat alone.

## Evidence Rules

- Prove the whole flow, not just the final screen. Evidence must distinguish the claimed outcome from its likely false positive; successful commands or plausible screenshots alone may not do that. If the target itself cannot discriminate success, return `BLOCKED` for plan-owner clarification rather than inventing acceptance or editing code.
- For UI work, Observable evidence must show the app-owned result produced by
  the Primary Flow. A terminal, test runner, CI page, log viewer, source file,
  or screenshot of any of them is invalid Observable evidence even when it
  shows a passing result.
- A screenshot proves a static visible state. Use a short recording or the
  smallest ordered set of proof states when the claim depends on interaction,
  transition, persistence, timing, or ordering.
- Independently establish the candidate and assess the proof rather than accepting implementer claims. After corrections, identify affected claims and required rechecks. Reuse unaffected Observable evidence only with an explicit explanation of why changed files and conditions do not invalidate it; rerun affected proof on the current candidate. Coupled, uncertain, or consequential changes can warrant broader or full fresh verification. Mechanical is still rerun as required above.
- Capture only the evidence needed to support the verdict.
- Never record secrets, tokens, private user data, or unnecessary personal information.
- If any temporary diagnostic instrumentation was added during reproduction or
  diagnosis, it must be removed from the candidate or explicitly justified in
  Notes before `PASS`. Inspect the candidate diff and retained evidence for
  secrets, personal data, or full prompt bodies; if found, that is `FAIL` until
  sanitized.
- Raw snapshots, JSON, measurements, logs, base64, and duplicate media default
  to the OS temp area and are not durable unless the plan or leaf explicitly
  requires them. If `ISSUE_DIR` exists, store only
  retained evidence under `{ISSUE_DIR}/verification/` with `screenshots/` and
  `videos/` subfolders.
- Retain the minimum user-observable evidence needed by the claim: screenshots
  by default; a short video only when motion or lifecycle cannot be shown
  otherwise. Do not create evidence theater or retain artifacts that add no
  proof.
- Always include artifact paths in the final report when evidence exists.
- `"No artifacts"` is allowed only when Observable is `n/a`. If Observable names a path, that file must exist or the verdict is `FAIL`.

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

Return failed criteria, evidence/prerequisite owner, and required rechecks in Notes. For delivery, the caller routes defects through implementation and fresh code-quality review before acceptance; proof gaps return here without unrelated edits. Focused verification reports findings and stops, without assigning fixes or implying delivery approval. After 2 `FAIL` verdicts, including evidence-only failures, stop with `EXHAUSTED`; carry prior verdicts across dispatches. `BLOCKED` does not redispatch itself against an unchanged prerequisite. Never use exhaustion to waive acceptance.

Use this exact structure:

```md
## Verification Result

- Platform: `web|mobile-web|ios|macos|non-ui`
- Objective: [single outcome verified]
- Falsifier: [observation that would disprove the Objective]
- Primary flow: [short description]
- Regression check: [short description or "None"]
- Mechanical: [command] → [exit code / quoted raw excerpt]
- Observable: [artifact path or `n/a`]
- Checks run: [concise list, including any observation window]
- Verdict: `PASS|FAIL|BLOCKED`

### Evidence

- [artifact path; `"No artifacts"` only when Observable is `n/a`]
- Report: [pipeline `{ISSUE_DIR}/verification/result.md` or authorized standalone `result.md` path]

### Notes

- [key proof point, failure point, or blocker]
- Why another probe was or was not warranted: [unresolved question and new signal, or "Result already decisive"]

### Risk

- [anything not verified, or "None within the declared target"]

### Next Action

- [commit / fix issue / unblock environment]
```

## Examples

- `web`: Select model -> enter prompt -> submit -> generated images appear.
- `mobile-web`: Open settings on mobile viewport -> verify new card, copy, and CTA render correctly.
- `ios`: Build and launch app -> complete primary flow in simulator -> success state appears.
- `macos`: Build and launch app -> complete primary flow -> success state appears.
- `non-ui`: Run export command -> confirm output file exists and contains expected records.
