# Platform: web, mobile-web, desktop

Covers browser UI (`web`), responsive browser UI (`mobile-web`), and Electron or other non-Mac native apps (`desktop`). Native Mac apps use `macos.md`. Behavior rules (what good looks like, recovery, bail-out, anti-patterns, verdicts) live in `SKILL.md`; this file only adds web specifics.

## Reach

- Run the candidate itself: the dev server or built bundle from the candidate commit (or base plus exact diff). Confirm identity with something observable, such as a served asset hash or a version string.
- If the app loads code from a path (a plugin, extension, or host-loaded bundle), reaching it means pointing the running host at the candidate. That is a shared-state change; follow the authority and restore rules in `SKILL.md`.
- Prefer a disposable instance (separate port or profile) when loading the candidate could interrupt an active session.

## Mechanical

Run the plan-named commands, or reuse a receipt per `SKILL.md`.

## Observable

- Load `agent-browser` once and follow its CLI-served guidance. Read only the section you need.
- Cycle: snapshot, interact, re-snapshot. Use a named session. Screenshots for static proof; a recording only when motion is the claim.
- `mobile-web`: same, with a mobile viewport or device profile.
- `desktop`: `agent-browser` for Electron when available. For other native apps, use `cua-driver` on the installed app's visible controls.
- Good looks like: the user completes the flow and the app-owned result is visible. Example: submit a prompt once and capture the generated result inside the app, not the request log.
- Anti-pattern: relying on only tests, logs, or source.
- Prefer the viewport for screenshots; avoid full-desktop captures that expose private content.

## Recovery

| Symptom | One narrow fix |
|---|---|
| Older build served or loaded | Reload or reinstall the candidate once, then re-confirm identity |
| Port in use or stale server | Start on a free port, using a PID you started |
| Browser session stuck | Close that named session and reopen once |
| Auth or seed data missing | Use the supplied test account or data; if none, BLOCKED with the owner |

## Hard blockers

Examples to confirm per project: a step needing a human (CAPTCHA, 2FA, mailbox approval); real third-party side effects (payments, messages to real people); production data or accounts no one authorized.
