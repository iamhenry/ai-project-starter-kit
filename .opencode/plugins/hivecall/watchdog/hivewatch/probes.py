from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import time
from pathlib import Path

from hivewatch.promise import bind_promise_paths, parse_promise
from hivewatch.shell import BB, command, parse_elapsed, parse_load, seconds, setting


def load_host_facts(root: str, now: float, env: dict[str, str]) -> dict:
    uptime, uptime_error = command(["uptime"], 3.0)
    load = parse_load(uptime)
    df, df_error = command(["df", "-k", "/"], 3.0)
    free_gb = None
    lines = df.splitlines()
    if len(lines) >= 2:
        fields = lines[-1].split()
        try:
            free_gb = int(fields[3]) * 1024 / 1_000_000_000
        except (IndexError, ValueError):
            pass

    ps, ps_error = command(["ps", "-axo", "pid=,ppid=,etime=,command="], 2.0)
    processes = []
    for line in ps.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) < 4:
            continue
        pid, ppid, elapsed, cmd = fields
        if not ("recordVideo" in cmd or "--console-pty" in cmd or
                re.search(r"\blog\s+stream\b|\bsimctl\s+(?:launch|spawn)\b", cmd)):
            continue
        try:
            age = parse_elapsed(elapsed)
        except (ValueError, IndexError):
            age = 0
        processes.append({"pid": int(pid), "ppid": int(ppid), "age": age, "command": cmd,
                          "orphan": int(ppid) == 1 or age > setting(env, "WATCH_ORPHAN_MIN", 15) * 60})

    # Keep the explicit recorder probe: ps supplies parentage and elapsed time.
    recorder_probe, _ = command(["pgrep", "-fl", "recordVideo"])
    recorder_pids = set()
    for line in recorder_probe.splitlines():
        m = re.match(r"(\d+)\s+", line)
        if m:
            recorder_pids.add(int(m.group(1)))
    if recorder_pids:
        for proc in processes:
            if "recordVideo" in proc["command"]:
                proc["from_pgrep"] = proc["pid"] in recorder_pids

    sims, sims_error = command(["xcrun", "simctl", "list", "devices", "booted"], 2.0)
    booted_sims = [line.strip() for line in sims.splitlines() if re.search(r"\(Booted\)", line)]

    # shortcut: prune Git internals and nested .lanes worktrees; add a watched folder if recordings move there.
    recent_big = []
    if root and os.path.isdir(root):
        args = ["find", root, "(", "-type", "d", "-name", ".git", "-o", "(", "-path",
                os.path.join(root, ".lanes", "*"), "-type", "d", ")", ")", "-prune", "-o",
                "-type", "f", "-cmin", f"-{int(setting(env, 'WATCH_LARGE_FILE_MIN', 15))}", "-print"]
        candidates, find_error = command(args, 2.5)
        for path in candidates.splitlines():
            try:
                stat = os.stat(path, follow_symlinks=False)
                created = getattr(stat, "st_birthtime", stat.st_ctime)
            except OSError:
                continue
            if stat.st_size > setting(env, "WATCH_LARGE_FILE_MB", 100) * 1024 * 1024 and now - created <= setting(env, "WATCH_LARGE_FILE_MIN", 15) * 60:
                recent_big.append({"path": path, "name": os.path.basename(path), "mtime": stat.st_mtime,
                                   "size": stat.st_size, "created": created})
    else:
        find_error = "REPO is not a directory"
    return {"load": load, "uptime": uptime, "uptime_error": uptime_error,
            "uptime_valid": not uptime_error and load is not None,
            "free_gb": free_gb, "df_error": df_error,
            "df_valid": not df_error and free_gb is not None,
            "processes": processes, "processes_valid": not ps_error,
            "ps_error": ps_error, "booted_sims": booted_sims,
            "sims_error": sims_error, "sims_valid": not sims_error,
            "recent_big": recent_big, "recent_big_valid": not find_error,
            "recent_big_error": find_error}


def load_server() -> dict:
    text, error = BB.command(["opencode"], 8.0)
    port_match = re.search(r"\bport\s*:\s*(\d+)", text, re.I)
    attached_match = re.search(r"\battached:\s*(true|false)\b", text, re.I)
    port = int(port_match.group(1)) if port_match else None
    attached = attached_match.group(1).lower() == "true" if attached_match else None
    reachable = False
    if port:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.35):
                reachable = True
        except OSError:
            pass
    valid = not error and port is not None and attached is not None
    return {"attached": attached, "port": port, "reachable": reachable, "valid": valid,
            "error": error or ("missing attached status or port" if not valid else "")}


def bb_child_sessions(thread_id: str) -> list[str]:
    """OpenCode sessions behind BB child threads of the orchestrator. A `bb thread spawn` child runs its
    own root session (no parent_id), so the parent_id query alone would not see it. Read-only."""
    return BB.child_sessions(thread_id)


