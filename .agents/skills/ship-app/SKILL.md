---
name: ship-app
description: Ship iOS application builds to TestFlight using local Xcode, xcodebuildmcp, App Store Connect CLI, and cua-driver. Use when the user asks to build, sign, upload, submit, distribute, or ship an iOS app, including its first App Store Connect build.
---

# Ship app

Build and upload the current iOS app to TestFlight without EAS. Stop at the exact stage the user requested. Upload, tester assignment, beta review, App Store review, and public release are separate permissions.

Useful user instructions include:

- `Ship this app to TestFlight. Stop when it is ready for internal testing.`
- `Upload the next build, but do not add testers or submit beta review.`
- `Add the processed build to the internal QA group. Do not enable external testing.`

## Process

### 1. Preflight

- Verify the intended Git candidate and inspect `git status`.
- Read canonical project configuration for the bundle ID, installed name, version, build number, deployment target, privacy strings, and encryption declaration.
- Check the installed tools and authentication:

  ```bash
  xcodebuildmcp --help
  xcodebuildmcp tools
  asc version
  asc auth status --validate
  cua-driver doctor
  ```

- Run the project's existing tests, typecheck, lint, and release checks. Stop on failure.
- Keep generated native projects, archives, IPAs, export options, ASC config, and web sessions out of Git.

### 2. Resolve app identity

- Query `asc apps list --output json` and discover current bundle-ID commands with `asc --help`.
- Existing app: reuse its bundle ID and App Store Connect record.
- New app: create the bundle ID if absent, then create the first App Store Connect record with `asc web apps create`.
- If web authentication is missing, run `asc web auth login` interactively. Never request or print passwords, 2FA codes, API keys, private-key paths, or cached sessions.
- Keep the installed app name separate from the globally unique store listing name. Use `--auto-rename=false`; ask the user for another store name if Apple rejects it.

### 3. Set version and build

- Read the latest live version and uploaded builds from App Store Connect.
- Keep the marketing version unless the requested release needs a new version.
- Set the build number higher than every uploaded build for that marketing version.
- Change canonical project configuration, not generated Xcode files.

### 4. Prepare Xcode and signing

- Regenerate ignored native output from canonical configuration only when the framework requires it.
- Use `xcodebuildmcp` help-first project discovery to find the workspace, scheme, and Release settings. Prefer the workspace when CocoaPods created one.
- Use Xcode-managed signing unless the repository defines another signing workflow.
- If signing requires Xcode UI, load `cua-driver` and follow its snapshot-before-action and snapshot-after-action loop. Do not use the App Store Connect website for operations supported by `asc`.

### 5. Archive and inspect

- Inspect `asc xcode archive --help` and `asc xcode export --help`, then create a Release archive and export an App Store Connect IPA.
- Do not use an export option that uploads before inspection.
- Verify the exported IPA has the intended bundle ID, display name, version, build, minimum OS, privacy strings, and encryption declaration.
- Verify Apple Distribution signing, an App Store profile, no device list, and `get-task-allow=false`.
- Inspect production code and linked native capabilities for required purpose strings. Indirect capability use still counts.

### 6. Upload and verify

- Inspect `asc builds upload --help`, then upload the verified IPA once.
- Poll with current `asc builds` commands until processing reaches a terminal state.
- A successful TestFlight upload reports the build valid and ready for internal testing. Set What to Test notes when supplied.
- Report internal and external testing states separately. A processed build is not distributed until a group or tester receives it.

### 7. Finish

Report:

- app and bundle ID
- version and build
- artifact path and signing result
- Apple processing and eligibility states
- files changed and checks run
- remaining tester, beta-review, store-review, or release decisions

Commit canonical configuration changes only when the user explicitly requested a commit. Never infer push authority.

## Failure handling

- Stop at the first failed stage and report the exact command or Apple validation code.
- Fix canonical configuration, increment the build number, rebuild, inspect, and upload a new artifact.
- Never retry a rejected IPA unchanged or reuse an uploaded build number.
- Never continue from upload to testers, review, or release without explicit authority.
