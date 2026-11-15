from __future__ import annotations

import datetime as dt
import json
import os
import re
import sqlite3
import stat as stat_module
import subprocess
import sys

def command(args: list[str], timeout: float = 1.5) -> tuple[str, str]:
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return p.stdout.strip(), p.stderr.strip() or (f"exit {p.returncode}" if p.returncode else "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", str(exc)

class BBAdapter:
    """Default BB integration; watchdog decisions stay reusable without BB."""

    def command(self, args: list[str], timeout: float = 8.0) -> tuple[str, str]:
        return command([os.environ.get("BB_CLI") or "bb", *args], timeout)

    def parse_json(self, args: list[str], timeout: float = 8.0):
        out, error = self.command(args, timeout)
        try:
            return json.loads(out), error
        except (json.JSONDecodeError, TypeError):
            return None, error or ("invalid JSON" if out else "empty output")

    def child_sessions(self, thread_id: str) -> list[str]:
        db = os.path.expanduser("~/.bb/bb.db")
        if not thread_id or not os.path.exists(db):
            return []
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3.0)
            con.execute("PRAGMA query_only=ON")
            rows = con.execute("""SELECT DISTINCT e.provider_thread_id FROM events e JOIN threads t ON t.id=e.thread_id
                WHERE t.parent_thread_id=? AND e.provider_thread_id LIKE 'ses_%'""", (thread_id,)).fetchall()
            con.close()
            return [row[0] for row in rows]
        except sqlite3.Error:
            return []

    def load(self, thread_id: str, sessions: list[dict], live_sessions: list[dict]) -> dict:
        return load_bb(thread_id, sessions, live_sessions)

BB = BBAdapter()

def seconds(value: object) -> float | None:
    try:
        n = float(value)
        return n / 1000 if n > 100_000_000_000 else n
    except (TypeError, ValueError):
        return None

def minutes_since(value: float | None, now: float) -> float | None:
    return max(0.0, (now - value) / 60) if value is not None else None

def parse_load(text: str) -> float | None:
    m = re.search(r"load averages?:\s*([0-9.]+)", text, re.I)
    return float(m.group(1)) if m else None

