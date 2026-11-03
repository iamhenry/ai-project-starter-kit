---
name: argent
description: Run Argent skills to drive, test, debug, profile, and prove iOS, Android, TV, and Chromium apps on simulators, emulators, and physical devices using the `argent` CLI without an LLM in the loop. Use whenever a task mentions Argent, an e2e test or flow YAML, argent MCP tools, device interaction, UI testing, profiling, Metro debugging, screen recording, screenshot diffs, or on-device user-flow proof, or when an iOS repro or verification task needs a replayable device flow. Builds and mechanical proof stay with xcodebuildmcp-cli; use that skill instead for compile/build/test commands.
---

# Argent (bundled skills, CLI-only)

This parent bundles all official Argent skills from `@swmansion/argent` (see `UPSTREAM.md` for source, version, and inventory). The skills in the direct `argent-*` child directories describe **MCP tool calls**; this parent is the **CLI translation layer** — no MCP client is required.

## CLI-only guard (applies to every nested skill)

- Everything an upstream skill phrases as "call tool X" runs as `argent run X --args '<json>'` (single-quoted JSON, matching the upstream examples verbatim), `argent run X --flag value` for simple flags, or `--args -` with JSON on stdin for large payloads. Discover exact flags with `argent tools describe <name>` — never guess from an MCP schema. (Note: `argent tools describe --help` treats `--help` as a tool name — use `argent tools --help` for help.)
- Discover tools with `argent tools` and `argent tools describe <name>`.
- Do not run `argent init`/`install`/`update`/`uninstall`, register MCP servers, or copy any argent config, skills, or rules into the repo — e2e tests run without init; the tool server auto-starts.
- Keep telemetry disabled (set it with `argent telemetry disable --scope global` if not already); never read telemetry status (it may list personal identifiers).
- Never put secrets, tokens, or private user data in flow YAML, run reports, or screenshots. Never type plaintext credentials — use the `{{secret:<NAME>}}` placeholder mechanism the nested skills document.
- Nested skills may name side-effectful setup (permission grants/resets, service teardown, feature flags such as `argent enable argent-lens`). Never run an unapproved keychain change (e.g. the `errSecInternalComponent` keychain fix in `argent-ios-device-setup` asks for the login password — ask the user first), device wipe/`-wipe-data`, unrelated process termination, or feature-config enablement — those need explicit user approval first. Prefer in-app and on-dialog paths (e.g. `argent-settings-permissions` is a last resort, exactly as that skill states).
- If the `argent` CLI is missing or no usable device exists, stop and report `BLOCKED` with the missing prerequisite.
- Device pick: `argent run list-devices --json`. Simulator = iOS entry without `kind: "device"` (boot with `argent run boot-device --udid <UDID>`). Physical iPhone = iOS entry with `kind: "device"`; only `state: "connected"` (cabled, USB usable) can run — `paired` means not reachable, and there is no `boot-device` for phones. The first e2e run on a phone builds and signs an on-device runner (minutes cold).

## CLI invocations for the tool calls in nested skills

- Tool call `X { "udid": "...", ... }` → `argent run X --args '{"udid":"..."}'`. Nested `run-sequence` steps arrive as `--steps-json '[...]'`. Booleans: `--flag`, `--flag true`, `--flag=false`, `--no-flag`. Arrays are repeatable flags.
- Tool output images (screenshot, screenshot-diff): the CLI writes the PNG to a temp path and prints it instead of attaching an image; pass `--includeImageInContext false` + `--scale 1.0` for full-resolution baselines (per argent-screenshot-diff) and open the printed path when pixels matter.
- Returned file paths (screenshots, recordings, profiler traces, log files) are real host paths — follow them with your file tools as the nested skill says.
- Tools listed as unavailable in a context (e.g. on a physical iPhone) fail the same way through the CLI; the nested skill's limits still hold.
- E2E tests: `argent e2e run <name|path.yaml|dir> --device <id> --platform ios --json` (`argent flow run` is the older alias and still works). See the storage section below.

## E2E test storage

Use upstream's default: saved e2e tests live in `.argent/e2e/<safe-name>.yaml` (safe name: letters, numbers, `_`, `-`), committed with the repo so `reproduce-bug` and `verification-gate` can replay the exact file on the candidate. The legacy `.argent/flows/` is still read; save new tests only under `.argent/e2e/`. Snapshot baselines live beside the tests under `.argent/e2e/__baselines__/`, as upstream documents. The recorder tools (`e2e-start-recording`, `e2e-add-step`, `e2e-add-echo`, `e2e-add-script`, `e2e-finish-recording`) write there and are available through the CLI (`argent run <tool> --args '<json>'`). Never commit `.argent/secrets.env`; it is gitignored.

