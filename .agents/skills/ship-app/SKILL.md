---
name: ship-app
description: Ship application builds to TestFlight or app stores. Use whenever the user asks to ship, upload, distribute, submit, or release a mobile or desktop app, including the first build for a brand-new app record.
---

# Ship app

Move an application build to the exact distribution stage the user requested. Keep repository publication separate from application distribution.

For iOS and TestFlight work, read `references/ios-testflight.md` before acting. Add another platform reference instead of putting provider-specific commands in this file.

## Direct brief commands

Users can set a precise boundary with short requests:

- `Ship this iOS app to TestFlight. Stop when the build is ready for internal testing.`
- `Upload the next build, but do not add testers or submit beta review.`
- `Add the processed build to the internal QA group. Do not enable external testing.`
- `Submit the build for external beta review. Do not submit the App Store version.`
- `Submit the approved store version for review. Keep release manual.`

If the word `ship` does not identify whether the user means source publication or application distribution, ask one question before changing remote state.

## Authority boundaries

Treat each stage as separate authority:

1. Prepare identity and signing.
2. Build, archive, and export a distributable artifact.
3. Upload the artifact.
4. Assign internal testers or groups.
5. Submit external beta review.
6. Submit store review.
7. Release publicly.

Permission for one stage does not authorize the next. Report the last completed stage and stop there.

## Inputs

Derive values from canonical project configuration and live provider state. Ask only for values that cannot be derived safely:

- platform and destination
- requested stopping point
- application identifier
- installed display name
- store listing name
- SKU or equivalent provider identifier
- version and build number
- primary locale
- build path, such as local native tooling or a hosted service
- signing team or account when more than one valid choice exists

Do not copy values from examples, old artifacts, generated native projects, or another application.

## Workflow

### 1. Record the release contract

State the application, platform, destination, exact stopping point, candidate commit or diff, and actions that remain forbidden. A first-app submission normally includes required identity and app-record setup, but it still does not imply tester assignment or review submission.

### 2. Inspect before changing remote state

Check:

- the worktree and intended candidate
- canonical version, build number, identifier, display name, privacy strings, and encryption declaration
- build-provider configuration
- release notes or testing notes required by the destination
- authentication without printing credential values
- whether the identifier and store record already exist
- ignored paths for generated archives, packages, logs, and credentials

Never store passwords, two-factor codes, session cookies, API private keys, provisioning profiles, or personal review-contact data in the repository or retained logs.

### 3. Choose the existing-app or first-app branch

For an existing app, reuse the live identifier and app record. Do not create duplicates or change identity during submission.

For a brand-new app:

1. Check that the application identifier is final and available.
2. Create the provider identifier only if it is absent.
3. Create the store record only if it is absent.
4. Keep the installed display name separate from the globally unique store listing name.
5. Disable automatic renaming when name conflicts require a product decision.
6. Ask for a new store name if the chosen name is unavailable.

Use public provider APIs when they support the operation. If the provider requires an authenticated web workflow for first-record creation, use the documented CLI workflow with a cached session and explicit authority. Stop for interactive login rather than requesting credentials in chat or shell history.

### 4. Select and verify the build path

Use the build path already selected by the project. Do not introduce a hosted service when the project uses local native tooling, or replace a configured hosted path with local scripts.

Before upload:

- regenerate ignored native output from canonical configuration when the framework requires it
- use the workspace when dependency tooling generated one
- build the release configuration
- archive and export with distribution signing
- inspect the exported artifact, not only the archive
- verify identifier, display name, version, build number, minimum OS, privacy strings, encryption declaration, entitlements, signing certificate, profile type, and debug entitlement state

### 5. Check privacy and compliance

Inspect imported native capabilities and the production code paths that call them. Ensure every linked sensitive capability has a clear purpose string even when the app uses it indirectly, such as scanning an image instead of opening a live camera.

Declare encryption/export compliance from evidence. Do not guess. Keep human-owned legal, privacy, review-contact, and demo-account fields out of repository documentation unless the user explicitly supplies safe public values.

### 6. Upload once and observe the provider result

Upload only the verified artifact. Poll until the provider returns a terminal processing or eligibility state. Record the provider error code and message when validation fails.

If the provider rejects a build:

1. Fix canonical configuration, not only generated output.
2. Increment the build number.
3. Regenerate, archive, export, and inspect a new artifact.
4. Upload the new build once.

Never reuse an uploaded build number or loop unchanged uploads.

### 7. Stop at the authorized stage

After processing, report these states separately:

- upload and processing
- internal-testing eligibility
- external-testing eligibility and beta-review state
- store-version attachment and review state
- release state

Set testing notes when authorized and supported. Do not create tester groups, add people, submit beta review, submit store review, or release publicly unless the user named that stage.

### 8. Clean up and report

Keep generated archives, packages, export options, native build folders, provisioning output, and logs ignored. Commit only canonical configuration and sanitized release documentation when the user explicitly requests a commit. Push only with explicit authority.

Return:

- application and platform
- version and build
- artifact identity and signing result
- completed remote stage
- provider processing and eligibility states
- remaining human or distribution decisions
- files changed and checks run

Do not call an upload a release, or a processed build distributed, until that exact stage is complete.