def parse_elapsed(text: str) -> float:
    days = 0
    if "-" in text:
        day, text = text.split("-", 1)
        days = int(day)
    parts = [int(x) for x in text.split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, *parts
    else:
        h, m, s = 0, 0, parts[0]
    return days * 86400 + h * 3600 + m * 60 + s


def setting(env: dict[str, str], name: str, default: float) -> float:
    try:
        value = float(env.get(name, default))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default

def flatten_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from flatten_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from flatten_dicts(child)

def load_bb(thread_id: str, sessions: list[dict], live_sessions: list[dict]) -> dict:
    result = {"children": [], "binding": {}, "orch_status": None, "queue_count": None,
              "errors": [], "list_valid": False, "show_valid": False,
              "queue_valid": False, "binding_valid": False}
    if not thread_id:
        result["errors"].append("ORCH_THREAD is unset")
        return result

    raw_binding = None
    binding_path = os.path.expanduser("~/.bb/plugins/opencode/task-bound.json")
    try:
        with open(binding_path, encoding="utf-8") as f:
            raw_binding = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(f"task-bound: {exc}")
    if isinstance(raw_binding, dict):
        values = raw_binding.get("bindings", raw_binding)
        if isinstance(values, dict):
            result["binding"] = {str(k): str(v) for k, v in values.items() if isinstance(v, str)}
            result["binding_valid"] = all(isinstance(v, str) for v in values.values())
            if not result["binding_valid"]:
                result["errors"].append("task-bound: invalid session/thread binding value")
        elif isinstance(values, list):
            for item in values:
                if not isinstance(item, dict) or not isinstance(item.get("sessionId"), str) or not isinstance(item.get("threadId"), str):
                    result["binding_valid"] = False
                    break
                result["binding"][item["sessionId"]] = item["threadId"]
            else:
                result["binding_valid"] = True
            if not result["binding_valid"]:
                result["errors"].append("task-bound: invalid binding row")
        else:
            result["errors"].append("task-bound: unsupported binding format")
    else:
        result["errors"].append("task-bound: unsupported binding format")

    listing, error = BB.parse_json(["thread", "list", "--json"], 8.0)
    if isinstance(listing, list):
        result["children"] = [row for row in listing if isinstance(row, dict) and isinstance(row.get("id"), str) and
                              row.get("parentThreadId") == thread_id and row.get("id") != thread_id]
        result["list_valid"] = True
    else:
        result["errors"].append(f"thread list: {error}")

    shown, error = BB.parse_json(["thread", "show", thread_id, "--json"], 8.0)
    if shown is not None:
        for obj in flatten_dicts(shown):
            if obj.get("id") == thread_id and isinstance(obj.get("status"), str):
                result["orch_status"] = obj.get("status")
                break
        if result["orch_status"] is None and isinstance(shown, dict):
            result["orch_status"] = shown.get("status")
        result["show_valid"] = isinstance(result["orch_status"], str) and bool(result["orch_status"])
        if not result["show_valid"]:
            result["errors"].append("thread show: status missing")
    else:
        result["errors"].append(f"thread show: {error}")

    qout, qerror = BB.command(["thread", "queue", "list", thread_id], 8.0)
    if not qerror and "no queued" in qout.lower():
        result["queue_count"] = 0
        result["queue_valid"] = True
    elif not qerror:
        try:
            q = json.loads(qout)
            if isinstance(q, list):
                result["queue_count"] = len(q)
                result["queue_valid"] = True
            elif isinstance(q, dict):
                items = q.get("items", q.get("messages"))
                if isinstance(items, list):
                    result["queue_count"] = len(items)
                    result["queue_valid"] = True
        except json.JSONDecodeError:
            pass
        if not result["queue_valid"]:
            result["errors"].append("thread queue list: unknown output")
    else:
        result["errors"].append(f"thread queue list: {qerror}")

    visible_ids = {row.get("id") for row in result["children"] if row.get("status") == "active" and
                   row.get("visibility") == "visible" and not row.get("deletedAt") and not row.get("archivedAt")}
    by_id = {row.get("id"): row for row in result["children"] if row.get("id")}
    live_ids = {s.get("id") for s in live_sessions}
    for sess in sessions:
        sess["thread_id"] = result["binding"].get(sess["id"])
        sess["visible"] = sess["thread_id"] in visible_ids if sess["thread_id"] else False
        bound = by_id.get(sess["thread_id"], {}) if sess["thread_id"] else {}
        # Facts for the alert, so the orchestrator checks by id, never by title.
        sess["binding_fact"] = (f"bound to {sess['thread_id']} (title '{bound.get('title', '?')}', "
                                f"status {bound.get('status', 'not listed')}, "
                                f"visibility {bound.get('visibility', '?')})"
                                if sess["thread_id"] else "no BB thread bound to this session")
    for child in result["children"]:
        if child.get("status") == "active":
            child["visible"] = child.get("id") in visible_ids
            child["last_activity"] = seconds(child.get("latestAttentionAt") or child.get("updatedAt") or child.get("createdAt"))
            child["bound_sessions"] = [s for s in sessions if s.get("thread_id") == child.get("id")]
            child["sessions"] = [s for s in child["bound_sessions"] if s.get("id") in live_ids]
    result["by_id"] = by_id
    return result

def state_read(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def state_write(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")

def append_note(root: str, note: str, dry_run: bool) -> None:
    path = os.path.join(root, ".lanes", "watch-ALERT.txt")
    if dry_run:
        print(f"DRY-RUN: would append user note to {path}: {note}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {note}\n")

def dispatch(thread_id: str, messages: list[str], dry_run: bool, mode: str = "queue") -> None:
    """Queue by default; `auto` interrupts a live turn (urgent alerts, rate-limited by the caller)."""
    if not messages:
        return
    lines = [message.replace("\n", " ").strip() for message in messages]
    text = "\n".join(lines)
    if dry_run:
        suffix = "" if mode == "queue" else f" (--mode {mode}, interrupts now)"
        print(f"DRY-RUN: would queue to {thread_id}:{suffix}\n{text}")
        return
    out, error = BB.command(["thread", "tell", thread_id, "--mode", mode, text], 8.0)
    if error:
        print(f"WATCH ERROR: bb thread tell failed: {error}", file=sys.stderr)
    elif out:
        print(out)