When to record or replay a saved test is owned by `reproduce-bug` and `verification-gate`, not by this bundle. QA records into its evidence directory (`project_root` set there); only a recording from a `PASS` is copied into the repo's `.argent/e2e/`. That recording is the proof run itself: promote it only if every recorded step succeeded with no unrecorded recovery, otherwise report `Saved test: none` (never edit or rerun just to get a recording). Skip `argent-create-e2e`'s polish-and-replay step and `argent-qa-e2e`'s two-pass proof for it. Those rules still apply when a task explicitly asks to author or harden a test.

## Candidate provenance before any replay (mandatory)

Before replaying a flow on an installed app, establish that the installed app **is the exact candidate being verified** (same commit/build). If the app is missing or stale (built from an earlier commit, or provenance cannot be established), build and install the candidate via `xcodebuildmcp-cli` first; if provenance cannot be established at all, report `BLOCKED`. When the candidate is already proven installed on the device, do not rebuild routinely. A stale build can produce a false pass; this check is what makes flow proof candidate-bound.

## Division of labor

- `xcodebuildmcp-cli` owns builds and mechanical proof; Argent owns user-flow proof. Do not run both routinely.
- This bundle has no MCP client, so wherever a nested skill says `e2e-execute`, replay with `argent e2e run <name|path.yaml>`.

## iOS reproduction contract (with reproduce-bug)

For bug reproduction the flow is the shortest faithful replay of the reported entry point, and it must be discriminating — not just "the actions ran":

1. **Initial-state assertion**: start with a check on the screen the reporter started from (e.g. `await: { visible: { id: ... } }`), so a wrong-screen run fails loudly instead of passing vacuously.
2. **Reported entry point**: replay the shortest sequence from that entry point, no extra setup.
3. **Expected-behavior assertion**: end with a condition that holds only when the bug is fixed (`assert:`/`await:` on the expected state), so the same flow proves the fix and fails on the bug. Never weaken a requested check to obtain a pass.
4. Unexpected replay failure → only the diagnosis the failure needs (e.g. a `snapshot:` step or one-off `argent run describe`); do not expand into broad QA.

## Router — load only the nested skill the task needs

Each nested skill is self-contained; load only what the current task needs, and use its exact local path below.

| Task need | Load |
| --- | --- |
| iOS simulator boot / pick a UDID | `argent-ios-simulator-setup/SKILL.md` |
| Android emulator boot / serial | `argent-android-emulator-setup/SKILL.md` |
| Physical iPhone cabling/trust/signing setup | `argent-ios-device-setup/SKILL.md` |
| Tap, swipe, type, screenshots, waits on any platform | `argent-device-interact/SKILL.md` (references: `references/gesture-examples.md`, `references/secrets.md`, `references/chromium.md`, `references/harmonyos.md`) |
| Physical iPhone interaction contract | `argent-ios-device-interact/SKILL.md` |
| Apple TV / Android TV / Fire TV control | `argent-tv-interact/SKILL.md` |
| Create / record / edit / repair an e2e test YAML | `argent-create-e2e/SKILL.md` (references: `references/e2e-yaml.md`, `references/live-authoring.md`, `references/reliability-and-recovery.md`) |
| QA regression e2e test with two-pass proof | `argent-qa-e2e/SKILL.md` |
| Interactive UI testing loops | `argent-test-ui-flow/SKILL.md` |
| Visual regression / before-after screenshot compare | `argent-screenshot-diff/SKILL.md` |
| Record the screen as video | `argent-screen-recording/SKILL.md` |
| Grant/deny/reset runtime permissions | `argent-settings-permissions/SKILL.md` |
| Metro/JS-runtime debugging (CDP) | `argent-metro-debugger/SKILL.md` (references: `references/failure-scenarios.md`, `references/source-maps.md`) |
| Start/debug RN app, Metro, builds | `argent-react-native-app-workflow/SKILL.md` |
| Native profiling (xctrace/Perfetto) | `argent-native-profiler/SKILL.md` |
| React/Hermes profiling | `argent-react-native-profiler/SKILL.md` (references: `references/diagnostic-tools.md`) |
| RN performance optimization pipeline | `argent-react-native-optimization/SKILL.md` (references: `references/lint-rules.md`, `references/semantic-checklist.md`, `references/fix-reference.md`) |
| Design variants with human pick (Lens) | `argent-lens/SKILL.md` |

For iOS bug reproduction and user-flow verification, start with the `reproduce-bug` / `verification-gate` routing outside this bundle, then use `argent-create-e2e` (authoring) and `argent-ios-simulator-setup` / `argent-ios-device-setup` (device pick) from here.

## License notice

The nested skills are imported from `@swmansion/argent` (Software Mansion), licensed under the Apache License, Version 2.0, copyright 2026 Software Mansion S.A. The complete upstream license text is bundled verbatim at `LICENSE` in this directory and must travel with any redistribution of this bundle; it also carries the upstream package's additional terms for its proprietary binary components, none of which are included in this skills-only bundle. See `UPSTREAM.md` for exact provenance.
