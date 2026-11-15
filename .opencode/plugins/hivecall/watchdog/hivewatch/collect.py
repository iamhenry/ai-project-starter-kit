from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path

from hivewatch.ledger import load_results, parse_isa, read_run_card
from hivewatch.promise import normalize_ident
from hivewatch.probes import (
    bb_child_sessions,
    load_host_facts,
    load_lane_facts,
    load_server,
    load_sessions,
)
from hivewatch.shell import BB, command, minutes_since


def collect(env: dict[str, str], now: float | None = None) -> dict:
    now = now or time.time()
    root = env.get("REPO", "")
    isa = parse_isa(env.get("LEDGER") or env.get("ISA") or os.path.join(root, "_ai/docs/ISA.html"), root)
    run_card = read_run_card(env.get("RUN_CARD") or os.path.join(root, ".hivecall", "run.md"))
    run_status = run_card["status"]
    host = load_host_facts(root, now, env)
    sessions = load_sessions(env.get("ORCH_SESSION", ""), now, root, env.get("VERIFY_DIR", ""),
                             bb_child_sessions(env.get("ORCH_THREAD", "")))
    bb = BB.load(env.get("ORCH_THREAD", ""), sessions["children"], sessions["live"])
    server = load_server()
    promised_paths = {session["promise"].get("result_path") for session in sessions["children"]
                      if session.get("promise") and session["promise"].get("result_path")}
    evidence = load_results(env.get("VERIFY_DIR", ""), isa, now, promised_paths)
    lanes = load_lane_facts(sessions["live"])
    head, head_error = command(["git", "-C", root, "rev-parse", "HEAD"], 2.0)
    # Candidate = HEAD plus uncommitted product edits (run files excluded), for the DRIFT check.
    diff, diff_error = command(["git", "-C", root, "diff", "HEAD", "--", ".", ":(exclude).hivecall",
                                ":(exclude).lanes", ":(exclude)_ai"], 3.0)
    # New, untracked source files change the candidate too; screenshots and logs a tester writes do not.
    others, others_error = command(["git", "-C", root, "ls-files", "--others", "--exclude-standard", "--", ".",
                                    ":(exclude).hivecall", ":(exclude).lanes", ":(exclude)_ai"], 3.0)
    untracked = []
    for name in sorted(others.splitlines()) if not others_error else []:
        if re.search(r"\.(html?|css|scss|m?js|jsx|tsx?|py|swift|kt|go|rs|json)$", name):
            try:
                st = os.stat(os.path.join(root, name))
                untracked.append(f"{name}:{st.st_size}:{st.st_mtime_ns}")
            except OSError:
                pass
    candidate = (hashlib.sha256((f"{head}\n{diff}\n" + "\n".join(untracked)).encode()).hexdigest()
                 if head and not head_error and not diff_error else None)
    return {"now": now, "host": host, "server": server, "sessions": sessions, "bb": bb,
            "isa": isa, "run_status": run_status, "run_card": run_card, "evidence": evidence,
            "lanes": lanes, "head": head, "candidate": candidate,
            "head_valid": bool(head and not head_error),
            "head_error": head_error}


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
    climb = f" · {snapshot['climb']}" if snapshot.get("climb") else ""
    return (f"load {load:.0f}" if load is not None else "load ?") + " · " + \
        (f"disk {free:.0f} GB" if free is not None else "disk ? GB") + \
        f" · {agents} · {ledger} · {status}{climb}"


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
