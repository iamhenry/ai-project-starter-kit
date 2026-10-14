#!/usr/bin/env python3
# PURPOSE — keep a hivecall run healthy and moving: watch machine health,
# check that every agent is on track with what it promised, and keep the run
# going until the ledger (checklist.md or ISA.html) is complete, only genuine
# hard blockers remain, or the run card says the run is closed.
#
# INVARIANTS — what this script is and is not. Change these only with the user's OK.
#
# 1. Watch, never act on the run. It never stops agents, fixes code, records
#    results or edits the ISA. It pauses its own automation when done and
#    deletes it on the check after the run card closes.
#    (Other exception: at most one OpenCode reload per hour when the server is down.)
# 2. No AI, cheap, every 5 minutes. A plain script that finishes in seconds
#    and adds no load of its own.
# 3. Quiet unless it matters. One status line per run. A message only for a
#    real problem, seen on two runs in a row, sent once per problem.
# 4. Judge agents only against their own promise. "Off track" means no real
#    progress on the work the agent's brief promised, past its pace.
#    Never guess from activity, tone or file names.
# 5. Real progress means proof. Testers: a new PASS/FAIL with evidence.
#    Builders: a growing build log or edits in their own lane. Placeholders
#    and "waiting" don't count.
# 6. Fewer false alarms beats more checks. When an alarm is wrong, remove or
#    loosen the check. Never add a special case.
# 7. Never alarm on missing data. If a read fails (BB, OpenCode, files), skip
#    that check for this run.
# 8. Every agent must be visible in BB. An agent running but not shown is
#    always reported.
# 9. Protect the machine. Report high load, low disk, huge files and orphaned
#    recorders or log processes.
# 10. Keep the run moving, without spinning. Nudge the orchestrator when work
#     remains and nothing is running. Progress means a ledger verdict change.
#     Stop nudging after 3 checks with no change and leave the user a note.
# 11. Stop when done. When the ledger is complete or only parked items remain,
#     pause its own automation; when the run card says closed, pause first and
#     delete the automation on the check after a successful pause.
#     While the run card says waiting, never nudge; keep the other checks.

