# Platform: macos

Behavior rules (what good looks like, recovery, bail-out, anti-patterns, verdicts) live in `SKILL.md`; this file only adds macOS specifics.

## Reach

Confirm the running app is the candidate before any proof. Build or launch with `xcodebuildmcp-cli` only when that is needed to reach it; an already-running, attributable candidate needs neither.

## Mechanical

`xcodebuildmcp-cli` for build, launch, and tests when the target requires them. It supplies mechanical proof, not window interaction.

## Observable

- Use the installed `agent-device` CLI for native Mac UI proof on the exact candidate.
- Fall back to `cua-driver` only for a concrete tool or permission blocker, an unsupported interaction, or a background-only requirement.
- Load the selected tool's skill. Do not configure MCP or upgrade shared runtimes.
- Retain app-owned evidence per the evidence rules in `SKILL.md` (screenshots by default, a recording when motion or timing is the claim).
- Good looks like: the user completes the flow and the app-owned result is visible.
- Anti-pattern: relying on only build and test output.

### Screenshot hygiene

- Capture the app window, or the active sheet or modal bounds.
- Menu bar apps: capture the opened popover, panel, or menu bounds. Prefer deterministic QA hooks or launch flags over raw status-item clicks.
- If bounded capture is unavailable, crop tightly, close unrelated windows first, and retake or delete any artifact with private desktop content.
- If only full-desktop capture is possible and would expose private content, return BLOCKED instead of saving it.

## Recovery

| Symptom | One narrow fix |
|---|---|
| Tool cannot reach the app | Retry with the fallback tool named above, once |
| Permission prompt blocks automation | BLOCKED naming the owner who can grant it |
| Stale build running | Relaunch the candidate once and re-confirm identity |

## Hard blockers

Cannot be proven locally, whatever the effort. Examples to confirm per project: Mac App Store review; a system permission only a human can grant; behavior needing hardware this Mac lacks.

Check before calling these hard: notarization depends on credentials and service access, so it is a capability or authority question, not impossible by default.
