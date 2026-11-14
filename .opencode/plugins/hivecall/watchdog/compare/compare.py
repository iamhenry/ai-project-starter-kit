"""Old-vs-new watchdog check. Run with python3 compare.py [--old PATH] [--new PATH] [--coverage].

Add one JSON file to fixtures/ with name, argv, optional env/files/sqlite/answers/epoch.
The isolated runner compares output, exit code, command actions, and REPO/HOME files.
"""
import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import sys

HERE = Path(__file__).resolve().parent
WATCH = HERE.parent / "watch.py"
TAG = "watchpy-baseline-2026-11-13"
SHA = "5e7a8483df43d35fa29124aec9b837f05340382d"
sys.path.insert(0, str(HERE))
from sandbox import run

def baseline():
    for ref in (TAG, SHA):
        proc = subprocess.run(["git", "show", f"{ref}:.opencode/plugins/hivecall/watchdog/watch.py"], capture_output=True, text=True)
        if proc.returncode == 0: return proc.stdout
    raise RuntimeError("Cannot read baseline tag or commit")

def executable_lines(source, filename):
    code = compile(source, filename, "exec")
    def visit(c):
        result = {line for _, _, line in c.co_lines() if line}
        for item in c.co_consts:
            if hasattr(item, "co_lines"): result |= visit(item)
        return result
    return visit(code)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old"); ap.add_argument("--new"); ap.add_argument("--coverage", action="store_true"); ap.add_argument("--report")
    args = ap.parse_args()
    old_tmp = None
    if args.old: old = Path(args.old)
    else:
        fd, name = tempfile.mkstemp(prefix="watch-baseline-", suffix=".py"); os.close(fd)
        old_tmp = Path(name); old_tmp.write_text(baseline()); old = old_tmp
    new = Path(args.new).resolve() if args.new else WATCH.resolve()
    fixtures = [json.loads(p.read_text()) for p in sorted((HERE / "fixtures").glob("*.json"))]
    differences = 0; hit = set()
    try:
        for fixture in fixtures:
            answers = fixture.get("answers", [])
            fixture["answers"] = answers if isinstance(answers, list) else []
            a = run(old.resolve(), fixture, args.coverage)
            b = run(new, fixture)
            hit |= set(a.pop("hits", []))
            changed = bool(a.get("timeout") or b.get("timeout"))
            if changed: print(f"{fixture['name']} timeout (old={bool(a.get('timeout'))} new={bool(b.get('timeout'))})")
            for field in a:
                if field in ("stdout", "stderr"):
                    # argparse includes the launch filename in help; it is not watchdog output.
                    a[field] = re.sub(r"watch-baseline-[^\s]+\.py", "watch.py", a[field])
                    b[field] = re.sub(r"watch-baseline-[^\s]+\.py", "watch.py", b[field])
                if a[field] != b[field]:
                    changed = True; print(f"{fixture['name']} {field}")
                    print("".join(difflib.unified_diff(str(a[field]).splitlines(True), str(b[field]).splitlines(True), fromfile="old", tofile="new"))[:1500])
            differences += changed
        print(f"{differences} differences ({len(fixtures)} scenarios)")
        if args.coverage:
            source = old.read_text(); lines = executable_lines(source, str(old.resolve()))
            unreachable = {}
            for path in sorted((HERE / "unreachable").glob("*.json")):
                unreachable.update(json.loads(path.read_text()))
            unreachable = {int(line): reason for line, reason in unreachable.items()}
            false_unreachable = sorted(set(unreachable) & hit)
            misses = sorted(lines-hit-set(unreachable))
            def ranges(nums):
                out=[]
                for n in nums:
                    if out and n == out[-1][-1]+1: out[-1].append(n)
                    else: out.append([n])
                return ", ".join(str(r[0]) if len(r)==1 else f"{r[0]}-{r[-1]}" for r in out)
            report = Path(args.report) if args.report else Path("_ai/task/2026-11-13/kit6/coverage.txt"); report.parent.mkdir(parents=True, exist_ok=True)
            text = (f"Covered {len(hit & lines)}/{len(lines)} executable lines ({100*len(hit & lines)/len(lines):.2f}%)\n"
                    f"Unreachable: {len(set(unreachable) & lines)}\nCovered + unreachable = total? {len((hit | set(unreachable)) & lines) == len(lines)}\n"
                    f"Missed ranges: {ranges(misses)}\n")
            text += "".join(f"watch.py:{line} — {unreachable[line]}\n" for line in sorted(set(unreachable) & lines))
            if false_unreachable: text += "FALSE UNREACHABLE (hit by a run): " + ranges(false_unreachable) + "\n"
            report.write_text(text)
            print(report)
        return int(differences > 0 or bool(args.coverage and false_unreachable))
    finally:
        if old_tmp: old_tmp.unlink(missing_ok=True)

if __name__ == "__main__": raise SystemExit(main())
