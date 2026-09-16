---
name: xcodebuildmcp-cli
description: Official skill for the XcodeBuildMCP CLI. Use when doing iOS/macOS/watchOS/tvOS/visionOS work (build, test, run, debug, log, UI automation, or release-build preparation).
---

# XcodeBuildMCP CLI

Use XcodeBuildMCP tools via the `xcodebuildmcp` executable instead of raw `xcodebuild`, `xcrun`, or `simctl`.

## Step 1: Ensure the CLI Exists

Check availability:
```bash
xcodebuildmcp --help
```

If missing, install with one of:
```bash
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

```bash
npm install -g xcodebuildmcp@latest
```

Re-check after install:
```bash
xcodebuildmcp --help
```

## Step 2: Use Help-First Discovery

Discover workflows and arguments from the CLI itself:
```bash
xcodebuildmcp --help
xcodebuildmcp tools
xcodebuildmcp <workflow> --help
xcodebuildmcp <workflow> <tool> --help
```

Use this discovery path instead of memorizing static tool lists.

## Step 3: Keep Execution Minimal

- Choose the smallest command sequence that satisfies the request.
- Prefer direct workflow commands over manual multi-step chains unless explicitly requested.
- For simulator run intent, prefer the combined `build-and-run` command.
- Do not chain `build` then `build-and-run` unless explicitly requested.

## Capability Overview

`xcodebuildmcp` supports:
- simulator and device build/test/run
- debugging and log capture
- UI automation
- project discovery and scaffolding
- session defaults and workflow configuration

## Release Handoff

For archive, export, upload, TestFlight, or App Store intent, load `ship-app`. This skill owns native discovery and build mechanics; `ship-app` owns identity, signing, provider state, authority boundaries, and distribution.

Use help-first discovery to check whether the installed CLI exposes the required archive or export workflow. If it does not, return to `ship-app` and use the project's established release CLI. Do not fall back to memorized raw `xcodebuild` commands, infer upload authority, or treat a successful Release build as a distributable artifact.

## Exit Criteria

- CLI presence is verified or installation steps are provided.
- Commands are discovered via `--help` / `tools`.
- Session defaults are checked before first build/run/test action.
- Release intent is handed to `ship-app` before archive, export, or upload actions.
