#!/usr/bin/env python3
"""bb-swarm launcher. Plumbing only: set up a run directory, start peers as BB
child threads, keep the clock (warning + stop), report status, confirm the stop
actually happened, and log any human message. It never plans or splits work.
Stdlib only.
"""

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shlex
from string import Template
import subprocess
import sys

SKILL = Path(__file__).resolve().parent.parent
COORD = SKILL / "scripts" / "coord.py"
DEFAULT_NAMES = ["Ava", "Ben", "Cleo", "Dana", "Eli", "Finn", "Gia", "Hal"]


def now():
    return dt.datetime.now().astimezone()


def stamp(t=None):
    return (t or now()).isoformat(timespec="seconds")


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def bb(*args, check=True):
    r = subprocess.run(["bb", *args], capture_output=True, text=True, timeout=60)
    if check and r.returncode:
        die(f"bb {' '.join(args[:3])} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r


def bb_json(*args):
    out = bb(*args, "--json").stdout
    return json.loads(out)


def self_thread():
    try:
        d = bb_json("thread", "show", "--self")
    except SystemExit:
        return {}
    return d.get("thread", d)


def load(run):
    p = Path(run).resolve() / "run.json"
    if not p.exists():
        die(f"No run.json in {run}")
    return p, json.loads(p.read_text())


def parse_peers(specs, default_model, count):
    peers = {}
    if specs:
        for spec in specs:
            name, _, model = spec.partition("=")
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", name) or name in peers:
                die("Peer names must be unique, simple names (letters, digits, _ or -).")
            peers[name] = model or default_model
    else:
        if not default_model:
            die("Pass --model or --peer NAME=provider/model[:reasoning]")
        if not 1 <= count <= len(DEFAULT_NAMES):
            die(f"--count must be between 1 and {len(DEFAULT_NAMES)}")
        for name in DEFAULT_NAMES[:count]:
            peers[name] = default_model
    out = {}
    for name, m in peers.items():
        model, _, reasoning = m.partition(":")
        if not model:
            die(f"No model for {name}")
        out[name] = {"model": model, "reasoning": reasoning or None, "thread": None}
    return out


def cmd_preflight(a):
    """Send each model one tiny message. Listed is not the same as usable."""
    bad = 0
    for model in a.model:
        try:
            r = subprocess.run(["opencode", "run", "-m", model, "Reply with the single word OK."],
                               capture_output=True, text=True, timeout=a.timeout)
            ok = r.returncode == 0 and "ok" in r.stdout.lower()
            detail = r.stdout.strip()[-120:] or r.stderr.strip()[-200:]
        except (OSError, subprocess.TimeoutExpired) as e:
            ok, detail = False, str(e)
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {model}: {detail}")
    raise SystemExit(1 if bad else 0)


def cmd_start(a):
    root = Path(a.run).resolve()
    if root.exists() and any(root.iterdir()):
        die(f"{root} is not empty. Use a fresh directory (separate dry-run and live paths).")
    if not 0 < a.warn_before < a.minutes:
        die("--minutes must exceed --warn-before, and both must be positive")
    output = (root / a.output_dir).resolve()
    if output == root or not output.is_relative_to(root):
        die("--output-dir must name a subdirectory inside the run")
    problem = Path(a.problem).read_text().strip()
    done = Path(a.done).read_text().strip()
    boundaries = Path(a.boundaries).read_text().strip() if a.boundaries else "No extra boundaries given."
    peers = parse_peers(a.peer, a.model, a.count)

    me = {} if a.dry_run else self_thread()
    parent = a.parent or me.get("id")
    project = a.project or me.get("projectId")
    environment = a.environment or me.get("environmentId")
    if not a.dry_run and not (parent and project and environment):
        die("Could not resolve parent thread/project/environment. Pass --parent --project --environment.")
    if not a.dry_run:
        target = bb_json("thread", "show", parent)
        target = target.get("thread", target)
        if target.get("parentThreadId") is not None:
            die("The parent must be a root thread; nested BB swarms are not supported.")
        if target.get("projectId") != project or target.get("environmentId") != environment:
            die("Parent project/environment does not match the requested run location.")

    root.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    (root / "problem.md").write_text(problem + "\n")
    (root / "done.md").write_text(done + "\n")
    (root / "boundaries.md").write_text(boundaries + "\n")
    (root / "board.md").write_text("# Team board\n")

    start = now()
    deadline = start + dt.timedelta(minutes=a.minutes)
    cfg = {
        "started": stamp(start), "deadline": stamp(deadline), "minutes": a.minutes,
        "warn_before": a.warn_before, "idle_minutes": a.idle_minutes, "output_dir": a.output_dir,
        "provider": a.provider, "parent": parent, "project": project, "environment": environment,
        "peers": peers, "automations": {},
    }
    (root / "run.json").write_text(json.dumps(cfg, indent=2))

    template = Template((SKILL / "references" / "peer-brief.md").read_text())
    names = list(peers)
    (root / "briefs").mkdir(exist_ok=True)
    for name in names:
        brief = template.safe_substitute(
            name=name, peers=", ".join(n for n in names if n != name), run=str(root),
            coord=f"python3 {COORD} --run {root}", problem=problem, done=done, boundaries=boundaries,
            minutes=a.minutes, deadline=f"{deadline:%H:%M %Z}", warn_before=a.warn_before,
            output=str(output), how=str(SKILL / "references" / "how-we-work.md"))
        (root / "briefs" / f"{name}.md").write_text(brief)

    log = [f"# Launch", f"Started: {stamp(start)}", f"Deadline: {stamp(deadline)}", f"Parent: {parent}", ""]
    if a.dry_run:
        print(f"DRY RUN: wrote {root} (briefs in {root / 'briefs'}). Nothing spawned or scheduled.")
        for n, p in peers.items():
            print(f"  would start {n}: {p['model']} {p['reasoning'] or ''}")
        return

    try:
        for name, p in peers.items():
            prompt = (f"You are {name}, one of {len(peers)} equal peers on a BB swarm. "
                      f"Read your brief first: {root / 'briefs' / (name + '.md')} . Everything you need is there.")
            args = ["thread", "spawn", "--parent-thread", parent, "--project", project, "--environment", environment,
                    "--provider", a.provider, "--model", p["model"], "--title", f"swarm {root.name}: {name}",
                    "--visibility", "visible", "--prompt", prompt]
            if p["reasoning"]:
                args += ["--reasoning-level", p["reasoning"]]
            t = bb_json(*args)
            p["thread"] = t.get("thread", t)["id"]
            (root / "run.json").write_text(json.dumps(cfg, indent=2))
            log.append(f"- {name}: {p['model']} {p['reasoning'] or ''} -> {p['thread']}")
            print(f"Started {name}: {p['thread']}")

        threads = " ".join(shlex.quote(p["thread"]) for p in peers.values())
        warn_text = (f"Time check: {a.warn_before} minutes left. Finish or release what you hold, record verdicts "
                     f"with what you saw, and have one peer run close. Snapshot: python3 {COORD} --run {root} open")
        warn = f'for t in {threads}; do bb thread tell "$t" --mode auto {shlex.quote(warn_text)}; done'
        stop = f'for t in {threads}; do bb thread stop "$t"; done'
        for key, when, script in (("warn", a.minutes - a.warn_before, warn), ("stop", a.minutes, stop)):
            auto = bb_json("automation", "create", "--project", project, "--name", f"bb-swarm {root.name} {key}",
                           "--in", f"{when}m", "--interpreter", "bash", "--timeout", "120s", "--script", script)
            cfg["automations"][key] = auto.get("automation", auto)["id"]
            log.append(f"- {key} automation at +{when}m: {cfg['automations'][key]}")
            (root / "run.json").write_text(json.dumps(cfg, indent=2))
    except (SystemExit, KeyError, ValueError, OSError, subprocess.TimeoutExpired):
        (root / "launch.md").write_text("\n".join(log + ["Launch failed; stopping started peers."]) + "\n")
        for p in peers.values():
            if p["thread"]:
                bb("thread", "stop", p["thread"], check=False)
        raise
    (root / "launch.md").write_text("\n".join(log) + "\n")
    print(f"Run live. Deadline {deadline:%H:%M}. Status: python3 {Path(__file__).resolve()} status --run {root}")


def thread_status(tid):
    r = bb("thread", "show", tid, "--json", check=False)
    if r.returncode:
        return "unknown"
    t = json.loads(r.stdout)
    t = t.get("thread", t)
    return (t.get("runtime") or {}).get("displayStatus") or t.get("status") or "unknown"


def automation(cfg, key):
    aid = cfg.get("automations", {}).get(key)
    if not aid:
        return None
    r = bb("automation", "show", aid, "--project", cfg["project"], "--json", check=False)
    if r.returncode:
        return {"id": aid, "lastRunStatus": "unknown"}
    d = json.loads(r.stdout)
    return d.get("automation", d)


def cmd_status(a):
    _, cfg = load(a.run)
    left = int((dt.datetime.fromisoformat(cfg["deadline"]) - now()).total_seconds() // 60)
    print(f"{now():%H:%M}  " + (f"{left} min to deadline" if left >= 0 else "past deadline"))
    for name, p in cfg["peers"].items():
        print(f"  {name}: {thread_status(p['thread']) if p['thread'] else 'not started'}")
    sys.stdout.flush()
    subprocess.run([sys.executable, str(COORD), "--run", str(Path(a.run).resolve()), "open"])


def cmd_confirm_stop(a):
    """A scheduled stop is not proof. Check the automation ran and nobody is still active."""
    _, cfg = load(a.run)
    stop = automation(cfg, "stop")
    ran = stop and stop.get("lastRunStatus") == "succeeded"
    print(f"stop automation: {stop.get('id') if stop else 'none'} -> {stop.get('lastRunStatus') if stop else 'n/a'}")
    unfinished = []
    for name, p in cfg["peers"].items():
        s = thread_status(p["thread"]) if p["thread"] else "not started"
        print(f"  {name}: {s}")
        if s not in ("idle", "stopped", "completed"):
            unfinished.append(name)
    if ran and not unfinished:
        print("CONFIRMED: stop ran and no peer is active.")
    else:
        print("NOT CONFIRMED: " + ("stop has not succeeded. " if not ran else "") +
              (f"not confirmed stopped: {', '.join(unfinished)}" if unfinished else ""))
        raise SystemExit(1)


def cmd_tell(a):
    """Human/observer message to a peer. Always logged, because it changes the run."""
    p, cfg = load(a.run)
    peer = cfg["peers"].get(a.to)
    if not peer or not peer.get("thread"):
        die(f"Unknown or unstarted peer {a.to}")
    text = " ".join(a.text)
    with (p.parent / "interventions.md").open("a") as f:
        f.write(f"- {stamp()} to {a.to}: {text}\n")
    bb("thread", "tell", peer["thread"], "--mode", "auto", text)
    print(f"Sent and logged in {p.parent / 'interventions.md'}.")


def main():
    ap = argparse.ArgumentParser(description="bb-swarm launcher: setup, clock, status, confirm stop.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("preflight", help="send each model one tiny message (opencode)")
    s.add_argument("--model", action="append", required=True); s.add_argument("--timeout", type=int, default=120)
    s = sub.add_parser("start", help="set up the run dir, start peers, schedule warn + stop")
    s.add_argument("--run", required=True, help="fresh run directory")
    s.add_argument("--problem", required=True, help="file with the user's problem, word for word")
    s.add_argument("--done", required=True, help="file with the user's definition of done, word for word")
    s.add_argument("--boundaries", help="file with limits and permissions")
    s.add_argument("--model", help="provider/model[:reasoning] for every peer")
    s.add_argument("--peer", action="append", help="NAME=provider/model[:reasoning]; repeat per peer")
    s.add_argument("--count", type=int, default=5)
    s.add_argument("--minutes", type=int, default=90)
    s.add_argument("--warn-before", type=int, default=5)
    s.add_argument("--idle-minutes", type=int, default=10)
    s.add_argument("--output-dir", default="output")
    s.add_argument("--provider", default="opencode")
    s.add_argument("--parent"); s.add_argument("--project"); s.add_argument("--environment")
    s.add_argument("--dry-run", action="store_true")
    for name in ("status", "confirm-stop"):
        s = sub.add_parser(name); s.add_argument("--run", required=True)
    s = sub.add_parser("tell", help="send a logged human message to one peer")
    s.add_argument("--run", required=True); s.add_argument("--to", required=True); s.add_argument("text", nargs="+")
    a = ap.parse_args()
    {"preflight": cmd_preflight, "start": cmd_start, "status": cmd_status,
     "confirm-stop": cmd_confirm_stop, "tell": cmd_tell}[a.cmd](a)


if __name__ == "__main__":
    main()
