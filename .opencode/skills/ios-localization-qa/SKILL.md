---
name: ios-localization-qa
description: Run adaptive iOS simulator localization QA for Expo or React Native apps across one or more locales. Use when the user wants to verify localized UI strings, capture locale screenshots, test onboarding/main app screens in Simulator, or repeat QA for newly added languages. Prefer this skill for multi-locale iOS QA even when the user does not explicitly say "skill".
compatibility: OpenCode, Expo dev-client, Xcode Simulator, XcodeBuildMCP CLI
---

# iOS Localization QA

Run evidence-backed localization QA with an OODA loop: observe the current app/simulator state, orient around constraints, decide the safest next action, act with the proven tool map, then repeat per locale and screen.

## Goal Contract

Produce a locale-by-locale QA result that proves what localized UI rendered, where evidence was saved, and what blocked deeper coverage.

Success means:

- target locales were attempted
- simulator locale was changed per target locale
- reachable target screens were captured with screenshots
- visible localization issues were recorded
- blockers were labeled instead of hidden
- app behavior was not changed unless the user approved a temporary QA bypass

## OODA Workflow

Use this loop for every session. Each session starts from zero context.

### 1. Observe

Collect only facts needed to launch, localize, capture, and report.

- User scope: locales, screens, artifact path, image-only preference.
- App config: bundle id, URL scheme, supported locales, launch scripts.
- Runtime: booted simulator, simulator UDID, Metro status, native/dev-client launch path.
- Current UI: first visible screen, gate state, errors, prompts, or redboxes.

Generic places to inspect:

| Question           | Places to check                                                                |
| ------------------ | ------------------------------------------------------------------------------ |
| Is this Expo?      | `app.json`, `app.config.*`, `package.json`, `eas.json`                         |
| Bundle id?         | Expo `ios.bundleIdentifier`, native `ios/*/Info.plist`, Xcode project settings |
| URL scheme?        | Expo `scheme`, iOS URL types, dev-client prompt behavior                       |
| Supported locales? | Expo `ios.infoPlist.CFBundleLocalizations`, i18n config, locale dictionaries   |
| Launch command?    | `package.json` scripts, Expo dev-client setup, existing run docs               |
| Screens to QA?     | user scope first, then app navigation/onboarding/settings/paywall conventions  |

### 2. Orient

Convert observations into a QA stance before acting.

- Classify launch path: Expo dev-client, direct native launch, or blocked.
- Classify QA mode: onboarding, main app, gated flow, settings, modal, or custom scope.
- Map each locale to `AppleLanguages` and `AppleLocale`.
- Identify blockers early: paywall, auth, missing service config, no Metro, no booted simulator.
- Decide evidence depth: image-only, screenshot plus semantic snapshot, or video only if explicitly useful.

Common locale pairs:

| Language          | `AppleLanguages` | `AppleLocale` |
| ----------------- | ---------------- | ------------- |
| German            | `de`             | `de_DE`       |
| Spanish           | `es`             | `es_ES`       |
| Japanese          | `ja`             | `ja_JP`       |
| Korean            | `ko`             | `ko_KR`       |
| Portuguese        | `pt`             | `pt_PT`       |
| Portuguese Brazil | `pt-BR`          | `pt_BR`       |
| French            | `fr`             | `fr_FR`       |
| Italian           | `it`             | `it_IT`       |
| Dutch             | `nl`             | `nl_NL`       |

Prefer user-provided locale/region pairs over this table. Terminate and relaunch the app after locale changes because many apps read locale only on startup.

### 3. Decide

Choose the smallest safe next action that increases evidence.

- If scope, locales, or artifact path are ambiguous and matter, ask one short question.
- If a safe default exists, proceed without asking.
- If a gate blocks target screens, ask before adding any auth, onboarding, paywall, or subscription bypass.
- If a destructive reset, app data wipe, or sensitive screenshot seems necessary, ask first.
- If the app is blocked by service config, capture localized error state; do not request secrets.

### 4. Act

Use the tool map as proven defaults. Adapt only when evidence shows the app uses a different port, simulator, scheme, or launch path.

For each locale:

1. Stop the app.
2. Set simulator language and region.
3. Relaunch through the chosen launch path.
4. Wait for UI to settle.
5. Capture screenshot evidence.
6. Capture semantic UI when useful for text extraction or element refs.
7. Navigate only within requested scope.
8. Copy screenshots into stable locale folders.
9. Record findings or blockers.

### 5. Loop

Repeat OODA per locale and per blocked screen.

- Re-observe after every relaunch, prompt, navigation, or blocker.
- Re-orient when the app shows a different state than expected.
- Stop when all requested locale/screen evidence is captured, or when remaining progress requires user approval or missing prerequisites.

## Dependencies

Confirm these before deep QA:

