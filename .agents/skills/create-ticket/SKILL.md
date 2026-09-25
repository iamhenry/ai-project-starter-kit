---
name: create-ticket
description: Draft and file a ticket as a GitHub issue or a local `_ai/task/{YYYY-MM-DD}/{slug}/ticket.md` after categorizing it as bug, feature, or task. Use whenever the user wants to create, open, write, or file a GitHub issue, gh issue, bug report, feature request, task ticket, or local ticket.md, or attach supplied screenshots or videos to a new or existing GitHub issue. Prefer this over freeform issue writing. Do not use for the issue-to-pr pipeline.
---

# Create Ticket

Categorize first. Draft the matching template. File only after the user confirms, unless they already said to create/file it, or AGENTS.md already requires a ticket because work may continue.

Do not implement the issue. Do not use this for `issue-to-pr`. Local tickets belong at `_ai/task/{YYYY-MM-DD}/{slug}/ticket.md`.

## 1. Categorize

Pick exactly one type:

| Type | Use when | Not when |
| --- | --- | --- |
| `Bug` | Something is broken or wrong vs expected | The current behavior is intended |
| `Feature` | New user-facing capability or behavior | Fixing broken behavior, or internal cleanup |
| `Task` | Docs, refactor, chore, deps, CI, cleanup | User-facing product change or a defect |

If the request is a question or discussion, do not file a ticket. Say so in one line.

If type is unclear, ask one question, then stop.

## 2. Draft

Write a specific title, ~70 characters, no `FEAT:`/`BUG:` prefix. For GitHub, `--type` carries the category.

Fill only the sections that have content. Delete empty ones. Keep the body short enough that a later agent can execute without guessing.

Ask one question if a required field below is missing and would make the ticket useless. Otherwise draft with what you have and mark unknowns as `unknown`.

Ground the problem statement in first principles: who or what is affected, what they need to achieve, what observable gap prevents it, and why that gap matters. Separate facts from assumptions; do not present a requested solution or suspected root cause as the problem. Use only supplied or verified evidence and mark unknowns rather than inventing rationale.

Make done provable. Definition of done lists observable results: `- [ ] <user does Y, sees X>`. Verification says how each one is proven: where it runs, the proof step, and the receipt kept as evidence. Name any real side effects the agent must never trigger (for example, sending email). Prefer the real entry point over mocks. If an item cannot be checked, say so and mark it `unverified`. Never let a skipped or substitute check count as passing.

Exit criteria are heuristics, not counters. Do not set time or iteration budgets. Add ticket-specific escalations (for example, a dependency that will not install) only when known. Default text, adapted to the ticket:

```md
## Exit criteria

- Stop when every Definition of done item passes its proof. No extra polish.
- Keep going while attempts produce new information.
- Stop and report BLOCKED when stuck: the same error recurs, attempts change nothing, or the next attempt has no testable hypothesis. Record the error, what was tried, and what each attempt showed.
- Never weaken Definition of done or leave scope to force a pass.
```

Scope: In names what this ticket changes. Out lists nearby work an agent would be tempted to do; omit Out when nothing is tempting.

### Bug

Required: what happened, what should happen, how to repro.

```md
## What happened

## What should happen

## Repro

1.

## Evidence

## Definition of done

- [ ] Repro no longer triggers

## Verification

- Verify on: <where it runs>
- Never: <real side effects to avoid>
- <done item> — proof: <repro steps> — receipt: <screenshot, output, or file>

## Scope

- In:
- Out:

## Exit criteria
```

### Feature

Required: problem, observable outcome, definition of done.

```md
## Problem

## Outcome

## Definition of done

- [ ] <user does Y, sees X>

## Verification

- Verify on: <where it runs>
- Never: <real side effects to avoid>
- <done item> — proof: <real step or command> — receipt: <screenshot, output, or file>

## Scope

- In:
- Out:

## Exit criteria
```

### Task

Required: why, definition of done.

```md
## Why

## Change

## Definition of done

- [ ] <user does Y, sees X>

## Verification

- Verify on: <where it runs>
- Never: <real side effects to avoid>
- <done item> — proof: <real step or command> — receipt: <screenshot, output, or file>

## Scope

- In:
- Out:

## Exit criteria
```

## 3. File

Show the destination, type, title, and body first.

Create only after confirm, or immediately when the user already said create/file/open the ticket.

**GitHub** when they asked for a GitHub/`gh` issue. **Local `_ai/task/{YYYY-MM-DD}/{slug}/ticket.md`** otherwise. If work may continue after a GitHub issue, write the local ticket too and put the issue URL in it.

When supplied screenshots or videos are included in a GitHub issue or local ticket, retain the attachment, link, or path in the existing body or Evidence/media section. Add concise factual prose for a later session without media access: relevant visible state, important visible text or annotations, dimensions or sequence when material, and what the media demonstrates. Omit irrelevant visual details, personal data, and speculation. If the media cannot be inspected, state that rather than guessing.

### GitHub

```bash
gh issue create --title "<title>" --body-file /tmp/gh-issue-body.md --type <Bug|Feature|Task>
```

If `--type` is rejected, the issue may still have been created — a non-zero exit does not mean the create failed. Before retrying, check whether the issue already exists (`gh issue list -R <owner>/<repo> --state open --search "<title>" --json number,title` or any URL in the error output). If it exists, use it (add the missing metadata with `gh issue edit` if needed); only re-run create if no issue was created. Do not invent labels. Do not add assignees, projects, or milestones unless asked.

After any `gh issue create` failure or retry, verify what landed (`gh issue view <number-or-url>`) before declaring success — a create can partially succeed despite a non-zero exit, and retrying blindly creates a duplicate.

#### Media attachments

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

### Local

Write `_ai/task/{YYYY-MM-DD}/{slug}/ticket.md`. Use `date +%Y-%m-%d` for the date. Slug is 3-5 words from the title. Resume that directory if it already exists. Update the existing `ticket.md` instead of creating a second one.

```md
# <title>

Type: <Bug|Feature|Task>

<body>
```

Put supplied screenshot or video paths under Evidence. Do not copy media into the repo.

Return the file path.

## Constraints

- One ticket per request. Split unrelated asks.
- No secrets, tokens, emails, or private logs in the body.
- No commits or code changes. The only local file this skill may write is `_ai/task/{YYYY-MM-DD}/{slug}/ticket.md`.
