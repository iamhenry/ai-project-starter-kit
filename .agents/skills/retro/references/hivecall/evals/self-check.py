#!/usr/bin/env python3
"""Offline regressions for structured ledger moments, redaction and append-only updates."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import redact

spec = importlib.util.spec_from_file_location("builder", SCRIPTS / "build-dataset.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def event(event_id, text, item_type="agentMessage", at=1000):
    if item_type == "client":
        return {"id": event_id, "type": "client/turn/requested", "createdAt": at,
                "data": {"input": [{"text": text}]}}
    return {"id": event_id, "type": "item/completed", "createdAt": at,
            "data": {"item": {"type": item_type, "text": text}}}


def completed(event_id, item_type, at=1000, **fields):
    return {"id": event_id, "type": "item/completed", "createdAt": at,
            "data": {"item": {"type": item_type, "status": "completed", **fields}}}


# Prose mentions and read-only commands are not structured ledger edits.
proposal = event("proposal", "ISC-342: Then a tick for each once a tester proves it.")
assert builder.item_decisions([proposal], 0) == []
mention = event("mention", "ISC-17: PASS - I will add this later.")
assert builder.item_decisions([mention], 0) == []
read_only = completed("read", "commandExecution", command="grep 'ISC-23: PASS' .hivecall/ISA.html")
assert builder.item_decisions([read_only], 0) == []

# A tool edit that newly checks one identified ledger item is a real B1/B2 moment.
edit = completed("edit", "toolCall", tool="edit", arguments={
    "filePath": ".hivecall/checklist.html",
    "oldString": '<li id="ISC-17"><input type="checkbox"></li>',
    "newString": '<li id="ISC-17"><input type="checkbox" checked></li>',
})
assert [(item, state, done) for item, state, _, done in builder.item_decisions([edit], 0)] == [
    ("ISC-17", "tick", True)]

# The first full write establishes prior state; only a newly checked row counts later.
write_files = {}
baseline = completed("write0", "toolCall", tool="write", arguments={
    "filePath": ".hivecall/ISA.html",
    "content": '<ul><li id="ISC-18"><input type="checkbox"></li></ul>',
})
assert builder.item_decisions([baseline], 0, write_files) == []
write = completed("write1", "toolCall", tool="write", arguments={
    "filePath": ".hivecall/ISA.html",
    "content": '<ul><li id="ISC-18"><input type="checkbox"></li>'
               '<li id="ISC-19"><input type="checkbox" checked></li></ul>',
})
assert [(item, state, done) for item, state, _, done in builder.item_decisions([write], 0, write_files)] == [
    ("ISC-19", "tick", True)]

patch = completed("patch", "toolCall", tool="apply_patch", arguments={"patch": (
    "*** Begin Patch\n*** Update File: .hivecall/ISA.html\n"
    "@@\n+ISC-20: PASS - screenshot evidence\n*** End Patch")})
assert [(item, state, done) for item, state, _, done in builder.item_decisions([patch], 0)] == [
    ("ISC-20", "pass", True)]

# The ledger helper reads the command's staged content, not an ISC id in narration.
helper = completed("helper", "commandExecution", command=(
    "cat > .hivecall/tick.txt <<'EOF'\nISC-21: PASS - screenshot evidence\nEOF\n"
    "python3 _ai/tools/ledger.py .hivecall/tick.txt"))
assert [(item, state, done) for item, state, _, done in builder.item_decisions([helper], 0)] == [
    ("ISC-21", "pass", True)]
append = completed("append", "commandExecution", command=(
    "cat >> .hivecall/ISA.html <<'EOF'\nISC-22: BLOCKED - owner unavailable\nEOF"))
assert [(item, state, done) for item, state, _, done in builder.item_decisions([append], 0)] == [
    ("ISC-22", "blocked", False)]

refused = completed("refused", "commandExecution", approvalStatus="denied", command=(
    "cat >> .hivecall/ISA.html <<'EOF'\nISC-24: FAIL - refused\nEOF"))
failed = completed("failed", "commandExecution", command=(
    "cat >> .hivecall/ISA.html <<'EOF'\nISC-25: FAIL - command failed\nEOF"))
failed["data"]["item"]["status"] = "failed"
assert builder.item_decisions([refused], 0) == []
assert builder.item_decisions([failed], 0) == []

moments = builder.extract_moments("thr_fixture123", "2026-W42", [helper, append], 0)
assert [(m["behavior"], m["itemId"]) for m in moments] == [
    (1, "ISC-21"), (2, "ISC-21"), (1, "ISC-22")]
assert builder.status_rows("| Done | In progress | Not started |\n|---|---|---|") == []

alert = event("alert", "HOST load: high", "client", 1)
envelope = event("envelope", "[bb system] @thread:fake completed: FAIL", "client", 2)
assert builder.watchdog_alerts(alert) == ["HOST load: high"]
assert builder.watchdog_alerts(envelope) == []
assert not builder.is_delegation_action(event("help", "bb thread spawn --help", "commandExecution"))
start = {"id": "start", "type": "item/started", "createdAt": 5,
         "data": {"item": {"type": "delegation", "id": "d1", "label": "Mia (qa)", "status": "pending"}}}
finish = {"id": "finish", "type": "item/delegation/completed", "createdAt": 9,
          "data": {"item": {"type": "delegation", "id": "d1", "label": "Mia (qa)", "status": "completed"}}}
report = event("report", "Sent 3 workers in parallel; lanes are running", at=10)
stop = event("stop", "Please stop the worker now", "client", 7)
deleg = builder.extract_moments("thr_fixture123", "2026-W42",
                                [event("before", "Plan the lane", at=1), start, stop, finish, report], 0)
assert sorted((m["behavior"], m["eventId"]) for m in deleg if m["behavior"] in (4, 6)) == [
    (4, "start"), (6, "start")]
assert all(m["actualNextAction"]["eventType"] == "item/started"
           and m["actualNextAction"]["status"] == "pending" for m in deleg if m["behavior"] in (4, 6))
assert all("stop" not in m["context"] and "Plan the lane" in m["context"]
           for m in deleg if m["behavior"] in (4, 6))
events = [event("prior", "Before", at=0), alert, event("action", "Respond", at=3),
          event("future", "must not leak", at=4)]
ctx = builder.context(events, 2, trigger=1, trigger_text="HOST load: high")
assert "HOST load: high" in ctx and "must not leak" not in ctx

private_ids = ("proj_abcd123456 ses_abcdefghijk auto_abcdefghij msg_abcdefghij "
               "env_abcdefghij host_abcdefghij prt_abcdefghij call_abcdefghij "
               "auto_7pyi__rzd54 arun_ct_qp73jk-y proj_ab_cd-1234 ses_alpha_beta auto_abcdefgh_ijkl")
redacted = redact.redact(private_ids + " THR_abcdefghij thr_fixture123 evt_fixture123")
assert all(value not in redacted for value in private_ids.split())
assert "THR_abcdefghij" not in redacted
assert "thr_fixture123" in redacted and "evt_fixture123" in redacted
assert redact.redact("task_bounds_not_detected follow_up_present") == "task_bounds_not_detected follow_up_present"
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=SCRIPTS.parents[5] / ".lanes",
                                 prefix="id-scan-self-check-", suffix=".json", delete=False) as f:
    id_path = Path(f.name)
    f.write(json.dumps({"ids": private_ids + " thr_fixture123 evt_fixture123"}))
scan_output = io.StringIO()
with contextlib.redirect_stdout(scan_output):
    assert redact.scan(id_path)
id_path.unlink()
assert json.loads(scan_output.getvalue())["private_identifiers"] == len(private_ids.split())

old = {"runId": "run", "lastEvent": 10,
       "workers": [{"id": "thr_worker12345", "report": "old", "readable": True}],
       "moments": [{"runId": "run", "behavior": 1, "eventId": "old", "momentId": "old"}]}


def built(run):
    return {"runId": "run", "lastEvent": run["lastEvent"], "workers": [
        {"id": "thr_worker12345", "report": "revised", "readable": True},
        {"id": "thr_worker67890", "report": "new", "readable": True}], "moments": [
            old["moments"][0]] + ([{"runId": "run", "behavior": 1,
                                     "eventId": "new", "momentId": "new"}]
                                   if run["lastEvent"] > 10 else [])}


assert builder.plan_appends([{"id": "run", "lastEvent": 10}], [old], lambda run: old) == []
worker_only = builder.plan_appends([{"id": "run", "lastEvent": 10}], [old], built)
assert len(worker_only) == 1 and worker_only[0]["moments"] == []
assert worker_only[0]["workers"] == [
    {"id": "thr_worker12345", "report": "revised", "readable": True},
    {"id": "thr_worker67890", "report": "new", "readable": True}]
updates = builder.plan_appends([{"id": "run", "lastEvent": 11}], [old], built)
assert len(updates) == 1 and [m["momentId"] for m in updates[0]["moments"]] == ["new"]
assert updates[0]["workers"] == [
    {"id": "thr_worker12345", "report": "revised", "readable": True},
    {"id": "thr_worker67890", "report": "new", "readable": True}]
assert builder.plan_appends([{"id": "run", "lastEvent": 11}], [old, *worker_only, *updates], built) == []
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=SCRIPTS.parents[5] / ".lanes",
                                 prefix="append-self-check-", suffix=".jsonl", delete=False) as f:
    sample_path = Path(f.name)
    f.write(json.dumps(old) + "\n")
original_line = sample_path.read_bytes().splitlines(keepends=True)[0]
with sample_path.open("a", encoding="utf-8") as f:
    for row in [*worker_only, *updates]:
        f.write(json.dumps(row) + "\n")
written = sample_path.read_bytes().splitlines(keepends=True)
sample_path.unlink()
assert written[0] == original_line
saved_worker_update, saved_run_update = map(json.loads, written[1:])
assert saved_worker_update["moments"] == [] and saved_worker_update["workers"] == worker_only[0]["workers"]
assert saved_run_update["moments"][0]["momentId"] == "new"
assert saved_run_update["workers"] == updates[0]["workers"]
print("PASS: structured ledger edits, decision filters, B1/B2, redaction families, alert context, resumed append-only workers")
