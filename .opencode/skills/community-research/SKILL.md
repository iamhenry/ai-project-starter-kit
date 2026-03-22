---
name: community-research
description: Orchestrate community research across x-reader and reddit-reader, normalize findings, dedupe repeated text, and return citation-safe JSON with direct URLs.
---

# Community Research

Use this skill as the thin orchestrator.

## Source skills
- `x-reader` for structured X/Twitter search
- `reddit-reader` for structured Reddit search via PullPush

## Output shape
Read `references/output-schema.json` and return an array of objects in exactly that shape.

## Workflow
1. Run each source skill with the same query, time range, and limit.
2. Keep only items with non-empty `directUrl`.
3. Normalize fields to the shared schema.
4. Dedupe on normalized `text`; keep the higher `engagementScore` if duplicates collide.
5. Sort by `engagementScore` desc unless the user asks otherwise.
6. Return JSON only unless the user asks for synthesis.

## Rules
- Do not rebuild adapters here.
- Keep source-specific logic inside the source skills.
- Never cite a quote without a clickable URL.
- If one source fails, return partial results plus an `errors` array.
