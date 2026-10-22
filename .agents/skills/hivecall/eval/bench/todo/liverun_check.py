"""Outside check for a live benchmark run (see LIVERUN.md). Runs as a BB script automation every 5 min.

Read-only on the run and never messages it. Messages PARENT only when the run looks broken, a tool call
touched a path that could hold answers, or the run ended (closed, or the time cap). At the cap it stops the
run thread, its BB children and the run project's automations, then deletes itself.

Env: RUN_THREAD, RUN_DIR, RUN_PROJECT, PARENT_THREAD, SELF_PROJECT, SELF_NAME, START_EPOCH (seconds);
optional CAP_MIN (125), SILENT_MIN (30), LEAKS (comma-separated path fragments).
"""
import json, os, re, shutil, sqlite3, subprocess, time

E = os.environ
RUN, RUN_DIR, PARENT = E["RUN_THREAD"], E["RUN_DIR"], E["PARENT_THREAD"]
RUN_PROJECT, SELF_PROJECT, SELF_NAME = E["RUN_PROJECT"], E["SELF_PROJECT"], E["SELF_NAME"]
START, CAP = float(E["START_EPOCH"]), float(E.get("CAP_MIN", "125")) * 60
SILENT = float(E.get("SILENT_MIN", "30")) * 60
STATE = os.path.join(os.getcwd(), "liverun-check-state.json")
LEAKS = [p for p in E.get("LEAKS", "swarm-test,hivecall/eval,bench/todo,_ai/task,.evals/hivecall,"
                                    "ai-project-starter-kit/.agents/skills/hivecall").split(",") if p]
BB = E.get("BB_CLI") or shutil.which("bb") or os.path.expanduser("~/.bb/bin/bb")
now = time.time()


def bb(*a):
    return subprocess.run([BB, *a], capture_output=True, text=True, timeout=60).stdout


def bbj(*a):
    try:
        return json.loads(bb(*a, "--json"))
    except Exception:
        return None


def tell(msg):
    bb("thread", "tell", PARENT, f"[run check {time.strftime('%H:%M')}] {msg}")


st = json.load(open(STATE)) if os.path.exists(STATE) else {"sent": []}


def once(key, msg):
    if key not in st["sent"]:
        st["sent"].append(key)
        tell(msg)


def delete_self():
    for a in bbj("automation", "list", "--project", SELF_PROJECT) or []:
        if a.get("name") == SELF_NAME:
            bb("automation", "delete", a["id"], "--project", SELF_PROJECT, "--yes")


# Keep the run thread on the orchestrator agent. The OpenCode BB plugin holds this stamp in memory and can
# fall back to `build` after a bind failure (iamhenry/bb-opencode#39).
stamp = os.path.join(os.getcwd(), "liverun-check-stamp.json")
json.dump({"threadId": RUN, "agent": "orchestrator", "queued": False}, open(stamp, "w"))
bb("plugin", "rpc", "call", "opencode", "stampAgent", "--input-file", stamp)

card = os.path.join(RUN_DIR, ".hivecall", "run.md")
status = ""
if os.path.exists(card):
    m = re.search(r"^status:\s*(\S+)", open(card, errors="replace").read(), re.M)
    status = m.group(1).lower() if m else ""
tstatus = ((bbj("thread", "show", RUN) or {}).get("thread", {}).get("status") or "unknown").lower()
mins = int((now - START) / 60)

# Leak scan + last activity, from the OpenCode DB (read-only), this run's sessions only.
last_activity, hits = None, []
try:
    db = sqlite3.connect("file:" + os.path.expanduser("~/.local/share/opencode/opencode.db") + "?mode=ro", uri=True)
    ids = [r[0] for r in db.execute("SELECT id FROM session_v2 WHERE directory LIKE ? AND time_created >= ?",
                                    (f"%{os.path.basename(RUN_DIR.rstrip('/'))}%", int(START * 1000) - 60000))]
    if ids:
        q = ",".join("?" * len(ids))
        last_activity = db.execute(f"SELECT MAX(time_updated) FROM session_message WHERE session_id IN ({q})", ids).fetchone()[0]
        for sid, data in db.execute(f"SELECT session_id, data FROM session_message WHERE session_id IN ({q}) AND type='assistant'", ids):
            s = " ".join(json.dumps(c.get("input") or c.get("arguments") or c.get("state", {}).get("input") or "")
                         for c in (json.loads(data).get("content") or []) if c.get("type") not in ("text", "reasoning"))
            hits += [(p, sid, s[:160]) for p in LEAKS if p in s]
except Exception as e:
    once("dbfail", f"Could not read the OpenCode DB for the leak scan: {type(e).__name__}. Checks continue.")

for p, sid, s in hits:
    once(f"leak:{p}:{sid}", f"POSSIBLE LEAK: session {sid} used '{p}' in a tool call: {s}")

head = subprocess.run(["git", "-C", RUN_DIR, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
if now - START >= CAP:
    bb("thread", "stop", RUN)
    for c in bbj("thread", "list", "--parent-thread", RUN, "--project", RUN_PROJECT) or []:
        if (c.get("status") or "").lower() not in ("idle", "stopped"):
            bb("thread", "stop", c["id"])
    for a in bbj("automation", "list", "--project", RUN_PROJECT) or []:
        bb("automation", "delete", a["id"], "--project", RUN_PROJECT, "--yes")
    tell(f"CAP: {mins} min reached; run card status '{status or 'none'}'. Stopped the run thread, its children and its watchdog. Start blind QA.")
    delete_self()
elif status == "closed":
    # A run can reopen after closing, so report each close once and keep watching until the cap.
    once(f"closed:{head}", f"DONE: run card says closed after {mins} min at {head} (thread {tstatus}). Start blind QA once the thread is idle.")
else:
    if tstatus in ("failed", "error", "errored", "stopped"):
        once(f"broken:{tstatus}", f"BROKEN: run thread is '{tstatus}' at {mins} min; run card status '{status or 'none'}'.")
    silent = now - (last_activity / 1000 if last_activity else START)
    if silent >= SILENT and tstatus != "running":
        once(f"silent:{int(last_activity or 0)}", f"BROKEN?: no activity from the run or its helpers for {int(silent / 60)} min (thread {tstatus}, {mins} min in).")

json.dump(st, open(STATE, "w"))
