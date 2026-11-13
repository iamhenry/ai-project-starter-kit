"""Run a deployed script under frozen time and optional line tracing."""
import json
import runpy
import sys
import time
from pathlib import Path

target, epoch, hits_path, *args = sys.argv[1:]
time.time = lambda: float(epoch)
import datetime
class FrozenDateTime(datetime.datetime):
    """datetime.now() follows the frozen clock too (append_note stamps notes with it)."""
    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(float(epoch), tz)
datetime.datetime = FrozenDateTime
sys.argv = [target, *args]
mon = getattr(sys, "monitoring", None)
if hits_path != "-" and mon:
    tool = mon.DEBUGGER_ID
    mon.use_tool_id(tool, "watch-compare")
    hits = set()
    names = {target, str(Path(target).resolve())}
    def line(code, number):
        # One hit per line is enough; DISABLE keeps the traced run near normal speed.
        if code.co_filename in names:
            hits.add(number)
        return mon.DISABLE
    mon.register_callback(tool, mon.events.LINE, line)
    mon.set_events(tool, mon.events.LINE)
try:
    runpy.run_path(target, run_name="__main__")
finally:
    if hits_path != "-" and mon:
        Path(hits_path).write_text(json.dumps(sorted(hits)))
        mon.set_events(tool, 0)
        mon.free_tool_id(tool)
