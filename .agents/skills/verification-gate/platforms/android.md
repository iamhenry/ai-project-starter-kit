# Platform: android

Behavior rules (what good looks like, recovery, bail-out, anti-patterns, verdicts) live in `SKILL.md`; this file only adds Android specifics.

## Reach

Build, install, and launch the candidate on the target emulator or device with the plan-named commands. Confirm what is installed is the candidate (version or build identity) before any proof.

## Mechanical

Run the plan-named build or test command.

## Observable

- Load `argent` and operate the exact candidate on the target emulator or device.
- Replay the faithful reproduction flow when one exists, or a saved test in the repo's `.argent/e2e/` for this same claim, with `argent e2e run <path.yaml> --device <id> --platform android --json`. A saved test counts only if it ends on the Pass Criteria's visible result. If it fails where the target says the screen changed on purpose, prove live instead. Any other failure is `FAIL`. Never edit it.
- Otherwise drive the Primary Flow live through the Argent recorder (`e2e-start-recording` with `project_root` set to the evidence directory), so the proof run is also the recording. If Argent cannot record, prove it directly, report `Saved test: none`, and say why in Notes.
- Good looks like: the user completes the flow and the app-owned result is visible.
- Anti-pattern: relying on only build and test output.

## Recovery

| Symptom | One narrow fix |
|---|---|
| Emulator not running or unresponsive | Boot or restart that emulator once |
| Stale install | Reinstall the candidate once and re-confirm identity |
| Runner or build error | Retry once after fixing the named cause; otherwise BLOCKED with the owner |

## Hard blockers

Cannot be proven on an emulator, whatever the effort. Examples to confirm per project: Play Store review or release; real billing; physical hardware (NFC, camera sensors); carrier features (SMS, calls).
