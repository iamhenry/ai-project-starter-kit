#!/usr/bin/env python3
"""Print stored decision-moment counts for behaviors 1–7."""
import argparse
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "evals" / "dataset.jsonl"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", nargs="?", default=str(DEFAULT))
    path = Path(p.parse_args().dataset)
    counts = {str(i): 0 for i in range(1, 8)}
    run_ids = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            run_ids.add(row["runId"])
            for moment in row.get("moments", []):
                key = str(moment["behavior"])
                counts[key] += 1
    print(json.dumps({"runs": len(run_ids), "momentsByBehavior": counts}, indent=2))


if __name__ == "__main__":
    main()
