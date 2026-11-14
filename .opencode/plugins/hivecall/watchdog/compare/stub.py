#!/usr/bin/env python3
"""One argv-recording executable, linked under each external command name."""
import json
import os
import sys
import time
from pathlib import Path

argv = [Path(sys.argv[0]).name, *sys.argv[1:]]
with open(os.environ["CALLS"], "a") as log:
    log.write(json.dumps({"argv": argv}) + "\n")
answers = json.loads(Path(os.environ["ANSWERS"]).read_text())
answer = next((a for a in answers if argv[:len(a.get("match", []))] == a.get("match", [])), {})
if answer.get("sleep"):
    time.sleep(float(answer["sleep"]))
sys.stdout.write(answer.get("stdout", ""))
sys.stderr.write(answer.get("stderr", ""))
raise SystemExit(answer.get("rc", 0))
