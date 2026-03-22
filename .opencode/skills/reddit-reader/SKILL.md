---
name: reddit-reader
description: Search Reddit posts and comments with PullPush, then return citation-safe findings with direct Reddit URLs.
---

# Reddit Reader

Use PullPush, not `scrapi_reddit` or the official Reddit API.

## Working endpoints
- Posts: `GET https://api.pullpush.io/reddit/search/submission/?q=<query>&subreddit=<sub>&size=<n>`
- Comments: `GET https://api.pullpush.io/reddit/search/comment/?q=<query>&subreddit=<sub>&size=<n>`

## Workflow
1. Search posts when you want themes, titles, and demand signals.
2. Search comments when you want pain points and exact language.
3. Prefer a subreddit filter when the niche is known.
4. Sort or filter results by `score`, `created_utc`, and relevance to the query.
5. Build the direct URL as `https://reddit.com` + `permalink`.

## Return shape
```json
{"text":"...","author":"...","timestamp":"...","engagementScore":0,"directUrl":"https://reddit.com/...","source":"reddit"}
```

## Mapping
- `text` = `title + selftext` for posts, or `body` for comments
- `author` = `author`
- `timestamp` = ISO-8601 from `created_utc`
- `engagementScore` = `score`
- `directUrl` = `https://reddit.com` + `permalink`

## What does not work
- `scrapi_reddit` is blocked from our VPS with 403s
- Official Reddit API requires OAuth and is unnecessary here
