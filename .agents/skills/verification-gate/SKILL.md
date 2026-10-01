---
name: verification-gate
description: Independent verification gate for completed work before commit or merge. Use when implementation is done and a fresh agent must prove the work functions for its real user, verify the main flow, and return a PASS/FAIL/BLOCKED verdict with evidence. Supports the explicitly selected low-risk combined assurance route. Platform detail (web, mobile-web, desktop, ios, android, macos, non-ui) lives in platforms/.
---

# Verification Gate

## Purpose

An agent that did the work tends to say it is done. This gate runs in a fresh agent that does not trust that claim. It proves, on the real surface and the exact candidate, whether the work functions for its real user. It returns `PASS` (proceed), `FAIL` (ask for revision), or `BLOCKED` (a named blocker). Keep it cheap and proportional: one claim, one decisive observation, then stop.

This skill does not edit application code, tests, or scorers, and it is not exploratory QA (use `dogfood`).

Use it for delivery acceptance after implementation and `code-quality-gate` approval, for an explicitly selected `assurance: combined-low-risk` change (`references/combined-assurance.md`, which owns the eligibility contract), or for an explicitly focused request to verify existing behavior. Focused proof is not delivery approval; it stops at its verdict and authorizes no fixes, commits, or publication. A focused run proceeds without the code-quality stage within the supplied target and authority, keeps a fresh verifier, and states in Notes that the verdict proves only the requested behavior.

**Independence.** For standard delivery, run acceptance in a fresh `qa` agent, separate from implementation and from code-quality review. The caller must use exact `subagent_type: qa`; the `qa` configuration owns its model. Invoking this skill in the implementer's or reviewer's session does not supply independence. If fresh separation is unavailable, return `BLOCKED`.

**Modes.** The default is issue mode below. Only an explicit `mode: isa` uses `references/isa-mode.md`; do not auto-detect it, and do not mix issue artifacts into ISA verification or the reverse. The Mechanical and Observable lanes below are issue mode only. `assurance` is independent of `mode`.

## What good looks like

- A real user can complete the task on the exact candidate, and you hold a receipt (what the user would see, preserved). Example: for a dark mode toggle, a screenshot of the real app after one toggle showing the dark theme, on the candidate build.
- Backend work that feeds a UI is proven when the user-visible result appears. Tests and logs support the claim; they do not prove it.
- Nothing user-facing? Name the real consumer (next caller, build step, or agent). Good means that consumer gets what it needs from the real interface, and the real output is the receipt. Example: for a changed export command, run the real command and check the file holds the expected records. `Observable: n/a` only for a genuinely internal change with no consumer-observable difference, with the reason stated.
- Proportional: one claim, one decisive observation, then stop. Example: toggle dark mode once; reload only when persistence is the claim.

## Inputs

Collect the minimum. `plan.md` references mean the supplied Verification Target; standalone calls supply the same fields with approved scope, exact candidate identity, and an authorized evidence directory.

- Verification Target: `Platform` (`web|mobile-web|desktop|ios|android|macos|non-ui`), `Objective`, `Falsifier`, `Primary Flow`, `Regression Check` (or `None`), `Mechanical` (command plus expected result), `Observable` (retained path, or `n/a`), `Pass Criteria`, `Blocked Conditions`.
- Optional `Reach`: how the candidate gets onto the surface, who authorized it, how to restore it, or "default surface already runs the candidate." In pipeline plans, Reach is the loading, activation-permission, and restoration statement in `Primary Flow` and `Blocked Conditions`.
- Changed behavior or files, target URL or command, auth, seed data, prerequisites.
- Bug tasks: the reproduction result and evidence from `reproduce-bug`, supplying the faithful smoke to reuse.
- Standard delivery: `APPROVE_CODE` from `code-quality-gate`. Missing, `REVISE_CODE`, or `ASK_USER` returns `BLOCKED` without running QA. Combined assurance and explicitly focused verification follow `references/combined-assurance.md` and the focused-scope rule above.

If `Mechanical` is missing, return `BLOCKED` naming the missing command and its owner. Do not invent one. If the target cannot distinguish success from its falsifier, return `BLOCKED` naming the target owner and the clarification needed; do not invent acceptance. Missing pipeline inputs never authorize switching to focused verification.

## Workflow

1. **Frame.** For each claim, write the observation that shows it works and the one that would show it is broken (the falsifier). Add one lightweight regression check only when adjacent behavior could easily break.
2. **Pick the platform** from the real entry point, not the file types changed. Timing, persistence, delivery, synchronization, and background behavior can need a visible product flow even when no UI source changed. Read exactly one file:
   - `web`, `mobile-web`, `desktop` -> `platforms/web.md`
   - `ios` -> `platforms/ios.md`
   - `android` -> `platforms/android.md`
   - `macos` -> `platforms/macos.md`
   - `non-ui` -> `platforms/non-ui.md`
