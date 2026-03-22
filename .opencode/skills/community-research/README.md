# Community Research Skill

A reusable adapter-driven community research pipeline for Reddit, Discord, and Twitter/X.

## What it does

- Accepts one research query and multiple source definitions
- Runs each source adapter concurrently
- Normalizes all results to one schema
- Deduplicates near-identical text across platforms
- Enforces a clickable `directUrl` on every retained item
- Returns machine-readable JSON for follow-on summarization or analysis

## Directory layout

```text
community-research/
  adapters/
  examples/
  scripts/
  tests/
  SKILL.md
  README.md
```

## Setup

### Python

Requires Python 3.10+.

### Reddit adapter

Install ScrapiReddit:

```bash
pip install scrapi-reddit
```

Source config keys:
- `type`: `reddit`
- `subreddit`: subreddit name
- `limit`: optional integer
- `time_range`: optional string like `day`, `week`, `month`, `year`, `all`

Notes:
- No auth required for the default workflow.
- The adapter expects the `scrapi_reddit` package to be importable.

### Discord adapter

This adapter consumes a DiscordChatExporter JSON export.

Export example:

```bash
DiscordChatExporter.Cli export \
  --token "$DISCORD_BOT_TOKEN" \
  --channel <CHANNEL_ID> \
  --format Json \
  --output /tmp/discord-export.json
```

Source config keys:
- `type`: `discord`
- `channel_export_path`: path to exported JSON file
- `limit`: optional integer
- `server_id`: optional metadata
- `channel_id`: optional metadata

Notes:
- Use a bot token, not a personal token.
- The skill reads the export file locally so collection and parsing stay decoupled.

### Twitter/X adapter

Uses X recent search via bearer token and shapes output to the common schema.

Environment:

```bash
export X_BEARER_TOKEN=...
```

Source config keys:
- `type`: `twitter_x`
- `search_term`: optional override; falls back to top-level query
- `limit`: optional integer
- `time_range`: optional metadata string

Notes:
- The adapter is intentionally written so it can coexist with an external `x-reader` workflow, but it does not require the skill to be installed.
- It uses only app/bearer auth.

## Run

```bash
python3 scripts/research.py \
  --query "why do sober streak apps lose users after week two" \
  --sources-file examples/sources.example.json \
  --pretty
```

## Output shape

```json
{
  "query": "...",
  "generatedAt": "2026-03-22T00:00:00Z",
  "items": [
    {
      "text": "...",
      "author": "...",
      "timestamp": "2026-03-21T11:22:33Z",
      "engagementScore": 18,
      "directUrl": "https://...",
      "source": "reddit",
      "replies": []
    }
  ],
  "errors": []
}
```

## Testing

```bash
python3 -m unittest tests.test_engine
```

The included tests cover:
- normalized-item validation
- cross-platform dedupe behavior
- direct URL filtering
- engine aggregation