- macOS with Xcode Simulator available
- booted iOS simulator, or permission to boot one
- app has an iOS bundle id in Expo config or native project settings
- Expo dev-client or native launch path is known
- Metro can run locally when using Expo dev-client
- `xcrun simctl` is available
- `xcodebuildmcp` CLI is available through `npx -y xcodebuildmcp@latest` or global install
- output directory is writable
- if a gate blocks target screens, user approval exists before adding any bypass

Do not request API keys, tokens, or secrets.

## Tool Map

Use these proven defaults before inventing new commands:

- Find booted simulator: `xcrun simctl list devices booted`
- Start Expo dev-client Metro: `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 npx expo start --dev-client --clear > <log-path> 2>&1 &`
- Check Metro: `curl -fsS http://127.0.0.1:8081/status`
- Mac LAN IP for Simulator URL: `ipconfig getifaddr en0 || ipconfig getifaddr en1`
- Stop app: `xcrun simctl terminate booted <bundle-id> || true`
- Set language: `xcrun simctl spawn booted defaults write NSGlobalDomain AppleLanguages -array <lang>`
- Set region: `xcrun simctl spawn booted defaults write NSGlobalDomain AppleLocale <locale>`
- Open Expo dev-client bundle: `xcrun simctl openurl booted "<bundle-id>://expo-development-client/?url=http%3A%2F%2F<mac-ip>%3A8081"`
- Capture screenshot: `npx -y xcodebuildmcp@latest simulator screenshot --simulator-id <udid> --return-format path --output json`
- Capture semantic UI: `npx -y xcodebuildmcp@latest simulator snapshot-ui --simulator-id <udid> --output json`
- Tap element: `npx -y xcodebuildmcp@latest ui-automation tap --simulator-id <udid> --element-ref <ref>`
- Swipe/advance: `npx -y xcodebuildmcp@latest ui-automation gesture --simulator-id <udid> --preset scroll-left --screen-width <w> --screen-height <h> --post-delay 1`
- Cleanup Metro: `pkill -f "expo start"; pkill -f "@expo/cli"` only when cleanup is requested

When XcodeBuildMCP returns a temporary screenshot path, copy it into the artifact directory with a stable filename such as `cp "<returned-path>" "<artifact-dir>/<locale-slug>/<screen-name>.png"`.

Use a log path outside the repo for long-running Metro logs unless the user asks to keep logs, for example `/var/folders/.../opencode/<app>-locale-qa.log` or another approved temp directory.

## Failure Recovery

Use these recoveries before broad rediscovery:

| Symptom                        | Likely cause                              | Recovery                                                               |
| ------------------------------ | ----------------------------------------- | ---------------------------------------------------------------------- |
| `No script URL provided`       | Dev-client app launched without Metro URL | Open encoded Expo dev-client URL with bundle id scheme                 |
| iOS "Open in <app>?" prompt    | Simulator asks to confirm custom scheme   | Tap Open once, then continue                                           |
| Blank white screen             | Metro unavailable or wrong host           | Check Metro, use LAN IP, terminate/relaunch                            |
| Locale still old               | App read locale before change             | Terminate app and relaunch after `AppleLanguages`/`AppleLocale` writes |
| Paywall/auth blocks screens    | Expected app gate                         | Ask before bypass; otherwise capture blocker                           |
| Service singleton/config error | Missing dev service setup                 | Capture localized error; do not ask for secrets                        |
| Snapshot has no targets        | UI accessibility snapshot limited         | Use screenshots plus gestures/taps from visible evidence               |

## Temporary Bypass Policy

Only add a bypass when the user approves it for QA. Keep it narrow:

- dev-only guard, such as `__DEV__` plus an explicit env var
- no production behavior change
- minimal file touch
- verify the bypass reaches the target screens
- remove the bypass before cleanup or commit unless the user explicitly wants it kept

If a bypass is not approved, capture the localized blocker screen and return `PARTIAL` or `BLOCKED`.

## Evidence Rules

- Prefer image files for user-facing QA evidence.
- Use semantic snapshots to extract text and element refs, but do not keep JSON artifacts if the user only wants screenshots.
- If the user asks for image-only folders, remove or avoid `.json`, `.md`, logs, and other non-image files in those folders.
- Never capture secrets, tokens, API keys, or private user data.
- Name locale folders clearly, for example `de-german`, `es-spanish`, `ja-japanese`.
- If only partial coverage was possible, say exactly which screens were covered and which were not.

## Output

Return this structure:

```md
## iOS Localization QA Result

- Scope: [onboarding/main/settings/etc]
- Locales: [list]
- Verdict: PASS | PARTIAL | BLOCKED

### Evidence

- [locale]: [screenshot paths]

### Findings

- [locale/screen]: [issue or "No issue found"]

### Blockers

- [blocker or "None"]

### Next Action

- [fix copy / approve bypass / rerun locale / cleanup]
```

Use `PASS` only when requested screens were captured for all target locales without unresolved blockers. Use `PARTIAL` when evidence exists but some screens/locales were not reachable. Use `BLOCKED` when prerequisites prevent meaningful capture.
