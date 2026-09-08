# Argent bundle — upstream provenance, license, and inventory

Source of truth: the **complete** skills tree shipped inside the globally installed npm package `@swmansion/argent@0.24.0` (npm latest at import time; gitHead `1068430b919b45a365a1f9270ec3bfc6bcdede46`; integrity `sha512-PhMW298Swxsb4frdBzCb+rDFJyjJhjNoZGPGRsXEk5G1QvAv+bWYofyjLnNCSpMk9MGTtfqDKHFa4b6ms5XqUw==`; tarball `https://registry.npmjs.org/@swmansion/argent/-/argent-0.24.0.tgz`), installed at `/opt/homebrew/lib/node_modules/@swmansion/argent/`.

**License:** the upstream skills docs are governed by the Apache License, Version 2.0, copyright **2026 Software Mansion S.A.** — the upstream package's exact `LICENSE` file is bundled verbatim at `./LICENSE` in this directory (195 lines: full Apache-2.0 text, the copyright line, and the upstream "Additional Terms: Proprietary Binary Components" section). There is no separate upstream NOTICE file. The additional terms apply only to the package's proprietary binaries, none of which are imported here — the 28 imported files are Markdown docs covered by the Apache-2.0 grant, which requires retaining the license text and copyright notice on redistribution; `./LICENSE` provides both.

Import path: `<upstream-dir>/` directly beneath `.agents/skills/argent/` for each of the 18 upstream skill directories, imported verbatim (full content, not summaries) except for the precise adaptations listed below. This file is the only place recording the upstream relationship.

## Complete upstream inventory (source → destination)

| Upstream path (package root `skills/`) | Destination (repo root `.agents/skills/argent/`) |
| --- | --- |
| `argent-android-emulator-setup/SKILL.md` | `argent-android-emulator-setup/SKILL.md` |
| `argent-create-flow/SKILL.md` | `argent-create-flow/SKILL.md` |
| `argent-create-flow/references/flow-yaml.md` | `argent-create-flow/references/flow-yaml.md` |
| `argent-create-flow/references/live-authoring.md` | `argent-create-flow/references/live-authoring.md` |
| `argent-create-flow/references/reliability-and-recovery.md` | `argent-create-flow/references/reliability-and-recovery.md` |
| `argent-device-interact/SKILL.md` | `argent-device-interact/SKILL.md` |
| `argent-device-interact/references/gesture-examples.md` | `argent-device-interact/references/gesture-examples.md` |
| `argent-ios-device-interact/SKILL.md` | `argent-ios-device-interact/SKILL.md` |
| `argent-ios-device-setup/SKILL.md` | `argent-ios-device-setup/SKILL.md` |
| `argent-ios-simulator-setup/SKILL.md` | `argent-ios-simulator-setup/SKILL.md` |
| `argent-lens/SKILL.md` | `argent-lens/SKILL.md` |
| `argent-metro-debugger/SKILL.md` | `argent-metro-debugger/SKILL.md` |
| `argent-metro-debugger/references/failure-scenarios.md` | `argent-metro-debugger/references/failure-scenarios.md` |
| `argent-metro-debugger/references/source-maps.md` | `argent-metro-debugger/references/source-maps.md` |
| `argent-native-profiler/SKILL.md` | `argent-native-profiler/SKILL.md` |
| `argent-qa-flows/SKILL.md` | `argent-qa-flows/SKILL.md` |
| `argent-react-native-app-workflow/SKILL.md` | `argent-react-native-app-workflow/SKILL.md` |
| `argent-react-native-optimization/SKILL.md` | `argent-react-native-optimization/SKILL.md` |
| `argent-react-native-optimization/references/fix-reference.md` | `argent-react-native-optimization/references/fix-reference.md` |
| `argent-react-native-optimization/references/lint-rules.md` | `argent-react-native-optimization/references/lint-rules.md` |
| `argent-react-native-optimization/references/semantic-checklist.md` | `argent-react-native-optimization/references/semantic-checklist.md` |
| `argent-react-native-profiler/SKILL.md` | `argent-react-native-profiler/SKILL.md` |
| `argent-react-native-profiler/references/diagnostic-tools.md` | `argent-react-native-profiler/references/diagnostic-tools.md` |
| `argent-screen-recording/SKILL.md` | `argent-screen-recording/SKILL.md` |
| `argent-screenshot-diff/SKILL.md` | `argent-screenshot-diff/SKILL.md` |
| `argent-settings-permissions/SKILL.md` | `argent-settings-permissions/SKILL.md` |
| `argent-test-ui-flow/SKILL.md` | `argent-test-ui-flow/SKILL.md` |
| `argent-tv-interact/SKILL.md` | `argent-tv-interact/SKILL.md` |