def load_sessions(session_id: str, now: float, root: str = "", verify_dir: str = "",
                  extra_ids: list[str] | None = None) -> dict:
    db = os.path.expanduser("~/.local/share/opencode/opencode.db")
    result = {"live": [], "children": [], "last_orch_message": None, "last_compaction": None,
              "error": "", "valid": False}
    if not session_id:
        result["error"] = "ORCH_SESSION is unset"
        return result
    if not os.path.exists(db):
        result["error"] = "OpenCode database missing"
        return result
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3.0)
        con.execute("PRAGMA query_only=ON")
        con.execute("PRAGMA busy_timeout=3000")
        extra = [ident for ident in (extra_ids or []) if ident != session_id]
        rows = con.execute(f"""SELECT s.id,s.agent,s.time_created,MAX(m.time_updated),
            MAX(CASE WHEN m.type='assistant' THEN m.time_updated END),s.time_idle,s.idle_outcome
            FROM session_v2 s LEFT JOIN session_message m ON m.session_id=s.id
            WHERE s.parent_id=? {"OR s.id IN (" + ",".join("?" * len(extra)) + ")" if extra else ""}
            GROUP BY s.id""",
                            (session_id, *extra)).fetchall()
        for ident, agent, created, last, last_assistant, time_idle, idle_outcome in rows:
            last_s = seconds(last)
            if ident == session_id:
                continue
            child = {"id": ident, "agent": agent or "unknown", "created": seconds(created),
                     "last_message": last_s, "last_assistant": seconds(last_assistant),
                     "time_idle": time_idle, "idle_outcome": idle_outcome}
            result["children"].append(child)
            if time_idle is None and idle_outcome is None:
                result["live"].append(child)
        if result["children"]:
            placeholders = ",".join("?" for _ in result["children"])
            query_deadline = time.monotonic() + 1.0
            con.set_progress_handler(lambda: int(time.monotonic() > query_deadline), 1000)
            try:
                messages = con.execute(f"""SELECT session_id,seq,time_created,data FROM session_message
                    WHERE type='user' AND session_id IN ({placeholders}) ORDER BY session_id,seq""",
                                       tuple(child["id"] for child in result["children"])).fetchall()
            finally:
                con.set_progress_handler(None, 0)
            by_id = {child["id"]: child for child in result["children"]}
            grouped = {}
            for child_id, seq, created, raw in messages:
                try:
                    body = json.loads(raw)
                    text = body.get("text", "") if isinstance(body, dict) else ""
                    if not isinstance(text, str):
                        text = ""
                except (json.JSONDecodeError, TypeError):
                    by_id[child_id]["promise_read_valid"] = False
                    continue
                grouped.setdefault(child_id, []).append((seq, seconds(created), text))
            for child_id, child in by_id.items():
                user_messages = grouped.get(child_id, [])
                if user_messages:
                    promise = parse_promise(user_messages[0][2])
                    child["promise"] = bind_promise_paths(promise, root, verify_dir) if promise else None
                    child["steers"] = [stamp for _, stamp, _ in user_messages[1:] if stamp is not None]
                    child["brief_at"] = user_messages[0][1]
                    child["talkback"] = bool(re.search(r"^\s*TALK-BACK:", user_messages[0][2], re.M))
                else:
                    child["promise"] = None
                    child["steers"] = []
        row = con.execute("SELECT MAX(time_updated) FROM session_message WHERE session_id=?", (session_id,)).fetchone()
        result["last_orch_message"] = seconds(row[0]) if row else None
        # Only the latest assistant message can describe the current stop.
        ids = [session_id] + [child["id"] for child in result["children"]]
        result["stop_errors"] = []
        for ident in ids:
            row = con.execute("""SELECT seq,data FROM session_message WHERE session_id=? AND type='assistant'
                ORDER BY seq DESC LIMIT 1""", (ident,)).fetchone()
            try:
                body = json.loads(row[1]) if row else {}
                error = body.get("error") if isinstance(body, dict) else None
                message = error.get("message") if isinstance(error, dict) else None
                if isinstance(message, str):
                    result["stop_errors"].append({"id": f"{ident}:{row[0]}", "session": ident, "message": message})
            except (TypeError, ValueError):
                pass
        # Rule 12: a DCP compress call or a native compaction marks lost context.
        row = con.execute("""SELECT MAX(time_created) FROM session_message WHERE session_id=? AND
            (type='compaction' OR (type='assistant' AND data LIKE '%"name":"compress"%'))""",
                          (session_id,)).fetchone()
        result["last_compaction"] = seconds(row[0]) if row else None
        # Rule 13: the agent the orchestrator session started as, and the one it runs as now.
        for key, order in (("orch_agent_first", "ASC"), ("orch_agent", "DESC")):
            row = con.execute(f"""SELECT time_created, data FROM session_message WHERE session_id=? AND type='assistant'
                AND data LIKE '%"agent":%' ORDER BY seq {order} LIMIT 1""", (session_id,)).fetchone()
            try:
                result[key] = json.loads(row[1]).get("agent") if row else None
            except (TypeError, ValueError):
                result[key] = None
            if key == "orch_agent" and row:
                result["orch_agent_at"] = seconds(row[0])
        con.close()
        result["valid"] = True
    except (sqlite3.Error, OSError) as exc:
        result["error"] = str(exc)
    return result


def load_lane_facts(sessions: list[dict]) -> dict:
    facts = {}
    lane_cache = {}
    for sess in sessions:
        promise = sess.get("promise")
        if not promise or not promise.get("valid") or promise.get("kind") not in ("code", "build"):
            continue
        lane = promise.get("lane_path")
        item = {"valid": False, "latest_mtime": None, "build_mtime": None}
        if not lane:
            facts[sess["id"]] = item
            continue
        if lane not in lane_cache:
            output, error = command(["find", lane, "-type", "d", "-name", ".git", "-prune", "-o",
                                     "-type", "f", "-print"], 2.5)
            latest = None
            build_latest = None
            for path in output.splitlines() if not error else []:
                try:
                    stamp = os.stat(path, follow_symlinks=False).st_mtime
                except OSError:
                    error = f"lane file unreadable: {path}"
                    break
                latest = max(latest or stamp, stamp)
                try:
                    relative = Path(path).relative_to(lane)
                except ValueError:
                    continue
                if relative.suffix.lower() == ".log" and ".build" in relative.parts:
                    build_latest = max(build_latest or stamp, stamp)
            lane_cache[lane] = {"valid": not error, "error": error,
                                "latest_mtime": latest, "build_mtime": build_latest}
        item.update(lane_cache[lane])
        facts[sess["id"]] = item
    return facts
