from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from hivewatch.shell import minutes_since


PROMISE_DEFAULTS = {
    "screen": {"pace": 10, "signal": "answer"},
    "timed": {"pace": 15, "signal": "answer"},
    "build": {"pace": 10, "signal": "build-log"},
    "code": {"pace": 20, "signal": "lane-file"},
    "helper": {"pace": 20, "signal": "answer"},
}

OFF_TRACK_IDLE_MIN = 10


def normalize_ident(value: str) -> str:
    value = re.sub(r"^ISC-", "", value.strip(), flags=re.I)
    parts = value.split(".")
    try:
        parts[0] = f"{int(parts[0]):03d}"
    except ValueError:
        return ""
    return "ISC-" + ".".join(parts)

def parse_promise_rows(value: str) -> set[str] | None:
    if value == "-":
        return set()
    rows = set()
    for item in value.split(","):
        item = item.strip()
        m = re.fullmatch(r"(?:ISC-)?(\d+)-(?:ISC-)?(\d+)", item, re.I)
        if m:
            first, last = (int(part) for part in m.groups())
            if last < first or last - first > 999:
                return None
            rows.update(f"ISC-{number:03d}" for number in range(first, last + 1))
            continue
        if not re.fullmatch(r"(?:ISC-)?\d+(?:\.\d+)?", item, re.I):
            return None
        ident = normalize_ident(item)
        if not ident:
            return None
        rows.add(ident)
    return rows

def parse_promise(text: str) -> dict | None:
    for line in text.splitlines():
        match = re.match(r"^\s*PROMISE:\s*(.*)$", line, re.I)
        if not match:
            continue
        body = match.group(1)
        marks = list(re.finditer(r"\b(kind|rows|result|lane|pace)=", body, re.I))
        fields = {mark.group(1).lower(): body[mark.end():marks[index + 1].start() if index + 1 < len(marks) else len(body)].strip()
                  for index, mark in enumerate(marks)}
        kind = fields.get("kind", "").lower()
        rows = parse_promise_rows(fields.get("rows", ""))
        try:
            pace = float(fields["pace"]) if "pace" in fields else PROMISE_DEFAULTS[kind]["pace"]
        except (ValueError, KeyError):
            pace = 0
        valid = (kind in PROMISE_DEFAULTS and rows is not None and
                 all(name in fields for name in ("rows", "result", "lane")) and pace > 0)
        return {"kind": kind, "rows": rows or set(), "result": fields.get("result", "-"),
                "lane": fields.get("lane", "-"), "pace": pace, "valid": valid,
                "error": "invalid PROMISE line" if not valid else ""}
    return None

def declared_path(value: str, base: str, root: str) -> str | None:
    if not value or value == "-":
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        parts = path.parts
        if parts and parts[0] == "MAIN":
            path = Path(root, *parts[1:])
        else:
            path = Path(base, path)
    return str(path.resolve())

BB_WORKTREES = Path.home() / ".bb/plugins/environment-git-worktree/host-data/worktrees"

def lane_roots(repo: Path) -> list[Path]:
    """Folders a PROMISE lane may live in: the repo, BB worktrees, and any LANE_ROOTS (os.pathsep-separated)."""
    roots = [repo]
    if BB_WORKTREES.is_dir():
        roots.append(BB_WORKTREES.resolve())
    for extra in os.environ.get("LANE_ROOTS", "").split(os.pathsep):
        if extra.strip():
            roots.append(Path(extra.strip()).expanduser().resolve())
    return roots

def bind_promise_paths(promise: dict, root: str, verify_dir: str) -> dict:
    if not promise.get("valid"):
        return promise
    try:
        repo = Path(root).resolve()
        verify = Path(verify_dir).resolve()
        lane = declared_path(promise["lane"], root, root)
        result = declared_path(promise["result"], verify_dir, root)
        if lane and not any(Path(lane).is_relative_to(r) for r in lane_roots(repo)):
            raise ValueError("lane outside allowed roots")
        if result:
            Path(result).relative_to(verify)
        promise.update(lane_path=lane, result_path=result)
    except (OSError, RuntimeError, ValueError):
        promise.update(valid=False, error="PROMISE path is outside its allowed folder")
    return promise

