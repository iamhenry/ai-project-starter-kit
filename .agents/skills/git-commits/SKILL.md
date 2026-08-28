---
name: git-commits
description: Git commit workflow and message format. Use when making commits, asking about commit conventions, or after completing code changes. Enforces atomic commits with structured messages (type/scope/summary + what/why body).
---

# Git Commits

## WORKFLOW

1. Run command to see all modified files `git status --porcelain`
2. Run brief diff command to understand changes `git diff`
3. PRE-FLIGHT (before any commit): scan staged diff + filenames for sensitive info
   - What to look for: passwords, API keys, tokens, secrets, private keys, credentials, personal data (emails, phone numbers, names of private individuals), logs, screenshots, session data
   - Scan the diff (`git diff` / `git diff --cached`) AND filenames (e.g. `debug.log`, `screenshot.png`, `notes.txt`)
   - Also check untracked files about to be committed
   - If anything sensitive found: STOP, report it, ask the user. Never commit and "fix later". Git history keeps secrets forever.
   - If clean: proceed
4. Commit ALL (skip staging) using commit format below
5. Push changes
6. Then stop

## Format
```
<type>(<scope>): <summary>
<body with what changed and why>
```
- Title (first line): Required - follows `<type>(<scope>): <summary>` format
- Body (after blank line): REQUIRED - for each changed file, add a parent bullet with the file path, then nested bullets for what changed and why.

## Example
```
  <type>(<scope>): <summary>

  src/components/button.js
    - What: Added Button with size props.
    - Why: Enable dynamic size adjustments for a customizable UI.

  tests/button.test.js
    - What: Created tests for Button sizing.
    - Why: Ensure reliable rendering and detect regressions.
```

## SCOPE

Specifies area of change:
- auth, user, dashboard, api, database, ui, transfer, etc.

## ANTI-PATTERNS

- NEVER skip the body - it documents intent