"""Cheap watchdog for a long-running BB/ISA task."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import socket
import sqlite3
import stat as stat_module
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path


VERDICT = re.compile(r"^\|\s*((?:ISC-)?\d+(?:\.\d+)?)\s*\|\s*(PASS|FAIL|BLOCKED)\b(.*)$", re.I)
ISA_VERDICT = re.compile(r"^(ISC-[0-9.]+):\s*(PASS|FAIL|BLOCKED)\s*-\s*([^;]*)", re.I)
PROMISE_DEFAULTS = {
    "screen": {"pace": 10, "signal": "answer"},
    "timed": {"pace": 15, "signal": "answer"},
    "build": {"pace": 10, "signal": "build-log"},
    "code": {"pace": 20, "signal": "lane-file"},
    "helper": {"pace": 20, "signal": "answer"},
}
OFF_TRACK_IDLE_MIN = 10
PLACEHOLDER = re.compile(r"not probed|group stopped|not run|stopped after|pending", re.I)
EVIDENCE_REFERENCE = re.compile(r"(?:`[^`]+\.[^`]+`|[\w./-]+\.(?:png|jpe?g|json|txt|mp4|log|csv|mov|webm)\b|https?://\S+)", re.I)


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


def command(args: list[str], timeout: float = 1.5) -> tuple[str, str]:
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return p.stdout.strip(), p.stderr.strip() or (f"exit {p.returncode}" if p.returncode else "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", str(exc)


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


def extract_html_ledger(source: str):
    """ISA.html: checkbox criteria, owner table, verification section, test strategy."""
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)  # template examples live in comments
    criteria = {}
    for m in re.finditer(r'<li\s+id="(ISC-[0-9.]+)"[^>]*>\s*<input type="checkbox"([^>]*)>', source, re.S):
        criteria[m.group(1)] = "checked" in m.group(2).split()
    owner = []
    table = re.search(r'<table[^>]*id="owner-verification-table"[^>]*>(.*?)</table>', source, re.S)
    if table:
        owner = re.findall(r'<tr>\s*<td>.*?<a href="#(ISC-[0-9.]+)"', table.group(1), re.S)
    verdict_texts = []
    ver = re.search(r'<section id="verification"[^>]*>(.*?)</section>', source, re.S)
    if ver:
        verdict_texts = [html.unescape(re.sub(r"<[^>]*>", "", item)).strip()
                         for item in re.findall(r"<li>(.*?)</li>", ver.group(1), re.S)]
    front = re.search(r"<tr>\s*<th>progress</th>\s*<td>([^<]+)</td>", source, re.S)
    frontmatter = html.unescape(front.group(1)).strip() if front else None
    test_tools = {}
    strategy = re.search(r'<table[^>]*id="test-strategy-table"[^>]*>(.*?)</table>', source, re.S)
    if strategy:
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", strategy.group(1), re.S):
            cells = [html.unescape(re.sub(r"<[^>]*>", "", cell)).strip()
                     for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            ident = re.search(r"ISC-[0-9.]+", cells[0]) if cells else None
            if ident and len(cells) >= 2:
                test_tools[ident.group()] = cells[-1].upper()
    return criteria, owner, verdict_texts, frontmatter, test_tools


def extract_markdown_ledger(source: str):
    """checklist.md: `- [x] ISC-1 ...` items; `ISC-1: PASS - ...` lines under `## Verification`.

    Owner-only items are filtered out at kickoff, so they never count here.
    """
    criteria = {}
    verdict_texts = []
    in_verification = False
    for line in source.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        if heading:
            in_verification = heading.group(1).strip().lower().startswith("verification")
            continue
        item = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+\**(ISC-[0-9.]+)\b", line)
        if item and not in_verification:
            criteria[item.group(2)] = item.group(1).lower() == "x"
        elif in_verification:
            text = re.sub(r"^\s*[-*]\s+", "", line).strip()
            if ISA_VERDICT.match(text):
                verdict_texts.append(text)
    progress = re.search(r"^progress:\s*(.+)$", source, re.M | re.I)
    return criteria, [], verdict_texts, progress.group(1).strip() if progress else None, {}


def read_run_status(path: str) -> str | None:
    """Lifecycle status from the run card: running | waiting-owner | waiting-usage | closed."""
    return read_run_card(path)["status"]


def read_run_card(path: str) -> dict:
    """Read the run-card lifecycle and any current waiting note."""
    try:
        source = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {"valid": False, "status": None, "waiting_text": None}
    m = re.search(r"^\s*(?:[-*]\s*)?\**status\**:\s*`?([a-z-]+)", source, re.M | re.I)
    waiting = re.search(r"^\s*waiting\s*:\s*(\S.*?)\s*$", source, re.M | re.I)
    return {"valid": True, "status": m.group(1).lower() if m else None,
            "waiting_text": waiting.group(1).strip() if waiting else None}


def pause_automation(env: dict[str, str], dry_run: bool) -> str:
    """Rule 11: switch itself off. Returns a short result for the heartbeat."""
    automation_id = env.get("AUTOMATION_ID", "")
    if "AUTOMATION_ID" not in env and env.get("PROJECT_ID") and env.get("ORCH_THREAD"):
        listing, _ = parse_json_command(["bb", "automation", "list", "--project", env["PROJECT_ID"], "--json"])
        name = f"hivecall watchdog {env['ORCH_THREAD']}"
        for item in flatten_dicts(listing):
            if item.get("name") == name and str(item.get("id", "")).startswith("auto_"):
                automation_id = item["id"]
                break
    if not automation_id:
        return "no automation id (set AUTOMATION_ID or PROJECT_ID)"
    if dry_run:
        print(f"DRY-RUN: would run bb automation pause {automation_id}")
        return f"would pause {automation_id}"
    args = ["bb", "automation", "pause", automation_id]
    if env.get("PROJECT_ID"):
        args += ["--project", env["PROJECT_ID"]]  # bb requires it outside a thread
    _, error = command(args, 10.0)
    return f"pause {automation_id} failed: {error}" if error else f"paused {automation_id}"


def delete_automation(env: dict[str, str], dry_run: bool) -> str:
    """Delete itself after a closed run. Unlike pause, deletion never looks up by name."""
    automation_id = env.get("AUTOMATION_ID", "")
    if not automation_id:
        return "no explicit automation id; not deleting"
    if not env.get("PROJECT_ID"):
        return "no project id; not deleting"
    args = ["bb", "automation", "delete", automation_id, "--project", env["PROJECT_ID"], "--yes"]
    if dry_run:
        print(f"DRY-RUN: would run {' '.join(args)}")
        return f"would delete {automation_id}"
    _, error = command(args, 10.0)
    return f"delete {automation_id} failed: {error}" if error else f"deleted {automation_id}"


def finish_closed_run(state: dict, env: dict[str, str], dry_run: bool) -> None:
    """Retry pause until successful, then retry deletion; only an explicit id is deleted."""
    state["done"] = True
    if not state.get("closed_pause_recorded"):
        state["pause_result"] = pause_automation(env, dry_run)
        if not dry_run and state["pause_result"].startswith("paused "):
            state["closed_pause_recorded"] = True
            state["closed_automation_id"] = env.get("AUTOMATION_ID", "")
        print(f"WATCH DONE: run card closed; {state['pause_result']}")
        return
    if state.get("automation_deleted"):
        return
    automation_id = state.get("closed_automation_id") or env.get("AUTOMATION_ID", "")
    delete_env = dict(env, AUTOMATION_ID=automation_id)
    state["delete_result"] = delete_automation(delete_env, dry_run)
    if state["delete_result"].startswith("deleted "):
        state["automation_deleted"] = True
    print(f"WATCH DONE: run card closed; {state['delete_result']}")


def clear_done_state(state: dict) -> None:
    for key in ("done", "pause_result", "closed_pause_recorded", "closed_automation_id",
                "delete_result", "automation_deleted"):
        state.pop(key, None)


def parse_isa(path: str, root: str = "") -> dict:
    try:
        source = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": str(exc), "pass": 0, "total": 0, "owner": [], "owner_done": 0,
                "blocked": [], "checked": [], "done": False, "pass_lines": 0, "frontmatter": None,
                "pass_ids": [], "fails": [], "test_tools": {}, "latest_verdicts": {},
                "ledger_mtime": None, "criteria": [], "regressions": [], "owner_only_ids": [],
                "verdict_count": 0}
    try:
        ledger_mtime = Path(path).stat().st_mtime
    except OSError:
        ledger_mtime = None

    if str(path).lower().endswith((".md", ".markdown")):
        criteria, owner, verdict_texts, frontmatter, test_tools = extract_markdown_ledger(source)
        owner_only_ids = set()
    else:
        criteria, owner, verdict_texts, frontmatter, test_tools = extract_html_ledger(source)
        uncommented = re.sub(r"<!--.*?-->", "", source, flags=re.S)
        owner_only = re.search(r'<ul[^>]*id="owner-only"[^>]*>(.*?)</ul>', uncommented, re.S)
        owner_only_ids = {normalize_ident(ident) for ident in
                          re.findall(r"ISC-[0-9.]+", owner_only.group(1) if owner_only else "")}
    checked = {ident for ident, value in criteria.items() if value}

    latest: dict[str, tuple[str, str]] = {}
    pass_ids = set()
    pass_lines = 0
    fails = []
    fail_occurrences = {}
    fail_counts: dict[str, int] = {}
    pass_history = set()
    verdict_count = 0
    if verdict_texts:
        for text in verdict_texts:
            m = ISA_VERDICT.match(text)
            if not m:
                continue
            ident, status, reason = m.groups()
            status = status.upper()
            verdict_count += 1
            latest[ident] = (status, reason.strip())
            if status == "PASS":
                pass_lines += 1
                pass_ids.add(ident)
                pass_history.add(normalize_ident(ident))
                fail_counts[normalize_ident(ident)] = 0
            if status == "FAIL":
                fail_counts[normalize_ident(ident)] = fail_counts.get(normalize_ident(ident), 0) + 1
                signature = hashlib.sha256(text.encode()).hexdigest()[:12]
                fail_occurrences[signature] = fail_occurrences.get(signature, 0) + 1
                fails.append((ident, f"{signature}-{fail_occurrences[signature]}", text))

    blocked = {ident for ident, (status, _) in latest.items() if status == "BLOCKED" and ident not in checked}
    parked = (set(owner) | blocked) - checked
    regressions = {normalize_ident(ident) for ident, (status, _) in latest.items()
                   if status == "FAIL" and normalize_ident(ident) in pass_history}
    latest_fail_ids = {normalize_ident(ident) for ident, (status, _) in latest.items() if status == "FAIL"}
    criteria_ids = {normalize_ident(ident) for ident in criteria}
    checked_ids = {normalize_ident(ident) for ident in checked}
    completion_parked = ({normalize_ident(ident) for ident in owner} |
                         {normalize_ident(ident) for ident in blocked} | owner_only_ids) - checked_ids
    done = (bool(criteria) and not (latest_fail_ids & (criteria_ids - completion_parked)) and
            all(ident in checked_ids or ident in completion_parked for ident in criteria_ids))
    owner_done = sum(ident in checked for ident in owner)
    root_path = Path(root).resolve() if root else Path.cwd().resolve()
    enriched_fails = []
    for ident, signature, text in fails:
        evidence = re.search(r"(?:^|;)\s*evidence\s+([^;]+)", text, re.I)
        evidence_mtime = None
        if evidence:
            evidence_path = Path(evidence.group(1).strip())
            try:
                evidence_path = (evidence_path if evidence_path.is_absolute() else root_path / evidence_path).resolve()
                evidence_path.relative_to(root_path)
                evidence_mtime = evidence_path.stat().st_mtime
            except (OSError, RuntimeError, ValueError):
                pass
        enriched_fails.append((ident, signature, text, test_tools.get(ident), evidence_mtime))
    return {"pass": len(checked), "total": len(criteria), "owner": owner, "owner_done": owner_done,
            "blocked": sorted(blocked), "parked": sorted(parked), "checked": sorted(checked),
            "done": done, "pass_lines": pass_lines, "pass_ids": sorted(pass_ids),
            "frontmatter": frontmatter, "fails": enriched_fails, "test_tools": test_tools,
            "latest_verdicts": {normalize_ident(ident): {"status": status, "reason": reason}
                                for ident, (status, reason) in latest.items()},
            "fail_counts": fail_counts,
            "criteria": sorted(normalize_ident(ident) for ident in criteria),
            "regressions": sorted(regressions), "owner_only_ids": sorted(owner_only_ids),
            "ledger_mtime": ledger_mtime, "verdict_count": verdict_count,
            "owner_only": len(re.findall(r"<li\b", re.sub(r"<!--.*?-->", "", (
                re.search(r'<ul[^>]*id="owner-only"[^>]*>(.*?)</ul>', source, re.S) or re.match(r"()", "")).group(1), flags=re.S))),
            "error": "" if criteria else "no ISA criteria found"}


def walk_files(root: str, errors: list[str] | None = None):
    if not root or not os.path.isdir(root):
        return

    def onerror(exc: OSError) -> None:
        if errors is not None:
            errors.append(str(exc))

    for base, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            path = os.path.join(base, name)
            try:
                stat = os.stat(path, follow_symlinks=False)
            except OSError as exc:
                if errors is not None:
                    errors.append(f"{path}: {exc}")
                continue
            if not stat_module.S_ISREG(stat.st_mode):
                continue
            yield {"path": path, "name": name, "mtime": stat.st_mtime, "size": stat.st_size,
                   "created": getattr(stat, "st_birthtime", stat.st_mtime)}


def setting(env: dict[str, str], name: str, default: float) -> float:
    try:
        value = float(env.get(name, default))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


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
    text, error = command(["bb", "opencode"], 8.0)
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


def load_sessions(session_id: str, now: float, root: str = "", verify_dir: str = "") -> dict:
    db = os.path.expanduser("~/.local/share/opencode/opencode.db")
    result = {"live": [], "children": [], "last_orch_message": None, "error": "", "valid": False}
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
        rows = con.execute("""SELECT s.id,s.agent,s.time_created,MAX(m.time_updated),
            MAX(CASE WHEN m.type='assistant' THEN m.time_updated END),s.time_idle,s.idle_outcome
            FROM session_v2 s LEFT JOIN session_message m ON m.session_id=s.id
            WHERE s.parent_id=? GROUP BY s.id""",
                            (session_id,)).fetchall()
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
        con.close()
        result["valid"] = True
    except (sqlite3.Error, OSError) as exc:
        result["error"] = str(exc)
    return result


def parse_json_command(args: list[str], timeout: float = 8.0):
    out, error = command(args, timeout)
    try:
        return json.loads(out), error
    except (json.JSONDecodeError, TypeError):
        return None, error or ("invalid JSON" if out else "empty output")


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

    listing, error = parse_json_command(["bb", "thread", "list", "--json"], 8.0)
    if isinstance(listing, list):
        result["children"] = [row for row in listing if isinstance(row, dict) and isinstance(row.get("id"), str) and
                              row.get("parentThreadId") == thread_id and row.get("id") != thread_id]
        result["list_valid"] = True
    else:
        result["errors"].append(f"thread list: {error}")

    shown, error = parse_json_command(["bb", "thread", "show", thread_id, "--json"], 8.0)
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

    qout, qerror = command(["bb", "thread", "queue", "list", thread_id], 8.0)
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
    for child in result["children"]:
        if child.get("status") == "active":
            child["visible"] = child.get("id") in visible_ids
            child["last_activity"] = seconds(child.get("latestAttentionAt") or child.get("updatedAt") or child.get("createdAt"))
            child["bound_sessions"] = [s for s in sessions if s.get("thread_id") == child.get("id")]
            child["sessions"] = [s for s in child["bound_sessions"] if s.get("id") in live_ids]
    result["by_id"] = by_id
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


def parse_result_text(text: str, mtime: float) -> dict:
    rows = []
    table_rows = []
    waits = {}
    for line in text.splitlines():
        match = VERDICT.match(line)
        if match:
            ident, status, detail = match.groups()
            ident = normalize_ident(ident)
            status = status.upper()
            rows.append((ident, status))
            table_rows.append({"id": ident, "status": status,
                               "text": detail.strip().strip("|").strip(),
                               "placeholder": bool(PLACEHOLDER.search(detail)),
                               "evidence": bool(EVIDENCE_REFERENCE.search(detail)),
                               "signature": hashlib.sha256(line.encode()).hexdigest()})
        pending = re.search(r"PENDING-WAIT\s+(?:(ISC-[0-9.]+)\s+)?until\s+([^\s;]+)", line, re.I)
        if not pending:
            continue
        ident = normalize_ident(pending.group(1)) if pending.group(1) else "*"
        value = pending.group(2)
        try:
            if re.fullmatch(r"\d{1,2}:\d{2}", value):
                local = dt.datetime.fromtimestamp(mtime).astimezone()
                deadline = local.replace(hour=int(value[:2]), minute=int(value[3:]), second=0, microsecond=0)
                if deadline.timestamp() < mtime - 12 * 3600:
                    deadline += dt.timedelta(days=1)
                stamp = deadline.timestamp()
            else:
                deadline = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if deadline.tzinfo is None:
                    deadline = deadline.astimezone()
                stamp = deadline.timestamp()
            waits[ident] = {"until": stamp + 300, "from": mtime}
        except (ValueError, OverflowError):
            continue
    return {"rows": rows, "table_rows": table_rows, "waits": waits,
            "pending_wait": max((wait["until"] for wait in waits.values()), default=None)}


def load_results(directory: str, isa: dict, now: float, promised_paths: set[str] | None = None) -> dict:
    valid = bool(directory and os.path.isdir(directory) and os.access(directory, os.R_OK))
    error = "" if valid else f"verification folder unavailable: {directory or '(unset)'}"
    scan_errors = []
    files = list(walk_files(directory, scan_errors))
    newest = max(files, key=lambda f: f["mtime"], default=None)
    result_files = []
    for f in files:
        if not f["name"].endswith("-result.md") or (
                now - f["mtime"] > 6 * 3600 and f["path"] not in (promised_paths or set())):
            continue
        try:
            text = Path(f["path"]).read_text(encoding="utf-8", errors="replace")
            parsed = parse_result_text(text, f["mtime"])
        except OSError as exc:
            scan_errors.append(f"verification result unreadable: {f['path']}: {exc}")
            continue
        result_files.append({"path": f["path"], "name": f["name"], "mtime": f["mtime"],
                             **parsed, "verdict_count": len(parsed["rows"]),
                             "builder": bool(re.search(r"build|builder", f["path"], re.I))})
    if scan_errors:
        valid = False
        error = f"verification scan incomplete ({len(scan_errors)} errors): {scan_errors[0]}"
    return {"files": files, "newest": newest, "results": result_files,
            "valid": valid, "error": error}


def collect(env: dict[str, str], now: float | None = None) -> dict:
    now = now or time.time()
    root = env.get("REPO", "")
    isa = parse_isa(env.get("LEDGER") or env.get("ISA") or os.path.join(root, "_ai/docs/ISA.html"), root)
    run_card = read_run_card(env.get("RUN_CARD") or os.path.join(root, ".hivecall", "run.md"))
    run_status = run_card["status"]
    host = load_host_facts(root, now, env)
    sessions = load_sessions(env.get("ORCH_SESSION", ""), now, root, env.get("VERIFY_DIR", ""))
    bb = load_bb(env.get("ORCH_THREAD", ""), sessions["children"], sessions["live"])
    server = load_server()
    promised_paths = {session["promise"].get("result_path") for session in sessions["children"]
                      if session.get("promise") and session["promise"].get("result_path")}
    evidence = load_results(env.get("VERIFY_DIR", ""), isa, now, promised_paths)
    lanes = load_lane_facts(sessions["live"])
    head, head_error = command(["git", "-C", root, "rev-parse", "HEAD"], 2.0)
    return {"now": now, "host": host, "server": server, "sessions": sessions, "bb": bb,
            "isa": isa, "run_status": run_status, "run_card": run_card, "evidence": evidence,
            "lanes": lanes, "head": head,
            "head_valid": bool(head and not head_error),
            "head_error": head_error}


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


def report(snapshot: dict) -> str:
    host, server, sessions, bb, isa, evidence = (snapshot[k] for k in
        ("host", "server", "sessions", "bb", "isa", "evidence"))
    newest = evidence["newest"]
    newest_text = (f"{Path(newest['path']).name} ({minutes_since(newest['mtime'], snapshot['now']):.0f} min ago)"
                   if newest else "none") if evidence.get("valid", False) else "unknown"
    port = server["port"] if server["port"] else "unknown"
    live_count = len(sessions["live"]) if sessions.get("valid", False) else "unknown"
    visible_count = (sum(1 for t in bb["children"] if t.get("status") == "active" and t.get("visible"))
                     if bb.get("list_valid", False) else "unknown")
    status = ("complete/parked-only" if isa["done"] else "work remains") if not isa.get("error") else "unknown"
    isa_progress = (f"{isa['pass']}/{isa['total']} checked, {isa['pass_lines']} PASS lines; "
                    f"frontmatter {isa.get('frontmatter') or 'unknown'}; owner {isa['owner_done']}/{len(isa['owner'])}; "
                    f"blocked {len(isa['blocked'])}; parked {len(isa.get('parked', []))}"
                    if not isa.get("error") else "unknown")
    lines = [
        "WATCH REPORT",
        f"Load (1m): {host['load'] if host.get('uptime_valid') else 'unknown'}; disk free: {host['free_gb']:.1f} GB" if host.get("df_valid") else f"Load (1m): {host['load'] if host.get('uptime_valid') else 'unknown'}; disk free: unknown",
        f"Booted simulators: {len(host['booted_sims']) if host.get('sims_valid') else 'unknown'}; watched processes: {len(host['processes']) if host.get('processes_valid') else 'unknown'}",
        f"OpenCode: attached={server['attached'] if server.get('valid') else 'unknown'} port={port} TCP={('reachable' if server['reachable'] else 'unreachable') if server.get('valid') else 'unknown'}",
        f"Live child sessions: {live_count}; BB-visible active children: {visible_count}; orchestrator={bb['orch_status'] if bb.get('show_valid') else 'unknown'}; queue={bb['queue_count'] if bb.get('queue_valid') else 'unknown'}",
        f"ISA: {isa_progress}; {status}",
        f"Newest evidence: {newest_text}; recent result files: {len(evidence['results']) if evidence.get('valid') else 'unknown'}",
    ]
    errors = [e for e in (isa.get("error"), host.get("uptime_error"), host.get("df_error"),
                           host.get("sims_error"), host.get("ps_error"), host.get("recent_big_error"),
                           server.get("error"), sessions.get("error"), evidence.get("error"),
                           *bb.get("errors", [])) if e]
    if errors:
        lines.append("Read warnings: " + "; ".join(errors))
    return "\n".join(lines)


def summary_line(snapshot: dict, alert_tags: list[str]) -> str:
    host = snapshot.get("host", {})
    sessions = snapshot.get("sessions", {})
    bb = snapshot.get("bb", {})
    isa = snapshot.get("isa", {})
    load = host.get("load") if host.get("uptime_valid") else None
    free = host.get("free_gb") if host.get("df_valid") else None
    visible = (sum(1 for child in bb.get("children", [])
                   if child.get("status") == "active" and child.get("visible"))
               if bb.get("list_valid") else None)
    live = len(sessions.get("live", [])) if sessions.get("valid") else None
    if visible is None and live is None:
        agents = "? agents visible"
    elif visible is not None and visible == live:
        agents = f"{visible} agents visible"
    else:
        agents = f"{visible if visible is not None else '?'}/{live if live is not None else '?'} agents visible"
    ledger = (f"{isa['pass']}/{isa['total']}" if not isa.get("error") and
              isa.get("pass") is not None and isa.get("total") is not None else "?/?")
    status = "OK" if not alert_tags else f"ALERT: {alert_tags[0]}" + (
        f" +{len(alert_tags) - 1}" if len(alert_tags) > 1 else "")
    return (f"load {load:.0f}" if load is not None else "load ?") + " · " + \
        (f"disk {free:.0f} GB" if free is not None else "disk ? GB") + \
        f" · {agents} · {ledger} · {status}"


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


def append_note(root: str, note: str, dry_run: bool) -> None:
    path = os.path.join(root, ".lanes", "watch-ALERT.txt")
    if dry_run:
        print(f"DRY-RUN: would append user note to {path}: {note}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {note}\n")


def dispatch(thread_id: str, messages: list[str], dry_run: bool) -> None:
    if not messages:
        return
    lines = [message.replace("\n", " ").strip() for message in messages]
    text = "\n".join(lines)
    if dry_run:
        print(f"DRY-RUN: would queue to {thread_id}:\n{text}")
        return
    out, error = command(["bb", "thread", "tell", thread_id, "--mode", "queue", text], 8.0)
    if error:
        print(f"WATCH ERROR: bb thread tell failed: {error}", file=sys.stderr)
    elif out:
        print(out)


def status_table(snapshot: dict) -> list[str]:
    """One-row owner status table appended to every watchdog message (lines, not one string)."""
    isa = snapshot.get("isa", {})
    if isa.get("error") or not isa.get("total"):
        return []
    checked = {normalize_ident(i) for i in isa.get("checked", [])}
    parked = {normalize_ident(i) for i in isa.get("parked", [])} - checked
    owner = {normalize_ident(i) for i in isa.get("owner", [])} - checked
    promised = set()
    for sess in snapshot.get("sessions", {}).get("live", []):
        promise = sess.get("promise") or {}
        promised |= {normalize_ident(i) for i in promise.get("rows", set())}
    in_progress = promised - checked - parked - owner
    total = isa["total"]
    not_started = max(total - len(checked) - len(parked) - len(owner) - len(in_progress), 0)
    owner_cell = f"{len(owner)}" + (f" (+{isa.get('owner_only', 0)} not counted)" if isa.get("owner_only") else "")
    return ["| Done | In progress | Not started | Stuck | Owner-only |",
            "|---|---|---|---|---|",
            f"| {len(checked)}/{total} ({round(len(checked) * 100 / total)}%) | {len(in_progress)} | "
            f"{not_started} | {len(parked)} | {owner_cell} |"]


def evaluate(snapshot: dict, state: dict, env: dict[str, str], dry_run: bool) -> list[str]:
    now = snapshot["now"]
    host, server, sessions, bb, isa, evidence = (snapshot[k] for k in
        ("host", "server", "sessions", "bb", "isa", "evidence"))
    root = env.get("REPO", "")
    thread_id = env.get("ORCH_THREAD", "")
    run_status = snapshot.get("run_status")
    messages: list[str] = []
    notes: list[str] = []
    alert_tags: list[str] = []
    conditions = state.setdefault("conditions", {})

    def emit() -> None:
        if messages:
            messages.extend(status_table(snapshot))
        dispatch(thread_id, messages, dry_run)

    review = state.setdefault("review", {"last_at": now, "alerts": {},
                                          "promise_agents": [], "other_agents": []})
    if not isinstance(review, dict):
        review = state["review"] = {"last_at": now, "alerts": {},
                                    "promise_agents": [], "other_agents": []}
    review.setdefault("last_at", now)
    review.setdefault("alerts", {})
    review.setdefault("promise_agents", [])
    review.setdefault("other_agents", [])

    isa_valid = not isa.get("error")
    if isa_valid:
        active_regressions = set(isa.get("regressions", []))
        for key in list(conditions):
            if key.startswith("regression:") and key.split(":", 1)[1] not in active_regressions:
                conditions.pop(key, None)
        alerted = set(state.get("regressions_alerted", []))
        state["regressions_alerted"] = sorted(alerted & active_regressions)
    if run_status == "running" and isa_valid and not isa.get("done"):
        clear_done_state(state)
    if run_status == "closed":
        finish_closed_run(state, env, dry_run)
        return alert_tags
    if state.get("done"):
        # Ledger-only completion stays paused until the run card is closed.
        state.pop("closed_pause_recorded", None)
        state.pop("closed_automation_id", None)
        state.pop("delete_result", None)
        state["pause_result"] = pause_automation(env, dry_run)
        return alert_tags
    if isa_valid and isa["done"]:
        summary = (f"{isa['pass']}/{isa['total']} PASS, {len(isa.get('parked', []))} parked "
                   f"(owner {isa['owner_done']}/{len(isa['owner'])}, blocked {len(isa['blocked'])})"
                   if isa_valid else "ledger unreadable")
        state["done"] = True
        state["pause_result"] = pause_automation(env, dry_run)
        messages.append(f"WATCH DONE: ledger complete or parked-only ({summary}); watchdog {state['pause_result']}. "
                        "Set the run card status to closed and send the owner the final report.")
        print(f"WATCH DONE: {summary}; {state['pause_result']}")
        emit()
        return alert_tags
    waiting = bool(run_status and run_status.startswith("waiting"))
    if state.get("last_run_status", "").startswith("waiting") and run_status == "running":
        state["continue"] = {}  # owner unblocked the run: nudging may resume
    state["last_run_status"] = run_status or ""

    def trigger(key: str, active: bool, detail: str, severity: int = 1, valid: bool = True) -> bool:
        if not valid:
            return False
        rec = conditions.setdefault(key, {"streak": 0, "last_alert": 0, "severity": 0})
        rec["streak"] = rec.get("streak", 0) + 1 if active else 0
        if not active:
            rec["last_alert"] = 0
            rec["severity"] = 0
        due = active and rec["streak"] >= 2 and not rec.get("last_alert")
        if due:
            rec["last_alert"] = now
            rec["severity"] = severity
            messages.append(detail)
            tag = {
                "high-load": "high load", "low-disk": "low disk", "big-file": "large file",
                "orphan-process": "orphan process", "stuck-builder-log": "stuck builder",
                "stuck-agent": "stuck agent", "unrecorded-pass": "unrecorded PASS",
                "long-agent": "long-running agent", "invisible-agent": "invisible agent",
                "ghost-agent": "ghost agent", "fail-load": "FAIL under load",
                "opencode-down": "server down", "sim-without-agent": "idle simulator",
                "off-track": "off track", "no-talkback": "no talk-back",
                "repeat-fail": "repeat failure", "unclaimed": "unclaimed work",
                "plateau": "plateau", "regression": "regression",
                "leftover-session": "leftover session",
            }.get(key.split(":", 1)[0], "alert")
            if tag not in alert_tags:
                alert_tags.append(tag)
            review["alerts"][tag] = review["alerts"].get(tag, 0) + 1
        return due

    all_live_sessions = list(sessions.get("live", []))
    leftover_sessions = []
    can_check_bindings = (sessions.get("valid", False) and bb.get("list_valid", False) and
                          bb.get("binding_valid", False))
    if can_check_bindings:
        for sess in all_live_sessions:
            child_thread = sess.get("thread_id")
            thread = bb.get("by_id", {}).get(child_thread, {}) if child_thread else {}
            status = thread.get("status")
            if isinstance(status, str) and status.lower() in ("failed", "stopped", "idle"):
                leftover_sessions.append((sess, child_thread))
        if leftover_sessions:
            leftover_ids = {sess["id"] for sess, _ in leftover_sessions}
            sessions["live"] = [sess for sess in all_live_sessions if sess["id"] not in leftover_ids]
        active_leftovers = {"leftover-session:" + sess["id"] for sess, _ in leftover_sessions}
        for key in list(conditions):
            if key.startswith("leftover-session:") and key not in active_leftovers:
                trigger(key, False, "", valid=True)
    for sess, child_thread in leftover_sessions:
        trigger("leftover-session:" + sess["id"], True,
                f"LEFTOVER session {sess['id']} still running after its BB thread {child_thread} ended; "
                "interrupt it before relaunching.",
                valid=can_check_bindings)

    load = host.get("load")
    load_limit = setting(env, "WATCH_LOAD_LIMIT", 150)
    trigger("high-load", load is not None and load > load_limit,
            f"HOST load: 1-minute load {load:.1f} (>{load_limit:g}) on two checks; uptime reports this value."
            if load is not None else "HOST load: uptime reading unavailable.",
            int(load // load_limit) if load else 1, valid=host.get("uptime_valid", False))
    free = host.get("free_gb")
    disk_limit = setting(env, "WATCH_DISK_FREE_GB", 10)
    disk_valid = host.get("df_valid", False)
    critical_disk = free is not None and free < 5
    normal_disk = free is not None and free < disk_limit and not critical_disk
    if critical_disk:
        trigger("low-disk", False, "", valid=disk_valid)
        trigger("low-disk:critical", True,
                f"🚦 HOST disk: only {free:.1f} GB free on / (<5 GB); see df -h /.",
                2, valid=disk_valid)
    else:
        trigger("low-disk:critical", False, "", valid=disk_valid)
        trigger("low-disk", normal_disk,
                f"HOST disk: only {free:.1f} GB free on / (<{disk_limit:g} GB); see df -h /."
                if free is not None else "HOST disk: df reading unavailable.",
                1, valid=disk_valid)
    for f in host.get("recent_big", []):
        age = minutes_since(f["created"], now) or 0
        size_mb = f["size"] / 1_048_576
        trigger("big-file:" + f["path"], True,
                f"HOST large file: {f['path']} is {size_mb:.0f} MB, created {age:.0f} min ago.",
                max(1, int(size_mb // 100)), valid=host.get("recent_big_valid", False))
    orphan_state = state.setdefault("orphan_idle", {})
    no_agent_elapsed = None
    if sessions.get("valid", False):
        if sessions.get("live"):
            orphan_state["no_agent_since"] = None
        else:
            if orphan_state.get("no_agent_since") is None:
                orphan_state["no_agent_since"] = now
            no_agent_elapsed = (now - orphan_state["no_agent_since"]) / 60
    no_agent_long_enough = (no_agent_elapsed is not None and
                            no_agent_elapsed >= setting(env, "WATCH_GHOST_MIN", 15))
    for proc in host.get("processes", []):
        if proc["orphan"]:
            age = proc["age"] / 60
            trigger("orphan-process:" + str(proc["pid"]), no_agent_long_enough,
                    f"HOST orphan process: pid {proc['pid']} ppid {proc['ppid']}, {age:.0f} min; {proc['command'][:160]}.",
                    2 if proc["age"] > 3600 else 1,
                    valid=host.get("processes_valid", False) and sessions.get("valid", False))

    deduped_passes = state.get("unrecorded_passes")
    if not isinstance(deduped_passes, dict):
        deduped_passes = state["unrecorded_passes"] = {}
    for result in evidence["results"]:
        age_m = minutes_since(result["mtime"], now) or 0
        unchanged_or_finished = age_m >= 20 or result_session_finished(result, snapshot)
        rows = result.get("table_rows", [])
        if not rows:
            rows = [{"id": normalize_ident(ident), "status": status, "text": ""}
                    for ident, status in result.get("rows", [])]
        for row in rows:
            ident, status, text = row.get("id"), row.get("status"), row.get("text", "")
            if status != "PASS" or not ident:
                continue
            key = result_verdict_key(result["path"], ident, status, text)
            if key in deduped_passes:
                continue
            legacy = conditions.get(f"unrecorded-pass:{result['path']}:{ident}", {})
            if legacy.get("last_alert"):
                deduped_passes[key] = legacy["last_alert"]
                continue

            latest = isa.get("latest_verdicts", {}).get(ident)
            ledger_has_pass = latest is not None and latest.get("status") == "PASS"
            ledger_is_newer = (latest is not None and isa.get("ledger_mtime") is not None and
                               isa["ledger_mtime"] > result["mtime"])
            if ledger_has_pass or ledger_is_newer:
                trigger("unrecorded-pass:" + key, False, "",
                        valid=evidence.get("valid", False) and isa_valid)
                continue
            due = trigger("unrecorded-pass:" + key, unchanged_or_finished,
                          f"LEDGER {ident}: PASS in {result['path']} is not in a newer ledger entry; record it.",
                          max(1, int(age_m // 60)),
                          valid=evidence.get("valid", False) and isa_valid)
            if due:
                deduped_passes[key] = now

    if sessions.get("valid", False):
        for sess in sessions.get("children", []):
            if sess.get("time_idle") is not None or sess.get("idle_outcome") is not None:
                trigger("off-track:" + sess["id"], False, "")
    for sess in sessions.get("live", []):
        if sess.get("time_idle") is not None or sess.get("idle_outcome") is not None:
            trigger("off-track:" + sess["id"], False, "",
                    valid=sessions.get("valid", False))
            continue
        promise = sess.get("promise")
        if not promise or not promise.get("valid"):
            quiet = minutes_since(sess.get("last_message") or sess.get("created"), now) or 0
            trigger("stuck-agent:" + sess["id"], quiet >= setting(env, "WATCH_AGENT_STUCK_MIN", 10),
                    f"AGENT {sess.get('agent', 'agent')} ({sess['id']}): no session activity for {quiet:.0f} min.",
                    max(1, int(quiet // 60)), valid=sessions.get("valid", False))
        metrics = promise_metrics(sess, snapshot, state)
        if metrics is None:
            continue
        child_id = sess.get("thread_id") or sess["id"]
        child = bb.get("by_id", {}).get(child_id, {})
        title = child.get("title") or sess.get("agent", "agent")
        role = sess.get("agent", "agent")
        unanswered = metrics["unanswered"]
        message_count = f"{unanswered} message{'s' if unanswered != 1 else ''} not acted on"
        idle = off_track_idle_age(sess, snapshot)
        detail = (f"OFF TRACK {title} ({role}) {child_id}: no evidence or session message for "
                  f"{idle:.0f} min (idle limit {OFF_TRACK_IDLE_MIN} min); "
                  f"{metrics['coverage']} rows answered; {metrics['placeholders']} placeholders; "
                  f"{message_count}.") if idle is not None else ""
        trigger("off-track:" + sess["id"],
                idle is not None and idle >= OFF_TRACK_IDLE_MIN, detail,
                valid=metrics["valid"] and idle is not None)

    # Builder sessions with a quiet build log are called out separately from result-file progress.
    for sess in sessions["live"]:
        age = minutes_since(sess.get("created"), now)
        if age is not None:
            max_hours = setting(env, "WATCH_AGENT_MAX_HOURS", 3)
            trigger("long-agent:" + sess["id"], age > max_hours * 60,
                    f"AGENT {sess['agent']} ({sess['id']}): active {age:.0f} min; wrap up and report.",
                    max(1, int(age // (max_hours * 60))), valid=sessions.get("valid", False))
        if not sess.get("visible"):
            idle = minutes_since(sess.get("last_message"), now) or 0
            trigger("invisible-agent:" + sess["id"], True,
                    f"AGENT {sess['agent']} session {sess['id']} is not bound to a visible active BB child; last message {idle:.0f} min ago.",
                    valid=(sessions.get("valid", False) and bb.get("list_valid", False) and
                           bb.get("binding_valid", False)))

    for child in bb["children"]:
        ghost_key = "ghost-agent:" + str(child.get("id"))
        if child.get("status") != "active":
            trigger(ghost_key, False, "", valid=(sessions.get("valid", False) and
                    bb.get("list_valid", False) and bb.get("binding_valid", False)))
            continue
        ghost_min = setting(env, "WATCH_GHOST_MIN", 15)
        bound = child.get("bound_sessions", [])
        active_bound = [s for s in bound if s.get("time_idle") is None and s.get("idle_outcome") is None]
        working = [s for s in active_bound if
                   (minutes_since(s.get("last_message"), now) is not None and
                    minutes_since(s.get("last_message"), now) < ghost_min)]
        if not bound:
            ghost = True
            evidence_text = "no bound OpenCode session"
            inactive = ghost_min
        elif not active_bound:
            ghost = False
            evidence_text = "bound OpenCode session idle or finished"
            inactive = 0
        elif working:
            ghost = False
            evidence_text = f"{len(working)} bound session(s) with recent activity"
            inactive = 0
        else:
            ghost = True
            ages = [minutes_since(s.get("last_message"), now) for s in bound]
            inactive = max((age if age is not None else 10_000 for age in ages), default=10_000)
            evidence_text = ", ".join(
                f"{s['id']} idle={s.get('time_idle') is not None or s.get('idle_outcome') is not None} "
                f"last={minutes_since(s.get('last_message'), now):.0f}m"
                if s.get("last_message") is not None else f"{s['id']} has no session message"
                for s in bound)
        if ghost:
            trigger(ghost_key, True,
                    f"GHOST BB child {child.get('id')} ({child.get('title', 'untitled')}): active; {evidence_text}.",
                    max(1, int(inactive // 60)),
                    valid=(sessions.get("valid", False) and bb.get("list_valid", False) and
                           bb.get("binding_valid", False)))
        else:
            trigger(ghost_key, False, "", valid=(sessions.get("valid", False) and
                    bb.get("list_valid", False) and bb.get("binding_valid", False)))

    # Keep recent samples so FAILs can be judged at the evidence file's timestamp.
    load_samples = state.get("load_samples", [])
    if not isinstance(load_samples, list):
        load_samples = []
    if host.get("uptime_valid", False) and load is not None:
        load_samples.append({"time": now, "load": load})
    load_samples = [sample for sample in load_samples
                    if isinstance(sample, dict) and isinstance(sample.get("time"), (int, float)) and
                    isinstance(sample.get("load"), (int, float)) and abs(now - sample["time"]) <= 7 * 86400]
    state["load_samples"] = load_samples

    # Only gesture/recording/timing FAILs with a nearby high-load evidence sample qualify.
    if isa_valid:
        fail_first = state.setdefault("fail_first_load", {})
        if not state.get("fail_rows_initialized"):
            for ident, signature, *_ in isa.get("fails", []):
                fail_first[ident + ":" + signature] = {"baseline": True, "first_seen": now}
            state["fail_rows_initialized"] = True
        for ident, signature, _, tool, evidence_mtime in isa.get("fails", []):
            key = ident + ":" + signature
            if key not in fail_first:
                fail_first[key] = {"baseline": False, "first_seen": now}
            first = fail_first[key]
            if first.get("baseline"):
                continue
            nearest = min((sample for sample in load_samples
                           if evidence_mtime is not None and abs(sample["time"] - evidence_mtime) <= 600),
                          key=lambda sample: abs(sample["time"] - evidence_mtime), default=None)
            qualifies = tool in ("REC", "GESTURE", "TIME") and nearest is not None and nearest["load"] > 40
            age = minutes_since(evidence_mtime, now) or 0
            detail = (f"FAIL {ident}: {tool} probe evidence was modified at load {nearest['load']:.1f} "
                      f"(>40), {age:.0f} min ago; recheck under calm load." if qualifies else "")
            trigger("fail-load:" + key, qualifies, detail)

    # Three failed attempts are enough to park a row instead of repeating it.
    if isa_valid:
        checked = {normalize_ident(ident) for ident in isa.get("checked", [])}
        parked = {normalize_ident(ident) for ident in isa.get("parked", [])}
        parked |= {normalize_ident(ident) for ident in isa.get("blocked", [])}
        for ident, verdict in isa.get("latest_verdicts", {}).items():
            count = isa.get("fail_counts", {}).get(ident, 0)
            trigger("repeat-fail:" + ident,
                    verdict.get("status") == "FAIL" and count >= 3 and ident not in checked and ident not in parked,
                    f"LOOP {ident}: {count} FAIL verdicts. After 3 different attempts, park it with its exact "
                    "unlock condition and move to other work.")

        active_regressions = set(isa.get("regressions", []))
        alerted_regressions = set(state.setdefault("regressions_alerted", []))
        for ident in sorted(active_regressions):
            due = trigger("regression:" + ident, ident not in alerted_regressions,
                          f"REGRESSION {ident}: passed before, now FAIL. Revert the merge that broke it first, fix on the side.")
            if due:
                alerted_regressions.add(ident)
        state["regressions_alerted"] = sorted(alerted_regressions)

        ledger_signature = hashlib.sha256(json.dumps({
            "criteria": sorted(isa.get("criteria", [])),
            "checked": sorted(isa.get("checked", [])),
            "owner": sorted(isa.get("owner", [])),
            "parked": sorted(isa.get("parked", [])),
            "blocked": sorted(isa.get("blocked", [])),
            "owner_only": sorted(isa.get("owner_only_ids", [])),
            "latest_verdicts": isa.get("latest_verdicts", {}),
            "verdict_count": isa.get("verdict_count", 0),
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        run_card = snapshot.get("run_card", {})
        if (run_card.get("valid", False) and snapshot.get("head_valid", False) and
                isa.get("ledger_mtime") is not None):
            waiting_text = run_card.get("waiting_text")
            waiting_note = state.get("unclaimed_waiting")
            if (not isinstance(waiting_note, dict) or "text" not in waiting_note or
                    "fresh" not in waiting_note or
                    "ledger_signature" not in waiting_note or "head" not in waiting_note):
                fresh = False  # first observation is a baseline, not proof the note is new
            else:
                identity_unchanged = (waiting_note.get("ledger_signature") == ledger_signature and
                                      waiting_note.get("head") == snapshot.get("head"))
                text_changed = waiting_note.get("text") != waiting_text
                fresh = bool(waiting_text) and identity_unchanged and text_changed
                if not text_changed and identity_unchanged:
                    fresh = bool(waiting_text) and bool(waiting_note.get("fresh"))
            state["unclaimed_waiting"] = {"text": waiting_text,
                                           "ledger_signature": ledger_signature,
                                           "head": snapshot.get("head"),
                                           "fresh": fresh}
        session_promises_valid = all(sess.get("promise_read_valid", True)
                                     for sess in sessions.get("live", []))
        unclaimed_valid = (run_status == "running" and run_card.get("valid", False) and
                           sessions.get("valid", False) and session_promises_valid and
                           snapshot.get("head_valid", False) and isa.get("ledger_mtime") is not None)
        waiting_note = state.get("unclaimed_waiting") or {}
        waiting_is_current = (bool(waiting_note.get("text")) and waiting_note.get("fresh", False) and
                              unclaimed_valid and
                              waiting_note.get("text") == run_card.get("waiting_text") and
                              waiting_note.get("ledger_signature") == ledger_signature and
                              waiting_note.get("head") == snapshot.get("head"))
        if unclaimed_valid:
            checked = {normalize_ident(ident) for ident in isa.get("checked", [])}
            parked = {normalize_ident(ident) for ident in isa.get("parked", [])}
            owner = {normalize_ident(ident) for ident in isa.get("owner", [])}
            owner_only = {normalize_ident(ident) for ident in isa.get("owner_only_ids", [])}
            open_items = set(isa.get("criteria", [])) - checked - parked - owner - owner_only
            open_rows = sorted(open_items)
            if state.get("unclaimed_open_set") != open_rows:
                for key in list(conditions):
                    if key.startswith("unclaimed:"):
                        trigger(key, False, "")
                state["unclaimed_open_set"] = open_rows
            claimed = set()
            for sess in sessions.get("live", []):
                promise = sess.get("promise") or {}
                if promise.get("valid"):
                    claimed |= {normalize_ident(ident) for ident in promise.get("rows", set())}
            if open_items and not (open_items & claimed) and not waiting_is_current:
                key = "unclaimed:" + hashlib.sha256("\n".join(open_rows).encode()).hexdigest()[:12]
                trigger(key, True,
                        f"UNCLAIMED: {len(open_rows)} open items have no agent ({', '.join(open_rows)}); "
                        f"{len(sessions.get('live', []))} agents running. Start real work on one, or write a `waiting: <reason>` line in the run card.")
            else:
                for key in list(conditions):
                    if key.startswith("unclaimed:"):
                        trigger(key, False, "")
        elif run_card.get("valid", False) and run_status is not None and run_status != "running":
            for key in list(conditions):
                if key.startswith("unclaimed:"):
                    trigger(key, False, "")
            state["unclaimed_open_set"] = None

    if isa_valid and sessions.get("valid", False):
        signature = [isa.get("verdict_count", 0),
                     [[ident, verdict.get("status"), verdict.get("reason")] for ident, verdict in
                      sorted(isa.get("latest_verdicts", {}).items())]]
        plateau = state.setdefault("plateau", {"active": [], "finish_count": 0,
                                                 "verdict_signature": None})
        if not isinstance(plateau, dict):
            plateau = state["plateau"] = {"active": [], "finish_count": 0,
                                           "verdict_signature": None}
        changed = plateau.get("verdict_signature") is not None and plateau["verdict_signature"] != signature
        if changed:
            plateau["finish_count"] = 0
            plateau["no_progress_since"] = None
        previous_active = set(plateau.get("active", []))
        live_ids = {sess["id"] for sess in all_live_sessions}
        current_active = {sess["id"] for sess in sessions.get("live", [])
                          if (sess.get("promise") or {}).get("valid") and
                          (sess.get("promise") or {}).get("rows")}
        current_active |= previous_active & live_ids
        if not changed:
            plateau["finish_count"] = plateau.get("finish_count", 0) + len(previous_active - current_active)
        plateau.update(active=sorted(current_active), verdict_signature=signature)
        finish_count = plateau["finish_count"]
        if finish_count and plateau.get("no_progress_since") is None:
            plateau["no_progress_since"] = now
        elif not finish_count:
            plateau["no_progress_since"] = None
        since = (dt.datetime.fromtimestamp(plateau["no_progress_since"]).astimezone().isoformat(timespec="minutes")
                 if plateau.get("no_progress_since") is not None else "unknown time")
        trigger("plateau", finish_count >= 3,
                f"PLATEAU (heuristic): 3 helpers ended with no new verdict since {since}. Helpers that finish between "
                "checks are not counted. If the work is stuck, change approach or park.",
                valid=isa_valid and sessions.get("valid", False))

    # OpenCode recovery is intentionally one reload per hour, followed by a user note if still down.
    server_state = state.setdefault("server", {})
    if server.get("valid", False):
        down = not server.get("reachable")
        server_state["down_streak"] = server_state.get("down_streak", 0) + 1 if down else 0
        if not down:
            server_state.pop("reload_pending_at", None)
        elif server_state["down_streak"] >= 2:
            last_reload = server_state.get("last_reload", 0)
            pending = server_state.get("reload_pending_at")
            if not pending and now - last_reload >= 3600:
                server_state["last_reload"] = now
                server_state["reload_pending_at"] = now
                if dry_run:
                    print("DRY-RUN: would run bb plugin reload opencode (server unreachable on two checks).")
                else:
                    out, error = command(["bb", "plugin", "reload", "opencode"], 8.0)
                    print("WATCH: ran bb plugin reload opencode" + (f" ({error})" if error else ""))
            elif pending and now > pending:
                detail = f"OpenCode server still unreachable at port {server.get('port')}; check `bb opencode` and restart the plugin."
                if trigger("opencode-down", True, f"OPENCODE server: {detail}"):
                    notes.append(detail)
                    server_state["reload_pending_at"] = None

    # Only booted simulators accrue no-agent time.
    if sessions.get("valid", False) and host.get("sims_valid", False):
        if not sessions["live"] and host["booted_sims"]:
            sim_idle = state.setdefault("sim_idle", {})
            if sim_idle.get("no_agent_since") is None:
                sim_idle["no_agent_since"] = now
            sim_elapsed = (now - sim_idle["no_agent_since"]) / 60
            trigger("sim-without-agent", sim_elapsed >= setting(env, "WATCH_GHOST_MIN", 15),
                    f"SIMULATOR: {len(host['booted_sims'])} booted simulator(s), no live agent for {sim_elapsed:.0f} min.",
                    valid=sessions.get("valid", False) and host.get("sims_valid", False))
        else:
            state.setdefault("sim_idle", {})["no_agent_since"] = None
            trigger("sim-without-agent", False, "")

    # A brief without TALK-BACK leaves a blocked worker silent until it finishes.
    if sessions.get("valid", False):
        for sess in sessions.get("live", []):
            trigger("no-talkback:" + sess["id"], sess.get("talkback") is False,
                    f"BRIEF {sess.get('agent', 'agent')} {sess['id']}: no TALK-BACK block in its first message, so it "
                    "cannot report BUG/BLOCKED/QUESTION mid-run. Steer it the TALK-BACK block from subagent-delegation.")

    # Continue is rate-limited; only latest ledger verdicts count as progress.
    orch_idle = bb.get("orch_status") not in (None, "active")
    queue_empty = bb.get("queue_count") == 0
    last_msg_age = minutes_since(sessions.get("last_orch_message"), now)
    eligible = (not waiting and isa_valid and sessions.get("valid", False) and bb.get("show_valid", False) and
                bb.get("queue_valid", False) and not isa["done"] and orch_idle and queue_empty and not sessions["live"] and
                snapshot.get("head_valid", False) and last_msg_age is not None and
                last_msg_age > setting(env, "WATCH_CONTINUE_MIN", 15))
    cont = state.setdefault("continue", {})
    if eligible and not cont.get("stopped") and now - cont.get("last_at", 0) >= 900:
        signature = {ident: verdict.get("status")
                     for ident, verdict in sorted(isa.get("latest_verdicts", {}).items())}
        old = cont.get("signature")
        cont["last_at"] = now
        if old is not None and old == signature:
            cont["no_progress"] = cont.get("no_progress", 0) + 1
            print(f"WATCH: skipped unchanged continue ({cont['no_progress']}/3 no-progress checks).")
            if cont["no_progress"] >= 3:
                cont["stopped"] = True
                notes.append("No ledger-verdict progress across three continue checks; watchdog stopped prompting.")
                messages.append("🚦 WATCH STALLED: no ledger-verdict progress across three continue checks, so the watchdog "
                                "stopped nudging (machine and agent checks continue). Tell the owner what is blocking "
                                "and what would unlock it, set the run card status to waiting-owner, then wait.")
        else:
            cont["no_progress"] = 0
            cont["signature"] = signature
            facts = (f"orchestrator={bb.get('orch_status')}, last message {last_msg_age:.0f} min ago, "
                     f"queue empty, no live child sessions, HEAD={snapshot.get('head') or 'unknown'}")
            messages.append(f"WATCH CONTINUE: you are idle with ISA work left ({isa['pass']}/{isa['total']} PASS, "
                            f"{len(isa.get('parked', []))} parked). Re-check these facts cheaply before acting: {facts}. "
                            "Then take the next step per the hivecall loop and the run card, or set the run card status to "
                            "waiting-owner and tell the owner why if genuinely blocked.")

    for note in notes:
        append_note(root, note, dry_run)
    if sessions.get("valid", False):
        for sess in sessions.get("live", []):
            key = "promise_agents" if sess.get("promise") else "other_agents"
            if sess["id"] not in review[key]:
                review[key].append(sess["id"])
    if now - review.get("last_at", now) >= 60 * 60 and (
            review["promise_agents"] or review["other_agents"]):
        counts = review.get("alerts", {})
        total = sum(counts.values())
        by_type = ", ".join(f"{kind} {count}" for kind, count in sorted(counts.items())) or "none"
        messages.append(f"WATCH REVIEW: {total} alerts since last review by type ({by_type}); "
                        f"PROMISE agents {len(review['promise_agents'])}, without {len(review['other_agents'])}; "
                        "check alerts matched reality, note false alarms in the run card's lessons section.")
        review.update(last_at=now, last_sent_at=now, alerts={}, promise_agents=[], other_agents=[])
    emit()
    return alert_tags


def synthetic(name: str, now: float) -> dict:
    old = now - 25 * 60
    isa = {"pass": 0, "total": 2, "pass_lines": 0, "owner": [], "owner_done": 0, "blocked": [],
           "parked": [], "checked": [], "fails": [], "done": False, "error": "",
           "latest_verdicts": {}, "fail_counts": {}, "criteria": ["ISC-001", "ISC-002"],
           "regressions": [], "owner_only_ids": [], "ledger_mtime": now - 100,
           "verdict_count": 0}
    host = {"load": 5.0, "uptime_valid": True, "free_gb": 80.0, "df_valid": True,
            "processes": [], "processes_valid": True, "recent_big": [], "recent_big_valid": True,
            "booted_sims": [], "sims_valid": True, "files": []}
    server = {"reachable": True, "valid": True, "attached": True, "port": 49374}
    sessions = {"live": [], "children": [], "last_orch_message": now, "error": "", "valid": True}
    bb = {"children": [], "orch_status": "active", "queue_count": 1, "binding": {}, "errors": [],
          "list_valid": True, "show_valid": True, "queue_valid": True, "binding_valid": True}
    evidence = {"files": [], "newest": {"path": "/fixture/evidence.txt", "name": "evidence.txt", "mtime": now},
                "results": [], "valid": True}
    if name == "stuck-agent":
        evidence["newest"]["mtime"] = old
        evidence["files"].append({"path": "/fixture/worker-result.md", "name": "worker-result.md", "mtime": old, "size": 100})
        evidence["results"].append({"path": "/fixture/INT8-A-result.md", "name": "INT8-A-result.md",
                                    "mtime": old, "rows": [], "table_rows": [],
                                    "verdict_count": 0, "pending_wait": None, "builder": False})
    elif name == "unrecorded-pass":
        row = {"id": "ISC-123", "status": "PASS", "text": "observed expected result; evidence result.png",
               "placeholder": False, "evidence": True}
        evidence["results"].append({"path": "/fixture/worker-result.md", "name": "worker-result.md",
                                    "mtime": old, "rows": [("ISC-123", "PASS")], "table_rows": [row],
                                    "verdict_count": 1, "pending_wait": None, "builder": False})
        evidence["newest"]["mtime"] = now
    elif name == "superseded-pass":
        result_mtime = now - 60 * 60
        evidence["results"].append({"path": "/fixture/ISC-013.1-result.md", "name": "ISC-013.1-result.md",
                                    "mtime": result_mtime, "rows": [("ISC-013.1", "PASS")],
                                    "table_rows": [{"id": "ISC-013.1", "status": "PASS",
                                                    "text": "old pass; evidence old.png"}],
                                    "verdict_count": 1, "pending_wait": None, "builder": False})
        isa["latest_verdicts"] = {"ISC-013.1": {"status": "FAIL", "reason": "newer smoke failed"}}
        isa["ledger_mtime"] = now - 30 * 60
    elif name in ("orphan-recorder", "orphan-recorder-active"):
        host["processes"] = [{"pid": 123, "ppid": 1, "age": 1200,
                              "command": "recordVideo /fixture/out.mp4", "orphan": True}]
        if name == "orphan-recorder-active":
            host["processes"].extend([
                {"pid": 124, "ppid": 1, "age": 1200,
                 "command": "xcrun simctl spawn booted launchd", "orphan": True},
                {"pid": 125, "ppid": 1, "age": 1200,
                 "command": "log stream --style compact", "orphan": True},
            ])
            promise = parse_promise("PROMISE: kind=screen rows=001 result=Jules-result.md lane=- pace=10")
            promise["result_path"] = "/fixture/Jules-result.md"
            sess = {"id": "ses-jules", "agent": "qa", "created": now - 5 * 60,
                    "last_message": now, "last_assistant": now, "time_idle": None,
                    "idle_outcome": None, "thread_id": "thr-jules", "visible": True,
                    "promise": promise, "promise_read_valid": True, "steers": []}
            sessions.update(live=[sess], children=[sess])
            bb["by_id"] = {"thr-jules": {"id": "thr-jules", "title": "Jules"}}
    elif name == "unclaimed":
        isa.update(total=5, criteria=[f"ISC-{i:03d}" for i in range(1, 6)],
                   owner=["ISC-004"], owner_only_ids=["ISC-005"], parked=["ISC-003"],
                   latest_verdicts={"ISC-003": {"status": "BLOCKED"}})
        promise = {"valid": True, "kind": "helper", "rows": set(), "result_path": "/fixture/helper.md",
                   "pace": 20}
        sess = {"id": "ses-claimer", "agent": "helper", "created": now, "last_message": now,
                "last_assistant": now, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-claimer", "visible": True, "promise": promise,
                "promise_read_valid": True, "steers": []}
        sessions.update(live=[sess], children=[sess])
        bb["by_id"] = {"thr-claimer": {"id": "thr-claimer", "title": "claimer"}}
    elif name == "leftover-session":
        promise = {"valid": True, "kind": "helper", "rows": {"ISC-001"},
                   "result_path": "/fixture/stale-result.md", "pace": 20}
        sess = {"id": "ses-leftover", "agent": "builder", "created": now - 601 * 60,
                "last_message": now - 601 * 60, "last_assistant": now - 601 * 60, "time_idle": None,
                "idle_outcome": None, "thread_id": "thr-ended", "visible": False,
                "promise": promise, "promise_read_valid": True, "talkback": False, "steers": []}
        sessions.update(live=[sess], children=[sess])
        bb["children"] = [{"id": "thr-ended", "status": "failed", "title": "ended helper",
                            "bound_sessions": [sess], "sessions": [sess]}]
        bb["by_id"] = {"thr-ended": bb["children"][0]}
    elif name == "idle-helper":
        sess = {"id": "ses-idle", "agent": "helper", "created": old,
                "last_message": old, "last_assistant": old, "time_idle": now - 60,
                "idle_outcome": "completed", "thread_id": "thr-idle", "visible": True,
                "promise": {"valid": True, "kind": "helper", "rows": {"ISC-001"},
                            "result_path": "/fixture/idle.md", "pace": 20}}
        bb["children"] = [{"id": "thr-idle", "status": "active", "title": "finished helper",
                            "bound_sessions": [sess], "sessions": []}]
        bb["by_id"] = {"thr-idle": bb["children"][0]}
        sessions["children"] = [sess]
    elif name == "ghost-agent":
        bb["children"] = [{"id": "thr-fixture", "title": "worker", "status": "active", "visible": True,
                            "last_activity": old, "sessions": []}]
    elif name == "ghost-agent-no-message":
        sess = {"id": "ses-fixture", "agent": "builder", "created": old,
                "last_message": None, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": True}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "worker", "status": "active",
                            "visible": True, "last_activity": old, "bound_sessions": [sess],
                            "sessions": [sess]}]
    elif name == "invisible-agent":
        sess = {"id": "ses-fixture", "agent": "builder", "created": old, "last_message": now,
                "time_idle": None, "idle_outcome": None, "thread_id": None, "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
    elif name == "high-load":
        host["load"] = 160.0
    elif name == "disk-big-file":
        host["free_gb"] = 4.0
        host["recent_big"] = [{"path": "/fixture/recording.mp4", "name": "recording.mp4", "size": 220*1024*1024, "created": now-60}]
    elif name == "fail-under-load":
        host["load"] = 41.0
        isa["fails"] = [("ISC-123", "sig123", "ISC-123: FAIL - fixture", "REC", now)]
    elif name == "server-down":
        server.update(reachable=False, port=49374)
    elif name in ("continue", "anti-spin"):
        bb.update(orch_status="idle", queue_count=0)
        sessions["last_orch_message"] = now - 20*60
    elif name == "working-old-bb":
        sess = {"id": "ses-working", "agent": "builder", "created": old,
                "last_message": now - 2 * 60, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": True}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "working child", "status": "active",
                            "visible": True, "last_activity": old, "bound_sessions": [sess],
                            "sessions": [sess]}]
    elif name == "resumed-idle-agent":
        sess = {"id": "ses-resumed", "agent": "builder", "created": old,
                "last_message": now, "time_idle": None, "idle_outcome": None,
                "thread_id": "thr-fixture", "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        bb["children"] = [{"id": "thr-fixture", "title": "resumed worker", "status": "idle",
                            "visible": False, "updatedAt": now}]
    elif name == "read-failure":
        host.update(load=200.0, uptime_valid=False, uptime_error="fixture timeout",
                    free_gb=1.0, df_valid=False, df_error="fixture timeout",
                    booted_sims=["Fixture (Booted)"])
        sess = {"id": "ses-fixture", "agent": "builder", "created": old, "last_message": now,
                "time_idle": None, "idle_outcome": None, "thread_id": None, "visible": False}
        sessions["live"] = [sess]
        sessions["children"] = [sess]
        sessions.update(valid=False, last_orch_message=now - 20 * 60, error="fixture SQLite timeout")
        server.update(valid=False, reachable=False, error="fixture timeout")
        bb.update(queue_count=None, list_valid=False, show_valid=False, queue_valid=False,
                  binding_valid=False, errors=["fixture read timeout"],
                  children=[{"id": "thr-fixture", "status": "active", "bound_sessions": [], "sessions": []}])
        isa.update(done=False, error="fixture ISA read failure")
        evidence.update(valid=False, error="fixture verification scan failure",
                        newest={"path": "/fixture/wait.md", "name": "wait.md", "mtime": old},
                        files=[{"path": "/fixture/build.log", "name": "build.log", "mtime": old,
                                "size": 100}],
                        results=[{"path": "/fixture/worker-result.md", "name": "worker-result.md",
                                  "mtime": old, "rows": [("ISC-123", "PASS")], "verdict_count": 1,
                                  "pending_wait": None, "builder": False}])
    elif name == "done":
        isa.update({"pass": 1, "total": 1, "pass_lines": 1, "pass_ids": ["ISC-001"],
                    "checked": ["ISC-001"], "done": True})
    return {"now": now, "host": host, "server": server, "sessions": sessions, "bb": bb,
            "isa": isa, "evidence": evidence,
            "run_status": "running" if name in ("done", "not-closed", "unclaimed", "reopen") else None,
            "run_card": {"valid": True, "status": None, "waiting_text": None},
            "head": "fixture-head", "head_valid": True}


def simulate(name: str, state_path: str, env: dict[str, str]) -> None:
    base = 1_800_000_000.0
    state = state_read(state_path)
    if name in ("orphan-recorder", "orphan-recorder-active"):
        state = {}
        if name == "orphan-recorder":
            state["orphan_idle"] = {"no_agent_since": base - 15 * 60}
    if name in ("closed-delete", "done", "not-closed"):
        sim_env = dict(env, AUTOMATION_ID="auto-fixture", PROJECT_ID="project-fixture")
        state = {}
        output = io.StringIO()
        if name == "closed-delete":
            first = synthetic(name, base)
            first["run_status"] = "closed"
            with redirect_stdout(output):
                evaluate(first, state, sim_env, True)
            if "DRY-RUN: would run bb automation delete" in output.getvalue():
                raise AssertionError("closed run deleted its automation on the first check")
            if "DRY-RUN: would run bb automation pause auto-fixture" not in output.getvalue():
                raise AssertionError(f"first closed check did not pause the automation: {output.getvalue()}")
            # Dry-run cannot persist a real pause, so model the completed first check here.
            state["closed_pause_recorded"] = True
            state["closed_automation_id"] = "auto-fixture"
            second = synthetic(name, base + 300)
            second["run_status"] = "closed"
            with redirect_stdout(output):
                evaluate(second, state, sim_env, True)
            if "DRY-RUN: would run bb automation delete auto-fixture --project project-fixture --yes" not in output.getvalue():
                raise AssertionError(f"next closed check did not delete the explicit automation id: {output.getvalue()}")
            no_id_env = {"REPO": env.get("REPO", ""), "ORCH_THREAD": "fixture-thread"}
            no_id_state = {}
            no_id_output = io.StringIO()
            for i in range(2):
                no_id_snapshot = synthetic(name, base + i * 300)
                no_id_snapshot["run_status"] = "closed"
                with redirect_stdout(no_id_output):
                    evaluate(no_id_snapshot, no_id_state, no_id_env, True)
            if "bb automation delete" in no_id_output.getvalue():
                raise AssertionError("closed run deleted without a saved or explicit automation id")
            print("SIM closed-delete: first closed check paused; next check would delete auto-fixture by explicit id; missing id did not delete.")
            print(summary_line(second, []))
            return
        if name == "not-closed":
            for status in ("running", "waiting-owner", "waiting-usage"):
                snap = synthetic(name, base)
                snap["run_status"] = status
                with redirect_stdout(output):
                    evaluate(snap, state, sim_env, True)
            if "bb automation delete" in output.getvalue():
                raise AssertionError(f"non-closed status deleted the automation: {output.getvalue()}")
            print("SIM not-closed: running, waiting-owner, and waiting-usage did not delete the automation.")
            print(summary_line(snap, []))
            return
        for i in range(2):
            snap = synthetic(name, base + i * 900)
            snap["run_status"] = "running"
            with redirect_stdout(output):
                evaluate(snap, state, sim_env, True)
        if "bb automation delete" in output.getvalue():
            raise AssertionError(f"ledger completion without closed status deleted the automation: {output.getvalue()}")
        print("SIM done: complete ledger paused the automation; no delete while run card was not closed.")
        print(summary_line(snap, []))
        return
    if name == "alert-once":
        state = {}
        sim_env = dict(env, WATCH_AGENT_MAX_HOURS="100")
        session = {"id": "ses-fixture", "agent": "builder", "created": base,
                   "last_message": base - 15 * 60, "time_idle": None, "idle_outcome": None,
                   "thread_id": "thr-fixture", "visible": True}
        output = io.StringIO()

        def run(now: float, last_message: float) -> list[str]:
            session["last_message"] = last_message
            snap = synthetic(name, now)
            snap["sessions"].update(live=[session], children=[session])
            with redirect_stdout(output):
                found = evaluate(snap, state, sim_env, True)
            return found

        persistent_alerts = 0
        for i in range(39):
            tags = run(base + i * 5 * 60, base - 15 * 60)
            persistent_alerts += tags.count("stuck agent")
        if persistent_alerts != 1:
            raise AssertionError(f"persistent condition alerted {persistent_alerts} times over 3+ hours")

        clear_at = base + 195 * 60
        tags = run(clear_at, clear_at)
        record = state["conditions"]["stuck-agent:ses-fixture"]
        if "stuck agent" in tags or record.get("streak") != 0 or record.get("last_alert") != 0:
            raise AssertionError(f"valid inactive read did not clear the alert occurrence: {record}")
        if "stuck agent" in run(clear_at + 5 * 60, clear_at):
            raise AssertionError("reactivated condition alerted before its second active check")
        tags = run(clear_at + 10 * 60, clear_at)
        if "stuck agent" in tags:
            raise AssertionError("reactivated condition alerted on its first active check")
        tags = run(clear_at + 15 * 60, clear_at)
        if "stuck agent" not in tags:
            raise AssertionError("reactivated condition did not alert on its second active check")
        tags = run(clear_at + 20 * 60, clear_at)
        if "stuck agent" in tags:
            raise AssertionError("reactivated persistent condition alerted more than once")
        print("SIM alert-once: one stuck-agent alert across 3+ hours; clear reset it; recurrence alerted once after two checks.")
        snap = synthetic(name, clear_at + 20 * 60)
        snap["sessions"].update(live=[session], children=[session])
        print(summary_line(snap, tags))
        return
    if name == "anti-spin":
        state = {}
        output = io.StringIO()
        unchanged_ledger = {"ISC-001": {"status": "PASS"}}
        for i in range(4):
            now = base + i * 900
            snap = synthetic(name, now)
            snap["head"] = f"fixture-commit-{i}"
            snap["isa"]["latest_verdicts"] = unchanged_ledger
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
            cont = state.get("continue", {})
            if cont.get("no_progress") != i:
                raise AssertionError(f"git commit counted as ledger progress on check {i + 1}: {cont}")
            if cont.get("stopped", False) != (i == 3):
                raise AssertionError(f"anti-spin stop mismatch on check {i + 1}: {cont}")

        cases = (
            ("PASS", {}, {"ISC-001": {"status": "PASS"}}),
            ("FAIL", {"ISC-001": "PASS"},
             {"ISC-001": {"status": "PASS"}, "ISC-002": {"status": "FAIL"}}),
            ("BLOCKED", {"ISC-001": "PASS", "ISC-002": "FAIL"},
             {"ISC-001": {"status": "PASS"}, "ISC-002": {"status": "FAIL"},
              "ISC-003": {"status": "BLOCKED"}}),
        )
        for i, (status, previous, current) in enumerate(cases, start=1):
            progress_state = {"continue": {"last_at": base + 3 * 900,
                                            "signature": previous, "no_progress": 2}}
            now = base + (3 + i) * 900
            snap = synthetic(name, now)
            snap["head"] = "fixture-commit"
            snap["isa"]["latest_verdicts"] = current
            alerts = evaluate(snap, progress_state, env, True)
            cont = progress_state["continue"]
            if cont.get("no_progress") != 0 or cont.get("stopped"):
                raise AssertionError(f"new {status} verdict did not reset the continue streak: {cont}")

        print("SIM anti-spin: 3 unchanged-ledger checks stopped prompting despite new commits; new PASS/FAIL/BLOCKED verdicts reset the streak.")
        print(summary_line(snap, alerts))
        return
    if name == "combined-alerts":
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic("high-load", base + i * 60)
            snap["host"].update(load=160.0, free_gb=4.0)
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
        text = output.getvalue()
        host_lines = [line for line in text.splitlines() if re.match(r"(?:🚦 )?HOST ", line)]
        if text.count("DRY-RUN: would queue to") != 1 or len(host_lines) != 2:
            raise AssertionError(f"alerts were not one combined, one-line-per-alert message: {text!r}")
        print(text, end="")
        print("SIM combined-alerts: two alerts would be sent in one combined message.")
        print(summary_line(snap, alerts))
        return
    if name == "lane-drift":
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builder_lane = root / "_ai" / "tools" / "watch"
            own_file = builder_lane / "watch.py"
            source = root / "src" / "tester-output.png"
            other_lane = root / ".lanes" / "other-live"
            other_source = other_lane / "src" / "other.ts"
            own_file.parent.mkdir(parents=True)
            source.parent.mkdir(parents=True)
            other_source.parent.mkdir(parents=True)
            started = time.time()
            own_file.write_text("initial lane file", encoding="utf-8")
            os.utime(own_file, (started - 600, started - 600))
            source.write_bytes(b"tester output")
            other_source.write_text("another live lane", encoding="utf-8")
            builder = {"id": "ses-builder", "created": started,
                       "promise": {"valid": True, "kind": "code",
                                    "lane_path": str(builder_lane)}}
            now = time.time()
            facts = load_lane_facts([builder])[builder["id"]]
            if not facts["valid"] or facts["latest_mtime"] != os.stat(own_file).st_mtime:
                raise AssertionError(f"out-of-lane files affected the promise lane signal: {facts}")
            own_file.write_text("changed inside promise lane", encoding="utf-8")
            detected = load_lane_facts([builder])[builder["id"]]
            if detected["latest_mtime"] != os.stat(own_file).st_mtime:
                raise AssertionError(f"change inside promise lane was missed: {detected}")
        print("SIM lane-drift: tester output elsewhere is ignored; own-lane change is the code signal.")
        return
    if name in ("on-track-code", "fast-jules", "new-testers-old-results", "superseded-pass"):
        state = {}
        alerts = []
        for i in range(2):
            now = base + i * 300
            snap = synthetic(name, now)
            if name == "on-track-code":
                sessions = []
                lanes = {}
                for agent in ("Sam", "Kai"):
                    ident = "ses-" + agent.lower()
                    promise = {"valid": True, "kind": "code", "rows": set(), "pace": 20,
                               "lane_path": f"/fixture/{agent}"}
                    sessions.append({"id": ident, "agent": "code", "created": base - 60 * 60,
                                     "last_message": now, "time_idle": None, "idle_outcome": None,
                                     "thread_id": "thr-" + agent.lower(), "visible": True,
                                     "promise": promise, "steers": []})
                    lanes[ident] = {"valid": True, "latest_mtime": base - 10 * 60,
                                    "build_mtime": None}
                    snap["bb"].setdefault("by_id", {})["thr-" + agent.lower()] = {
                        "title": agent}
                snap["sessions"].update(live=sessions, children=sessions)
                snap["lanes"] = lanes
                snap["evidence"]["results"] = [{"path": "/fixture/tester-changing-result.md",
                    "name": "tester-changing-result.md", "mtime": now, "rows": [],
                    "table_rows": [], "verdict_count": 0, "builder": False}]
            elif name == "fast-jules":
                rows = "\n".join(f"| ISC-{i:03d} | PASS | checked result; evidence ISC-{i:03d}.png |"
                                  for i in range(1, 11))
                mtime = now - 5 * 60
                parsed = parse_result_text(rows, mtime)
                promise = {"valid": True, "kind": "screen",
                           "rows": {f"ISC-{i:03d}" for i in range(1, 11)},
                           "pace": 10, "result_path": "/fixture/Jules-result.md"}
                sess = {"id": "ses-jules", "agent": "qa", "created": base - 60 * 60,
                        "last_message": now, "time_idle": None, "idle_outcome": None,
                        "thread_id": "thr-jules", "visible": True, "promise": promise,
                        "promise_read_valid": True, "steers": [now - 30 * 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-jules": {"title": "Jules"}}
                snap["evidence"]["results"] = [{"path": promise["result_path"],
                    "name": "Jules-result.md", "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "new-testers-old-results":
                sessions = []
                for n, agent in enumerate(("Sam", "Kai")):
                    promise = {"valid": True, "kind": "screen", "rows": {f"ISC-{n + 1:03d}"},
                               "pace": 10, "result_path": f"/fixture/{agent}-new-result.md"}
                    sessions.append({"id": f"ses-{agent.lower()}", "agent": "qa",
                                     "created": base - 5 * 60, "last_message": now,
                                     "time_idle": None, "idle_outcome": None,
                                     "thread_id": f"thr-{agent.lower()}", "visible": True,
                                     "promise": promise, "promise_read_valid": True, "steers": []})
                snap["sessions"].update(live=sessions, children=sessions)
                snap["bb"]["by_id"] = {f"thr-{agent.lower()}": {"title": agent}
                                        for agent in ("Sam", "Kai")}
                snap["evidence"]["results"] = [{"path": f"/fixture/INT{i}-A-result.md",
                    "name": f"INT{i}-A-result.md", "mtime": base - 45 * 60,
                    "rows": [], "table_rows": [], "verdict_count": 0,
                    "pending_wait": None, "builder": False}
                    for i in (8, 9, 10, 11, 12, 13, 14, 15)]
            print(f"SIM {name} run {i + 1}:")
            alerts = evaluate(snap, state, env, True)
            if "off track" in alerts or "stuck agent" in alerts:
                raise AssertionError(f"false no-progress alert: {alerts}")
        if name == "on-track-code":
            print("SIM on-track-code: Sam and Kai stayed silent within pace; unrelated tester output did not count.")
        elif name == "fast-jules":
            metrics = promise_metrics(snap["sessions"]["live"][0], snap, state)
            if metrics["answers"] != 10 or metrics["unanswered"] != 1 or metrics["breached"]:
                raise AssertionError(f"fast Jules context mismatch: {metrics}")
            print("SIM fast-jules: 10 recent answers and one unanswered steer did not raise off-track.")
        elif name == "new-testers-old-results":
            if any(key.startswith(("off-track:", "stuck-agent:")) and
                   (record.get("streak", 0) > 0 or record.get("last_alert", 0))
                   for key, record in state.get("conditions", {}).items()):
                raise AssertionError("old result files were attributed to new live testers")
            print("SIM new-testers-old-results: two new testers without result files plus eight old files stayed silent.")
        else:
            if "unrecorded PASS" in alerts:
                raise AssertionError("superseded ISC-013.1 PASS was reported as unrecorded")
            print("SIM superseded-pass: old ISC-013.1 PASS stayed silent after the ledger's newer FAIL.")
        print(summary_line(snap, alerts))
        return
    if name == "unrecorded-pass-reload":
        state = {}
        result = {"path": "/fixture/ISC-139-result.md", "name": "ISC-139-result.md",
                  "mtime": base - 25 * 60, "rows": [("ISC-139", "PASS")],
                  "table_rows": [{"id": "ISC-139", "status": "PASS", "text": "observed; evidence 139.png"}],
                  "verdict_count": 1, "builder": False}
        legacy = {"path": "/fixture/ISC-140-result.md", "name": "ISC-140-result.md",
                  "mtime": base - 25 * 60, "rows": [("ISC-140", "PASS")],
                  "table_rows": [{"id": "ISC-140", "status": "PASS", "text": "observed; evidence 140.png"}],
                  "verdict_count": 1, "builder": False}
        state["conditions"] = {"unrecorded-pass:/fixture/ISC-140-result.md:ISC-140":
                                {"streak": 2, "last_alert": base - 3600, "severity": 1}}
        for i in range(2):
            snap = synthetic(name, base + i * 300)
            snap["evidence"]["results"] = [result, legacy]
            alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
        if "unrecorded PASS" not in alerts:
            raise AssertionError(f"ISC-139 unrecorded PASS did not alert once: {alerts}")
        state = state_read(state_path)
        snap = synthetic(name, base + 10 * 60)
        snap["evidence"]["results"] = [result, legacy]
        alerts = evaluate(snap, state, env, True)
        if "unrecorded PASS" in alerts:
            raise AssertionError(f"unrecorded PASS repeated after reload: {alerts}")
        if not state.get("unrecorded_passes"):
            raise AssertionError("stable unrecorded-PASS dedupe was not persisted")
        print("SIM unrecorded-pass-reload: ISC-139 alerted once; reload stayed silent; old key migrated.")
        print(summary_line(snap, alerts))
        return
    if name in ("off-track", "on-track-timed", "no-promise", "review"):
        state = {}
        steps = 2
        for i in range(steps):
            now = (base + (59 if i == 0 else 60) * 60 if name == "review"
                   else base + i * 60)
            snap = synthetic(name, now)
            if name == "off-track":
                fixture = Path("/fixture/tester-result.md")
                text = ("| ISC | Verdict | Observed | Evidence |\n| --- | --- | --- | --- |\n"
                        "| ISC-064 | PASS | swipe opened the thread | `ISC-064-swipe.png` |\n"
                        "| ISC-067 | FAIL | flick opened nothing | `ISC-067-flick.json` |\n"
                        "| ISC-068 | BLOCKED | not probed after ISC-067 FAIL | `ISC-067-note.txt` |\n")
                mtime = base - 110 * 60
                parsed = parse_result_text(text, mtime)
                pass_rows = [row["id"] for row in parsed["table_rows"] if row["status"] == "PASS"]
                snap["isa"]["latest_verdicts"] = {ident: {"status": "PASS"} for ident in pass_rows}
                snap["isa"]["ledger_mtime"] = now
                promised = sorted({row["id"] for row in parsed["table_rows"]})
                promise = parse_promise(
                    f"PROMISE: kind=screen rows={','.join(promised)} "
                    "result=tester-result.md lane=-"
                )
                promise["result_path"] = str(fixture)
                sess = {"id": "ses-fixture", "agent": "tester", "created": base - 120 * 60,
                        "last_message": base - 30 * 60, "last_assistant": base - 30 * 60, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-fixture", "visible": True,
                        "promise": promise, "promise_read_valid": True,
                        "steers": [base - 90 * 60, base - 60 * 60, base - 30 * 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-fixture": {"id": "thr-fixture", "title": "sample tester"}}
                snap["evidence"]["results"] = [{"path": str(fixture),
                    "name": fixture.name, "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "on-track-timed":
                deadline = (dt.datetime.fromtimestamp(base).astimezone() + dt.timedelta(minutes=30)).strftime("%H:%M")
                mtime = base - 5 * 60
                parsed = parse_result_text(
                    f"| ISC-001 | PASS | observed expected result; evidence timed-result.json |\n"
                    f"PENDING-WAIT ISC-001 until {deadline}\n", mtime)
                promise = parse_promise(
                    "PROMISE: kind=timed rows=001 result=timed-result.md lane=-"
                )
                promise["result_path"] = "/fixture/timed-result.md"
                sess = {"id": "ses-timed", "agent": "tester", "created": base - 10 * 60,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-timed", "visible": True,
                        "promise": promise, "promise_read_valid": True, "steers": [base - 60]}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-timed": {"id": "thr-timed", "title": "timed tester"}}
                snap["evidence"]["results"] = [{"path": "/fixture/timed-result.md",
                    "name": "timed-result.md", "mtime": mtime, **parsed,
                    "verdict_count": len(parsed["rows"]), "builder": False}]
            elif name == "no-promise":
                sess = {"id": "ses-no-promise", "agent": "helper", "created": base - 2 * 3600,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-no-promise", "visible": True,
                        "promise": None}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["evidence"]["results"] = [{"path": "/fixture/old-result.md",
                    "name": "old-result.md", "mtime": base - 2 * 3600, "rows": [],
                    "table_rows": [], "verdict_count": 0, "pending_wait": None,
                    "waits": {}, "builder": False}]
            else:
                sess = {"id": "ses-review", "agent": "helper", "created": base - 5 * 60,
                        "last_message": now, "last_assistant": now, "time_idle": None,
                        "idle_outcome": None, "thread_id": "thr-review", "visible": True,
                        "promise": None}
                snap["sessions"].update(live=[sess], children=[sess])
                snap["bb"]["by_id"] = {"thr-review": {"id": "thr-review", "title": "review helper"}}
                state.setdefault("review", {"last_at": base, "alerts": {"off track": 2},
                                              "promise_agents": [], "other_agents": []})
            print(f"SIM {name} run {i+1}:")
            alerts = evaluate(snap, state, env, True)
            state_write(state_path, state)
            if name == "review" and i == 0 and state.get("review", {}).get("last_sent_at") is not None:
                raise AssertionError("review message sent before 60 minutes")
        if name == "off-track":
            if state.get("conditions", {}).get("off-track:ses-fixture", {}).get("last_alert") != base + 60:
                raise AssertionError("off-track promise did not alert after two checks")
            print("SIM off-track: an old result plus 30 minutes without session activity raised an alert.")
        elif name == "on-track-timed":
            if state.get("conditions", {}).get("off-track:ses-timed", {}).get("streak", 0) != 0:
                raise AssertionError("PENDING-WAIT did not pause the timed promise clock")
            print("SIM on-track-timed: PENDING-WAIT paused the clock; no off-track alert.")
        elif name == "no-promise":
            if any(key.startswith("off-track:") for key in state.get("conditions", {})):
                raise AssertionError("a session without PROMISE received an on-track check")
            print("SIM no-promise: no on-track alert for an unpromised session.")
        else:
            if state.get("review", {}).get("last_sent_at") != base + 60 * 60:
                raise AssertionError("review message did not send exactly once")
            print("SIM review: silent at 59 minutes; one queued review message at 60 minutes.")
        print(summary_line(snap, alerts))
        return
    if name == "fail-under-load":
        cases = (("SIM", 41.0, False), ("REC", 41.0, True), ("REC", 5.0, False))
        last_snapshot = None
        alerts = []
        for tool, load, expected in cases:
            case_state = {"fail_rows_initialized": True}
            for i in range(2):
                now = base + i * 60
                snap = synthetic(name, now)
                snap["host"]["load"] = load
                snap["isa"]["fails"] = [("ISC-123", "sig123", "ISC-123: FAIL - fixture", tool, base)]
                alerts = evaluate(snap, case_state, env, True)
                last_snapshot = snap
            observed = "FAIL under load" in alerts
            if observed != expected:
                raise AssertionError(f"{tool} at load {load} alert mismatch: {alerts}")
            print(f"SIM fail-under-load: {tool} at evidence load {load:.0f} "
                  f"{'alerted' if observed else 'did not alert'} as expected.")
        print(summary_line(last_snapshot, alerts))
        return
    if name == "disk-big-file":
        state = {}
        output = io.StringIO()
        disk_env = dict(env, WATCH_DISK_FREE_GB="10")
        for i, free in enumerate((8.0, 8.0, 4.0, 4.0)):
            snap = synthetic(name, base + i * 60)
            snap["host"]["free_gb"] = free
            with redirect_stdout(output):
                alerts = evaluate(snap, state, disk_env, True)
        disk_lines = [line for line in output.getvalue().splitlines() if "HOST disk:" in line]
        if len(disk_lines) != 2 or "🚦 HOST disk:" in disk_lines[0] or "🚦 HOST disk:" not in disk_lines[1]:
            raise AssertionError(f"disk escalation did not emit normal 8 GB then 🚦 4 GB alerts: {disk_lines}")
        calm_state = {}
        calm_output = io.StringIO()
        for i in range(2):
            calm = synthetic(name, base + 300 + i * 60)
            calm["host"]["free_gb"] = 6.0
            with redirect_stdout(calm_output):
                evaluate(calm, calm_state, disk_env, True)
        calm_line = next((line for line in calm_output.getvalue().splitlines() if "HOST disk:" in line), "")
        if not calm_line or "🚦" in calm_line:
            raise AssertionError(f"6 GB disk alert changed unexpectedly: {calm_line!r}")
        floor_state = {}
        floor_output = io.StringIO()
        for i in range(2):
            floor = synthetic(name, base + 600 + i * 60)
            floor["host"]["free_gb"] = 4.0
            with redirect_stdout(floor_output):
                floor_tags = evaluate(floor, floor_state, dict(env, WATCH_DISK_FREE_GB="3"), True)
            if ("low disk" in floor_tags) != (i == 1):
                raise AssertionError(f"4 GB disk floor did not alert after two checks: {floor_tags}")
        floor_lines = [line for line in floor_output.getvalue().splitlines() if "HOST disk:" in line]
        if len(floor_lines) != 1 or "🚦 HOST disk:" not in floor_lines[0] or "<5 GB" not in floor_lines[0]:
            raise AssertionError(f"4 GB free with WATCH_DISK_FREE_GB=3 did not raise the independent floor alert: {floor_lines}")
        print("SIM disk-big-file: normal 8 GB warning escalated at 4 GB; the <5 GB 🚦 floor also fired with WATCH_DISK_FREE_GB=3; 6 GB stayed unmarked.")
        print(summary_line(snap, alerts))
        return
    if name == "sim-idle-timer":
        state = {}
        checks = ((0, False), (14 * 60, False), (20 * 60, True), (35 * 60, True),
                  (36 * 60, False), (37 * 60, True), (52 * 60, True), (53 * 60, True))
        for i, (elapsed, booted) in enumerate(checks):
            snap = synthetic(name, base + elapsed)
            snap["host"]["booted_sims"] = ["Fixture (Booted)"] if booted else []
            tags = evaluate(snap, state, env, True)
            since = state.get("sim_idle", {}).get("no_agent_since")
            expected_since = base + (20 * 60 if i in (2, 3) else 37 * 60 if i >= 5 else 0) if booted else None
            if since != expected_since:
                raise AssertionError(f"simulator idle timer mismatch at check {i + 1}: {since} != {expected_since}")
            expected_alert = i == len(checks) - 1
            if ("idle simulator" in tags) != expected_alert:
                raise AssertionError(f"simulator idle alert mismatch at check {i + 1}: {tags}")
        print("SIM sim-idle-timer: no simulators accrued no-agent time; booting started a fresh timer; alert needed two checks.")
        print(summary_line(snap, tags))
        return
    if name == "repeat-fail":
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ISA.html"
            rows = "".join(f'<li id="ISC-{i:03d}"><input type="checkbox">{i}</li>'
                           for i in range(1, 5))
            ledger.write_text('<ul>' + rows + '</ul>'
                              '<table id="owner-verification-table"><tr><td>Owner</td><td><a href="#ISC-004">4</a></td></tr></table>'
                              '<section id="verification"><ul>'
                              '<li>ISC-001: FAIL - first</li><li>ISC-001: FAIL - second</li>'
                              '<li>ISC-001: PASS - recovered</li><li>ISC-001: FAIL - one after pass</li>'
                              '<li>ISC-002: FAIL - one</li><li>ISC-002: FAIL - two</li><li>ISC-002: FAIL - three</li>'
                              '<li>ISC-003: FAIL - one</li><li>ISC-003: FAIL - two</li><li>ISC-003: FAIL - three</li>'
                              '<li>ISC-003: BLOCKED - parked</li>'
                              '<li>ISC-004: FAIL - one</li><li>ISC-004: FAIL - two</li><li>ISC-004: FAIL - three</li>'
                              '</ul></section>', encoding="utf-8")
            isa = parse_isa(str(ledger), directory)
        if isa.get("fail_counts", {}).get("ISC-001") != 1:
            raise AssertionError(f"PASS did not reset repeat-fail count: {isa.get('fail_counts')}")
        if "ISC-003" not in isa.get("blocked", []) or "ISC-004" not in isa.get("parked", []):
            raise AssertionError(f"BLOCKED and owner-parked fixtures were not parsed: {isa}")
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            snap["isa"] = isa
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            if ("repeat failure" in tags) != (i == 1):
                raise AssertionError(f"repeat-fail did not honor two-check alerting: {tags}")
        loop_lines = [line for line in output.getvalue().splitlines() if line.startswith("LOOP ISC-")]
        if len(loop_lines) != 1 or not loop_lines[0].startswith("LOOP ISC-002:"):
            raise AssertionError(f"only the eligible 3-FAIL row should raise LOOP: {loop_lines}")
        print("SIM repeat-fail: 2 FAILs, post-PASS FAIL, BLOCKED and owner-parked rows stayed quiet; eligible 3 FAILs alerted.")
        print(summary_line(snap, tags))
        return
    if name == "unclaimed":
        state = {}
        output = io.StringIO()
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            with redirect_stdout(output):
                alerts = evaluate(snap, state, env, True)
            if i == 0 and "unclaimed work" in alerts:
                raise AssertionError("unclaimed set alerted on its first check")
            if i == 1 and "unclaimed work" not in alerts:
                raise AssertionError("unclaimed set did not alert on its second check")
        text = output.getvalue()
        if "UNCLAIMED: 2 open items have no agent (ISC-001, ISC-002); 1 agents running." not in text:
            raise AssertionError(f"unclaimed alert did not list all open rows: {text}")
        open_key = "unclaimed:" + hashlib.sha256(b"ISC-001\nISC-002").hexdigest()[:12]
        if state.get("conditions", {}).get(open_key, {}).get("last_alert") != base + 60:
            raise AssertionError("unclaimed set was not deduplicated by its sorted row set")

        quiet_state = {}
        for i in range(2):
            quiet = synthetic(name, base + i * 60)
            quiet["sessions"]["live"][0]["promise"]["rows"].add("ISC-001")
            quiet_tags = evaluate(quiet, quiet_state, env, True)
            if "unclaimed work" in quiet_tags:
                raise AssertionError(f"one claimed open row did not suppress the alert: {quiet_tags}")

        waiting_state = {}
        for i in range(2):
            existing = synthetic(name, base + i * 60)
            existing["run_card"].update(waiting_text="owner review")
            tags = evaluate(existing, waiting_state, env, True)
            note = waiting_state.get("unclaimed_waiting", {})
            if ("unclaimed work" in tags) != (i == 1) or note.get("fresh"):
                raise AssertionError("an existing waiting line on fresh state silenced UNCLAIMED")

        changed_note = synthetic(name, base + 120)
        changed_note["run_card"].update(waiting_text="waiting for the owner")
        if "unclaimed work" in evaluate(changed_note, waiting_state, env, True):
            raise AssertionError("a newly written waiting line with an unchanged identity did not silence UNCLAIMED")
        if not waiting_state["unclaimed_waiting"].get("fresh"):
            raise AssertionError("observed waiting-line text change was not marked fresh")
        stable_note = synthetic(name, base + 180)
        stable_note["run_card"].update(waiting_text="waiting for the owner")
        if "unclaimed work" in evaluate(stable_note, waiting_state, env, True):
            raise AssertionError("a fresh waiting line did not remain quiet while its identity stayed stable")
        state_write(state_path, waiting_state)
        waiting_state = state_read(state_path)  # watchdog restart preserves the old note identity
        for i in range(2):
            stale_note = synthetic(name, base + 240 + i * 60)
            stale_note["run_card"].update(waiting_text="waiting for the owner")
            stale_note["isa"].update(verdict_count=1,
                                      latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
            stale_note["head"] = "fixture-head-after-another-change"
            tags = evaluate(stale_note, waiting_state, env, True)
            if i == 0 and "unclaimed work" in tags:
                raise AssertionError("old waiting line alerted before its second check after a HEAD change")
            if i == 1 and "unclaimed work" not in tags:
                raise AssertionError("old waiting line stayed quiet after ledger/HEAD identity changed")
        fresh_waiting_state = waiting_state
        for i in range(2):
            fresh = synthetic(name, base + 360 + i * 60)
            fresh["run_card"].update(waiting_text="new owner review")
            fresh["isa"].update(verdict_count=1,
                                latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
            fresh["head"] = "fixture-head-after-another-change"
            tags = evaluate(fresh, fresh_waiting_state, env, True)
            if "unclaimed work" in tags:
                raise AssertionError("new waiting text did not silence UNCLAIMED for the unchanged identity")

        simultaneous_state = {}
        first = synthetic(name, base)
        evaluate(first, simultaneous_state, env, True)
        same_check_change = synthetic(name, base + 60)
        same_check_change["run_card"].update(waiting_text="new note")
        same_check_change["head"] = "fixture-head-changed-with-note"
        same_check_change["isa"].update(verdict_count=1,
                                         latest_verdicts={"ISC-001": {"status": "PASS", "reason": "new work"}})
        if "unclaimed work" not in evaluate(same_check_change, simultaneous_state, env, True):
            raise AssertionError("waiting text changed with HEAD/ledger and incorrectly silenced UNCLAIMED")

        cycling_state = {}
        for i, rows in enumerate(("ISC-001", "ISC-002", "ISC-001", "ISC-001")):
            cycling = synthetic(name, base + i * 60)
            cycling["isa"].update(criteria=[rows], total=1, parked=[], owner=[], owner_only_ids=[], checked=[])
            cycling["sessions"]["live"][0]["promise"]["rows"].clear()
            tags = evaluate(cycling, cycling_state, env, True)
            if i < 3 and "unclaimed work" in tags:
                raise AssertionError(f"open-set transition reused an earlier streak on step {i + 1}")
            if i == 3 and "unclaimed work" not in tags:
                raise AssertionError("stable open set did not alert on its second consecutive check")
        missing_state = {}
        for i in range(2):
            missing = synthetic(name, base + i * 60)
            missing["sessions"]["valid"] = False
            if "unclaimed work" in evaluate(missing, missing_state, env, True):
                raise AssertionError("unreadable sessions raised an unclaimed alert")
        missing_head_state = {}
        for i in range(2):
            missing_head = synthetic(name, base + i * 60)
            missing_head["run_card"].update(waiting_text="owner review")
            if not i:
                missing_head.update(head=None, head_valid=False)
            if "unclaimed work" in evaluate(missing_head, missing_head_state, env, True):
                raise AssertionError("an unreadable HEAD raised an unclaimed alert")
        if "unclaimed_waiting" not in missing_head_state:
            raise AssertionError("waiting note was not recorded when HEAD identity became readable")
        print("SIM unclaimed: fresh-start notes stayed untrusted; rewritten notes silenced only across unchanged ledger/HEAD identity, while identity changes re-armed alerts.")
        print(summary_line(snap, alerts))
        return
    if name == "regression":
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ISA.html"
            head = ('<ul><li id="ISC-001"><input type="checkbox" checked>Row</li></ul>'
                    '<section id="verification"><ul>')
            state = {}
            output = io.StringIO()
            sequence = []
            for verdict in ("PASS", "FAIL", "PASS", "FAIL"):
                sequence.append(verdict)
                lines = ''.join(f'<li>ISC-001: {value} - step {i}</li>'
                                for i, value in enumerate(sequence, 1))
                ledger.write_text(head + lines + '</ul></section>', encoding="utf-8")
                parsed = parse_isa(str(ledger), directory)
                if parsed.get("verdict_count") != len(sequence):
                    raise AssertionError(f"verdict history count was not parsed: {parsed}")
                if verdict == "FAIL" and parsed.get("done"):
                    raise AssertionError("latest FAIL on a checked criterion was treated as ledger completion")
                checks = 2 if verdict == "FAIL" else 1
                for check in range(checks):
                    snap = synthetic(name, base + len(sequence) * 60 + check)
                    snap["isa"] = parsed
                    snap["run_status"] = "running"
                    with redirect_stdout(output):
                        tags = evaluate(snap, state, env, True)
                    expected_alert = verdict == "FAIL" and check == 1
                    if ("regression" in tags) != expected_alert:
                        raise AssertionError(f"regression episode alert mismatch for {sequence}: {tags}")
            ledger.write_text(
                '<ul><li id="ISC-002"><input type="checkbox">Owner row</li></ul>'
                '<table id="owner-verification-table"><tr><td>Owner</td>'
                '<td><a href="#ISC-002">2</a></td></tr></table>'
                '<section id="verification"><ul><li>ISC-002: FAIL - owner parked</li></ul></section>',
                encoding="utf-8")
            owner_parked = parse_isa(str(ledger), directory)
            if not owner_parked.get("done"):
                raise AssertionError(f"unchecked owner-parked FAIL blocked completion: {owner_parked}")
            ledger.write_text(
                '<ul><li id="ISC-003"><input type="checkbox">Owner-only row</li></ul>'
                '<ul id="owner-only"><li>ISC-003: owner-only</li></ul>'
                '<section id="verification"><ul><li>ISC-003: FAIL - owner-only</li></ul></section>',
                encoding="utf-8")
            owner_only = parse_isa(str(ledger), directory)
            if not owner_only.get("done"):
                raise AssertionError(f"unchecked owner-only FAIL blocked completion: {owner_only}")
        text = output.getvalue()
        regression_lines = [line for line in text.splitlines() if line.startswith("REGRESSION ISC-001:")]
        if len(regression_lines) != 2 or any("Revert the merge that broke it first" not in line
                                              for line in regression_lines):
            raise AssertionError(f"PASS→FAIL→PASS→FAIL did not re-alert with revert-first guidance: {text}")
        print("SIM regression: checked-row FAIL stayed open; unchecked owner-parked/owner-only FAILs did not block completion; PASS re-armed regression alerts.")
        print(summary_line(snap, tags))
        return
    if name == "plateau":
        state = {}
        output = io.StringIO()
        for n in range(3):
            ident = f"ses-helper-{n}"
            promise = {"valid": True, "kind": "helper", "rows": {"ISC-001"},
                       "result_path": "/fixture/helper.md", "pace": 20}
            live = {"id": ident, "agent": "helper", "created": base + n * 120,
                    "last_message": base + n * 120, "time_idle": None, "idle_outcome": None,
                    "thread_id": None, "visible": True, "promise": promise}
            started = synthetic(name, base + n * 120)
            started["isa"].update(latest_verdicts={"ISC-001": {"status": "FAIL", "reason": "same failure"}},
                                  verdict_count=1)
            started["sessions"].update(live=[live], children=[live])
            with redirect_stdout(output):
                evaluate(started, state, env, True)
            ended = dict(live, time_idle=base + n * 120 + 60, idle_outcome="completed")
            finished = synthetic(name, base + n * 120 + 60)
            finished["isa"].update(latest_verdicts={"ISC-001": {"status": "FAIL", "reason": "same failure"}},
                                   verdict_count=1)
            finished["sessions"]["children"] = [ended]
            with redirect_stdout(output):
                tags = evaluate(finished, state, env, True)
            state_write(state_path, state)
            state = state_read(state_path)
            if n < 2 and "plateau" in tags:
                raise AssertionError("plateau alerted before three helper finishes")
            if n == 2 and "plateau" in tags:
                raise AssertionError("plateau skipped the two-check confirmation after its third finish")
        snap = synthetic(name, base + 3 * 120 + 60)
        snap["isa"].update(latest_verdicts={"ISC-001": {"status": "FAIL", "reason": "same failure"}},
                           verdict_count=1)
        with redirect_stdout(output):
            tags = evaluate(snap, state, env, True)
        since = dt.datetime.fromtimestamp(base + 60).astimezone().isoformat(timespec="minutes")
        expected = (f"PLATEAU (heuristic): 3 helpers ended with no new verdict since {since}. Helpers that finish "
                    "between checks are not counted. If the work is stuck, change approach or park.")
        if "plateau" not in tags or expected not in output.getvalue():
            raise AssertionError(f"third unchanged helper finish did not alert after confirmation: {tags}")
        changed = synthetic(name, base + 3 * 120 + 120)
        changed["isa"].update(latest_verdicts={"ISC-001": {"status": "FAIL", "reason": "same failure"}},
                               verdict_count=2)
        tags = evaluate(changed, state, env, True)
        if "plateau" in tags or state["plateau"].get("finish_count") != 0:
            raise AssertionError("new ledger verdict did not reset the plateau")

        incomplete = synthetic(name, base + 3 * 120 + 180)
        incomplete["isa"].update(latest_verdicts={"ISC-001": {"status": "FAIL", "reason": "same failure"}},
                                 verdict_count=2)
        incomplete_live = {"id": "ses-still-live", "agent": "helper", "created": base,
                           "last_message": base, "last_assistant": base, "time_idle": None,
                           "idle_outcome": None, "thread_id": None, "visible": True,
                           "promise": None, "promise_read_valid": False, "steers": []}
        incomplete["sessions"].update(live=[incomplete_live], children=[incomplete_live])
        incomplete_state = {"plateau": {"active": ["ses-still-live"], "finish_count": 2,
                                         "verdict_signature": [2, [["ISC-001", "FAIL", "same failure"]]]}}
        tags = evaluate(incomplete, incomplete_state, env, True)
        if "plateau" in tags or incomplete_state["plateau"].get("finish_count") != 2:
            raise AssertionError("unreadable PROMISE on a still-live helper counted as a finish")

        between_state = {}
        between = synthetic(name, base + 4 * 120)
        completed = {"id": "ses-between", "agent": "helper", "created": base,
                     "time_idle": base + 60, "idle_outcome": "completed",
                     "promise": {"valid": True, "rows": {"ISC-001"}}}
        between["sessions"]["children"] = [completed]
        evaluate(between, between_state, env, True)
        if between_state.get("plateau", {}).get("finish_count") != 0:
            raise AssertionError("helper finishing between checks was counted")
        print("SIM plateau: three observed helper finishes alerted with a timestamp; new verdicts and unobserved finishes did not count.")
        print(summary_line(changed, tags))
        return
    if name == "leftover-session":
        state = {}
        output = io.StringIO()
        statuses = ("failed", "active", "failed", "failed", "failed", "active", "failed", "failed")
        expected_alerts = {3, 7}
        for i, status in enumerate(statuses):
            snap = synthetic(name, base + i * 60)
            snap["bb"]["by_id"]["thr-ended"]["status"] = status
            with redirect_stdout(output):
                tags = evaluate(snap, state, env, True)
            if ("leftover session" in tags) != (i in expected_alerts):
                raise AssertionError(f"leftover failed/healthy sequence mis-alerted at {status} step {i + 1}: {tags}")
            if i == 0:
                suppressed = ("OFF TRACK", "AGENT builder (ses-leftover)", "AGENT builder session ses-leftover",
                              "BRIEF builder ses-leftover", "GHOST BB child thr-ended")
                if any(marker in output.getvalue() for marker in suppressed):
                    raise AssertionError(f"stale session raised additional alerts before recovery: {output.getvalue()}")
            if status == "active":
                rec = state.get("conditions", {}).get("leftover-session:ses-leftover", {})
                if rec.get("streak") != 0 or rec.get("last_alert"):
                    raise AssertionError(f"healthy session did not clear its LEFTOVER episode: {rec}")
        text = output.getvalue()
        leftover_lines = [line for line in text.splitlines() if line.startswith("LEFTOVER session ses-leftover")]
        if len(leftover_lines) != 2 or any("interrupt it before relaunching" not in line for line in leftover_lines):
            raise AssertionError(f"two separate stale-session episodes should each produce one LEFTOVER line: {leftover_lines}")
        if f"would queue to {env['ORCH_THREAD']}:" not in output.getvalue():
            raise AssertionError("leftover alert was not addressed to the orchestrator thread")

        stale_state = {"orphan_idle": {"no_agent_since": base - 16 * 60}}
        stale_tags = []
        for i in range(2):
            stale = synthetic(name, base + i * 60)
            stale["run_status"] = "running"
            stale["isa"].update(total=1, criteria=["ISC-001"], checked=[], owner=[], parked=[],
                                owner_only_ids=[], latest_verdicts={})
            stale["host"]["processes"] = [{"pid": 321, "ppid": 1, "age": 1200,
                                           "command": "recordVideo /fixture/orphan.mp4", "orphan": True}]
            stale["sessions"]["live"][0]["promise"]["rows"] = {"ISC-001"}
            stale["run_card"]["status"] = "running"
            stale_tags = evaluate(stale, stale_state, env, True)
            if stale["sessions"]["live"]:
                raise AssertionError("ended BB session remained an effective live claim")
        if not {"unclaimed work", "orphan process", "leftover session"}.issubset(stale_tags):
            raise AssertionError(f"ended helper suppressed unclaimed/orphan checks: {stale_tags}")
        print("SIM leftover-session: healthy checks reset LEFTOVER; failed/failed alerted once, and a recovered session re-armed it.")
        print(summary_line(snap, tags))
        return
    if name == "idle-helper":
        state = {"conditions": {"off-track:ses-idle": {"streak": 1, "last_alert": 0, "severity": 0}}}
        for i in range(2):
            snap = synthetic(name, base + i * 60)
            tags = evaluate(snap, state, env, True)
            if "off track" in tags or "ghost agent" in tags:
                raise AssertionError(f"finished helper was treated as active: {tags}")
        if state["conditions"]["off-track:ses-idle"].get("streak") != 0:
            raise AssertionError("idle helper did not clear its off-track streak")
        print("SIM idle-helper: finished OpenCode helper cleared off-track and BB ghost alerts.")
        print(summary_line(snap, tags))
        return
    if name == "reopen":
        state = {"done": True, "pause_result": "paused old run", "closed_pause_recorded": True,
                 "closed_automation_id": "auto-old", "delete_result": "deleted old", "automation_deleted": True}
        output = io.StringIO()
        snap = synthetic(name, base)
        with redirect_stdout(output):
            tags = evaluate(snap, state, dict(env, AUTOMATION_ID="auto-fixture", PROJECT_ID="fixture"), True)
        stale = {"done", "pause_result", "closed_pause_recorded", "closed_automation_id",
                 "delete_result", "automation_deleted"} & state.keys()
        if stale or "would run bb automation pause" in output.getvalue() or state.get("done"):
            raise AssertionError(f"reopened running run retained stale pause state: {stale}, {output.getvalue()}")
        print("SIM reopen: running card plus incomplete ledger cleared stale done/pause state without pausing.")
        print(summary_line(snap, tags))
        return
    steps = 2
    if name == "server-down":
        steps = 4
    elif name == "anti-spin":
        steps = 4
    elif name == "done":
        steps = 2
    elif name == "read-failure":
        steps = 2
        conditions = state.setdefault("conditions", {})
        for key in ("high-load", "low-disk", "invisible-agent:ses-fixture", "ghost-agent:thr-fixture",
                    "stuck-builder-log:/fixture/build.log", "stuck-agent:/fixture/worker-result.md",
                    "unrecorded-pass:/fixture/worker-result.md:ISC-123"):
            conditions[key] = {"streak": 1, "last_alert": 0, "severity": 0}
        state["server"] = {"down_streak": 1, "last_reload": 0}
    elif name == "working-old-bb":
        steps = 2
    elif name == "resumed-idle-agent":
        steps = 2
        state.setdefault("conditions", {})["invisible-agent:ses-resumed"] = {
            "streak": 0, "last_alert": 0, "severity": 0}
    for i in range(steps):
        now = base + i * 900
        snap = synthetic(name, now)
        alerts = []
        if name == "anti-spin" and i > 0:
            snap["now"] = now
        print(f"SIM {name} run {i+1}:")
        if state.get("done"):
            print("WATCH: done=true; future run exits without another message.")
            continue
        if name == "server-down":
            # Simulated server stays down; the real reload command is never invoked.
            pass
        alerts = evaluate(snap, state, env, True)
        if name == "read-failure":
            conditions = state.get("conditions", {})
            keys = ("high-load", "low-disk", "invisible-agent:ses-fixture", "ghost-agent:thr-fixture",
                    "stuck-builder-log:/fixture/build.log", "stuck-agent:/fixture/worker-result.md",
                    "unrecorded-pass:/fixture/worker-result.md:ISC-123")
            if any(conditions.get(key, {}).get("streak") != 1 for key in keys):
                raise AssertionError("a failed read changed an affected alert streak")
            if state.get("server", {}).get("down_streak") != 1:
                raise AssertionError("an OpenCode read failure advanced its recovery streak")
            print("SIM read-failure: no alert; affected host/BB/session streaks remain 1/2.")
        if name == "working-old-bb":
            streak = state.get("conditions", {}).get("ghost-agent:thr-fixture", {}).get("streak", 0)
            if streak != 0:
                raise AssertionError(f"working bound session was treated as ghost: streak={streak}")
            print("SIM working-old-bb: no ghost alert; bound session message is recent.")
        if name == "resumed-idle-agent":
            rec = state.get("conditions", {}).get("invisible-agent:ses-resumed", {})
            expected_streak = i + 1
            expected_alert = now if i == 1 else 0
            if rec.get("streak") != expected_streak or rec.get("last_alert") != expected_alert:
                raise AssertionError(f"resumed idle thread alert mismatch: {rec}")
            if i == 1:
                print("SIM resumed-idle-agent: invisible-agent alert fires on the second run.")
        if name == "ghost-agent-no-message" and i == 1:
            streak = state.get("conditions", {}).get("ghost-agent:thr-fixture", {}).get("streak", 0)
            if streak != 2 or "ghost agent" not in alerts:
                raise AssertionError(f"missing-message bound session did not raise the ghost alert: {alerts}")
            print("SIM ghost-agent-no-message: bound session without a message raised the ghost alert.")
        if name == "orphan-recorder" and i == 1:
            if "orphan process" not in alerts:
                raise AssertionError(f"orphan process did not alert after two no-agent checks: {alerts}")
            print("SIM orphan-recorder: orphan process alerted after two checks with no agent for 15 minutes.")
        if name == "orphan-recorder-active" and i == 1:
            records = [state.get("conditions", {}).get(f"orphan-process:{pid}", {}) for pid in (123, 124, 125)]
            if "orphan process" in alerts or any(record.get("streak") != 0 for record in records):
                raise AssertionError(f"active tester's recorder/simctl/log process raised an alert: {alerts}, {records}")
            print("SIM orphan-recorder-active: active tester's orphan recorder stayed quiet.")
        state_write(state_path, state)
    if name == "anti-spin" and state.get("continue", {}).get("stopped"):
        print("SIM: anti-spin stopped after three unchanged checks.")
    if name == "stuck-agent" and any(key.startswith("stuck-agent:") for key in state.get("conditions", {})):
        raise AssertionError("an old result file without a live session raised a stuck-agent alert")
    if name == "stuck-agent":
        print("SIM stuck-agent: finished-agent result file raised no no-progress alert.")
    print(summary_line(snap, alerts))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print queued messages instead of sending them")
    parser.add_argument("--once-report", action="store_true", help="print one read-only health summary")
    parser.add_argument("--find-session", action="store_true",
                        help="print the newest top-level OpenCode session for REPO (the orchestrator's ORCH_SESSION)")
    parser.add_argument("--simulate", choices=("stuck-agent", "ghost-agent", "ghost-agent-no-message", "invisible-agent", "high-load",
        "disk-big-file", "orphan-recorder", "orphan-recorder-active", "fail-under-load", "unrecorded-pass", "unrecorded-pass-reload",
        "superseded-pass", "server-down", "combined-alerts", "continue",
        "anti-spin", "done", "closed-delete", "not-closed", "read-failure", "working-old-bb", "resumed-idle-agent",
        "off-track", "on-track-timed", "on-track-code", "fast-jules", "new-testers-old-results",
        "no-promise", "review", "lane-drift", "alert-once", "repeat-fail", "unclaimed", "plateau", "sim-idle-timer",
        "regression", "leftover-session", "idle-helper", "reopen"),
        help="run a deterministic offline scenario; always dry-run")
    args = parser.parse_args()
    env = dict(os.environ)
    root = env.get("REPO", "")
    if not root:
        print("REPO is required", file=sys.stderr)
        return 2
    state_path = env.get("STATE_FILE") or os.path.join(root, ".lanes", "watch-state.json")
    if args.simulate:
        env.setdefault("ORCH_THREAD", "fixture-thread")
        simulate(args.simulate, state_path, env)
        return 0
    if args.once_report:
        print(report(collect(env)))
        return 0
    if args.find_session:
        db = os.path.expanduser("~/.local/share/opencode/opencode.db")
        try:
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3) as conn:
                rows = conn.execute(
                    "select id, agent, title from session_v2 where parent_id is null and directory = ? "
                    "order by time_updated desc limit 5", (os.path.realpath(root),)).fetchall()
        except sqlite3.Error as exc:
            print(f"OpenCode database read failed: {exc}", file=sys.stderr)
            return 1
        for row in rows:
            print("\t".join(str(value) for value in row))
        return 0 if rows else 1
    if not env.get("ORCH_THREAD") or not env.get("ORCH_SESSION") or not env.get("VERIFY_DIR"):
        print("ORCH_THREAD, ORCH_SESSION, and VERIFY_DIR are required", file=sys.stderr)
        return 2
    state = state_read(state_path)
    if state.get("done"):
        run_status = read_run_status(env.get("RUN_CARD") or os.path.join(root, ".hivecall", "run.md"))
        if run_status == "running":
            isa = parse_isa(env.get("LEDGER") or env.get("ISA") or os.path.join(root, "_ai/docs/ISA.html"), root)
            if not isa.get("error") and not isa.get("done"):
                clear_done_state(state)
        if state.get("done") and run_status == "closed":
            finish_closed_run(state, env, args.dry_run)
        elif state.get("done"):
            # Ledger-only completion retries pause until the run card is closed.
            state.pop("closed_pause_recorded", None)
            state.pop("closed_automation_id", None)
            state.pop("delete_result", None)
            state["pause_result"] = pause_automation(env, args.dry_run)
        if state.get("done"):
            state_write(state_path, state)
            print(f"WATCH: run already done; {state.get('delete_result') or state.get('pause_result', 'automation lifecycle complete')}.")
            print(summary_line({}, []))
            return 0
    snapshot = collect(env)
    alerts = evaluate(snapshot, state, env, args.dry_run)
    state_write(state_path, state)
    print(summary_line(snapshot, alerts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
