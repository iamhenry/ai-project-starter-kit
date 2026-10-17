#!/usr/bin/env python3
"""Turn find-runs.py output into countable facts, with Clef labels.

Usage: find-runs.py --days 7 > runs.json; digest.py runs.json > digest.json
Per run it reports duration (skill invocation to the first WATCH DONE, else the
last orchestrator event), active time (duration minus quiet gaps with no BB worker running),
orchestrator idle gaps over 30 minutes, every watchdog alert line, and every
child's final report. Clef (Cloudflare's decision model on Ollama Cloud)
labels each alert real/false and each child done/blocked/failed. A label
counts only when Clef is confident; otherwise it is "can't tell". Labels are
hints for the retro judge, not verdicts. Read-only for BB threads.
"""
import json, os, re, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

SURE = 0.8  # confidence needed before a label counts
GAP_MS = 30 * 60 * 1000
# Alert lines the hivecall watchdog sends (see hivecall/watchdog/watch.py).
ALERT = re.compile(r"^(?:🚦 )?(WATCH STALLED|WATCH DONE|WATCH ERROR|HOST|AGENT|GHOST|LEDGER|OFF TRACK|"
                   r"FAIL|LOOP|REGRESSION|UNCLAIMED|PLATEAU|LEFTOVER|OPENCODE|SIMULATOR|BRIEF|ALERT)\b")


