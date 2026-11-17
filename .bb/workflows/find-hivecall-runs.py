#!/usr/bin/env python3
"""Find archived threads with a completed hivecall skill invocation."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


def bb_json(*args):
    command = ["bb", *args]
    result = subprocess.run(command, capture_output=True, text=True)
    error = (result.stderr + result.stdout).lower()
    if result.returncode and "bb_cli" in error and any(word in error for word in ("stale", "not found", "no such file")) and "BB_CLI" in os.environ:
        env = os.environ.copy()
        del env["BB_CLI"]
        result = subprocess.run(command, capture_output=True, text=True, env=env)
    if result.returncode:
        raise RuntimeError(f"{' '.join(command)} failed: {result.stderr or result.stdout}")
    data = json.loads(result.stdout)
    if not isinstance(data, list):
        raise RuntimeError(f"{' '.join(command)} returned an error or unexpected data")
    return data


def archived_time(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def is_hivecall(thread_id):
    events = bb_json("thread", "log", thread_id, "--json", "--all")
    for event in events:
        item = event.get("data", {}).get("item", {})
        if (item.get("type") == "toolCall" and item.get("tool") == "skill"
                and item.get("status") == "completed"
                and isinstance(item.get("arguments"), dict)
                and item["arguments"].get("id") == "hivecall"):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--project")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    command = ["thread", "list", "--archived", "--include-hidden", "--json"]
    if args.project:
        command.extend(["--project", args.project])
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.days)
    candidates = []
    for thread in bb_json(*command):
        archived = archived_time(thread.get("archivedAt"))
        if archived is None or not cutoff <= archived <= now:
            continue
        candidates.append((archived, thread["id"]))
    candidates = [thread_id for _, thread_id in sorted(candidates, key=lambda candidate: candidate[0], reverse=True)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        runs = [thread_id for thread_id, matched in zip(candidates, pool.map(is_hivecall, candidates)) if matched]
    if args.limit is not None:
        runs = runs[:args.limit]
    folders = [path for path in (Path.home() / ".hivecall" / "runs").glob("*/*") if path.is_dir()]
    print(json.dumps([
        {"thread": thread_id, "folder": next((str(path) for path in folders if path.name.endswith("-" + thread_id)), "")}
        for thread_id in runs
    ]))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(f"find-hivecall-runs: {error}", file=sys.stderr)
        sys.exit(1)
