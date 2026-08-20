#!/bin/sh
# Re-apply: scan .agents/agents only (pi-open-agents wipes this on update).
set -e
f="$HOME/.pi/agent/npm/node_modules/pi-open-agents/src/config/paths.ts"
[ -f "$f" ] || { echo "pi-open-agents not installed: $f" >&2; exit 1; }
python3 - "$f" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
t = p.read_text()
old = """    dir: path.join(cwd, \".agents\"),
    source: \"project\",
    family: \"shared\",
    subdirs: [\"\"],"""
new = old.replace('subdirs: [""]', 'subdirs: ["agents"]')
if 'family: "shared",\n    subdirs: ["agents"]' in t:
    print("already patched")
elif old in t:
    p.write_text(t.replace(old, new, 1))
    print("patched")
else:
    print("pattern not found — plugin source changed", file=sys.stderr)
    sys.exit(1)
PY