def promise_metrics(sess: dict, snapshot: dict, state: dict) -> dict | None:
    promise = sess.get("promise")
    if (not promise or not promise.get("valid") or not sess.get("promise_read_valid", True) or
            not snapshot["sessions"].get("valid", False)):
        return None
    rows = promise["rows"]
    kind = promise["kind"]
    if kind in ("screen", "timed", "helper") and not promise.get("result_path"):
        return None
    evidence = snapshot["evidence"]
    if rows and not evidence.get("valid", False):
        return None
    if promise.get("result_path") and not evidence.get("valid", False):
        return None
    if promise.get("result_path"):
        sources = [item for item in evidence.get("results", [])
                   if item["path"] == promise["result_path"]]
    else:
        sources = []

    candidates = {}
    placeholders = 0
    waits = []
    for source in sources:
        waits.extend(source.get("waits", {}).items())
        for row in source.get("table_rows", []):
            if row.get("id") not in rows:
                continue
            if row.get("placeholder"):
                placeholders += 1
            if row.get("status") not in ("PASS", "FAIL") or row.get("placeholder") or not row.get("evidence"):
                continue
            candidate = dict(row, path=source["path"], mtime=source["mtime"])
            old = candidates.get(row["id"])
            if old is None or candidate["mtime"] >= old["mtime"]:
                candidates[row["id"]] = candidate

    row_state = state.setdefault("promise_rows", {}).setdefault(sess["id"], {})
    current = {}
    for ident, row in candidates.items():
        signature = row["path"] + ":" + row["signature"]
        previous = row_state.get(ident, {})
        if previous.get("signature") == signature:
            first_seen = previous.get("first_seen", row["mtime"])
        else:
            first_seen = min(row["mtime"], snapshot["now"])
        current[ident] = {"signature": signature, "first_seen": first_seen}
    state["promise_rows"][sess["id"]] = current
    answers = len(candidates)
    coverage = f"{answers}/{len(rows)}" if rows else "n/a"
    created = sess.get("created") or snapshot["now"]
    last_real = max((entry["first_seen"] for entry in current.values()), default=created)
    pace = promise["pace"]
    lane = snapshot.get("lanes", {}).get(sess["id"], {})
    if kind in ("code", "build"):
        if not promise.get("lane_path") or not lane.get("valid"):
            return None
        stamp = lane.get("build_mtime") if kind == "build" else lane.get("latest_mtime")
        signal_at = max(created, stamp or created)
        signal_name = "build log growth" if kind == "build" else "lane change"
    else:
        signal_at = max(created, last_real)
        signal_name = "real answer"

    pause_intervals = []
    if kind in ("screen", "timed", "helper"):
        for ident, wait in waits:
            if ident != "*" and ident not in rows:
                continue
            start = max(signal_at, wait["from"])
            end = min(snapshot["now"], wait["until"])
            if end > start:
                pause_intervals.append((start, end))
    pause_intervals.sort()
    paused = 0.0
    merged = []
    for start, end in pause_intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    for start, end in merged:
        paused += end - start
    pace_age = max(0.0, (snapshot["now"] - signal_at - paused) / 60)

    steer_events = [entry["first_seen"] for entry in current.values()]
    if kind in ("code", "build"):
        steer_events.append(signal_at)
    unanswered = 0
    for steer in sess.get("steers", []):
        deadline = steer + pace * 60
        if kind in ("screen", "timed", "helper"):
            for start, end in merged:
                if start < deadline and end > steer:
                    deadline += max(0.0, min(end, deadline) - max(start, steer))
        if snapshot["now"] >= deadline and not any(steer <= stamp <= deadline for stamp in steer_events):
            unanswered += 1

    return {"answers": answers, "placeholders": placeholders, "coverage": coverage,
            "pace_age": pace_age, "pace": pace, "signal_name": signal_name,
            "steers": len(sess.get("steers", [])), "unanswered": unanswered,
            "valid": True, "breached": pace_age > pace}

def off_track_idle_age(sess: dict, snapshot: dict) -> float | None:
    """Minutes since this promise last showed message or attributable file progress."""
    promise = sess.get("promise") or {}
    created = sess.get("created")
    stamps = [sess.get("last_message"), created]
    if promise.get("kind") in ("code", "build"):
        lane = snapshot.get("lanes", {}).get(sess["id"], {})
        if not lane.get("valid"):
            return None
        stamps.append(lane.get("build_mtime" if promise["kind"] == "build" else "latest_mtime"))
    else:
        evidence = snapshot.get("evidence", {})
        if not evidence.get("valid"):
            return None
        result_path = promise.get("result_path")
        result_name = Path(result_path).name if result_path else ""
        prefix = re.sub(r"-result\.md$", "", result_name, flags=re.I).casefold()
        rows = promise.get("rows", set())
        for item in (*evidence.get("files", []), *evidence.get("results", [])):
            path = item.get("path", "")
            name = (item.get("name") or Path(path).name).casefold()
            matches = (path == result_path or bool(prefix and name.startswith(prefix)) or
                       any(ident.casefold() in name for ident in rows))
            stamp = item.get("mtime")
            if matches and stamp is not None and (created is None or stamp >= created):
                stamps.append(stamp)
    latest = max((stamp for stamp in stamps if isinstance(stamp, (int, float))), default=None)
    return minutes_since(latest, snapshot["now"]) if latest is not None else None

def result_verdict_key(path: str, ident: str, status: str, text: str) -> str:
    identity = json.dumps([os.path.normcase(os.path.abspath(path)), normalize_ident(ident),
                           status.upper(), text], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(identity.encode()).hexdigest()

def result_session_finished(result: dict, snapshot: dict) -> bool:
    result_path = os.path.normcase(os.path.abspath(result["path"]))
    for sess in snapshot.get("sessions", {}).get("children", []):
        promise = sess.get("promise")
        if not promise or not promise.get("valid") or promise.get("kind") not in ("screen", "timed", "helper"):
            continue
        promised_path = promise.get("result_path")
        matches = bool(promised_path and
                       os.path.normcase(os.path.abspath(promised_path)) == result_path)
        if matches and (sess.get("time_idle") is not None or sess.get("idle_outcome") is not None):
            return True
    return False