def bb_log(tid):
    out = subprocess.run(["bb", "thread", "log", tid, "--json", "--all"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def ollama_key():
    if os.environ.get("OLLAMA_API_KEY"):
        return os.environ["OLLAMA_API_KEY"]
    auth = os.path.expanduser("~/.local/share/opencode/auth.json")
    try:
        return json.load(open(auth))["ollama-cloud"]["key"]
    except (OSError, KeyError, ValueError):
        sys.exit("No Ollama Cloud key: connect the ollama-cloud provider in OpenCode")


KEY = None


def clef(state, question):
    body = json.dumps({"model": "clef", "state": state,
                       "questions": {"q": question}}).encode()
    req = urllib.request.Request("https://ollama.com/v1/systemone", body, {
        "Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["answers"]["q"]
        except Exception as err:
            last = err
    return {"error": str(last)[:200]}


def label(answer, yes="real", no="false"):
    if "error" in answer:
        return "not checked", None
    if answer["type"] == "noul":
        p = answer["noul"]
        return (yes if p >= SURE else no if p <= 1 - SURE else "can't tell"), round(p, 3)
    best = answer["choice"]
    p = answer["probabilities"][best]
    return (best if p >= SURE else "can't tell"), round(p, 3)


def texts(e):
    d = e.get("data") or {}
    if e.get("type") == "client/turn/requested":
        return "\n".join(i.get("text") or "" for i in d.get("input") or [])
    it = d.get("item") or {}
    if e.get("type") == "item/completed" and it.get("type") == "agentMessage":
        return it.get("text") or ""
    return ""


ALERT_Q = {"type": "noul", "instructions":
           "A watchdog sent ALERT about a coding run. FOLLOW_UP is what the "
           "orchestrator said next. Did the follow-up show the alert described a "
           "real problem that needed action (true), rather than a false alarm or "
           "something already handled (false)?"}
GAP_Q = {"type": "choice", "instructions":
         "A coding run's orchestrator went quiet for a while. BEFORE is its last message "
         "before the quiet period; AFTER is the next message it received. Why was it quiet?",
         "criteria": {"closed": "The run had already finished or been closed or cleaned up",
                      "owner": "It had handed a question, result, or decision to the owner and was waiting for them",
                      "stalled": "Work was still open and should have continued, but nothing happened"}}
CHILD_Q = {"type": "choice", "instructions":
           "This is a worker agent's final report in a coding run. What was its outcome?",
           "criteria": {"done": "Finished its assigned task",
                        "blocked": "Stopped and needs someone else to unblock it",
                        "failed": "Tried and did not get the task working",
                        "partial": "Finished some of the task, not all"}}


def run_digest(run, pool):
    ev = bb_log(run["id"])
    # the run ends at the first WATCH DONE (closure); later follow-up work is out of scope
    closed = next((e["createdAt"] for e in ev if e["createdAt"] >= run["invokedAt"]
                   and e.get("type") == "client/turn/requested" and "WATCH DONE" in texts(e)), None)
    end = closed or float("inf")
    done = [e for e in ev if e.get("type") == "item/completed" and run["invokedAt"] <= e["createdAt"] <= end]
    last = max((e["createdAt"] for e in done), default=run["invokedAt"])
    gaps = []
    for a, b in zip(done, done[1:]):
        if b["createdAt"] - a["createdAt"] > GAP_MS:
            before = [texts(x) for x in done if x["createdAt"] <= a["createdAt"] and texts(x)][-1:]
            after = [texts(x) for x in ev if x["createdAt"] >= b["createdAt"] and texts(x)][:1]
            gaps.append({"from": a["createdAt"], "minutes": round((b["createdAt"] - a["createdAt"]) / 60000),
                         "state": {"BEFORE": "".join(before)[-2500:], "AFTER": "".join(after)[:1500]}})
    # watchdog alerts: alert lines in incoming turns that are not BB child reports
    alerts = []
    for i, e in enumerate(ev):
        if e.get("type") != "client/turn/requested" or not run["invokedAt"] <= e["createdAt"] <= end:
            continue
        t = texts(e)
        if t.startswith("[bb"):
            continue
        lines = [(ln, m) for ln in t.splitlines() for m in [ALERT.match(ln)] if m]
        if not lines:
            continue
        follow = [texts(x) for x in ev[i + 1:] if texts(x) and x.get("type") == "item/completed"][:2]
        for line, kind in lines:
            alerts.append({"eventId": e["id"], "at": e["createdAt"],
                           "kind": kind.group(1),
                           "line": line[:300],
                           "state": {"ALERT": line[:1500], "FOLLOW_UP": "\n---\n".join(f[:2000] for f in follow)}})
    children = []
    for cid in run["children"]:
        try:
            cev = bb_log(cid)
        except Exception as err:
            children.append({"id": cid, "outcome": "unreadable", "error": str(err)[:120]})
            continue
        msgs = [texts(x) for x in cev if x.get("type") == "item/completed" and texts(x)]
        stamps = [x["createdAt"] for x in cev if x.get("createdAt")]
        children.append({"id": cid, "start": min(stamps, default=None), "end": max(stamps, default=None),
                         "report": msgs[-1][:4000] if msgs else None})
    for a in alerts:  # an alert nobody answered cannot be judged
        if not a["state"]["FOLLOW_UP"]:
            a["label"], a["p"] = "no follow-up", None
    judged = [a for a in alerts if "label" not in a]
    for a, r in zip(judged, pool.map(lambda a: clef(a["state"], ALERT_Q), judged)):
        a["label"], a["p"] = label(r)
    for a in alerts:
        del a["state"]
    asked = [c for c in children if c.get("report")]
    for c, r in zip(asked, pool.map(lambda c: clef(c["report"], CHILD_Q), asked)):
        c["outcome"], c["p"] = label(r)
        c["report"] = c["report"][:300]
    for c in children:
        c.setdefault("outcome", "no report")
    # a stall is a quiet gap Clef reads as open work going nowhere, with no BB child
    # thread running through it. Native OpenCode subagents are invisible here.
    spans = [(c["start"], c["end"]) for c in children if c.get("start")]
    first_alert = min((a["at"] for a in alerts), default=None)
    for g, r in zip(gaps, pool.map(lambda g: clef(g["state"], GAP_Q), gaps)):
        end = g["from"] + g["minutes"] * 60000
        g["workerActive"] = any(s0 < end and e0 > g["from"] for s0, e0 in spans)
        g["watchdogSeenBefore"] = first_alert is not None and first_alert <= g["from"]
        g["why"], g["p"] = label(r)
        g["stall"] = g["why"] == "stalled" and not g["workerActive"]
        del g["state"]
    edges = sorted([(s0, 1) for s0, _ in spans] + [(e0, -1) for _, e0 in spans])
    live = peak = 0
    for _, step in edges:
        live += step
        peak = max(peak, live)
    count = lambda items, key: {k: sum(1 for x in items if x.get(key) == k)
                                for k in sorted({x.get(key) for x in items})}
    return {"id": run["id"], "title": run["title"], "projectId": run["projectId"],
            "closedBy": "WATCH DONE" if closed else "last orchestrator event",
            "durationMinutes": round((last - run["invokedAt"]) / 60000),
            "activeMinutes": round((last - run["invokedAt"]) / 60000) - sum(g["minutes"] for g in gaps if not g["workerActive"]),
            "stalls": [g for g in gaps if g["stall"]],
            "idleGapsOver30m": gaps, "peakConcurrentWorkers": peak, "alertCounts": count(alerts, "label"),
            "childOutcomes": count(children, "outcome"), "alerts": alerts, "children": children}


def main():
    global KEY
    KEY = ollama_key()
    found = json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)
    with ThreadPoolExecutor(8) as pool:
        runs = [run_digest(r, pool) for r in found["runs"]]
    print(json.dumps({"sure": SURE, "runs": runs, "unreadable": found.get("unreadable", [])}, indent=1))


if __name__ == "__main__":
    main()
