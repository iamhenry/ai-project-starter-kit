#!/usr/bin/env python3
"""List archived BB threads that explicitly invoked the hivecall skill.

Usage: find-runs.py [--days 7] [--skill hivecall]
Prints one JSON object: window, scanned count, and runs with their
children. A thread counts only when its log has a completed skill tool
call named exactly `hivecall`, or a user turn carrying the injected
skill body (a slash command). Titles, mentions and plain file reads of
SKILL.md do not count. Read-only: it only runs `bb thread list/log`.
"""
import argparse, json, re, subprocess, time
from concurrent.futures import ThreadPoolExecutor


def bb(*args):
    out = subprocess.run(["bb", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def invocation(events, skill):
    """Return (event id, how) for the first explicit invocation, else None."""
    body = re.compile(r'<skill_content[^>]*name="%s"' % re.escape(skill))
    for e in events:
        data = e.get("data") or {}
        item = data.get("item") or {}
        if (e.get("type") == "item/completed" and item.get("type") == "toolCall"
                and item.get("tool") == "skill" and item.get("status") == "completed"):
            a = item.get("arguments") or {}
            if skill in (a.get("name"), a.get("id")):
                return e.get("id"), "skill tool call"
        if e.get("type") == "client/turn/requested":
            for i in data.get("input") or []:
                if body.search(i.get("text") or ""):
                    return e.get("id"), "slash command"
    return None


def scan(t, skill):
    try:
        events = bb("thread", "log", t["id"], "--json", "--all")
    except Exception as err:  # unreadable log: report, never guess
        return t, None, str(err)[:200]
    hit = invocation(events, skill)
    if not hit:
        return t, None, None
    stamps = [e["createdAt"] for e in events if e.get("createdAt")]
    invoked = next(e["createdAt"] for e in events if e.get("id") == hit[0])
    return t, {"eventId": hit[0], "how": hit[1],
               "invokedAt": invoked, "lastEvent": max(stamps)}, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=float, default=7)
    p.add_argument("--skill", default="hivecall")
    o = p.parse_args()
    now = time.time() * 1000
    since = now - o.days * 86400000
    archived = bb("thread", "list", "--archived", "--include-hidden", "--json")
    window = [t for t in archived if (t.get("archivedAt") or 0) >= since]
    children = {}
    for t in archived:
        if t.get("parentThreadId"):
            children.setdefault(t["parentThreadId"], []).append(t["id"])
    runs, errors = [], []
    with ThreadPoolExecutor(8) as pool:
        for t, hit, err in pool.map(lambda t: scan(t, o.skill), window):
            if err:
                errors.append({"id": t["id"], "error": err})
            elif hit:
                runs.append({"id": t["id"], "title": t.get("title"),
                             "projectId": t.get("projectId"),
                             "parentThreadId": t.get("parentThreadId"),
                             "archivedAt": t.get("archivedAt"), **hit,
                             "children": children.get(t["id"], [])})
    print(json.dumps({"skill": o.skill, "days": o.days, "since": int(since),
                      "scanned": len(window), "runs": runs,
                      "unreadable": errors}, indent=2))


if __name__ == "__main__":
    main()
