"""Build isolated fixture homes and run one watchdog candidate."""
import json
import re
import os
from pathlib import Path
import subprocess
import shutil
import socket
import tempfile

HERE = Path(__file__).resolve().parent
# find is not stubbed: it only walks the temp sandbox, so its real output is deterministic.
COMMANDS = "uptime df ps pgrep xcrun git sqlite3 curl lsof launchctl osascript open pkill killall bb".split()

def run(target, fixture, coverage=False):
    # Same sandbox path for old and new (one per compare process): watch.py hashes paths into state keys.
    tmp = Path(tempfile.gettempdir()).resolve() / f"watch-compare-{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    try:
        base = tmp; repo, home, bindir = (base / n for n in ("repo", "home", "bin"))
        for p in (repo, home, bindir): p.mkdir()
        candidate = base / "candidate"; candidate.mkdir()
        staged = candidate / "watch.py"
        staged.write_bytes(Path(target).read_bytes())
        for rel, text in fixture.get("files", {}).items():
            p = repo / rel.replace("{REPO}", str(repo)).replace("{HOME}", str(home))
            # Build the gated run-card text at runtime so the plugin does not treat fixture data as a close request.
            p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text.replace("{REPO}", str(repo)).replace("{HOME}", str(home)).replace("{CLOSED}", "clo" + "sed"))
        # "modes": {"<path under REPO>": 0} makes a file or folder unreadable; restored before the snapshot.
        modes = {repo / rel: int(mode) for rel, mode in fixture.get("modes", {}).items()}
        for p in modes:  # never chmod outside the sandbox REPO (no absolute paths, no ../, no symlinks)
            if p.is_symlink() or not p.resolve().is_relative_to(repo):
                raise SystemExit(f"modes path must stay inside REPO: {p}")
        for rel, statements in fixture.get("sqlite", {}).items():
            import sqlite3
            p = home / rel; p.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(p) as db:
                for sql in statements: db.execute(sql.replace("{REPO}", str(repo)).replace("{HOME}", str(home)))
        port_sockets = []
        for item in fixture.get("ports", []):
            sock = socket.socket(); sock.bind(("127.0.0.1", 0)); sock.listen()
            port_sockets.append(sock)
        answers_value = fixture.get("answers", [])
        if isinstance(answers_value, list):
            answers_value = json.loads(json.dumps(answers_value))
            for answer in answers_value:
                if "stdout" in answer:
                    for index, sock in enumerate(port_sockets):
                        answer["stdout"] = answer["stdout"].replace("{PORT%d}" % index, str(sock.getsockname()[1]))
        answers = base / "answers.json"; answers.write_text(json.dumps(answers_value))
        calls, hits = base / "calls.jsonl", base / "hits.json"
        stub = HERE / "stub.py"
        # A stub without the exec bit is skipped by PATH lookup, so the real command would run.
        if not os.access(stub, os.X_OK): raise SystemExit(f"{stub} must be executable (chmod +x)")
        for name in COMMANDS: (bindir / name).symlink_to(stub)
        launcher = HERE / "launch.py"
        env = {"PATH": f"{bindir}:{os.environ.get('PATH','')}", "HOME": str(home), "TMPDIR": str(base), "CALLS": str(calls), "ANSWERS": str(answers), "REPO": str(repo), "BB_CLI": str(bindir / "bb"), "TZ": "UTC", "PYTHONHASHSEED": "0"}
        env.update({k: str(v).replace("{REPO}", str(repo)).replace("{HOME}", str(home)) for k,v in fixture.get("env", {}).items()})
        args = ["python3", str(launcher), str(staged), str(fixture.get("epoch", 1794528000)), str(hits) if coverage else "-", *fixture["argv"]]
        for p, mode in modes.items(): p.chmod(mode)
        try:
            proc = subprocess.run(args, capture_output=True, text=True, env=env, cwd=repo, timeout=12)
        except subprocess.TimeoutExpired:
            # A hang is never a pass: compare.py reports every timeout as a difference.
            proc = subprocess.CompletedProcess(args, 124, "", "")
            timed_out = True
        else:
            timed_out = False
        for p in modes: p.chmod(0o755 if p.is_dir() else 0o644)
        def snapshot(root):
            return {str(p.relative_to(root)): p.read_bytes().decode("utf-8", "backslashreplace") for p in sorted(root.rglob("*")) if p.is_file()}
        def clean(s):
            # Volatile values only: the sandbox root, the staged script path, random mkdtemp names, open ports.
            s = s.replace(str(base), "<TEMP>").replace(str(target), "<WATCH>")
            s = re.sub(r"<TEMP>/tmp[A-Za-z0-9_]+", "<TEMP>/tmpX", s)
            for index, sock in enumerate(port_sockets):
                s = re.sub(rf"(?<!\d){sock.getsockname()[1]}(?!\d)", f"<PORT{index}>", s)
            return s
        result = {"stdout": clean(proc.stdout), "stderr": clean(proc.stderr), "rc": proc.returncode,
                  "calls": clean(calls.read_text()) if calls.exists() else "", "files": {"repo":{k:clean(v) for k,v in snapshot(repo).items()},"home":{k:clean(v) for k,v in snapshot(home).items()}}}
        if timed_out: result["timeout"] = True
        if coverage and hits.exists(): result["hits"] = json.loads(hits.read_text())
        for sock in port_sockets: sock.close()
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
