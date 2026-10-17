#!/usr/bin/env python3
"""Small, local JSONL handoff/cache helpers for OpenCode-agent answers."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ID_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def cache_key(model, payload, identity=""):
    encoded = json.dumps({"model": model, "payload": payload, "identity": identity},
                         ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_cached_answer(cache_dir, answer_id):
    path = Path(cache_dir).expanduser() / f"{answer_id}.json"
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, None
    if isinstance(saved, dict) and saved.get("key") == answer_id and "result" in saved:
        return True, saved["result"]
    return False, None


def write_cached_answer(cache_dir, answer_id, answer, model="opencode-agent"):
    directory = Path(cache_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{answer_id}.json"
    found, _ = read_cached_answer(directory, answer_id)
    if found:
        return False
    encoded = json.dumps({"key": answer_id, "model": model, "result": answer},
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".answer-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def import_answers(cache_dir, answers_path):
    """Validate the entire answers file before adding any answers to the cache."""
    rows = []
    seen = set()
    for line_no, line in enumerate(Path(answers_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {answers_path}:{line_no}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"answer row at {answers_path}:{line_no} must be an object")
        answer_id, answer = row.get("id"), row.get("answer")
        if not isinstance(answer_id, str) or not ID_PATTERN.fullmatch(answer_id):
            raise ValueError(f"answer row at {answers_path}:{line_no} has an invalid id")
        if not isinstance(answer, str):
            raise ValueError(f"answer row at {answers_path}:{line_no} must contain raw answer text in `answer`")
        if answer_id in seen:
            raise ValueError(f"duplicate answer id at {answers_path}:{line_no}")
        seen.add(answer_id)
        rows.append((answer_id, answer))

    imported = skipped = 0
    for answer_id, answer in rows:
        if write_cached_answer(cache_dir, answer_id, answer):
            imported += 1
        else:
            skipped += 1
    return imported, skipped


def write_prompt_batch(requests, output_path, batch_size):
    """Write one role's bounded batch, preserving request order."""
    if not requests:
        return None
    role = next((candidate for candidate in ("tested", "judge")
                 if any(request["role"] == candidate for request in requests)), requests[0]["role"])
    batch = [request for request in requests if request["role"] == role][:batch_size]
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                      for row in batch).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".prompts-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path, role, len(batch)
