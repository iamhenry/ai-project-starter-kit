from __future__ import annotations

import datetime as dt
import hashlib
import html
import os
import re
import stat as stat_module
from pathlib import Path

from hivewatch.promise import normalize_ident
from hivewatch.shell import BB, flatten_dicts


VERDICT = re.compile(r"^\|\s*((?:ISC-)?\d+(?:\.\d+)?)\s*\|\s*(PASS|FAIL|BLOCKED)\b(.*)$", re.I)


ISA_VERDICT = re.compile(r"^(ISC-[0-9.]+):\s*(PASS|FAIL|BLOCKED)\s*-\s*([^;]*)", re.I)


PLACEHOLDER = re.compile(r"not probed|group stopped|not run|stopped after|pending", re.I)


EVIDENCE_REFERENCE = re.compile(r"(?:`[^`]+\.[^`]+`|[\w./-]+\.(?:png|jpe?g|json|txt|mp4|log|csv|mov|webm)\b|https?://\S+)", re.I)


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
        return {"valid": False, "status": None, "waiting_text": None, "goal": None,
                "owner_rules": [], "answers": {}, "needs": {}, "plan_valid": False}
    m = re.search(r"^\s*(?:[-*]\s*)?\**status\**:\s*`?([a-z-]+)", source, re.M | re.I)
    waiting = re.search(r"^\s*waiting\s*:\s*(\S.*?)\s*$", source, re.M | re.I)
    goal = re.search(r"^\s*goal\s*:\s*(\S.*?)\s*$", source, re.M | re.I)
    sections: dict[str, list[str]] = {}
    current = None
    for line in source.splitlines():
        heading = re.match(r"^##\s+(.*?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            sections.setdefault(current, [])
        elif current is not None and line.strip() and not line.strip().startswith("<"):
            sections[current].append(line.strip())
    answers = {}
    for line in source.splitlines():
        answer = re.search(r"\bANSWER\s+(W\d+)\s*:\s*(.*)$", line)
        if answer:
            answers[answer.group(1)] = answer.group(2).strip()
    needs = {}
    for line in sections.get("plan map", []):
        item = re.search(r"(ISC-[0-9.]+)\s+needs\s*:\s*([^·|]*)", line, re.I)
        if item:
            needs[normalize_ident(item.group(1))] = {normalize_ident(ident) for ident in
                                                      re.findall(r"ISC-[0-9.]+", item.group(2))}
    return {"valid": True, "status": m.group(1).lower() if m else None,
            "waiting_text": waiting.group(1).strip() if waiting else None,
            "goal": goal.group(1).strip() if goal else None,
            "owner_rules": [re.sub(r"^[-*]\s*", "", line) for line in sections.get("owner rules", [])],
            "answers": answers, "needs": needs, "plan_valid": bool(needs), "plan_checked": True}


def parse_isa(path: str, root: str = "") -> dict:
    # A ledger path is the repo's: a relative one (`.hivecall/checklist.html`), or one built from an empty $REPO
    # (`/.hivecall/checklist.html`, which made the watchdog report "Proven 0/0" on a 10/16 run).
    if root and path and not os.path.exists(path):
        candidate = os.path.join(root, path.lstrip("/"))
        if os.path.exists(candidate):
            path = candidate
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
    tries: dict[str, int] = {}
    latest_fail_sigs: dict[str, str] = {}
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
            norm = normalize_ident(ident)
            latest_fail_sigs.pop(norm, None)
            if status == "PASS":
                pass_lines += 1
                pass_ids.add(ident)
                pass_history.add(norm)
                fail_counts[norm] = 0
                tries[norm] = 0
            else:
                tries[norm] = tries.get(norm, 0) + 1  # FAIL and BLOCKED are both attempts
            if status == "FAIL":
                fail_counts[norm] = fail_counts.get(norm, 0) + 1
                signature = hashlib.sha256(text.encode()).hexdigest()[:12]
                fail_occurrences[signature] = fail_occurrences.get(signature, 0) + 1
                fails.append((ident, f"{signature}-{fail_occurrences[signature]}", text))
                latest_fail_sigs[norm] = f"{signature}-{fail_occurrences[signature]}"

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
            "fail_counts": fail_counts, "tries": tries, "latest_fail_sigs": latest_fail_sigs,
            "criteria": sorted(normalize_ident(ident) for ident in criteria),
            "regressions": sorted(regressions), "owner_only_ids": sorted(owner_only_ids),
            "ledger_mtime": ledger_mtime, "verdict_count": verdict_count,
            "owner_only": len(re.findall(r"<li\b", re.sub(r"<!--.*?-->", "", (
                re.search(r'<ul[^>]*id="owner-only"[^>]*>(.*?)</ul>', source, re.S) or re.match(r"()", "")).group(1), flags=re.S))),
            "error": "" if criteria else "no ISA criteria found"}


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


def pause_automation(env: dict[str, str], dry_run: bool) -> str:
    """Rule 11: switch itself off. Returns a short result for the heartbeat."""
    automation_id = env.get("AUTOMATION_ID", "")
    if "AUTOMATION_ID" not in env and env.get("PROJECT_ID") and env.get("ORCH_THREAD"):
        listing, _ = BB.parse_json(["automation", "list", "--project", env["PROJECT_ID"], "--json"])
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
    args = ["automation", "pause", automation_id]
    if env.get("PROJECT_ID"):
        args += ["--project", env["PROJECT_ID"]]  # bb requires it outside a thread
    _, error = BB.command(args, 10.0)
    return f"pause {automation_id} failed: {error}" if error else f"paused {automation_id}"


def delete_automation(env: dict[str, str], dry_run: bool) -> str:
    """Delete itself after a closed run. Unlike pause, deletion never looks up by name."""
    automation_id = env.get("AUTOMATION_ID", "")
    if not automation_id:
        return "no explicit automation id; not deleting"
    if not env.get("PROJECT_ID"):
        return "no project id; not deleting"
    args = ["automation", "delete", automation_id, "--project", env["PROJECT_ID"], "--yes"]
    if dry_run:
        print(f"DRY-RUN: would run bb {' '.join(args)}")
        return f"would delete {automation_id}"
    _, error = BB.command(args, 10.0)
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
