# Argent bundle — upstream provenance, license, and inventory

Source of truth: the **complete** skills tree shipped inside the npm package `@swmansion/argent@0.31.1` (released 2026-11-02; gitHead `e0dfcf24fd211459471a5c3f533c386dae40599b`; integrity `sha512-TOHGzGv7QlxVLh8LG5N17b3Pu5eF60Sz5zulYFeUJe2r/Lr6uteMIWAJAl766aQNw0+HTZ7fz4wpfaVwDCIR8g==`; tarball `https://registry.npmjs.org/@swmansion/argent/-/argent-0.31.1.tgz`). Re-imported 2026-11-03, replacing the earlier 0.24.0 import. Upstream 0.30.0 renamed "flows" to "e2e tests" (`argent-create-flow` → `argent-create-e2e`, `argent-qa-flows` → `argent-qa-e2e`, `flow-yaml.md` → `e2e-yaml.md`, default directory `.argent/flows/` → `.argent/e2e/`, `argent flow` kept as an alias).

**License:** the upstream skills docs are governed by the Apache License, Version 2.0, copyright **2026 Software Mansion S.A.** The upstream package's exact `LICENSE` file is bundled verbatim at `./LICENSE` (unchanged between 0.24.0 and 0.31.1). There is no separate upstream NOTICE file. The additional terms apply only to the package's proprietary binaries, none of which are imported here.

Import path: `<upstream-dir>/` directly beneath `.agents/skills/argent/` for each of the 18 upstream skill directories, imported verbatim (full content, not summaries) except for the precise adaptations listed below. This file is the only place recording the upstream relationship.

## Complete upstream inventory (source → destination)

| Upstream path (package root `skills/`) | Destination (repo root `.agents/skills/argent/`) |
| --- | --- |
| `argent-android-emulator-setup/SKILL.md` | `argent-android-emulator-setup/SKILL.md` |
| `argent-create-e2e/SKILL.md` | `argent-create-e2e/SKILL.md` |
| `argent-create-e2e/references/e2e-yaml.md` | `argent-create-e2e/references/e2e-yaml.md` |
| `argent-create-e2e/references/live-authoring.md` | `argent-create-e2e/references/live-authoring.md` |
| `argent-create-e2e/references/reliability-and-recovery.md` | `argent-create-e2e/references/reliability-and-recovery.md` |
| `argent-device-interact/SKILL.md` | `argent-device-interact/SKILL.md` |
| `argent-device-interact/references/chromium.md` | `argent-device-interact/references/chromium.md` |
| `argent-device-interact/references/gesture-examples.md` | `argent-device-interact/references/gesture-examples.md` |
| `argent-device-interact/references/harmonyos.md` | `argent-device-interact/references/harmonyos.md` |
| `argent-device-interact/references/secrets.md` | `argent-device-interact/references/secrets.md` |
| `argent-ios-device-interact/SKILL.md` | `argent-ios-device-interact/SKILL.md` |
| `argent-ios-device-setup/SKILL.md` | `argent-ios-device-setup/SKILL.md` |
| `argent-ios-simulator-setup/SKILL.md` | `argent-ios-simulator-setup/SKILL.md` |
| `argent-lens/SKILL.md` | `argent-lens/SKILL.md` |
| `argent-metro-debugger/SKILL.md` | `argent-metro-debugger/SKILL.md` |
| `argent-metro-debugger/references/failure-scenarios.md` | `argent-metro-debugger/references/failure-scenarios.md` |
| `argent-metro-debugger/references/source-maps.md` | `argent-metro-debugger/references/source-maps.md` |
| `argent-native-profiler/SKILL.md` | `argent-native-profiler/SKILL.md` |
| `argent-qa-e2e/SKILL.md` | `argent-qa-e2e/SKILL.md` |
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

Totals: 18 upstream skill directories, 31 files (18 SKILL.md + 13 reference files), all imported. No upstream file is dropped or summarized. The parent `SKILL.md`, this file, and `LICENSE` are bundle additions, not upstream content. 20 files are byte-identical to upstream; 11 carry the adaptations below.

## Adaptations applied

Every downstream consumer of this bundle has no MCP client; nested skills keep their MCP phrasing and the parent `SKILL.md` translates it. Deviations from upstream text, all recorded here:

1. **CLI context and unavailable agents:**
   - `argent-ios-simulator-setup/SKILL.md` §1 and `argent-device-interact/SKILL.md` §1: appended a CLI-translation parenthetical to the existing MCP-permissions sentence.
   - `argent-device-interact/SKILL.md` §7: added a parenthetical to the full-resolution screenshot note explaining CLI image-file output.
   - `argent-react-native-app-workflow/SKILL.md` §1.1 and §5: replaced both `argent-environment-inspector` result references with direct reading of project scripts/config; removed the unavailable-agent/tool condition from the manual-fallback label.
   - `argent-create-e2e/references/live-authoring.md` "Recorder contract": appended a parenthetical saying the recorder tools are called through the CLI (`argent run e2e-add-step --args '<json>'`).
2. **`argent.md` rule reference** — `argent-device-interact/SKILL.md` Best Practices item 1 referenced a `tapping_rule` from an `argent.md` rules file that is not bundled: replaced with "re-verify the target from a fresh `describe`" before tapping.
3. **ToolSearch prerequisite** — `argent-device-interact/SKILL.md` §1 "Load tool schemas before first use" is an MCP deferred-schema mechanism; replaced by one paragraph: pass numbers as JSON numbers, get flags from `argent tools describe <tool>`.
4. **CLI runner for e2e tests** — `argent-qa-e2e/SKILL.md` §5 item 1: appended that this bundle uses `argent e2e run` for both local and CI runs (no MCP client); item 3: translated the scoped service-recycle sentence to CLI forms; closing paragraph changes "obtain green output" to "obtain a green output". (The 0.24.0 import's repo override storing flows only under `_ai/task/{SLUG}/reproduction/flows/` and declaring the recorder unavailable was **removed** in this re-import; the repo now uses upstream's `.argent/e2e/` default.)
5. **`e2e-execute` replay wording** — `argent-test-ui-flow/SKILL.md` (2 lines), `argent-react-native-profiler/SKILL.md` (1 line), `argent-native-profiler/SKILL.md` (1 line): replay named as `argent e2e run <name-or-path.yaml>` instead of the MCP `e2e-execute` call.
6. **Explore subagent delegation** — `argent-metro-debugger/SKILL.md`: both "delegate to an `Explore` subagent" notes (the "Large log files" note, new upstream since 0.24.0, and the "If the file is too large" note) reworded to do the scoped grep yourself; the untrusted-data caveat is retained.
7. **Lens feature flag** — `argent-lens/SKILL.md`: `argent enable argent-lens` left verbatim with one added caution that enabling feature config is a user decision.
8. **Tool wording** — `argent-screen-recording/SKILL.md` frontmatter description changes "argent MCP tools" to "the argent `screen-recording` tools". `argent-test-ui-flow/SKILL.md` §1 changes "All interactions go through argent MCP tools" to "All interactions go through argent tools" with the parent's CLI-translation example. Other nested descriptions' MCP phrasing is unchanged and governed by the parent.
9. **Screenshot-diff convergence** — `argent-test-ui-flow/SKILL.md` §1 step 4 "Visual" bullet: appended one sentence (report the changed-pixel ratio and diff image, route diff regions back to implementation, re-diff until the ratio converges or remaining diffs are declared acceptable). This local edit was present in the 0.24.0 import but missing from its deviation list; it is now recorded.

All files keep upstream's final newline.
