#!/usr/bin/env python3
"""Hivecall eval: grade past hivecall runs from local traces. Read-only on every source.

  python3 eval.py --list            show every hivecall run found (skill tool call {"id":"hivecall"})
  python3 eval.py                   grade runs not graded yet, then rebuild the dashboard
  python3 eval.py --run 2           grade one run (index from --list, run id, or ses_ id)
  python3 eval.py --regrade         grade again even if a row exists
  python3 eval.py --judge-preview   write the secret-filtered Clef requests for inspection (sends nothing)
  python3 eval.py --judge-send      send the inspected requests to clef:cloud and store answers
  python3 eval.py --dashboard       rebuild ~/.evals/hivecall/dashboard.html (self-contained, private)
  python3 eval.py --freeze-baseline record the graded runs as the baseline later skill edits are compared to

Sources: OpenCode DB (~/.local/share/opencode/opencode.db) and BB DB (~/.bb/bb.db), both opened read-only.
Private output: ~/.evals/hivecall/ (never committed; eval/dashboard-data.js is a git-ignored copy of it). Check definitions: README.md.
"""
from __future__ import annotations

import argparse, datetime as dt, difflib, hashlib, json, os, re, sqlite3, subprocess, sys, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
REPO = SKILL.parents[2]
DEFAULT_OUT = Path.home() / ".evals/hivecall"
OUT = Path(os.environ.get("HIVECALL_EVAL_DIR", DEFAULT_OUT))
OC_DB = Path.home() / ".local/share/opencode/opencode.db"
BB_DB = Path.home() / ".bb/bb.db"
GAP = 5 * 60_000            # a gap longer than this between events is not "working"
FOLLOWUP_CAP = 24 * 3.6e6   # only look this far past the final close for follow-up hours
EVAL_VERSION = "4.3"        # bump when a check or judge question changes; result versions are not comparable
STALL_MS = 10 * 60_000      # the watchdog's stall clock; a longer gap without honest proof is "flat"
ANSWER_MS = 10 * 60_000     # an alert counts as acted on when its ANSWER and an action land this fast

# Ids are internal keys (judge answers and labels use them); the dashboard numbers rows in display order.
CHECKS = {
    "1": "Briefs with a talk-back block",
    "2": "Briefs with a valid PROMISE line",
    "4": "Agents visible as BB threads",
    "14": "Stuck workers who spoke up (BUG / BLOCKED / QUESTION) before finishing",
    "12": "Watchdog alerts that were real (not false alarms)",
    "6": "PASS ticks backed by a tester PASS + evidence",
    "10": "Ledger items proven at close",
    "7": "Orchestrator turns with no code edit or screenshot read",
    "8": "Run card closed",
    "9": "Hours: run / working / stalled / owner-wait / usage-wait",
    "3": "subagent-delegation loaded before first hand-off",
    "5": "Worker messages using talk-back words, to the right parent",
    "11": "Skill size (words in loaded SKILL.md)",
    "13": "Owner corrections per run hour (judge)",
    "16": "Final report overclaims (judge)",
    "18": "Useful watchdog alerts: real problem the orchestrator acted on (judge)",
    "19": "Re-read HOW-TO-WORK.md after each compaction",
    "20": "Watchdog alerts answered and acted on within 10 min",
    "21": "Longest stretch without honest proof (min)",
    "22": "Downhill steps (a proven item later broken)",
    "23": "Hill climb (reported, not scored)",
    "24": "Orchestrator turns run as the agent it started as",
    "25": "Helpers that ran as the agent their brief named",
}
# Score = average of these percentages (each behavior counts the same), grouped by the two jobs.
SCORE_CHECKS = ("1", "2", "4", "14", "12", "6", "10", "7", "8")
# 19-22 carry pass flags for the benchmark pass bar; they stay out of the score so old and new runs share one score.
CONTEXT_CHECKS = ("9", "19", "20", "21", "22", "23", "18", "3", "5", "11", "13", "16", "24", "25")
JUDGED_CHECKS = ("12", "18", "13", "16")

sys.path.insert(0, str(SKILL / "watchdog"))
from watch import parse_isa, parse_promise  # noqa: E402  (same parsers the watchdog uses)

TALKBACK = re.compile(r"^(BUG|BLOCKED|QUESTION|STOP)\b")
# PLATEAU is kept for runs graded before the stall ladder replaced it.
WATCHDOG = re.compile(r"^(?:🚦\s*)?(WATCH (REVIEW|DONE|STALLED|CONTINUE)|OFF TRACK|HOST\b|GHOST|UNCLAIMED|PLATEAU|STALL \d|FREE\b|PLAN\b|DRIFT\b"
                      r"|REANCHOR\b|UNANSWERED\b|LEDGER|AGENT |LOOP|REGRESSION|LEFTOVER|BRIEF\b)")
ALERT_ID = re.compile(r"\(alert (W\d+)\)")
REVIEW_VERDICT = re.compile(r"\b(APPROVE_CODE|REVISE_CODE|ASK_USER)\b")
PROGRESS = re.compile(r"progress\W*(?:</?t[hd][^>]*>\s*)*(\d+)\s*/\s*(\d+)", re.I)  # frontmatter "progress 12/40"
VERDICT_WORD = re.compile(r"\b(PASS|FAIL)\b")
WORKER_OTHER = re.compile(r"^((CORRECTION )?RESULT\b|Acknowledged\b)")  # worker posts that break talk-back rules; not the owner
BB_MSG = re.compile(r"^\[bb message from thread:\S+\]\s*")
STATUS = re.compile(r"status\s*:\s*(running|waiting-owner|waiting-usage|closed)\b", re.I)
STATUS_ASSIGN = re.compile(r"status\s*=\s*['\"](running|waiting-owner|waiting-usage|closed)['\"]", re.I)
STUCK_FINAL = re.compile(r"^\W*(?:(?:result|verdict|status)\s*[:=-]\s*)?\W*BLOCKED\b", re.I)  # checked on the start of the final result
TICK = re.compile(r"ISC-0*(\d+)\b[^\n<]{0,40}?\b(PASS|FAIL|BLOCKED|REOPENED)\b")
CODE_EXT = re.compile(r"\.(swift|tsx?|jsx?|mjs|py|kt|java|rb|go|rs|m|mm|c|cc|cpp|h|css|scss|sql)$")
IMAGE = re.compile(r"\.(png|jpe?g|gif|webp|heic)$", re.I)
EVIDENCE_PATH = re.compile(r"(?:/[\w.-]+(?:/[\w.-]+)*\.(?:png|jpe?g|mp4|mov|log|txt|json|md|html|xml|yaml|webm)|\b[\w.-]+(?:/[\w.-]+)*\.(?:png|jpe?g|mp4|mov|log|txt|json|md|html|xml|yaml|webm)\b)", re.I)


def ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000).isoformat(timespec="minutes")


def hours(ms: float) -> float:
    return round(ms / 3.6e6, 2)


# ---------------------------------------------------------------- finder

def find_runs(oc: sqlite3.Connection) -> list[dict]:
    """A run starts at the first `skill` tool call with input {"id":"hivecall"} in a top-level session."""
    rows = oc.execute("""
        select m.session_id, min(m.time_created), s.parent_id, s.directory, s.title from session_message m
        join session_v2 s on s.id = m.session_id
        where m.type = 'assistant' and m.data like '%"hivecall"%' and exists (
          select 1 from json_each(m.data, '$.content') c
          where json_extract(c.value, '$.type') = 'tool' and json_extract(c.value, '$.name') = 'skill'
            and json_extract(c.value, '$.state.input.id') = 'hivecall')
        group by m.session_id order by 2""").fetchall()
    runs = []
    for i, (ses, load, parent, directory, title) in enumerate(rows, 1):
        if parent:  # subagents never run this skill; a child load is not a run
            continue
        data = json.loads(oc.execute("select data from session_message where session_id=? and type='assistant' and time_created=?",
                                     (ses, load)).fetchone()[0])
        body = next((c["text"] for p in data.get("content", []) if p.get("name") == "skill"
                     and (p.get("state") or {}).get("input", {}).get("id") == "hivecall"
                     for c in (p.get("state") or {}).get("content", []) if c.get("type") == "text"), "")
        runs.append({"index": i, "run": f"{iso(load)[:10]}-{ses[-6:]}", "session": ses, "loaded_at": load,
                     "loaded_by": data.get("agent"), "directory": directory, "title": title, "_body": body})
    return runs


def skill_body(text: str) -> str:
    text = text.split("# Skill: hivecall", 1)[-1]
    text = re.split(r"\n(?:Base directory for this skill|<skill_files>)", text)[0]
    return re.sub(r"\s+", " ", text).strip()


def strip_front(text: str) -> tuple[str, str | None]:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    version = re.search(r"^version:\s*(\S+)", m.group(1), re.M).group(1) if m and re.search(r"^version:", m.group(1), re.M) else None
    return (text[m.end():] if m else text), version


