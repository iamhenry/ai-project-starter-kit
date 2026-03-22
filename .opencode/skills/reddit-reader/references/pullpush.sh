#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-comments}"; QUERY="$2"; SUBREDDIT="${3:-}"; LIMIT="${4:-10}"; AFTER="${5:-}"; BEFORE="${6:-}"
python3 - <<'PY' "$MODE" "$QUERY" "$SUBREDDIT" "$LIMIT" "$AFTER" "$BEFORE"
import json, sys, urllib.parse, urllib.request
mode, query, subreddit, limit, after, before = sys.argv[1:7]
endpoint_map = {'comments': ['comment'], 'posts': ['submission'], 'both': ['comment', 'submission']}
endpoints = endpoint_map.get(mode, [mode])
out = []
for endpoint in endpoints:
    url = f"https://api.pullpush.io/reddit/search/{endpoint}/?q={urllib.parse.quote(query)}&size={limit}"
    if subreddit: url += f"&subreddit={urllib.parse.quote(subreddit)}"
    if after: url += f"&after={after}"
    if before: url += f"&before={before}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        out.extend(json.load(r).get('data', []))
print(json.dumps({'data': out}))
PY
