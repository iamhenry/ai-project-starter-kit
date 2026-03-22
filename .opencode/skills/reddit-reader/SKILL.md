---
name: reddit-reader
description: Fetch Reddit posts or comments through PullPush, then return normalized citation-safe JSON items for community research.
---

# Reddit Reader

Use PullPush only: `https://api.pullpush.io/reddit/search/{submission|comment}/`.

## Inputs
- `query`
- `subreddit` optional
- `limit` optional, default 10
- `after` / `before` optional unix timestamps
- `mode`: `posts`, `comments`, or `both`

## Run
Use `references/pullpush.sh` to fetch JSON. Prefer `comments` for pain points, `posts` for broader demand, `both` when unspecified.

## Normalize each hit
```json
{"text":"...","author":"...","timestamp":"...","engagementScore":0,"directUrl":"https://reddit.com/...","source":"reddit"}
```

## Rules
- Build `directUrl` from `permalink`.
- `engagementScore` = `score`.
- `timestamp` = UTC ISO-8601 from `created_utc`.
- Drop removed/deleted text and empty URLs.
- Return JSON only unless asked for synthesis.
