# iOS and TestFlight

Use this reference for direct Xcode and App Store Connect delivery. Discover the installed CLI surface with `--help` before using release commands because command names and flags can change.

## Prerequisites

- macOS with the project-supported Xcode version
- Apple Developer membership with access to Certificates, Identifiers, and Profiles
- App Store Connect access for the intended application
- `xcodebuildmcp` for Apple project discovery and native build checks
- App Store Connect CLI `asc` for account state, app records, archive/export helpers when available, upload, and processing status

Start with:

```bash
xcodebuildmcp --help
xcodebuildmcp tools
asc version
asc auth status --validate
```

Do not print ASC profile contents, key identifiers, issuer identifiers, private-key paths, cookies, or web-session files.

## Identity preflight

Read canonical project configuration first, then compare it with generated native settings and live Apple state:

- bundle identifier
- installed display name
- store listing name
- SKU
- marketing version
- build number
- primary locale
- deployment target
- privacy-purpose strings
- `ITSAppUsesNonExemptEncryption`

The installed display name and App Store listing name may differ. Apple requires the store listing name to be globally available.

Useful read-only checks:

```bash
asc apps list --output json
asc builds info --app "$APP_ID" --latest --output json
```

Use `asc --help` to discover the current bundle-identifier commands before checking or creating one.

## First App Store Connect record

Apple's public App Store Connect API does not create the first app record. When no record exists:

1. Validate API-key authentication.
2. Check or create the bundle identifier through the supported CLI surface.
3. Run `asc web auth login` interactively if no reusable web session exists.
4. Inspect `asc web apps create --help`.
5. Create the record with explicit name, bundle identifier, SKU, locale, platform, and version. Set `--auto-rename=false` so a name conflict stops for a user decision.
6. Resolve the new numeric app ID with `asc apps list --output json`.

Treat cached web sessions as credentials. Never commit, copy into task artifacts, or print them.

## Native generation and signing

For generated-native frameworks, regenerate from canonical configuration before the release archive. Keep generated native output ignored when that is the project's established policy.

Use the workspace when CocoaPods or another dependency manager created one. Inspect commands first:

```bash
xcodebuildmcp project-discovery --help
xcodebuildmcp simulator --help
asc xcode --help
asc xcode archive --help
asc xcode export --help
```

Prefer Xcode-managed signing unless the project has an established manual-signing workflow. Archive Release, export for App Store Connect, then inspect the IPA.

Do not use an export option that also uploads or waits for processing before the exported IPA has passed inspection. Export and upload are separate authority stages.

Before upload, verify the exported app has:

- the intended bundle identifier, version, and build
- Apple Distribution signing
- an App Store provisioning profile
- no device list
- `get-task-allow=false`
- required privacy-purpose strings
- the intended minimum OS
- the correct encryption declaration

An archive may use different signing from the exported IPA. Judge the distribution artifact.

## Upload and processing

Inspect the installed upload command before acting:

```bash
asc builds upload --help
asc builds --help
```

Upload the exact verified IPA once. Poll the uploaded build until Apple returns a processing and eligibility result. `VALID`, `APP_STORE_ELIGIBLE`, and `READY_FOR_BETA_TESTING` are distinct observations. Report each one rather than collapsing them into "released."

If validation fails, preserve the failure code, update canonical configuration, increment the build number, and create a new artifact. Do not retry the rejected binary unchanged.

## Distribution stages

After a valid upload, keep these actions separate:

1. Update What to Test notes.
2. Assign an internal group or tester.
3. Submit external beta review.
4. Attach the build to a store version.
5. Submit App Store review.
6. Release manually or automatically according to explicit user instruction.

Stop after the requested stage. A TestFlight-ready build does not imply any tester can access it.
