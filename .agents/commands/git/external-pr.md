---
description: Create PR to external repo via GitHub API (no temp files)
---

Create a PR from current repo to an external repository using only GitHub API calls.

## Required Inputs
- Repo Target
- Which files

## SOP

1. **Get target repo main SHA**
   `gh api repos/OWNER/REPO/git/refs/heads/main --jq '.object.sha'`

2. **Create branch on target**
   `gh api repos/OWNER/REPO/git/refs -X POST -F ref=refs/heads/BRANCH -F sha=MAIN_SHA`

3. **Get existing file SHA (if updating)**
   `gh api repos/OWNER/REPO/contents/FILE_PATH --jq '.sha'`

4. **Push file via Contents API**
   `gh api repos/OWNER/REPO/contents/FILE_PATH -X PUT -F message="..." -F content="$(git show COMMIT:PATH | base64 | tr -d '\n')" -F sha=FILE_SHA -F branch=BRANCH`

5. **Create PR**
   `gh pr create --repo OWNER/REPO --head BRANCH --base main --title "..." --body "..."`

## Requirements
- gh CLI authenticated with write access to target repo
- No temp files - all API-based