def skill_version(loaded: str) -> dict:
    """Match the loaded body against every git version of SKILL.md (front matter is stripped in traces)."""
    rel = ".opencode/plugins/hivecall/SKILL.md"
    path = SKILL.relative_to(REPO) / "SKILL.md"
    # uncommitted copy first, then commits newest first; on a tie the oldest commit wins (when that body first appeared)
    cands = [("working-tree", (SKILL / "SKILL.md").read_text())]
    shas = subprocess.run(["git", "-C", str(REPO), "log", "--format=%h", "--", str(path)], capture_output=True, text=True).stdout.split()
    for sha in shas:
        cands.append((sha, subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{path}"], capture_output=True, text=True).stdout))
    want = skill_body(loaded)
    best = (0.0, "unknown", None)
    for sha, text in cands:
        body, version = strip_front(text)
        body = re.sub(r"\s+", " ", body.split("# Hivecall", 1)[-1]).strip()
        ratio = 1.0 if body and body in want else difflib.SequenceMatcher(None, want, body, autojunk=False).ratio()
        if ratio >= best[0] and ratio > 0:
            best = (ratio, sha, version)
    ratio, sha, version = best
    label = version or f"pre-1.0.0 ({sha})"
    return {"skill_version": label if ratio == 1.0 else f"~{label}", "skill_commit": sha, "match": round(ratio, 3),
            "skill_words": len(want.split()), "_file": rel}


# ---------------------------------------------------------------- exporter

def parts(data: dict) -> list[dict]:
    return data.get("content") or []


def msg_text(data: dict) -> str:
    if isinstance(data.get("text"), str):
        return data["text"]
    return "\n".join(p.get("text", "") for p in parts(data) if p.get("type") == "text")


def tools(data: dict):
    for p in parts(data):
        if p.get("type") == "tool":
            yield p.get("name"), (p.get("state") or {}).get("input") or {}


def file_writes(name: str, inp: dict) -> list[tuple[str, str]]:
    """(path, added text) for every file a write/edit/patch tool call changes."""
    if name in ("write", "edit"):
        return [(str(inp.get("path") or inp.get("filePath") or ""), inp.get("content") or inp.get("newString") or "")]
    if name == "patch":
        out = []
        for m in re.finditer(r"\*\*\* (?:Update|Add) File: ([^\n]+)\n(.*?)(?=\n\*\*\* (?:Update|Add|Delete) File:|\n\*\*\* End Patch|\Z)",
                             inp.get("patchText", ""), re.S):
            added = "\n".join(l[1:] for l in m.group(2).splitlines() if l.startswith("+"))
            out.append((m.group(1).strip(), added))
        return out
    return []


LEDGER_FILE = re.compile(r"(checklist|ISA)\.html\b|ledger\.py\b", re.I)
MESSAGE_SEND = re.compile(r"opencode\s+api\s+post|bb\s+thread\s+tell", re.I)
# Any shell write (used to spot run.md status changes made through shell).
SHELL_MUTATION = re.compile(r"sed\s+-i\b|perl\s+-i\b|tee\b|>>?\s*[^\s;]+|write_text\s*\(|open\s*\([^,]+,\s*['\"][wa]|\.write\s*\(|replace\s*\(|git\s+apply\b|patch\s+-", re.I)
# Only the file a shell command writes TO counts; a code path that is merely read, grepped or run does not.
SHELL_TARGETS = [
    re.compile(r"(?<![\d&<>])>>?\s*['\"]?([^\s;|&'\")]+)"),                       # > file, >> file
    re.compile(r"\btee\s+(?:-a\s+)?['\"]?([^\s;|&'\"]+)"),                        # tee file
    re.compile(r"Path\(\s*['\"]([^'\"]+)['\"]\s*\)\.write_(?:text|bytes)"),         # Path('x').write_text
    re.compile(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wa]"),                     # open('x', 'w')
]
SHELL_INPLACE = re.compile(r"\b(?:sed|perl)\s+-i\S*\s+(.*)")


def shell_targets(command: str) -> set[str]:
    """Files a shell command writes (redirect/tee targets, in-place sed/perl, Python writes)."""
    found = set()
    for rx in SHELL_TARGETS:
        found.update(rx.findall(command))
    for segment in re.split(r"[;\n|]|&&", command):
        m = SHELL_INPLACE.search(segment)
        if m:
            found.update(tok.strip("'\"") for tok in m.group(1).split()[1:])  # skip the expression
    return found


RUN_SCRATCH = re.compile(r"(^|/)\.(lanes|hivecall)/")  # the orchestrator's own ledger tools, not product code


def shell_code_writes(command: str) -> list[str]:
    return sorted(p for p in shell_targets(command) if CODE_EXT.search(p))


QUOTED_LEDGER = re.compile(r"['\"][^'\"\s]*(?:checklist|ISA)\.html['\"]", re.I)
PY_WRITE = re.compile(r"\.write(?:_text)?\s*\(")


def ledger_shell_write(command: str) -> bool:
    """True when the command writes the ledger itself. A tester appending a result row to its own file
    while the text mentions ISA.html is not a ledger tick."""
    if MESSAGE_SEND.search(command):
        return False
    if any(LEDGER_FILE.search(t) for t in shell_targets(command)):
        return True
    if re.search(r"\bledger\.py\b", command) and SHELL_MUTATION.search(command):
        return True
    return bool(QUOTED_LEDGER.search(command) and PY_WRITE.search(command))  # p='ISA.html'; open(p,'w').write(s)


def load_session(oc, ses: str) -> list[dict]:
    out = []
    for typ, t, raw in oc.execute("select type, time_created, data from session_message where session_id=? order by seq", (ses,)):
        d = json.loads(raw)
        d.pop("files", None)  # base64 screenshots: never copied
        for p in parts(d):
            st = p.get("state") or {}
            for c in st.get("content") or []:
                if isinstance(c, dict) and len(c.get("text", "")) > 4000:
                    c["text"] = c["text"][:4000] + " …[trimmed]"
            if p.get("type") == "reasoning":
                p.pop("state", None)
        out.append({"type": typ, "time": t, "agent": d.get("agent"), "source": (d.get("metadata") or {}).get("source"),
                    "text": msg_text(d), "tools": list(tools(d))})
    return out


def build_tree(oc, bb, run: dict) -> dict:
    """Whole agent tree: OpenCode subagent children (parent_id) + BB threads spawned under the run's thread."""
    root = run["session"]
    load = run["loaded_at"] - 60_000
    kids = defaultdict(list)
    for sid, parent, created, agent, title in oc.execute("select id, parent_id, time_created, agent, title from session_v2"):
        kids[parent].append((sid, created, agent, title))
    meta = {sid: (created, agent, title) for p in kids.values() for sid, created, agent, title in p}
    ses2thr, thr2ses = {}, defaultdict(set)
    for thr, ses in bb.execute("select distinct thread_id, provider_thread_id from events where provider_thread_id like 'ses_%'"):
        ses2thr.setdefault(ses, thr)
        thr2ses[thr].add(ses)
    threads = {r[0]: r for r in bb.execute("select id, parent_thread_id, visibility, title_fallback, title, created_at from threads")}
    bb_kids = defaultdict(list)
    for t in threads.values():
        bb_kids[t[1]].append(t[0])
    tree = {root: {"parent": None, "via": "root"}}
    stack = [root]
    while stack:
        s = stack.pop()
        for sid, created, agent, title in kids[s]:
            if sid not in tree and created >= load:
                tree[sid] = {"parent": s, "via": "opencode"}
                stack.append(sid)
        thr = ses2thr.get(s)
        for child in (bb_kids.get(thr, []) if thr else []):
            for sid in thr2ses.get(child, ()):
                if sid not in tree and meta.get(sid, (0,))[0] >= load:
                    tree[sid] = {"parent": s, "via": "bb"}
                    stack.append(sid)
    for sid, node in tree.items():
        created, agent, title = meta.get(sid, (None, None, None))
        thr = ses2thr.get(sid)
        node.update(created=created, agent=agent, title=title, bb_thread=thr,
                    visible=bool(thr and threads.get(thr) and threads[thr][2] == "visible"))
    return tree


def run_windows(sessions: dict, run: dict) -> tuple[list, list, int]:
    """Run window = skill load -> run card `status: closed`; a later `running` reopens it."""
    events = []
    for sid, msgs in sessions.items():
        for m in msgs:
            for name, inp in m["tools"]:
                blob = "\n".join(t for p, t in file_writes(name, inp) if p.endswith("run.md"))
                cmd = str(inp.get("command", "")) if name == "shell" else ""
                if "run.md" in cmd.lower() and SHELL_MUTATION.search(cmd):
                    blob = cmd
                matches = [(x.start(), x.group(1).lower()) for rx in (STATUS, STATUS_ASSIGN) for x in rx.finditer(blob)]
                for _, status in sorted(matches):
                    if m["time"] >= run["loaded_at"]:
                        events.append((m["time"], status))
    events.sort(key=lambda x: x[0])
    last = max((m["time"] for msgs in sessions.values() for m in msgs), default=run["loaded_at"])
    windows, start = [], run["loaded_at"]
    for t, s in events:
        if s == "closed" and start is not None:
            windows.append((start, t)); start = None
        elif s != "closed" and start is None:
            start = t
    if start is not None:
        windows.append((start, last))
    return windows, events, last


def norm_id(ident: str) -> str:
    return ".".join(str(int(x)) for x in re.findall(r"\d+", ident))


def ledger_at_end(directory: str | None, end_ms: int, out: Path) -> dict:
    """The ledger as it stood when the run ended: the working file if it was last written by then (5-min grace),
    else the last commit before the end. Parsed by the watchdog's own parser. `at` dates the snapshot so newer
    trace verdicts are never overridden by it. Once the run folder is deleted, the copy saved at grading is used."""
    snap = out / "ledger-at-end.html"
    if not directory or not Path(directory).is_dir():
        return ledger_summary(snap, out, "saved copy", end_ms, snap.name) if snap.is_file() else {}
    root = Path(directory)
    card = root / ".hivecall/run.md"
    named = re.search(r"^ledger:\s*(\S+)", card.read_text(errors="replace"), re.M) if card.is_file() else None
    paths = ([named.group(1)] if named else []) + ["ISA.html", ".hivecall/checklist.html", "_ai/docs/ISA.html"]
    path = next((root / p for p in paths if (root / p).is_file()), None)
    if not path:
        return {}
    rel = path.relative_to(root).as_posix()
    before = dt.datetime.fromtimestamp(end_ms / 1000).isoformat(timespec="seconds")
    git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)
    mtime = path.stat().st_mtime * 1000
    commit = git("log", "-1", f"--before={before}", "--format=%H %ct", "--", rel).stdout.split()
    if mtime <= end_ms + GAP:
        text, source, at = path.read_text(errors="replace"), "working file", int(mtime)
    elif commit:
        text, source, at = git("show", f"{commit[0]}:{rel}").stdout, f"git {commit[0][:7]}", int(commit[1]) * 1000
    else:
        return {"path": rel, "source": None, "note": "ledger changed after the run and no commit before its end"}
    snap.write_text(text)
    return ledger_summary(snap, root, source, at, rel)


STRAY_VERDICT = re.compile(r"<li>\s*(ISC-[0-9.]+):\s*(PASS|FAIL|BLOCKED)\s*-", re.I)


def ledger_summary(snap: Path, root: Path, source: str, at: int, rel: str) -> dict:
    isa = parse_isa(str(snap), str(root))
    counted = {norm_id(i) for i in isa.get("criteria", [])}
    checked = {norm_id(i) for i in isa.get("checked", [])}
    latest = {}
    for ident, v in (isa.get("latest_verdicts") or {}).items():
        num = norm_id(ident)
        if num in counted:
            status = v.get("status")
            latest[num] = "OPEN" if status == "PASS" and num not in checked else status  # an unticked PASS is not proven
    # A tick script can append its verdict line to the wrong list. Read such lines for items the
    # verification section has no line for; the last one wins.
    stray = {}
    for ident, status in STRAY_VERDICT.findall(re.sub(r"<!--.*?-->", "", snap.read_text(errors="replace"), flags=re.S)):
        stray[norm_id(ident)] = status.upper()
    for num, status in stray.items():
        if num in counted and num not in latest:
            latest[num] = "OPEN" if status == "PASS" and num not in checked else status
    open_tries = {norm_id(i): n for i, n in (isa.get("tries") or {}).items() if norm_id(i) in counted - checked}
    return {"path": rel, "source": source, "at": at, "total": isa.get("total") or len(counted), "checked": sorted(checked),
            "latest": latest, "open_tries": open_tries}


REPORT_SECTION = re.compile(r"^##\s*(?:Final|Progress) report\b.*?(?=^##\s|\Z)", re.I | re.M | re.S)


def final_report_written(sessions: dict, directory: str | None) -> bool:
    """A `## Final report` or (skill 1.4.6, while waiting on the owner) `## Progress report` section with content,
    written into run.md during the run or present in it now."""
    texts = [t for msgs in sessions.values() for m in msgs for name, inp in m["tools"]
             for p, t in file_writes(name, inp) if p.endswith("run.md")]
    texts += [str(inp.get("command", "")) for msgs in sessions.values() for m in msgs for name, inp in m["tools"]
              if name == "shell" and "run.md" in str(inp.get("command", "")) and re.search(r"(?:Final|Progress) report", str(inp.get("command", "")))]
    card = Path(directory or "") / ".hivecall/run.md"
    if directory and card.is_file():
        texts.append(card.read_text(errors="replace"))
    for text in texts:
        for sec in REPORT_SECTION.finditer(text):
            if [l for l in sec.group(0).splitlines()[1:] if l.strip() and not l.strip().startswith("<")]:
                return True
    return False


def export(oc, bb, run: dict) -> dict:
    tree = build_tree(oc, bb, run)
    # Deleting a run's BB project removes its threads from bb.db; the tree saved at an earlier grade keeps them.
    saved = OUT / "runs" / run["run"] / "run.json"
    before = json.loads(saved.read_text()) if saved.is_file() else {}
    if saved.is_file():
        known = {r[0] for r in bb.execute("select id from threads")}
        for sid, node in (before.get("tree") or {}).items():
            if node.get("bb_thread") and node["bb_thread"] not in known and not (tree.get(sid) or {}).get("bb_thread"):
                tree[sid] = {**tree.get(sid, {}), **node}
    sessions = {sid: load_session(oc, sid) for sid in tree}
    for sid, node in tree.items():  # the agent named on its messages wins; a session row can keep a stale default
        said = Counter(m["agent"] for m in sessions[sid] if m["type"] == "assistant" and m["agent"])
        if said:
            node["agent"] = said.most_common(1)[0][0]
    windows, status_events, last = run_windows(sessions, run)
    end = windows[-1][1]
    for sid in list(tree):  # drop children created after the run ended (follow-up chat helpers are counted separately)
        if tree[sid]["via"] != "root" and (tree[sid]["created"] or 0) > end + FOLLOWUP_CAP:
            tree.pop(sid); sessions.pop(sid)
    d = OUT / "runs" / run["run"]
    (d / "sessions").mkdir(parents=True, exist_ok=True)
    for sid, msgs in sessions.items():
        (d / "sessions" / f"{sid}.json").write_text(json.dumps(msgs))
    info = {k: v for k, v in run.items() if not k.startswith("_")}
    info.update(tree=tree, windows=windows, status_events=status_events, last_activity=last,
                closed=bool(status_events and status_events[-1][1] == "closed"),
                ledger=ledger_at_end(run.get("directory"), end, d),
                final_report_written=final_report_written(sessions, run.get("directory")),
                prompt_files=saved_prompt_files(sessions[run["session"]], run.get("directory"), before.get("prompt_files")))
    (d / "run.json").write_text(json.dumps(info, indent=1))
    return {"info": info, "sessions": sessions}


# ---------------------------------------------------------------- checks

def classify_inbound(m: dict) -> str:
    t = m["text"].strip()
    if m["source"] == "subagent":
        return "subagent-result"
    if t.startswith("[bb system]"):
        return "system"
    body = BB_MSG.sub("", t)
    if WATCHDOG.match(body):
        return "watchdog"
    if TALKBACK.match(body):
        return "talkback"
    if BB_MSG.match(t) or WORKER_OTHER.match(body):
        return "worker-other"
    if t.startswith("You are a subagent spawned") or t.startswith("<"):
        return "system"
    return "owner"


def briefs_of(msgs: list[dict], window, prompt_files: dict | None = None) -> list[dict]:
    """One brief per hand-off. A `bb thread spawn --prompt-file` brief is the file's text (saved at grading),
    one per file a simple `for x in a b; do` loop expands to; without saved files the command itself is the brief."""
    out = []
    for m in msgs:
        if not window(m["time"]):
            continue
        for name, inp in m["tools"]:
            cmd = str(inp.get("command", "")) if name == "shell" else ""
            if name == "subagent":
                out.append({"time": m["time"], "agent": inp.get("agent"), "text": inp.get("prompt", "")})
            elif "bb thread spawn" in cmd and "--prompt" in cmd:  # `--help`, greps and notes naming it are not hand-offs
                paths = prompt_file_paths(cmd)
                if any(p in (prompt_files or {}) for p in paths):
                    out += [{"time": m["time"], "agent": "bb", "text": prompt_files.get(p, cmd)} for p in paths]
                else:
                    out.append({"time": m["time"], "agent": "bb", "text": cmd})
    return out


SUBAGENT_PREAMBLE = "You are a subagent spawned by another session."
ROLE_LINE = re.compile(r"\A\s*agent:\s*(build|qa|reviewer|general|plan)\b", re.I)          # BB briefs: no agent flag
ROLE_NAME = re.compile(r"\bYou are [^\n()]{1,40}\((build|qa|reviewer|general|plan)\)", re.I)  # "You are Cy (qa)"


def briefed_role(tree: dict, sessions: dict, sid: str) -> str | None:
    """The agent a helper was briefed as: the `agent` of the subagent call that sent its prompt, else the
    brief's `agent: <role>` line or `You are <Name> (<role>)`."""
    text = next((m["text"] for m in sessions.get(sid, []) if m["type"] == "user" and m["text"].strip()), "").strip()
    if text.startswith(SUBAGENT_PREAMBLE):
        text = text[len(SUBAGENT_PREAMBLE):].strip()
    for m in sessions.get(tree[sid].get("parent"), []):
        for name, inp in m["tools"]:
            if name == "subagent" and inp.get("agent") and str(inp.get("prompt", "")).strip() == text:
                return inp["agent"]
    hit = ROLE_LINE.match(text) or ROLE_NAME.search(text)
    return hit.group(1).lower() if hit else None


PROMPT_FILE = re.compile(r"--prompt-file[= ]\s*['\"]?([^\s'\";|&)]+)")
FOR_LOOP = re.compile(r"\bfor\s+(\w+)\s+in\s+([^;\n]+?)\s*;\s*do\b")


def prompt_file_paths(command: str) -> list[str]:
    """Files a spawn command reads its prompt from; `$x` in a path is expanded from `for x in a b; do`."""
    loops = {m.group(1): [w.strip("'\"") for w in m.group(2).split()] for m in FOR_LOOP.finditer(command)}
    out = []
    for m in PROMPT_FILE.finditer(command):
        path = m.group(1)
        var = re.search(r"\$\{?(\w+)\}?", path)
        words = loops.get(var.group(1)) if var else None
        out += [path.replace(var.group(0), w) for w in words] if words else [path]
    return out


def saved_prompt_files(sessions: list[dict], directory: str | None, saved: dict) -> dict:
    """Text of every prompt file the orchestrator spawned from, read from the run folder at grading.
    Files written by scripts never appear in the trace, so the folder is the only source; once it is
    deleted, the copy saved at the last grade is used."""
    out = dict(saved or {})
    root = Path(directory) if directory else None
    for m in sessions:
        for name, inp in m["tools"]:
            cmd = str(inp.get("command", "")) if name == "shell" else ""
            if "bb thread spawn" not in cmd:
                continue
            for p in prompt_file_paths(cmd):
                f = Path(p) if Path(p).is_absolute() else (root / p if root else None)
                if f and f.is_file():
                    out[p] = f.read_text(errors="replace")
    return out


def worker_messages(msgs: list[dict], inside=lambda _t: True) -> list[dict]:
    out = []
    for m in msgs:
        if not inside(m["time"]):
            continue
        for name, inp in m["tools"]:
            cmd = str(inp.get("command", "")) if name == "shell" else ""
            target = re.search(r"/api/session/(ses_\w+)/prompt", cmd) or re.search(r"bb thread tell\s+(thr_\w+)", cmd)
            if not target:
                continue
            body = re.search(r'"text"\s*:\s*"(.*?)"\s*,\s*"delivery"', cmd, re.S) or re.search(r"<<'?EOF'?\n(.*?)\nEOF", cmd, re.S) \
                or re.search(r"tell\s+thr_\w+\s+(?:--\S+\s+\S+\s+)*['\"](.*)", cmd, re.S)
            text = (body.group(1) if body else "").strip()
            out.append({"time": m["time"], "to": target.group(1), "text": text[:300], "ok": bool(TALKBACK.match(text))})
    return out


def activity(times: list[int], windows, owner_times: list[int], usage) -> dict:
    tot = Counter()
    for a, b in windows:
        pts = [a] + [t for t in times if a <= t <= b] + [b]
        tot["run"] += b - a
        for x, y in zip(pts, pts[1:]):
            gap = y - x
            tot["working"] += min(gap, GAP)
            idle = gap - GAP
            if idle <= 0:
                continue
            if any(x < o <= y + 1000 for o in owner_times):
                tot["owner_wait"] += idle
            elif usage(x):
                tot["usage_wait"] += idle
            else:
                tot["stalled"] += idle
    return {k: hours(v) for k, v in tot.items()}


def grade(exp: dict) -> dict:
    info, sessions = exp["info"], exp["sessions"]
    root = info["session"]
    tree = info["tree"]
    windows = info["windows"]
    inside = lambda t: any(a <= t <= b for a, b in windows)
    end = windows[-1][1]
    rmsgs = sessions[root]
    checks = {}

    def put(cid, name, value, ok=None, n=None, note=""):
        checks[cid] = {"name": name, "value": value, "pass": ok, "n": n, "note": note}

    # 1, 2: brief contract
    briefs = briefs_of(rmsgs, inside, info.get("prompt_files"))
    nb = len(briefs)
    tb = sum(bool(re.search(r"talk[- ]?back", b["text"], re.I)) for b in briefs)
    pr = sum(bool((parse_promise(b["text"]) or {}).get("valid")) for b in briefs)
    rate = lambda k: round(k / nb, 2) if nb else None
    put("1", CHECKS["1"], rate(tb), bool(nb) and tb == nb, nb, f"{tb}/{nb} briefs")
    put("2", CHECKS["2"], rate(pr), bool(nb) and pr == nb, nb, f"{pr}/{nb} briefs (watchdog parser)")

    # 3: delegation skill loaded before first hand-off
    first = min((b["time"] for b in briefs), default=None)
    # A load earlier in the same session (even before hivecall) still sits in the orchestrator's context.
    loads = [m["time"] for m in rmsgs if first is not None and m["time"] < first for name, inp in m["tools"]
             if name == "skill" and inp.get("id") == "subagent-delegation"]
    ok3 = first is not None and any(t < first for t in loads)
    put("3", CHECKS["3"], ok3, None, None,
        "no hand-off in run" if first is None else f"{len(loads)} loads in root session")

    # A child is attributable only when it was created in one of the active run windows.
    children = [s for s, n in tree.items() if n["via"] != "root" and n.get("created") is not None and inside(n["created"])]
    # A BB spawn cannot name an agent, so a BB helper's role is the one its brief names (check 25 reports when
    # it ran as another agent). An OpenCode subagent could name its agent, so the agent it ran as is its role.
    briefed = {s: briefed_role(tree, sessions, s) for s in tree if tree[s]["via"] != "root"}
    role = lambda s: briefed.get(s) if tree[s]["via"] == "bb" and briefed.get(s) else tree[s].get("agent")
    is_tester = lambda s: "qa" in (tree[s].get("agent"), role(s))

    # 4: every in-window agent visible in BB
    vis = sum(tree[s]["visible"] for s in children)
    put("4", CHECKS["4"], round(vis / len(children), 2) if children else None,
        bool(children) and vis == len(children), len(children), f"{vis}/{len(children)} children visible")

    # 5: worker messages are only BUG/BLOCKED/QUESTION/STOP, sent to the real parent
    sent = [dict(w, parent=tree[s]["parent"], parent_thread=tree.get(tree[s]["parent"] or "", {}).get("bb_thread"))
            for s in children for w in worker_messages(sessions[s], inside)]
    good = [w for w in sent if w["ok"] and w["to"] in (w["parent"], w["parent_thread"], root, tree[root]["bb_thread"])]
    put("5", CHECKS["5"], round(len(good) / len(sent), 2) if sent else None, None, len(sent),
        f"{len(good)}/{len(sent)} ok; wrong word {sum(not w['ok'] for w in sent)}, wrong target "
        f"{sum(w['ok'] and w not in good for w in sent)}" if sent else "no worker messages")

    # 6, 10: ledger ticks
    ticks, ids, ledger_writes, proof_times, progress = [], set(), 0, [], []
    blobs = []
    for s in tree:
        for m in sessions[s]:
            if not inside(m["time"]):
                continue
            for name, inp in m["tools"]:
                writes = file_writes(name, inp)
                blob = "\n".join(t for p, t in writes if re.search(r"(checklist|ISA)\.html$|ledger", p, re.I))
                cmd = str(inp.get("command", "")) if name == "shell" else ""
                # Ledgers are often ticked through shell (python replace, a ledger.py helper fed a tick file).
                if cmd and ledger_shell_write(cmd):
                    blob = cmd
                if blob:
                    blobs.append((m["time"], s, blob))
                elif is_tester(s):  # a tester's evidenced PASS/FAIL row is proof too (watchdog rule 10)
                    rows = "\n".join(t for _, t in writes) or (cmd if cmd and SHELL_MUTATION.search(cmd) else "")
                    if any(v in ("PASS", "FAIL") for _, v in TICK.findall(rows)) and EVIDENCE_PATH.search(rows):
                        proof_times.append(m["time"])
    seen_lines = set()  # a full rewrite repeats old verdict lines; only new lines are events
    for time_, s, blob in sorted(blobs, key=lambda b: b[0]):
        ledger_writes += 1
        frac = PROGRESS.findall(blob)
        if frac:  # replace(old, new) puts the new value last
            progress.append((time_, int(frac[-1][0]), int(frac[-1][1])))
        ids.update(re.findall(r"ISC-0*(\d+)", blob))
        fresh = False
        for line in blob.splitlines():
            found = TICK.findall(line)
            if not found or line.strip() in seen_lines:
                continue
            seen_lines.add(line.strip())
            fresh = True
            for num, verdict in found:
                ticks.append({"time": time_, "isc": num, "verdict": verdict, "line": line.strip()[:200], "by": s})
        # Loop-written ticks (f"ISC-{n}") parse no lines; a PASS/FAIL word still marks the write as proof.
        if fresh or (not any(TICK.search(l) for l in blob.splitlines()) and VERDICT_WORD.search(blob)):
            proof_times.append(time_)
    latest = {}
    for t in sorted(ticks, key=lambda t: t["time"]):
        latest[t["isc"]] = t
    # The ledger as it stood at the end is the truth for what closed; trace parsing misses ticks written
    # through loops (f"ISC-{n}"). Its verdicts are dated at the run end.
    ledger = info.get("ledger") or {}
    snap_at = min(ledger.get("at") or end, end)
    for num, status in (ledger.get("latest") or {}).items():
        trace = latest.get(num)
        if (trace or {}).get("verdict") != status and (not trace or trace["time"] <= snap_at):
            tick = {"time": snap_at, "isc": num, "verdict": status, "line": "ledger at run end", "by": "ledger"}
            latest[num] = tick
            ticks.append(tick)
    pass_ticks = [t for t in ticks if t["verdict"] == "PASS"]
    latest_passes = [t for t in latest.values() if t["verdict"] == "PASS"]

    def proven(t):
        for sid in children:
            node = tree[sid]
            if not is_tester(sid) or not node.get("created") or node["created"] >= t["time"]:
                continue
            before = [m for m in sessions[sid] if inside(m["time"]) and m["time"] < t["time"]]
            finals = [m for m in before if m["type"] == "assistant" and m["text"].strip()]
            final = max(finals, key=lambda m: m["time"])["text"] if finals else ""
            # Testers usually write result rows to a verification file (by tool or shell), often while
            # still running for later items, and return a bare verdict.
            writes = [(p, txt) for m in before for name, inp in m["tools"] for p, txt in file_writes(name, inp)]
            writes += [("", str(inp.get("command", ""))) for m in before for name, inp in m["tools"]
                       if name == "shell" and SHELL_MUTATION.search(str(inp.get("command", "")))
                       and not MESSAGE_SEND.search(str(inp.get("command", "")))]
            pool = "\n".join([final] + [txt for _, txt in writes])
            item = rf"ISC-0*{t['isc']}\b"
            row_pass = any(re.search(rf"\b{item}[^\n]*\bPASS\b|\bPASS\b\s+(?:for|on)\s+{item}", line, re.I)
                           for line in pool.splitlines())
            # A bare PASS counts when it wrote a file named for the item, or its brief named only this item.
            brief = next((m["text"] for m in sessions[sid] if m["type"] == "user" and m["text"].strip()), "")
            only_this = set(re.findall(r"ISC-0*(\d+)\b", brief)) == {t["isc"]}
            file_pass = re.match(r"\s*\**PASS\b", final) and (
                only_this or any(re.search(rf"isc-0*{t['isc']}(?!\d)", p, re.I) for p, _ in writes))
            evidence = EVIDENCE_PATH.search(pool) or writes
            if (row_pass or file_pass) and evidence:
                return True
        return False

    backed = {id(t): proven(t) for t in pass_ticks}
    good6 = sum(backed.values())
    if not pass_ticks:
        put("6", CHECKS["6"], None, None, None,
            "n/a: no PASS ticks parsed in the run window" + (f" ({len(ticks)} FAIL/BLOCKED ticks)" if ticks else ""))
    else:
        put("6", CHECKS["6"], round(good6 / len(pass_ticks), 2) if pass_ticks else 1.0,
            good6 == len(pass_ticks), len(pass_ticks),
            (f"{good6}/{len(pass_ticks)} PASS ticks backed"
             + (lambda miss: f"; not backed: {', '.join(miss[:6])}" + (f" +{len(miss) - 6} more" if len(miss) > 6 else "") if miss else "")(
                 sorted({f"ISC-{t['isc']}" for t in pass_ticks if not backed[id(t)]}, key=lambda s: int(s[4:]))))
            if pass_ticks else "no PASS ticks in parsed ledger updates")
    proven_at_close = sum(backed.get(id(t), False) for t in latest_passes)

    # 7: orchestrator discipline in the root session
    code_edits = image_reads = pushes = turns = dirty = 0
    for m in rmsgs:
        if not inside(m["time"]) or m["type"] != "assistant":
            continue
        turns += 1
        before = code_edits + image_reads
        for name, inp in m["tools"]:
            p = str(inp.get("path", ""))
            code_edits += sum(bool(CODE_EXT.search(fp)) and not RUN_SCRATCH.search(fp) for fp, _ in file_writes(name, inp))
            if name == "shell":
                code_edits += sum(not RUN_SCRATCH.search(fp) for fp in shell_code_writes(str(inp.get("command", ""))))
            image_reads += name == "read" and bool(IMAGE.search(p))
            pushes += name == "shell" and "git push" in str(inp.get("command", ""))
        dirty += code_edits + image_reads > before
    put("7", CHECKS["7"], round((turns - dirty) / turns, 2) if turns else None, turns > 0 and dirty == 0, turns,
        f"{turns - dirty}/{turns} turns clean; code edits {code_edits}, image reads {image_reads}, git push {pushes} (push authority not checked)")

    # 8: run card closed. A run that stops on the owner counts when it wrote its Final or Progress report.
    last_status = info["status_events"][-1][1] if info["status_events"] else None
    paused_ok = last_status == "waiting-owner" and bool(info.get("final_report_written"))
    closed = bool(info["closed"] or paused_ok)
    put("8", CHECKS["8"], 1.0 if closed else 0.0, closed, 1,
        (f"{len(info['status_events'])} status changes" if info["status_events"] else "no run card status found")
        + ("; waiting-owner with a Final or Progress report" if paused_ok else "")
        + ("; last status waiting-owner, no Final or Progress report" if last_status == "waiting-owner" and not paused_ok else ""))

    # 9: hours
    times = sorted(m["time"] for s in tree for m in sessions[s] if m["type"] in ("user", "assistant"))
    kinds = {id(m): classify_inbound(m) for m in rmsgs if m["type"] == "user"}
    owner_times = [m["time"] for m in rmsgs if inside(m["time"]) and kinds.get(id(m)) == "owner"]
    ev = info["status_events"]
    usage = lambda t: next((s for e, s in reversed(ev) if e <= t), "") == "waiting-usage"
    hrs = activity(times, windows, owner_times, usage)
    proven_n = proven_at_close if ticks else 0
    hrs["per_proven_item"] = round(hrs.get("working", 0) / proven_n, 2) if proven_n else None
    put("9", CHECKS["9"], hrs, None, None, "5-min gap rule")

    # 10: proven at close + follow-up
    total = ledger.get("total") or len(ids)
    post = [t for t in times if end < t <= end + FOLLOWUP_CAP] if info["closed"] else []
    follow = hours(sum(min(y - x, GAP) for x, y in zip(post, post[1:])))
    share = round(proven_n / total, 2) if total and ticks else None
    note10 = f"{proven_n}/{total} items proven at close; follow-up after close {follow} h" if ticks else f"n/a: no ledger ticks parsed; follow-up after close {follow} h"
    put("10", CHECKS["10"], share, None if share is None else share == 1, total, note10)
    checks["10"]["followup_h"] = follow

    # 11: skill size
    put("11", CHECKS["11"], info.get("skill_words"), None, None, f"version {info.get('skill_version')}")

    # 14: a worker whose final result says BLOCKED is stuck; it spoke up if it sent a talk-back word before that.
    stuck = spoke = 0
    for s in children:
        finals = [m for m in sessions[s] if m["type"] == "assistant" and inside(m["time"]) and m["text"].strip()]
        if not finals or not STUCK_FINAL.match(finals[-1]["text"].strip()[:200]):
            continue
        stuck += 1
        spoke += any(w["ok"] and w["time"] <= finals[-1]["time"] for w in worker_messages(sessions[s], inside))
    put("14", CHECKS["14"], round(spoke / stuck, 2) if stuck else None, (spoke == stuck) if stuck else None, stuck,
        f"{spoke}/{stuck} blocked workers spoke up first" if stuck else "n/a: no worker ended BLOCKED")

    # facts the judge checks reuse (scripted parts)
    inbound = Counter(kinds.get(id(m)) for m in rmsgs if m["type"] == "user" and inside(m["time"]))
    alerts = Counter(WATCHDOG.match(BB_MSG.sub("", m["text"].strip())).group(1) for m in rmsgs
                     if kinds.get(id(m)) == "watchdog" and inside(m["time"]))
    for cid in JUDGED_CHECKS:
        put(cid, CHECKS[cid], None, None, None, "judge: awaiting answers")
    checks["12"]["facts"] = {"alerts": sum(alerts.values()), "by_kind": dict(alerts)}
    checks["13"]["facts"] = {"owner_messages": inbound["owner"], "run_h": hrs.get("run")}
    checks["16"]["facts"] = {"loop_alerts": alerts.get("LOOP", 0), "blocked_items": sum(t["verdict"] == "BLOCKED" for t in latest.values()),
                              "ledger_items": total, "latest_pass": len(latest_passes), "proven": proven_at_close,
                              "unproven": len(latest_passes) - proven_at_close}

    # 19: re-read the working rules after every compaction, before the next hand-off.
    compactions = [m["time"] for m in rmsgs if inside(m["time"]) and
                   (m["type"] == "compaction" or any(name == "compress" for name, _ in m["tools"]))]
    def reads(name_rx):
        return [m["time"] for m in rmsgs for name, inp in m["tools"]
                if (name == "read" and re.search(name_rx, str(inp.get("path") or inp.get("filePath") or "")))
                or (name == "shell" and re.search(name_rx, str(inp.get("command", "")))
                    and not re.search(r"bb\s+thread\s+(?:spawn|tell)|opencode\s+(?:run|api)|>\s*\S*" + name_rx,
                                      str(inp.get("command", ""))))]  # a prompt naming the file is not a read
    rule_reads, card_reads = reads(r"HOW-TO-WORK\.md"), reads(r"\.hivecall/run\.md")
    brief_times = [b["time"] for b in briefs]
    reread = card = 0
    for i, c in enumerate(compactions):
        stop = min([t for t in brief_times if t > c] + compactions[i + 1:i + 2] + [end])
        reread += any(c <= t < stop for t in rule_reads)
        card += any(c <= t < stop for t in card_reads)
    put("19", CHECKS["19"], round(reread / len(compactions), 2) if compactions else None,
        (reread == len(compactions)) if compactions else None, len(compactions),
        f"{reread}/{len(compactions)} compactions followed by HOW-TO-WORK.md before the next hand-off; run card {card}/{len(compactions)}"
        if compactions else "n/a: no compaction in the run")

    # 20: alerts with an id need an ANSWER line plus a visible action (hand-off, ledger write, stop) within 10 min.
    asked = {}
    for m in rmsgs:
        if m["type"] == "user" and inside(m["time"]) and kinds.get(id(m)) == "watchdog":
            for aid in ALERT_ID.findall(m["text"]):
                asked.setdefault(aid, m["time"])
    # An ANSWER counts only when it is written into the run card.
    writes_text = [(m["time"], t) for m in rmsgs for name, inp in m["tools"] for p, t in file_writes(name, inp) if p.endswith("run.md")]
    writes_text += [(m["time"], str(inp.get("command", ""))) for m in rmsgs for name, inp in m["tools"]
                    if name == "shell" and "run.md" in str(inp.get("command", "")) and SHELL_MUTATION.search(str(inp.get("command", "")))]
    action_times = brief_times + proof_times + [m["time"] for m in rmsgs for name, inp in m["tools"]
                                                if name == "shell" and re.search(r"bb thread (stop|spawn)|git commit", str(inp.get("command", "")))]
    acted = 0
    for aid, t in asked.items():
        answered = any(t <= w <= t + ANSWER_MS and re.search(rf"ANSWER {aid}\b", txt) for w, txt in writes_text)
        acted += answered and any(t <= a <= t + ANSWER_MS for a in action_times)
    unanswered = sum(len(re.findall(r"\bUNANSWERED W\d+", m["text"])) for m in rmsgs
                     if m["type"] == "user" and kinds.get(id(m)) == "watchdog" and inside(m["time"]))
    put("20", CHECKS["20"], round(acted / len(asked), 2) if asked else None, (acted == len(asked)) if asked else None, len(asked),
        f"{acted}/{len(asked)} alerts answered and acted on within 10 min; UNANSWERED escalations {unanswered}"
        if asked else "n/a: no alert ids (watchdog before 4.0 or no run-moving alerts)")

    # 21 + flat share: honest proof = a ledger write carrying PASS/FAIL or a commit. Waiting on the owner or usage is not a stall.
    commits = [m["time"] for s in tree for m in sessions[s] if inside(m["time"]) for name, inp in m["tools"]
               if name == "shell" and re.search(r"\bgit commit\b", str(inp.get("command", "")))]
    marks = sorted(set(proof_times + commits))
    waiting = lambda t: next((s for e, s in reversed(ev) if e <= t), "").startswith("waiting")
    gaps = []
    for a, b in windows:  # status changes split gaps, so owner or usage waits drop out cleanly
        pts = sorted(set([a] + [t for t in marks if a <= t <= b] + [e for e, _ in ev if a < e < b] + [b]))
        gaps += [(x, y - x) for x, y in zip(pts, pts[1:]) if not waiting(x)]
    longest = max((g for _, g in gaps), default=0)
    run_ms = sum(b - a for a, b in windows)
    flat = sum(g for _, g in gaps if g > STALL_MS)
    at = next((x for x, g in gaps if g == longest), None)
    put("21", CHECKS["21"], round(longest / 60_000) if gaps else None, (longest <= 2 * STALL_MS) if gaps else None, len(marks),
        f"longest {round(longest / 60_000)} min from {iso(at)[11:16] if at else '?'} (pass ≤ 20 min); {len(marks)} proof marks" if gaps else "n/a")

    # 22: downhill = the progress count fell, or an item went from PASS to something else.
    progress.sort()
    drops = sum(max(0, p[1] - q[1]) for p, q in zip(progress, progress[1:]))
    seen_pass, broke = set(), Counter()
    for t in sorted(ticks, key=lambda t: t["time"]):
        if t["verdict"] == "PASS":
            seen_pass.add(t["isc"])
        elif t["isc"] in seen_pass:
            broke[t["isc"]] += 1; seen_pass.discard(t["isc"])
    still = sorted({n for n in broke if latest.get(n, {}).get("verdict") != "PASS"},
                   key=lambda n: [int(x) for x in n.split(".")])
    down = max(drops, sum(broke.values()))
    put("22", CHECKS["22"], down, not still, None,
        f"{down} downhill steps (count drops {drops}, PASS later broken {sum(broke.values())}); still broken at end: {', '.join('ISC-' + n for n in still) or 'none'}")

    # 23: reported, not scored: how fast and how wide the climb was.
    curve = [(t, n) for t, n, _ in progress]
    if not curve:  # no progress field: count distinct items whose latest trace verdict is PASS
        state = {}
        for t in sorted(ticks, key=lambda t: t["time"]):
            state[t["isc"]] = t["verdict"]
            curve.append((t["time"], sum(v == "PASS" for v in state.values())))
    denom = total or max((d for _, _, d in progress), default=0)
    start = windows[0][0]
    reach = lambda share: next((round(hours(t - start), 2) for t, n in curve if denom and n >= share * denom), None)
    def life(s):
        times = [m["time"] for m in sessions[s] if m["type"] in ("user", "assistant")]
        return (tree[s]["created"], max(times)) if times else None
    spans = {s: life(s) for s in children}
    visible_ms = sum(max(0, min(b, sp[1]) - max(a, sp[0])) for s, sp in spans.items() if sp and tree[s]["visible"] for a, b in windows)
    build = sorted((sp[1] - sp[0]) / 60_000 for s, sp in spans.items() if sp and role(s) == "build")
    verdicts = Counter()
    for s in children:
        if role(s) != "reviewer":
            continue
        finals = [m["text"] for m in sessions[s] if m["type"] == "assistant" and m["text"].strip() and inside(m["time"])]
        hit = REVIEW_VERDICT.search(finals[-1]) if finals else None
        verdicts[hit.group(1) if hit else "none"] += 1
    reviews = sum(verdicts.values())
    open_tries = ledger.get("open_tries") or {}
    climb = {
        "to_50%_h": reach(0.5), "to_90%_h": reach(0.9), "to_100%_h": reach(1.0),
        "proven_per_h": round(proven_n * 3.6e6 / run_ms, 2) if run_ms and proven_n else None,
        "flat_share": round(flat / run_ms, 2) if run_ms else None,
        "avg_visible_helpers": round(visible_ms / run_ms, 1) if run_ms else None,
        "builder_median_min": round(build[len(build) // 2], 1) if build else None,
        "builders_within_15_min": f"{sum(b <= 15 for b in build)}/{len(build)}" if build else None,
        "review_approve_rate": round(verdicts["APPROVE_CODE"] / (verdicts["APPROVE_CODE"] + verdicts["REVISE_CODE"]), 2)
        if verdicts["APPROVE_CODE"] + verdicts["REVISE_CODE"] else None,
        "reviews_per_approval": round(reviews / verdicts["APPROVE_CODE"], 1) if verdicts["APPROVE_CODE"] else None,
        "most_tries_open": max(open_tries.values(), default=None),
        "owner_messages": inbound["owner"],
    }
    put("23", CHECKS["23"], climb, None, None,
        f"proven curve from {'the ledger progress field' if progress else 'trace ticks'}; reviewer verdicts {dict(verdicts)}")

    # 24: the orchestrator session kept the agent it started as (a plugin restart can switch it silently).
    said = [m for m in rmsgs if m["type"] == "assistant" and m.get("agent") and inside(m["time"])]
    if said:
        first = said[0]["agent"]
        other = [m for m in said if m["agent"] != first]
        late_h = round((said[-1]["time"] - other[0]["time"]) / 3_600_000, 2) if other else 0
        put("24", CHECKS["24"], round(1 - len(other) / len(said), 2), not other, len(said),
            f"{len(said) - len(other)}/{len(said)} turns as {first}"
            + (f"; switched to {other[0]['agent']} at {iso(other[0]['time'])}, {late_h} h before the end" if other else ""))
    else:
        put("24", CHECKS["24"], None, None, 0, "no orchestrator turns with an agent name")

    # 25: each helper ran as the agent its brief named (a BB spawn has no agent flag and starts the default agent).
    # Judged on its own turns, like 24: every turn must be the briefed agent, so a helper pinned after its first
    # turn already ran as build is reported as "ran build+reviewer". The session's agent is the fallback only.
    def ran(s):
        names = [m["agent"] for m in sessions[s] if m["type"] == "assistant" and m.get("agent") and inside(m["time"])]
        return list(dict.fromkeys(names)) or [tree[s]["agent"]] * bool(tree[s].get("agent"))
    known = {s: ran(s) for s in children if briefed.get(s)}
    known = {s: a for s, a in known.items() if a}
    wrong = Counter(f"briefed {briefed[s]}, ran {'+'.join(a)}" for s, a in known.items() if a != [briefed[s]])
    miss = sum(wrong.values())
    put("25", CHECKS["25"], round(1 - miss / len(known), 2) if known else None, (not miss) if known else None, len(known),
        (f"{len(known) - miss}/{len(known)} helpers ran as briefed"
         + (f"; {miss} ran as another agent: " + ", ".join(f"{k} {v}" for k, v in wrong.most_common()) if miss else ""))
        if known else "n/a: no helper brief names its agent")
    return checks


# ---------------------------------------------------------------- judges (Clef)

SECRET = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[private-key]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
    (re.compile(r"\b(sk|pk|rk|ghp|gho|ghs|ghu|github_pat|xox[abpr]|glpat|AKIA)[-_]?[\w-]{10,}"), "[secret]"),
    (re.compile(r"Bearer\s+\S+", re.I), "Bearer [secret]"),
    (re.compile(r"\b([A-Z][A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASS))\s*[=:]\s*\S+"), r"\1=[secret]"),
    (re.compile(r"\b[A-Za-z0-9+_-]{40,}\b"), "[long-token]"),
    (re.compile(r"/Users/[^/\s]+"), "/Users/[user]"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"), "[ip]"),
]


def redact(s: str) -> str:
    for rx, rep in SECRET:
        s = rx.sub(rep, s)
    return s


# Reports and summaries, not alarms: a review request, the done summary, a keep-going nudge.
NOT_AN_ALARM = re.compile(r"WATCH (REVIEW|DONE|CONTINUE)\b")
ALERT_LINE = re.compile(r"\n\s*\n|\n(?=(?:🚦\s*)?[A-Z]{3,}[ A-Z]*[: ])")


def alert_lines(text: str) -> list[str]:
    """One watchdog message can carry several alerts (a GHOST line plus five FAIL lines). Judge each one."""
    return [p.strip() for p in ALERT_LINE.split(BB_MSG.sub("", text.strip())) if p.strip()]


def orchestrator_follow_up(root: list[dict], i: int, inside) -> str:
    """What the orchestrator said and did after message i: up to 8 turns, stopping at the next owner or watchdog message."""
    out, turns = [], 0
    for r in root[i + 1:]:
        if not inside(r["time"]):
            continue
        if r["type"] == "user":
            if classify_inbound(r) in ("owner", "watchdog"):
                break
            continue
        if r["type"] != "assistant":
            continue
        if r["text"].strip():
            out.append("SAY: " + r["text"].strip()[:900])
        out += [f"DO: {name}: {json.dumps(inp)[:160]}" for name, inp in (r.get("tools") or [])[:3]]
        turns += 1
        if turns >= 8 or sum(map(len, out)) > 3500:
            break
    return "\n".join(out)[:3500]


FINAL_SECTION = re.compile(r"^##\s*Final report\b.*?(?=^##\s|\Z)", re.I | re.M | re.S)


def final_report(info: dict, root: list[dict], sess: dict, inside) -> str:
    """The skill closes the run card, then sends the report. Prefer a `## Final report` section in run.md,
    then the orchestrator's last message after the close and before the owner's next message (30 min cap),
    then the last message inside the run."""
    if info["closed"]:
        end = info["windows"][-1][1]
        written = [(m["time"], x.group(0)) for msgs in sess.values() for m in msgs for name, inp in m["tools"]
                   for p, t in file_writes(name, inp) if p.endswith("run.md") for x in [FINAL_SECTION.search(t)] if x]
        if written:
            return max(written)[1]
        after = []
        for m in root:
            if m["time"] < end or not m["text"].strip():
                continue
            if m["time"] > end + 1.8e6 or (m["type"] == "user" and classify_inbound(m) == "owner"):
                break
            if m["type"] == "assistant":
                after.append(m["text"])
        if after:
            return after[-1]
    final = [m["text"] for m in root if m["type"] == "assistant" and m["text"].strip() and inside(m["time"])]
    return final[-1] if final else ""


def judge_items(run_id: str) -> list[dict]:
    """One small item per judgment. Each item is a state + the question id from judges.json.
    `ref` is stable (message time, child session, or 'final'), so keys survive changes to other checks."""
    d = OUT / "runs" / run_id
    info = json.loads((d / "run.json").read_text())
    sess = {p.stem: json.loads(p.read_text()) for p in (d / "sessions").glob("*.json")}
    root = sess[info["session"]]
    inside = lambda t: any(a <= t <= b for a, b in info["windows"])
    items = []
    for i, m in enumerate(root):
        if m["type"] != "user" or not inside(m["time"]):
            continue
        kind = classify_inbound(m)
        if kind == "watchdog":
            lines, follow = alert_lines(m["text"]), orchestrator_follow_up(root, i, inside)
            for n, line in enumerate(lines):
                if NOT_AN_ALARM.match(line):
                    continue
                items.append({"check": "12", "q": "watchdog_false_alarm", "ref": f"{m['time']}:{n}",
                              "state": {"alert": line[:1200], "other_alerts_in_same_message": [x[:200] for x in lines if x != line][:6],
                                        "orchestrator_follow_up": follow}})
                items.append(dict(items[-1], check="18", q="useful_alert"))
        elif kind == "owner":
            items.append({"check": "13", "q": "owner_correction", "ref": m["time"], "state": {"owner_message": m["text"][:1500]}})
    ledger_facts = next((r.get("checks", {}).get("16", {}).get("facts", {}) for r in results() if r.get("run") == run_id), {})
    items.append({"check": "16", "q": "honest_ending", "ref": "final",
                  "state": {"final_report": final_report(info, root, sess, inside)[:4000], "run_card_closed": info["closed"],
                            "ledger_facts": ledger_facts}})
    for it in items:
        it["state"] = json.loads(redact(json.dumps(it["state"])))
    return items


def hash_input(question: dict, state: dict) -> str:
    raw = json.dumps({"question": question, "input": state}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def judge_requests(run_ids: list[str]) -> list[dict]:
    qs = json.loads((HERE / "judges.json").read_text())
    reqs = []
    for rid in run_ids:
        for it in judge_items(rid):
            q = qs["questions"][it["q"]]
            reqs.append({"run": rid, "check": it["check"], "ref": it["ref"], "key": f"{rid}#{it['check']}#{it['ref']}",
                         "input_hash": hash_input(q, it["state"]),
                         "body": {"model": qs["model"], "state": it["state"], "questions": {it["q"]: q}}})
    return reqs


def latest_answers() -> dict[str, dict]:
    p = OUT / "judge-answers.jsonl"
    out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            answer = json.loads(line)
            out[answer["key"]] = answer
    return out


def judge_preview(run_ids: list[str]) -> Path:
    reqs = judge_requests(run_ids)
    path = OUT / "judge-request.json"
    path.write_text(json.dumps({"eval_version": EVAL_VERSION, "requests": reqs}, indent=1))
    leaks = [r["key"] for r in reqs for rx, _ in SECRET[:5] if rx.search(json.dumps(r["body"]))]
    latest = latest_answers()
    by_key = {r["key"]: r for r in reqs}
    stale = sum(1 for key, ans in latest.items() if key not in by_key or ans.get("input_hash") != by_key[key]["input_hash"])
    print(f"preview: {path} · {len(reqs)} requests · stale stored answers: {stale} · secret scan: {'clean' if not leaks else leaks}")
    return path


def ollama_key() -> str | None:
    """Reuse OpenCode's Ollama Cloud login. The parser drops every other provider's entry as it reads,
    so only the ollama-cloud key is ever kept; it lives in memory only and is never printed, logged, or written."""
    auth = Path.home() / ".local/share/opencode/auth.json"
    if not auth.exists():
        return None
    keep = lambda pairs: {k: v for k, v in pairs if k in ("ollama-cloud", "type", "key")}
    with auth.open() as f:
        entry = json.load(f, object_pairs_hook=keep).get("ollama-cloud") or {}
    return entry.get("key") if entry.get("type") == "api" else None


def judge_send() -> None:
    qs = json.loads((HERE / "judges.json").read_text())
    pkt = json.loads((OUT / "judge-request.json").read_text())
    if pkt["eval_version"] != EVAL_VERSION:
        sys.exit("preview is stale: run --judge-preview again and inspect it first")
    run_ids = sorted({r["run"] for r in pkt["requests"]})
    expected = {r["key"]: r["input_hash"] for r in judge_requests(run_ids)}
    if {r["key"]: r.get("input_hash") for r in pkt["requests"]} != expected:
        sys.exit("judge prompt or item changed: run --judge-preview again and inspect it first")
    host = os.environ.get("OLLAMA_HOST", "https://ollama.com").rstrip("/")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("OLLAMA_API_KEY") or ollama_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    out = OUT / "judge-answers.jsonl"
    done = latest_answers()
    sent = 0
    for r in pkt["requests"]:
        if done.get(r["key"], {}).get("input_hash") == r["input_hash"]:
            continue
        req = urllib.request.Request(f"{host}/v1/systemone", json.dumps(r["body"]).encode(), headers)
        try:
            ans = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:  # exit rule: unreachable -> scripted checks only
            sys.exit(f"judge checks BLOCKED: clef:cloud unreachable at {host} ({e})")
        (q, a), = ans["answers"].items()
        with out.open("a") as f:
            f.write(json.dumps({"key": r["key"], "run": r["run"], "check": r["check"], "ref": r["ref"],
                                "input_hash": r["input_hash"], "p_yes": a.get("noul"),
                                "yes": a.get("noul", 0) >= qs["yes_above"]}) + "\n")
        sent += 1
    print(f"answers: {out} · sent {sent} stale/missing item(s)")


def judge_summary() -> dict:
    """Only hash-current answers count. A judge is trusted at >= 80% agreement with >= 20 trace-audit labels."""
    run_ids = [r["run"] for r in results() if (OUT / "runs" / r["run"] / "run.json").exists()]
    expected = {r["key"]: r for r in judge_requests(run_ids)}
    stored = latest_answers()
    valid = [a for key, a in stored.items() if key in expected and a.get("input_hash") == expected[key]["input_hash"]]
    stale = sum(1 for key, a in stored.items() if key not in expected or a.get("input_hash") != expected[key]["input_hash"])
    label_rows = defaultdict(list)
    if (OUT / "labels.jsonl").exists():
        for l in (OUT / "labels.jsonl").read_text().splitlines():
            x = json.loads(l); label_rows[x["key"]].append(x)
    labels = {}
    for key, vals in label_rows.items():
        humans = [x for x in vals if str(x.get("source", "")).lower().startswith("human")]
        labels[key] = humans[-1] if humans else vals[-1]
    stats = defaultdict(lambda: {"tp": 0, "fn": 0, "tn": 0, "fp": 0, "n": 0, "sources": Counter()})
    for a in valid:
        label = labels.get(a["key"])
        if not label or not isinstance(label.get("yes"), bool):
            continue
        s = stats[a["check"]]
        s["n"] += 1; s["sources"][label.get("source", "unspecified")] += 1
        if label["yes"] and a["yes"]: s["tp"] += 1
        elif label["yes"]: s["fn"] += 1
        elif a["yes"]: s["fp"] += 1
        else: s["tn"] += 1
    per = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for a in valid:
        per[a["run"]][a["check"]][0] += a["yes"]; per[a["run"]][a["check"]][1] += 1
    calibration = {}
    for c, s in stats.items():
        sens = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
        spec = s["tn"] / (s["tn"] + s["fp"]) if s["tn"] + s["fp"] else None
        calibration[c] = {"sensitivity": round(sens, 3) if sens is not None else None,
                          "specificity": round(spec, 3) if spec is not None else None,
                          "label_count": s["n"], "label_sources": dict(s["sources"]),
                          "agreement": round((s["tp"] + s["tn"]) / s["n"], 3) if s["n"] else None,
                          "trusted": s["n"] >= 20 and (s["tp"] + s["tn"]) / s["n"] >= .8}
    return {"calibration": calibration, "per_run": {r: {c: v for c, v in cs.items()} for r, cs in per.items()},
            "stale_answers": stale, "valid_answers": len(valid), "expected_answers": len(expected),
            "label_source_used": {k: v.get("source", "unspecified") for k, v in labels.items()}}


# ---------------------------------------------------------------- results + dashboard

def results() -> list[dict]:
    p = OUT / "results.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def skill_fingerprint(commit: str) -> str:
    """Hash the full skill source at the commit matched to the run (or the matched working tree)."""
    root = SKILL.relative_to(REPO)
    fixed = [root / "SKILL.md", root / "HOW-TO-WORK.md", root / "watchdog/watch.py", root / "watchdog/lessons.md"]
    if commit == "working-tree":
        files = [p for p in fixed if (REPO / p).is_file()]
        refs = sorted((root / "references").glob("**/*"))
        files += [p for p in refs if (REPO / p).is_file()]
        entries = [(p.as_posix(), (REPO / p).read_bytes()) for p in files]
    else:
        names = [p.as_posix() for p in fixed]
        names.append((root / "references").as_posix())
        listed = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", commit, "--", *names],
                                capture_output=True, text=True, check=True).stdout.splitlines()
        entries = []
        for name in listed:
            data = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{name}"],
                                  capture_output=True, check=True).stdout
            entries.append((name, data))
    digest = hashlib.sha256()
    for name, data in sorted(entries):
        digest.update(name.encode()); digest.update(b"\0"); digest.update(data); digest.update(b"\0")
    return digest.hexdigest()


def score(checks: dict) -> dict:
    """Average of the behavior percentages that apply to this run; n/a behaviors are left out, not zero."""
    vals = [checks[c]["value"] for c in SCORE_CHECKS if isinstance(checks.get(c, {}).get("value"), (int, float))]
    return {"score": round(100 * sum(vals) / len(vals)) if vals else None, "used": len(vals)}


def baseline_data() -> dict | None:
    p = OUT / "baseline.json"
    return json.loads(p.read_text()) if p.exists() else None


def scored_rows(js: dict) -> list[dict]:
    """Results with trusted judge values filled in and the per-run score; used by the dashboard and the freeze."""
    rows = json.loads(json.dumps(results()))
    for row in rows:
        for cid in JUDGED_CHECKS:
            check = row["checks"][cid]
            calibration = js["calibration"].get(cid, {})
            pair = js["per_run"].get(row["run"], {}).get(cid)
            trusted = calibration.get("trusted", False)
            check.update(judge_trusted=trusted, agreement=calibration.get("agreement"),
                         sensitivity=calibration.get("sensitivity"),
                         specificity=calibration.get("specificity"),
                         label_count=calibration.get("label_count", 0),
                         label_sources=calibration.get("label_sources", {}))
            if not trusted:
                check.update(value=None, note=f"judge not trusted: agreement {calibration.get('agreement')} on {calibration.get('label_count', 0)} labels")
            elif not pair:
                check.update(value=None, n=0, note="no items to judge in this run")
            else:
                yes, n = pair
                if cid == "12":  # scored as the share of alerts that were real
                    check.update(value=round(1 - yes / n, 2), n=n, note=f"{n - yes}/{n} alerts real (judge)")
                elif cid == "18":
                    check.update(value=yes, n=n, note=f"{yes}/{n} alerts caught a real problem that was acted on (judge)")
                elif cid == "13":
                    run_h = check.get("facts", {}).get("run_h")
                    check.update(value=round(yes / run_h, 2) if run_h else None, n=n, note=f"{yes} corrections in {run_h} run h (judge)")
                else:
                    check.update(value=yes, n=n, note=f"{yes} of {n} final reports overclaim (judge)")
        row["score"] = score(row["checks"])
    return rows


def dashboard() -> Path:
    js = judge_summary()
    rows = scored_rows(js)
    base = baseline_data()
    payload = {"rows": rows, "baseline": base, "eval_version": EVAL_VERSION,
               "built_at": dt.datetime.now().isoformat(timespec="minutes"),
               "score_checks": SCORE_CHECKS, "context_checks": CONTEXT_CHECKS,
               "judges": js["calibration"], "stale_answers": js["stale_answers"]}
    data = OUT / "dashboard-data.js"
    data.write_text("window.HIVECALL = " + json.dumps(payload) + ";\n")
    # The repo's dashboard.html reads a git-ignored copy next to it. A real file, not a symlink: BB's preview
    # can't follow a link out of the repo. Only written when grading into the default private folder.
    local = HERE / "dashboard-data.js"
    if OUT == DEFAULT_OUT:
        if local.is_symlink() or local.exists():
            local.unlink()
        local.write_text(data.read_text())
    # A self-contained private copy too, for opening outside the repo.
    template = (HERE / "dashboard.html").read_text()
    inline = json.dumps(payload).replace("<", "\\u003c")
    private = template.replace('<script src="dashboard-data.js"></script>', f"<script>window.HIVECALL = {inline};</script>")
    (OUT / "dashboard.html").write_text(private)
    return OUT / "dashboard.html"


def freeze_baseline(force: bool = False) -> Path:
    """Write an immutable snapshot; it is deliberately never called by the normal grading path."""
    rows = results()
    if not rows or {r.get("eval_version") for r in rows} != {EVAL_VERSION}:
        sys.exit(f"refusing baseline: results must all be eval {EVAL_VERSION}; run --regrade first")
    out = OUT / "baseline.json"
    if out.exists() and not force:
        sys.exit("baseline already exists; use --force only when explicitly replacing it")
    snapshot = []
    for row in scored_rows(judge_summary()):
        fp = row.get("skill_fingerprint") or skill_fingerprint(row["skill_commit"])
        snapshot.append({"run": row["run"], "skill_version": row.get("skill_version"), "skill_commit": row.get("skill_commit"),
                         "skill_fingerprint": fp, "score": row["score"], "checks": row["checks"]})
    payload = {"eval_version": EVAL_VERSION, "frozen_at": dt.datetime.now().isoformat(timespec="seconds"), "runs": snapshot}
    temp = out.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=1)); temp.replace(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run")
    ap.add_argument("--regrade", action="store_true")
    ap.add_argument("--judge-preview", action="store_true")
    ap.add_argument("--judge-send", action="store_true")
    ap.add_argument("--dashboard", action="store_true")
    ap.add_argument("--freeze-baseline", action="store_true")
    ap.add_argument("--force", action="store_true", help="allow replacing an existing frozen baseline")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.freeze_baseline:
        print(freeze_baseline(a.force)); print(dashboard()); return
    if a.force:
        ap.error("--force is only valid with --freeze-baseline")
    if a.dashboard:
        print(dashboard()); return
    if a.judge_send:
        judge_send(); print(dashboard()); return
    oc, bb = ro(OC_DB), ro(BB_DB)
    runs = find_runs(oc)
    if a.list:
        for r in runs:
            print(f"{r['index']:>2}  {r['run']}  {r['session']}  loaded {iso(r['loaded_at'])} by {r['loaded_by']}  {(r['title'] or '')[:50]}")
        return
    if a.run:
        runs = [r for r in runs if a.run in (str(r["index"]), r["run"], r["session"])]
        if not runs:
            sys.exit(f"no hivecall run matches {a.run}")
    if a.judge_preview:
        judge_preview([r["run"] for r in runs if (OUT / "runs" / r["run"] / "run.json").exists()]); return
    graded = {r["session"] for r in results()}
    todo = [r for r in runs if a.regrade or r["session"] not in graded]
    for r in list(todo):
        r.update(skill_version(r.pop("_body")))
        if r["skill_commit"] == "unknown":
            print(f"skipped {r['run']}: its loaded skill body matches no SKILL.md version")
            todo.remove(r)
            continue
        r["skill_fingerprint"] = skill_fingerprint(r["skill_commit"])
        exp = export(oc, bb, r)
        info = exp["info"]
        row = {"run": r["run"], "session": r["session"], "bb_thread": info["tree"][r["session"]]["bb_thread"],
                "directory": r["directory"], "title": r["title"], "loaded_at": iso(r["loaded_at"]), "loaded_by": r["loaded_by"],
                "skill_version": r["skill_version"], "skill_commit": r["skill_commit"], "skill_match": r["match"],
                "skill_fingerprint": r["skill_fingerprint"],
                "agents": len(info["tree"]), "eval_version": EVAL_VERSION, "graded_at": dt.datetime.now().isoformat(timespec="seconds"),
                "checks": grade(exp)}
        keep = [x for x in results() if x["session"] != r["session"]]
        (OUT / "results.jsonl").write_text("".join(json.dumps(x) + "\n" for x in keep + [row]))
        sc = score(row["checks"])
        print(f"graded {r['run']} ({r['skill_version']}): {len(info['tree'])} agents, score {sc['score']}% from {sc['used']} behaviors (judge check 12 counts after --dashboard)")
    print(f"{len(todo)} run(s) graded · {dashboard()}")


if __name__ == "__main__":
    main()
