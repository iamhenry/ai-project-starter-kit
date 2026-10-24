"""Progress reporter for a live benchmark run (see LIVERUN.md). Runs as a BB script automation.

Read-only on the run. Sends PARENT one short status line every PERIOD_MIN (default 15) minutes, or sooner
when the run card status changes. Deletes itself when the run card says closed or the thread is gone.

Env: RUN_THREAD, RUN_DIR, RUN_PROJECT, PARENT_THREAD, SELF_PROJECT, SELF_NAME, START_EPOCH (seconds);
optional PERIOD_MIN (15).
"""
import collections, json, os, re, shutil, subprocess, time

E = os.environ
RUN, RUN_DIR, PARENT = E["RUN_THREAD"], E["RUN_DIR"], E["PARENT_THREAD"]
RUN_PROJECT, SELF_PROJECT, SELF_NAME = E["RUN_PROJECT"], E["SELF_PROJECT"], E["SELF_NAME"]
START, PERIOD = float(E["START_EPOCH"]), float(E.get("PERIOD_MIN", "15")) * 60
STATE = os.path.join(os.getcwd(), "liverun-progress-state.json")
BB = E.get("BB_CLI") or shutil.which("bb") or os.path.expanduser("~/.bb/bin/bb")
now = time.time()


def run(*a, cwd=None):
    return subprocess.run(a, capture_output=True, text=True, timeout=60, cwd=cwd).stdout


def bbj(*a):
    try:
        return json.loads(run(BB, *a, "--json"))
    except Exception:
        return None


def read(path):
    try:
        return open(path, errors="replace").read()
    except OSError:
        return ""


st = json.load(open(STATE)) if os.path.exists(STATE) else {"last": 0, "status": None}

card = read(os.path.join(RUN_DIR, ".hivecall", "run.md"))
m = re.search(r"^status:\s*(\S+)", card, re.M)
status = m.group(1) if m else "not-started"

threads = bbj("thread", "list", "--project", RUN_PROJECT, "--include-hidden") or []
by = collections.Counter(t.get("status") for t in threads if t["id"] != RUN)
orch = next((t.get("status") for t in threads if t["id"] == RUN), "gone")

commits = run("git", "log", "--oneline", cwd=RUN_DIR).strip().splitlines()
last = commits[0][:70] if commits else "-"

counts = collections.Counter()
for line in read(os.path.join(RUN_DIR, ".hivecall", "events.jsonl")).splitlines():
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("type") in ("blocked", "warning"):
        counts[f'{ev["type"]}:{ev.get("rule")}'] += 1

if st["last"] and status == st["status"] and now - st["last"] < PERIOD and orch != "gone":
    raise SystemExit
msg = (f"[run progress {time.strftime('%H:%M')}] {int((now - START) / 60)} min | card={status} | "
       f"orchestrator={orch} | helpers={dict(by) or 0} | commits={len(commits)} (last: {last}) | "
       f"hook events={dict(counts) or 'none'}")
run(BB, "thread", "tell", PARENT, "--mode", "queue", msg)
st.update(last=now, status=status)
json.dump(st, open(STATE, "w"))

if status == "closed" or orch == "gone":
    for a in bbj("automation", "list", "--project", SELF_PROJECT) or []:
        if a.get("name") == SELF_NAME:
            run(BB, "automation", "delete", a["id"], "--project", SELF_PROJECT, "--yes")
