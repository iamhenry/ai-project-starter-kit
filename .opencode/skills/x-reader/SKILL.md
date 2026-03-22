---
name: x-reader
description: Search X/Twitter with bearer-token auth and return normalized citation-safe JSON items, not just prose digests.
---

# X Reader

Use X recent search when the user needs structured evidence, not only a digest.

## Inputs
- `query`
- `limit` optional, default 10
- `start_time` / `end_time` optional ISO-8601

## Request
Call `GET https://api.x.com/2/tweets/search/recent` with bearer auth and:
- `query`
- `max_results`
- `tweet.fields=created_at,public_metrics,author_id`
- `expansions=author_id`
- `user.fields=username`

## Normalize each tweet
```json
{"text":"...","author":"username","timestamp":"...","engagementScore":0,"directUrl":"https://x.com/<username>/status/<id>","source":"twitter"}
```

## Rules
- `engagementScore` = likes + retweets + replies.
- Keep direct URLs for every item.
- Return JSON only unless the user asks for synthesis.
- This skill can be called directly or by `community-research`.