3. **Reach, before any proof or Mechanical run.** Answer three questions for the exact candidate (commit, or base plus exact diff):
   - Is the running surface executing it? Name the check (commit, bundle hash, loaded path, version).
   - Can this surface show the claim at all (tools, device, account, data, capture)?
   - Am I allowed to set that up?

   A missing `Reach` line is not a blocker; work out the narrowest way using the platform file. Changing shared state (installing the candidate into a running host, restarting a service, mutating shared data) needs authority stated in `Reach` or the task. Without it, return `BLOCKED` naming the owner and the unlock step. With it, record the original state first and restore it always, including when you stop early. If activation could interrupt the verifier, use a disposable executor, restore, and judge the retained evidence. Before a costly or state-changing flow, check the capture mechanism with the smallest disposable capture.
4. **Prove.** Run the Primary Flow through the actual user or consumer entry point first. Prefer the real surface to a replica; a replica can omit the very integration under test. If proof infrastructure would exceed the change itself, reconsider the route or return the precise blocker.
   - **Mechanical:** validate and reuse a supplied receipt only if the command, exit status or raw output, and exact candidate and relevant runtime conditions are available and sufficient for the declared check; otherwise run the named command and say why (missing, stale, unverifiable, a distinct risk, or an explicit fresh-run requirement). Quote raw output and mark it fresh or reused. An implementer's summary alone is not a receipt. Do not rewrite the command. Reuse never waives independent Observable proof. Example: reuse a passing export check tied to this exact diff and dataset; rerun a receipt that came from the previous candidate.
   - **Regression Check:** when not `None`, run that one regression. Add another counterexample only for a distinct named failure mode that is still unresolved.
   - **Observable:** required whenever user or consumer behavior changed, even if the plan omitted it. Tests, logs, source, CI pages, and screenshots of them are Mechanical evidence only.
   - **Bug fixes:** the primary flow is the same faithful reproduction smoke, now expected to pass. If it cannot be rerun, return `BLOCKED` instead of substituting a broader flow.
   - **Timing or ordering:** wait on observable events, not guessed delays; use inputs that distinguish old and corrected outcomes; verify each event belongs to the intended run.
   - **Async UI:** stop when the terminal observation appears even if unrelated status stays stale. If it does not appear after a short wait, use one authoritative fallback (run state, logs, network, a backend record) to answer only that question. If backend and UI disagree, report both.
   - **Instrumentation:** use existing evidence, logs, and debug flags first. Never edit the candidate to add logging; return the need to implementation.
   - **Visual comparison against a reference:** `references/visual-diff.md`.
   - **Model-backed product operations:** keep the model chosen by the target, product, or user; record provider/model, reasoning level, and submitted turns (`unknown` if not exposed).
5. **Stop** each claim as soon as its terminal observation appears. Before another probe, state the unresolved question, the new signal, how it could change the verdict, and its cost. If none is concrete, stop. Repeat only when repetition is the probe (timing, ordering, intermittency), with a stated window and stopping condition. An edit invalidates only the claims it could affect; reuse still-valid evidence when candidate identity, conditions, and the reason are explicit. In the report, separate claims proven by this check, prior evidence still valid for the current candidate, and anything unverified; keep receipts you still rely on rather than overwriting them.
6. **Verdict and report.**

## When stuck

1. Re-read the target, plan, and ticket for the missing item (a granted permission, a path, a credential), then look up the symptom in the platform file's Recovery table.
2. Make one narrow fix that changes the available evidence, within the authority already given. Never repeat an unchanged attempt.
3. If it did not help, or about 15 tool calls pass without progress (finding the loaded bundle path is progress; rereading unchanged logs is not), stop and return `BLOCKED` naming the owner and the unlock condition.

Cleanup and restore always run, including after you stop.

## Hard blockers: bail out

Ask: would more effort, a different tool, or the authority already given change the answer? If not, it is a hard blocker (for example, a simulator cannot submit an app for App Store review).

Stop immediately. No workaround, no substitute, no extra probes. Return `BLOCKED` with:
- what cannot be shown;
- why it is impossible here;
- who or what can supply it;
- what was proven anyway, labeled partial. Partial proof never becomes `PASS` and does not cover the rest.

Platform files list known examples.

## Anti-patterns

