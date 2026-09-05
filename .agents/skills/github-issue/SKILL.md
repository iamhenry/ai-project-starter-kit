---
name: github-issue
description: Draft and file GitHub issues after categorizing them as bug, feature, or task. Use whenever the user wants to create, open, write, or file a GitHub issue, gh issue, bug report, feature request, or task ticket, or attach supplied screenshots or videos to a new or existing issue. Prefer this over freeform issue writing. Do not use for local `_ai/task` plans or the issue-to-pr pipeline.
---

# GitHub Issue

Categorize first. Draft the matching template. File only after the user confirms, unless they already said to create/file it.

Do not implement the issue. Do not use this for `_ai/task/{date}/{slug}/issue.md` or `issue-to-pr`.

## 1. Categorize

Pick exactly one GitHub type:

| Type | Use when | Not when |
| --- | --- | --- |
| `Bug` | Something is broken or wrong vs expected | The current behavior is intended |
| `Feature` | New user-facing capability or behavior | Fixing broken behavior, or internal cleanup |
| `Task` | Docs, refactor, chore, deps, CI, cleanup | User-facing product change or a defect |

If the request is a question or discussion, do not file an issue. Say so in one line.

If type is unclear, ask one question, then stop.

## 2. Draft

Write a specific title, ~70 characters, no `FEAT:`/`BUG:` prefix. `--type` carries the category.

Fill only the sections that have content. Delete empty ones. Keep the body short enough that a later agent can execute without guessing.

Ask one question if a required field below is missing and would make the issue useless. Otherwise draft with what you have and mark unknowns as `unknown`.

### Bug

Required: what happened, what should happen, how to repro.

```md
## What happened

## What should happen

## Repro

1.

## Evidence
```

### Feature

Required: problem, observable outcome.

```md
## Problem

## Outcome

## Acceptance

- [ ]

## Out of scope
```

### Task

Required: why, done when.

```md
## Why

## Change

## Done when

- [ ]
```

## 3. File

Show the type, title, and body first.

Create only after confirm, or immediately when the user already said create/file/open the issue:

```bash
gh issue create --title "<title>" --body-file /tmp/gh-issue-body.md --type <Bug|Feature|Task>
```

If `--type` is rejected, retry without it. Do not invent labels. Do not add assignees, projects, or milestones unless asked.

### Media attachments

Only when the user supplies screenshots or videos. For an existing issue, skip categorizing and drafting: show the target issue and media, then attach only after the user asks or confirms.

- Run `gh --version`. `--attach` requires GitHub CLI 2.99.0 or later; if it is older, ask before upgrading rather than using another upload service.
- Verify each path is an existing, non-empty regular file and inspect the media and filename for secrets or private information. Public-repository uploads are public; ask before uploading when sensitivity or the target repository is unclear.
- Supported images are `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, and `.svg`; supported videos are `.mp4`, `.mov`, and `.webm`. Give every image concise, descriptive alt text. Video attachments do not support alt text.
- Attach only to the requested issue. Never copy media into the repository or upload it to an unrelated host.

Repeat `--attach` for each file. Add it to the create command above, or attach to one existing issue:

```bash
gh issue create --title "<title>" --body-file /tmp/gh-issue-body.md --type <Bug|Feature|Task> \
  --attach '/path/screenshot.png#Descriptive alt text' --attach /path/demo.mp4
gh issue edit <number-or-url> --attach '/path/screenshot.png#Descriptive alt text'
```

After either command, run `gh issue view <number-or-url> --json body --jq .body`. On GitHub.com, confirm every intended attachment appears under `https://github.com/user-attachments/`; do not claim success otherwise. An upload can partially succeed despite a non-zero exit, so inspect and report exactly what attached before retrying.

Return the issue URL.

## Constraints

- One issue per request. Split unrelated asks.
- No secrets, tokens, emails, or private logs in the body.
- No local plan artifacts, commits, or code changes.
