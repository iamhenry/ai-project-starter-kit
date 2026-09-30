---
name: agent-device
description: Drive and verify native macOS app windows and menu bar apps with the installed agent-device CLI. Prefer this for Mac UI tasks; use cua-driver as fallback when agent-device is unavailable, blocked, or cannot meet the task's background-interaction requirement. XcodeBuildMCP owns Apple builds and tests. Keep existing agent-browser and Argent routes for browser, Electron, and mobile tasks.
---

# agent-device for Mac apps

Use the installed CLI only. Do not register MCP, run mutable `npx` downloads, install packages, or change Node or other shared runtimes during an app task. Missing tooling is a prerequisite to report, not permission to install it.

## Choose the tool

- Use `xcodebuildmcp-cli` for Mac build, test, and candidate launch when needed. It does not supply native Mac window interaction.
- Use `agent-device` for native Mac UI observation and interaction. Read `agent-device help macos` and command-specific help when the command shape is unclear.
- If the CLI is unavailable, permissions are blocked, or the needed interaction is unsupported, load `cua-driver/SKILL.md` as the fallback. Do not alternate tools without a concrete failure.
- `open` can bring the target app forward. If the user requires background-only operation, use cua-driver instead unless the installed agent-device command explicitly supports that requirement. Never hide a focus change or claim a background guarantee.
- Leave browser/Electron and iOS/Android routing unchanged.

## Smallest useful loop

1. Establish the exact installed candidate before proof. Reuse a known current build; do not rebuild routinely.
2. Open only the authorized target in a named session. Discover the installed syntax with `agent-device help open`. For a normal window, use `--platform macos --session <name>`; add `--surface menubar` only for a menu bar target.
3. Inspect the initial output. Use `snapshot -i` with the same platform/session when current interactive refs are missing. Copy refs exactly; use stable IDs or selectors for durable scripts.
4. Act serially in that session. Prefer supported actions with `--settle` and their returned diff. Refresh the snapshot when refs are stale, output is incomplete, or the UI did not settle. Settling alone does not prove the expected result.
5. Verify the named visible outcome with an appropriate `wait`, `is`, `get`, or `find` check, then capture the smallest app-owned screenshot needed for proof. Inspect the actual image when the claim is visual or the accessibility tree is sparse.
6. Close only this task's session. Do not stop shared daemons or other agents' sessions.

- For an off-screen target, prefer `scroll down --until <selector>` where supported over repeated scroll-and-inspect calls.
- If the snapshot reports sparse or unavailable accessibility, do not use its refs or selectors. Inspect a safely bounded screenshot before using coordinates; retry `snapshot -i` after navigating.
- Use corrective error hints within the task's authority. They do not authorize installations or permission changes.

## Safety and evidence

- Mac permissions still belong to the user. Report the specific permission blocker; do not reset grants, re-sign helpers, or repeatedly trigger prompts. Switching to cua-driver does not bypass macOS consent.
- The npm CLI may build a local Swift helper on first Mac use. If the toolchain or helper trust is missing, report it. Do not upgrade Xcode/Swift or change security settings automatically.
- Prefer an app-window screenshot. Desktop and menu bar surfaces may capture the whole display. If safe bounded capture is unavailable, return `BLOCKED` rather than capture private content. Cropping afterward does not prevent the initial capture.
- Do not send messages, delete data, purchase, or submit forms without authority for that action. Never put secrets or personal data in commands, scripts, or receipts.
- Store retained screenshots and any explicitly requested `.ad` scripts in the owning task's evidence directory. A replay only proves the claim when it checks the expected state on the exact candidate. Follow `verification-gate` for independent acceptance; CLI success is not UI proof.

Reference: [upstream Mac guide](https://github.com/callstack/agent-device/blob/main/website/docs/docs/commands.md), plus version-matched `agent-device help macos`, `help workflow`, and `help <command>`.