Totals: 18 upstream skill directories, 28 files (18 SKILL.md + 10 reference files), all imported. No upstream file is dropped or summarized. The parent `SKILL.md`, this file, and `LICENSE` are bundle additions, not upstream content.

## Adaptations applied

Every downstream consumer of this bundle has no MCP client; nested skills keep their MCP phrasing and the parent `SKILL.md` translates it. Deviations from upstream text, all recorded here:

1. **CLI context and unavailable agents:**
   - `argent-ios-simulator-setup/SKILL.md` §1 and `argent-device-interact/SKILL.md` §1: appended a CLI-translation parenthetical to the existing MCP-permissions sentence.
   - `argent-device-interact/SKILL.md` §7: added a parenthetical to the full-resolution screenshot note explaining CLI image-file output.
   - `argent-react-native-app-workflow/SKILL.md` §1.1 and §5: replaced both `argent-environment-inspector` result references with direct reading of project scripts/config; removed the unavailable-agent/tool condition from the manual-fallback label.
2. **`argent.md` rule reference** — `argent-device-interact/SKILL.md` Best Practices item 1 referenced a `tapping_rule` from an `argent.md` rules file that is not bundled: replaced that one bullet with "re-verify the target from a fresh `describe` before tapping", which is what the rule enforced.
3. **ToolSearch prerequisite** — `argent-device-interact/SKILL.md` §1 "Load tool schemas before first use" is an MCP deferred-schema mechanism; replaced by one line: schemas/flags come from `argent tools describe <tool>`.
4. **Flow storage path (repo policy override)** — this repo stores flow YAML ONLY at `_ai/task/{SLUG}/reproduction/flows/<safe-name>.yaml`; upstream defaults to `.argent/flows/`:
   - `argent-create-flow/SKILL.md`: appended the task-path override and recorder-unavailable note to the opening definition; added the closing section "Authoring under the repo flow policy" explaining the recorder's hardwired `<project_root>/.argent/flows/` output, direct file-tool authoring using the upstream schema, and how to read the live-authoring reference. No temporary `.argent/flows` workaround is sanctioned. All other content verbatim.
   - `argent-create-flow/references/live-authoring.md`: the recorder `args`-JSON paragraph gained one parenthetical (CLI translation for the tool calls, plus a note that the recorder writes only under `<project_root>/.argent/flows/` and is unavailable under this repo's flow-storage contract). All `.argent/flows` audit-command examples remain verbatim — they describe upstream defaults and the parent override governs them.
   - `argent-qa-flows/SKILL.md` §5 items 1 and 3: selected `argent flow run <path.yaml>` as repo policy for task-path flows, not a technical limitation of `flow-execute` (which also accepts `flow_path`; only its name form resolves `.argent/flows/`); translated the scoped service-recycle sentence to CLI forms. The closing paragraph also changes "obtain green output" to "obtain a green output". All other content verbatim.
5. **`flow-execute` replay wording** — `argent-test-ui-flow/SKILL.md` (2 lines), `argent-react-native-profiler/SKILL.md` (1 line), `argent-native-profiler/SKILL.md` (1 line): replay named as `argent flow run <path.yaml>` instead of the MCP `flow-execute` call. All other content verbatim.
6. **Explore subagent delegation** — `argent-metro-debugger/SKILL.md`: the one "if the file is too large, delegate to an `Explore` subagent" note (§5) was reworded to do the scoped grep yourself (no Explore subagent exists in every consumer of this bundle); the untrusted-data caveat is retained verbatim in the replacement text.
7. **Lens feature flag** — `argent-lens/SKILL.md` says to run `argent enable argent-lens`: left verbatim with one added caution that enabling feature config is a user decision (the flag stays off by default; enabling it is not part of this bundle's tasks).
8. **Tool wording** — `argent-screen-recording/SKILL.md` frontmatter description changes "argent MCP tools" to "the argent `screen-recording` tools". `argent-test-ui-flow/SKILL.md` §1 changes "All interactions go through argent MCP tools" to "All interactions go through argent tools" with the parent's CLI-translation example. Other nested descriptions' MCP phrasing is unchanged and governed by the parent.

### Final-newline differences

Seven imported files omit the final newline present upstream:

- Newline-only differences: `argent-android-emulator-setup/SKILL.md`, `argent-ios-device-interact/SKILL.md`, `argent-ios-device-setup/SKILL.md`.
- Alongside text adaptations recorded above: `argent-create-flow/SKILL.md`, `argent-device-interact/SKILL.md`, `argent-ios-simulator-setup/SKILL.md`, `argent-lens/SKILL.md`.

The final import therefore has 13 byte-identical files, 3 newline-only files, and 12 text-adapted files (4 of those also omit the final newline). All differences are recorded above; all other content is unchanged, including platform limits and Android/TV/Chromium/Vega coverage.
