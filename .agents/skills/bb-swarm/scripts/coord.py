#!/usr/bin/env python3
"""bb-swarm team tool. Plumbing only: board, notices, claims, handoffs, verdicts,
locks, shared notes, close. It records and shows; peers decide. Stdlib only.

Every command ends with a "team now" snapshot so the whole picture is in view
at the moment each peer decides what to do next.
"""

import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

VERDICTS = ("PASS", "FAIL", "BLOCKED")


def now():
    return dt.datetime.now().astimezone()


def stamp(t=None):
    return (t or now()).isoformat(timespec="seconds")


def parse(s):
    return dt.datetime.fromisoformat(s)


def minutes_since(s):
    return int((now() - parse(s)).total_seconds() // 60)


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


class Run:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not (self.root / "run.json").exists():
            die(f"No run.json in {self.root}. Pass --run <run dir> or set BB_SWARM_RUN.")
        self.cfg = json.loads((self.root / "run.json").read_text())
        self.board = self.root / "board.md"
        self.state_path = self.root / "state.json"
        self.lock_path = self.root / ".state.lock"
        self.readers = self.root / "readers"
        self.peers = list(self.cfg["peers"])

    @contextmanager
    def state(self, write=True):
        with self.lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                data = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
                for key, empty in (("items", {}), ("locks", {}), ("notes", []), ("seen", {}), ("away", {}), ("next_id", 1)):
                    data.setdefault(key, empty)
                yield data
                if write:
                    fd, tmp = tempfile.mkstemp(prefix=".state.", dir=self.root)
                    with os.fdopen(fd, "w") as f:
                        json.dump(data, f, indent=2)
                    os.replace(tmp, self.state_path)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def check_name(self, name):
        if name not in self.peers:
            die(f"Unknown peer {name}. Peers: {', '.join(self.peers)}")

    def touch(self, data, name):
        data["seen"][name] = stamp()
        data["away"].pop(name, None)

    def append(self, name, text):
        text = " ".join(text.split())
        if not text:
            die("Empty message")
        with self.board.open("a+b") as b:
            fcntl.flock(b, fcntl.LOCK_EX)
            try:
                b.seek(0, os.SEEK_END)
                pos = b.tell()
                b.write(f"[{pos}] [{name}] [{stamp()}] {text}\n".encode())
            finally:
                fcntl.flock(b, fcntl.LOCK_UN)
        return pos

    def notify(self, recipient, sender, pos, item=None):
        thread = self.cfg["peers"].get(recipient, {}).get("thread")
        if not thread:
            print(f"(No thread registered for {recipient}; board post #{pos} stands.)")
            return
        prefix = ""
        if item and item.get("status") == "done":
            prefix = f"Already closed (#{item['id']} is done); nothing to do unless you disagree. "
        me = Path(__file__).resolve()
        text = (f"{prefix}Board post #{pos} from {sender} is for you. "
                f"Read: python3 {me} --run {self.root} read {recipient}")
        try:
            r = subprocess.run(["bb", "thread", "tell", thread, "--mode", "auto", text],
                               capture_output=True, text=True, timeout=20)
            print(f"Notified {recipient}." if r.returncode == 0 else
                  f"Notice to {recipient} failed; board post #{pos} stands.")
        except (OSError, subprocess.TimeoutExpired):
            print(f"Notice to {recipient} unknown (timeout/no bb); board post #{pos} stands. Check before resending.")

    def done_text(self):
        p = self.root / "done.md"
        return p.read_text().strip() if p.exists() else "(no done.md)"


def item_line(i):
    who = i.get("owner") or "nobody"
    return f"#{i['id']} {i['title']} [{i['status']}, {who}]"


def snapshot(run, data):
    deadline = run.cfg.get("deadline")
    left = ""
    if deadline:
        mins = int((parse(deadline) - now()).total_seconds() // 60)
        left = f", {mins} min left" if mins >= 0 else ", past deadline"
    idle_after = run.cfg.get("idle_minutes", 10)
    items = list(data["items"].values())
    groups = {
        "open, no owner": [i for i in items if i["status"] == "open"],
        "waiting for review": [i for i in items if i["status"] == "review"],
        "self-checked only (needs a peer)": [i for i in items if i["status"] == "self-checked"],
        "in progress": [i for i in items if i["status"] == "active"],
        "blocked": [i for i in items if i["status"] == "blocked"],
    }
    out = [f"--- team now ({now():%H:%M}{left}) ---"]
    for label, group in groups.items():
        if not group:
            continue
        out.append(f"{label}:")
        for i in group:
            extra = ""
            if i["status"] == "review" and i.get("reviewer"):
                extra = f" -> reviewer {i['reviewer']}, waiting {minutes_since(i['touched'])}m"
            elif i["status"] == "active":
                age = minutes_since(i["touched"])
                extra = f" untouched {age}m" + (" (stale?)" if age >= idle_after else "")
            out.append(f"  {item_line(i)}{extra}")
    done = [i for i in items if i["status"] == "done"]
    out.append(f"done (peer PASS): {len(done)}")
    idle = []
    for p in run.peers:
        if p in data["away"]:
            idle.append(f"{p} (stepped away)")
        elif p in data["seen"] and minutes_since(data["seen"][p]) >= idle_after:
            idle.append(f"{p} (quiet {minutes_since(data['seen'][p])}m)")
    if idle:
        out.append("idle peers (reachable with post --notify): " + ", ".join(idle))
    for path, h in data["locks"].items():
        out.append(f"lock {path}: {h['owner']} for {minutes_since(h['since'])}m")
    for n in data["notes"]:
        out.append(f"known limit ({n['by']}): {n['text']}")
    if data.get("closed"):
        out.append(f"CLOSED by {data['closed']['by']} at {data['closed']['at']}; see RESULTS.md")
    elif not any(groups.values()):
        out.append("Nothing open. If the done text is fully shown working, someone can run close.")
    print("\n".join(out))


def get_item(data, item_id):
    item = data["items"].get(str(item_id))
    if not item:
        die(f"No item #{item_id}")
    return item


def cmd_post(run, a):
    run.check_name(a.name)
    item = None
    with run.state() as data:
        run.touch(data, a.name)
        if a.item:
            item = get_item(data, a.item)
        pos = run.append(a.name, " ".join(a.message))
    print(f"Posted #{pos}.")
    if a.notify:
        run.check_name(a.notify)
        run.notify(a.notify, a.name, pos, item)


def cmd_read(run, a):
    run.check_name(a.name)
    run.readers.mkdir(exist_ok=True)
    cur = run.readers / f"{a.name}.json"
    off = json.loads(cur.read_text())["offset"] if cur.exists() else 0
    with run.board.open("rb") as b:
        fcntl.flock(b, fcntl.LOCK_SH)
        b.seek(off)
        chunk = b.read()
        fcntl.flock(b, fcntl.LOCK_UN)
    chunk = chunk[: chunk.rfind(b"\n") + 1]
    lines = [l for l in chunk.decode().splitlines() if l.startswith("[")]
    print("\n".join(lines) if lines else "No new posts.")
    cur.write_text(json.dumps({"offset": off + len(chunk)}))
    with run.state() as data:
        run.touch(data, a.name)


def cmd_claim(run, a):
    run.check_name(a.name)
    title = " ".join(" ".join(a.title).split())
    if not title:
        die("Say what you are taking on.")
    with run.state() as data:
        run.touch(data, a.name)
        iid = str(data["next_id"])
        data["next_id"] += 1
        data["items"][iid] = {"id": iid, "title": title, "owner": a.name, "status": "active",
                              "created": stamp(), "touched": stamp(), "verdicts": []}
    run.append(a.name, f"CLAIM #{iid}: {title}")
    print(f"You own #{iid}.")


def cmd_take(run, a):
    run.check_name(a.name)
    with run.state() as data:
        run.touch(data, a.name)
        i = get_item(data, a.id)
        prev = i.get("owner")
        i.update(owner=a.name, status="active", touched=stamp())
    note = f"TAKE #{a.id} {i['title']}" + (f" from {prev}" if prev and prev != a.name else "")
    if a.note:
        note += f": {' '.join(a.note)}"
    pos = run.append(a.name, note)
    if prev and prev != a.name and prev in run.peers:
        run.notify(prev, a.name, pos)
    print(f"You own #{a.id}.")


def cmd_release(run, a):
    run.check_name(a.name)
    with run.state() as data:
        run.touch(data, a.name)
        i = get_item(data, a.id)
        i.update(owner=None, status="open", touched=stamp())
    run.append(a.name, f"RELEASE #{a.id} {i['title']}" + (f": {' '.join(a.note)}" if a.note else ""))
    print(f"#{a.id} is open for anyone.")


def cmd_handoff(run, a):
    run.check_name(a.name)
    run.check_name(a.reviewer)
    with run.state() as data:
        run.touch(data, a.name)
        i = get_item(data, a.id)
        i.update(status="review", reviewer=a.reviewer, touched=stamp())
    pos = run.append(a.name, f"HANDOFF #{a.id} {i['title']} -> {a.reviewer}" + (f": {' '.join(a.note)}" if a.note else ""))
    run.notify(a.reviewer, a.name, pos, i)


def cmd_verdict(run, a):
    run.check_name(a.name)
    saw = " ".join(" ".join(a.saw).split()) if a.saw else ""
    with run.state() as data:
        run.touch(data, a.name)
        i = get_item(data, a.id)
        self_check = a.name == i.get("owner")
        kind = "self-check" if self_check else "peer"
        support = "supported" if saw else "unsupported (nothing seen recorded)"
        i["verdicts"].append({"by": a.name, "verdict": a.verdict, "kind": kind, "saw": saw, "at": stamp()})
        if a.verdict == "PASS":
            i["status"] = "done" if (not self_check and saw) else ("self-checked" if self_check else "review")
        elif a.verdict == "FAIL":
            i["status"] = "active"
        else:
            i["status"] = "blocked"
        i["touched"] = stamp()
        owner = i.get("owner")
    pos = run.append(a.name, f"VERDICT #{a.id} {a.verdict} ({kind}, {support}): {saw or '-'}")
    print("Done text this is judged against:\n" + run.done_text() + "\n")
    print(f"Recorded {a.verdict} as {kind}, {support}. #{a.id} is now {i['status']}.")
    if a.verdict == "FAIL" and owner and owner != a.name:
        run.notify(owner, a.name, pos)


def cmd_lock(run, a):
    run.check_name(a.name)
    with run.state() as data:
        run.touch(data, a.name)
        h = data["locks"].get(a.path)
        if h and h["owner"] != a.name:
            print(f"{a.path} is held by {h['owner']} for {minutes_since(h['since'])}m. "
                  "Do other work, or ask them on the board.")
            return 1
        data["locks"][a.path] = {"owner": a.name, "since": stamp()}
    print(f"Locked {a.path}. Edit, then unlock right away.")


def cmd_unlock(run, a):
    run.check_name(a.name)
    with run.state() as data:
        run.touch(data, a.name)
        h = data["locks"].get(a.path)
        if not h:
            print(f"{a.path} was not locked.")
            return
        if h["owner"] != a.name:
            run.append(a.name, f"UNLOCK {a.path} (held by {h['owner']} for {minutes_since(h['since'])}m)")
        del data["locks"][a.path]
    print(f"Unlocked {a.path}.")


def cmd_limit(run, a):
    run.check_name(a.name)
    text = " ".join(a.text)
    with run.state() as data:
        run.touch(data, a.name)
        data["notes"].append({"by": a.name, "text": text, "at": stamp()})
    run.append(a.name, f"TOOL LIMIT: {text}")
    print("Shared with the team.")


def cmd_away(run, a):
    run.check_name(a.name)
    with run.state() as data:
        data["seen"][a.name] = stamp()
        data["away"][a.name] = {"at": stamp(), "reason": " ".join(a.reason)}
        pending = [i for i in data["items"].values() if i["status"] != "done"]
    msg = f"AWAY: {a.name} stepped away; {len(pending)} item(s) not done"
    if pending:
        msg += ": " + "; ".join(item_line(i) for i in pending[:8])
    if a.reason:
        msg += f". Reason: {' '.join(a.reason)}"
    run.append(a.name, msg)
    print("Recorded. Any peer can wake you with post --notify.")


def cmd_open(run, a):
    pass  # the snapshot is the whole answer


def cmd_close(run, a):
    run.check_name(a.name)
    out_dir = (run.root / run.cfg.get("output_dir", "output")).resolve()
    with run.state() as data:
        run.touch(data, a.name)
        if data.get("closed"):
            print(f"Already closed by {data['closed']['by']} at {data['closed']['at']}. Reuse RESULTS.md.")
            return
        manifest = []
        if out_dir.exists():
            for p in sorted(out_dir.rglob("*")):
                if p.is_file():
                    manifest.append((hashlib.sha256(p.read_bytes()).hexdigest(), str(p.relative_to(out_dir))))
        items = list(data["items"].values())
        not_done = [i for i in items if i["status"] != "done"]
        outcome = a.outcome
        reason = " ".join(a.reason).strip()
        data["closed"] = {"by": a.name, "at": stamp(), "outcome": outcome, "reason": reason}
        notes = list(data["notes"])
    lines = [f"# Results", "", f"Outcome: **{outcome}** (team decision; closed by {a.name} at {stamp()})",
             f"Reason: {reason or 'Not recorded'}",
             f"Output: `{out_dir}`", "", "## Done text", "", run.done_text(), "", "## Work items", "",
             "| # | Item | Status | Owner | Verdicts (who, kind, what they saw) |", "|---|---|---|---|---|"]
    for i in items:
        v = "<br>".join(f"{x['verdict']} by {x['by']} ({x['kind']}): {x['saw'] or 'nothing recorded'}" for x in i["verdicts"]) or "-"
        lines.append(f"| {i['id']} | {i['title']} | {i['status']} | {i.get('owner') or '-'} | {v} |")
    if not_done:
        lines += ["", "## Not done", ""] + [f"- {item_line(i)}" for i in not_done]
    if notes:
        lines += ["", "## Known tool limits", ""] + [f"- {n['text']} ({n['by']})" for n in notes]
    lines += ["", "## Output fingerprints (SHA-256)", "", "```"] + [f"{h}  {p}" for h, p in manifest] + ["```", ""]
    (run.root / "RESULTS.md").write_text("\n".join(lines))
    run.append(a.name, f"CLOSE: outcome {outcome}; {len(manifest)} output file(s) fingerprinted once; RESULTS.md written. Reuse it, do not re-hash.")
    print(f"Closed: {outcome}. Wrote {run.root / 'RESULTS.md'}.")


def main():
    ap = argparse.ArgumentParser(description="bb-swarm team tool (board, claims, handoffs, verdicts, locks, close).")
    ap.add_argument("--run", default=os.environ.get("BB_SWARM_RUN"), help="run directory (or env BB_SWARM_RUN)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("post", help="add one board message; --notify wakes one peer"); s.add_argument("name"); s.add_argument("message", nargs="+"); s.add_argument("--notify"); s.add_argument("--item")
    s = sub.add_parser("read", help="show board posts you have not read"); s.add_argument("name")
    s = sub.add_parser("claim", help="take on a piece of work you describe"); s.add_argument("name"); s.add_argument("title", nargs="+")
    s = sub.add_parser("take", help="take over an existing item (posts a note, tells prior owner)"); s.add_argument("name"); s.add_argument("id"); s.add_argument("note", nargs="*")
    s = sub.add_parser("release", help="give an item back to the team"); s.add_argument("name"); s.add_argument("id"); s.add_argument("note", nargs="*")
    s = sub.add_parser("handoff", help="ask ONE peer to review an item"); s.add_argument("name"); s.add_argument("id"); s.add_argument("reviewer"); s.add_argument("note", nargs="*")
    s = sub.add_parser("verdict", help="record PASS/FAIL/BLOCKED and what you saw"); s.add_argument("name"); s.add_argument("id"); s.add_argument("verdict", choices=VERDICTS); s.add_argument("--saw", nargs="*")
    s = sub.add_parser("lock", help="short lock on a shared file before editing"); s.add_argument("name"); s.add_argument("path")
    s = sub.add_parser("unlock", help="release a lock"); s.add_argument("name"); s.add_argument("path")
    s = sub.add_parser("limit", help="share a tool limit you hit, once"); s.add_argument("name"); s.add_argument("text", nargs="+")
    s = sub.add_parser("away", help="record that you are stepping away"); s.add_argument("name"); s.add_argument("reason", nargs="*")
    sub.add_parser("open", help="show the team snapshot only")
    s = sub.add_parser("close", help="freeze once: record team outcome, fingerprint output, write RESULTS.md"); s.add_argument("name"); s.add_argument("outcome", choices=("DONE", "PARTIAL", "BLOCKED")); s.add_argument("reason", nargs="*")
    a = ap.parse_args()
    if not a.run:
        die("Pass --run <run dir> or set BB_SWARM_RUN.")
    run = Run(a.run)
    rc = globals()[f"cmd_{a.cmd}"](run, a)
    with run.state(write=False) as data:
        print()
        snapshot(run, data)
    raise SystemExit(rc or 0)


if __name__ == "__main__":
    main()
