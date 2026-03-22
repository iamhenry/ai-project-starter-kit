#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from adapters.reddit import RedditAdapter
from adapters.twitter_x import TwitterXAdapter

ADAPTERS = {
    "reddit": RedditAdapter,
    "twitter_x": TwitterXAdapter,
}


def load_sources(path: str) -> List[Dict[str, Any]]:
    return json.loads(Path(path).read_text())


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().split())


def fingerprint(item: Dict[str, Any]) -> str:
    text = normalize_text(item.get("text", ""))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dedupe_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    kept: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not item.get("directUrl"):
            continue
        key = fingerprint(item)
        existing = kept.get(key)
        if existing is None or item.get("engagementScore", 0) > existing.get("engagementScore", 0):
            kept[key] = item
    return sorted(kept.values(), key=lambda item: item.get("engagementScore", 0), reverse=True)


def run_adapter(query: str, source_config: Dict[str, Any], default_time_range: str | None, default_limit: int | None) -> Tuple[List[Dict[str, Any]], List[str]]:
    adapter_type = source_config.get("type")
    adapter_cls = ADAPTERS.get(adapter_type)
    if not adapter_cls:
        return [], [f"unsupported adapter type: {adapter_type}"]

    adapter = adapter_cls()
    result = adapter.fetch(
        query=query,
        source_config=source_config,
        time_range=default_time_range,
        limit=default_limit,
    )
    return [item.to_dict() for item in result.items], result.errors


def build_output(query: str, sources: List[Dict[str, Any]], time_range: str | None, limit: int | None) -> Dict[str, Any]:
    all_items: List[Dict[str, Any]] = []
    errors: List[str] = []

    with ThreadPoolExecutor(max_workers=max(1, len(sources))) as executor:
        futures = [executor.submit(run_adapter, query, source, time_range, limit) for source in sources]
        for future in as_completed(futures):
            items, adapter_errors = future.result()
            all_items.extend(items)
            errors.extend(adapter_errors)

    deduped = dedupe_items(all_items)
    if limit:
        deduped = deduped[:limit]

    return {
        "query": query,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": deduped,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run community research across source adapters")
    parser.add_argument("--query", required=True)
    parser.add_argument("--sources-file", required=True)
    parser.add_argument("--time-range")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    sources = load_sources(args.sources_file)
    output = build_output(args.query, sources, args.time_range, args.limit)
    print(json.dumps(output, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
