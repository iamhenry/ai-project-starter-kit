# Platform: ios

Behavior rules (what good looks like, recovery, bail-out, anti-patterns, verdicts) live in `SKILL.md`; this file only adds iOS specifics.

## Reach

- Expo project (`expo` in dependencies) with a usable dev build: prove through the Metro/Expo dev server on the simulator (`npx expo start`). A JS or TS-only change needs no native rebuild. A change to native modules, `app.json`, or the SDK version forces a native rebuild instead.
- Otherwise (bare or native project, native or app-config change, missing or stale dev build, physical-device or release-grade proof): build and install with `xcodebuildmcp-cli`.
- Establish provenance of the installed app before any proof. A stale or unprovable install is not a valid target.

## Mechanical

Honor the target's named Mechanical command. On the native build route, use `xcodebuildmcp-cli` build and test: verify the CLI exists, use help-first discovery, and choose the smallest build, test, or launch that proves the target. On the Expo route no native rebuild is needed for a JS or TS-only change.

## Observable

- With a reproduction flow from `reproduce-bug` (normally `{ISSUE_DIR}/reproduction/flows/<safe-name>.yaml`): load `argent` and replay that exact file with `argent flow run <path.yaml> --device <id> --platform ios --json`. A pass on the flow that triggered the bug is the strongest proof. Another path does not substitute.
- Without one: the smallest direct check. On the Expo route, interact with the Metro-served app. On the build route, use the smallest XcodeBuildMCP UI check. Do not author a flow during verification.
- Keep the device selection and replay report in the notes.
- Good looks like: the user completes the flow on the simulator and the app-owned result is visible.
- Anti-pattern: relying on only build and test output.

## Recovery

| Symptom | One narrow fix |
|---|---|
| Stale or unproven install | Reinstall the candidate once and re-confirm provenance |
| Simulator missing a needed asset (for example a voice) | Install it in a dedicated simulator if authorized |
| Build timed out | Retry once on a smaller target, or a faster route only if it still runs the exact candidate and proof class; a native change still needs a native build |
| Simulator or runtime does not expose the needed surface | Try one other simulator or runtime, then treat as hard |

## Hard blockers

Cannot be proven on a simulator, whatever the effort: App Store review or submission; physical hardware the simulator lacks (camera, NFC, Bluetooth). Report what cannot be shown and who can supply it (a physical device, or the App Store account owner).

Check before calling these hard, because they depend on capability or authority, not impossibility: remote push (supported simulators can receive notifications; check the runtime and credentials), and purchases (use StoreKit testing or sandbox; never real money).
