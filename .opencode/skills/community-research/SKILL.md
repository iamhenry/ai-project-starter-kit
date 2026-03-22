---
name: community-research
description: Research communities across Reddit, Discord, and Twitter/X through a single adapter-based pipeline. Use when you need repeatable community mining, cross-platform quote collection, audience pain-point research, trend gathering, or competitor/community signal gathering with source URLs attached to every finding.
---

# Community Research

Use this skill to gather structured community evidence from multiple platforms without changing the core workflow.

## Architecture

```text
community-research/
  SKILL.md
  README.md
  adapters/
    base.py
    reddit.py
    discord.py
    twitter_x.py
  scripts/
    research.py
  examples/
    sources.example.json
  tests/
    test_engine.py
```

The core principle is simple:
- keep one engine
- keep one normalized output shape
- isolate platform-specific behavior inside adapters

## Output contract

Every adapter returns items in this shape:

```json
{
  "text": "post or message text",
  "author": "username or display name",
  "timestamp": "ISO-8601 timestamp or null",
  "engagementScore": 123,
  "directUrl": "https://...",
  "source": "reddit|discord|twitter_x",
  "replies": []
}
```

If an adapter cannot produce a direct URL for an item, drop that item instead of returning an uncitable quote.

## Standard run

From the skill directory:

```bash
python3 scripts/research.py \
  --query "why do people relapse after a good streak" \
  --sources-file examples/sources.example.json \
  --pretty
```

Useful options:

```bash
python3 scripts/research.py --query "zero proof drinks" --sources-file examples/sources.example.json
python3 scripts/research.py --query "habit tracker churn" --sources-file examples/sources.example.json --limit 25
python3 scripts/research.py --query "discord onboarding pain points" --sources-file examples/sources.example.json --time-range 30d --pretty
```

## Source config

Pass a JSON file containing a list of source objects. Example:

```json
[
  {"type": "reddit", "subreddit": "stopdrinking", "limit": 10},
  {"type": "discord", "channel_export_path": "/tmp/community.json", "limit": 10},
  {"type": "twitter_x", "search_term": "zero proof drinks", "limit": 10}
]
```

## Adapter notes

Read only the adapter file you need to change:
- `adapters/reddit.py` for ScrapiReddit-based collection
- `adapters/discord.py` for DiscordChatExporter JSON ingestion
- `adapters/twitter_x.py` for X bearer-token search and x-reader-compatible shaping

## Citation rule

Treat this as non-negotiable: every quoted datapoint must keep its clickable source URL. The engine filters out items missing `directUrl` so downstream summaries stay citable.

## Deduplication

The engine deduplicates across adapters using normalized text fingerprints. This catches the common case where the same quote is reposted or mirrored across platforms.

## Failure handling

- Keep partial results if one adapter fails.
- Surface adapter errors in the final JSON.
- Never fabricate missing author, URL, or timestamp data.