- Calling `PASS` from tests, logs, or code reading when the claim needs real use, or with no receipt ("tests pass, so likely fine").
- Proving a different thing than the user path: a mock, a replica, or a stale install.
- Trusting the implementer's summary.
- Treating a hard blocker as a puzzle and burning calls on it.
- Repeating an unchanged setup or probe.
- Continuing after the success signal appears, or drifting into exploratory QA.
- Changing shared state without stated authority, not restoring it, or stopping processes by name instead of by a PID you started.
- Editing the candidate to make it pass.
- Building a harness larger than the change.
- Reporting `FAIL` when something was missing, or `BLOCKED` when the product is wrong.
- Declaring `BLOCKED` on an assumption: without the observation that proves it, or without checking the task, plan, and ticket first.

## Verdicts

- `PASS`: Mechanical passed, Observable proven (or `n/a` as above), and every cited receipt exists.
- `FAIL`: under valid conditions and a clear target, the product is wrong: Mechanical failed, the flow breaks, or the result is wrong. Say what the user saw. Separate code defects from evidence gaps and route to the real owner.
- `BLOCKED`: access, authority, tooling, data, or capture is missing, or a hard blocker applies. Name the owner and the unlock condition, and show the observation that proves it (command output, error, or screenshot), not an assertion. A required capture that cannot be taken is `BLOCKED`. `BLOCKED` is not redispatched against an unchanged prerequisite.
- A cited receipt missing at report time is an evidence gap: reacquire only that evidence, once. If it still cannot be captured, `BLOCKED`. Never `PASS` without it.
- After 2 `FAIL`s on the same affected claim, stop: report `FAIL` and write `EXHAUSTED` in Next Action (the verdict stays one of `PASS|FAIL|BLOCKED`). Carry prior verdicts across dispatches. Never use exhaustion to waive acceptance.
- Standard delivery: a `FAIL` routes through implementation and fresh code-quality review before acceptance. Focused verification reports and stops.

## Evidence

- Evidence must separate the claimed outcome from its likely false positive. For UI work it is the app-owned result of the Primary Flow. A terminal, test runner, log viewer, or source file, or a screenshot of any of them, is invalid Observable evidence.
- A screenshot proves a static state. Use a short recording only when motion or timing is the claim.
- Retain the minimum: screenshots by default, no duplicate media, no evidence theater. Capture the smallest app-owned area; never expose private desktop content.
- Never record secrets, tokens, or personal data. Inspect the diff and evidence for them; sanitize or `FAIL`.
- **One location rule:** write the result and retained evidence in `{ISSUE_DIR}/verification/` (`screenshots/`, `videos/`), or in the authorized durable directory for standalone calls. Never leave anything the caller consumes in OS temp. Raw snapshots, JSON, logs, and base64 stay in temp and are deleted before `PASS`, except sanitized output the target explicitly requires or that is itself the consumer receipt (for example an API response or an export); retain that in the evidence directory.
- Remove temporary diagnostic instrumentation from the candidate, or justify it in Notes, before `PASS`.

## Report

Write `{ISSUE_DIR}/verification/result.md` first (or `result.md` in the authorized standalone directory). Run `test -f` on it and on every cited Observable path. Do not return `PASS` from chat alone. Cite only paths that exist; for a capture you could not take, write "not captured" and the reason, so a `BLOCKED` report is not mistaken for a missing-file `FAIL`. Combined assurance includes the quality precheck in this one result.

```md
## Verification Result

- Platform: `web|mobile-web|desktop|ios|android|macos|non-ui`
- Assurance: `standard|combined-low-risk`
- Objective: [single outcome verified]
- Falsifier: [observation that would disprove the Objective]
- Primary flow: [short description]
- Regression check: [short description or "None"]
- Quality: [standard `APPROVE_CODE` receipt, or combined precheck result]
- Reach used: [exact steps and restore, or "default surface"; reusable on re-check]
- Mechanical: [command] -> [exit code and quoted raw excerpt; fresh or reused, source, reuse rationale]
- Observable: [artifact path or `n/a`]
- Checks run: [concise list, including any observation window]
- Model-backed product operations: [provider/model, reasoning, turns; `n/a`; or `unknown`]
- Verdict: `PASS|FAIL|BLOCKED`

### Evidence

- [artifact path; "No artifacts" only when Observable is `n/a`]
- Report: [result.md path]

### Notes

- [key proof point, failure point, or blocker with its proof, owner, and unlock]
- Extra probe: [only if one was added beyond the Primary Flow, with the unresolved question]

### Risk

- [anything not verified, partial proof, or "None within the declared target"]

### Next Action

- [commit / fix issue / unblock environment]
```
