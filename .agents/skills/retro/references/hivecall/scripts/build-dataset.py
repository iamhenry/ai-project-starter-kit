#!/usr/bin/env python3
"""Fetch explicit hivecall traces and append redacted run summaries and moments."""
import argparse
import ast
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import posixpath
from pathlib import Path
import re
import shlex
import subprocess
import sys

from redact import redact, redact_value

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
DEFAULT_OUT = HERE.parent / "evals" / "dataset.jsonl"
MAX_BYTES = 25 * 1024 * 1024
GAP_MS = 30 * 60 * 1000
STATUS = {"done": "done", "complete": "done", "completed": "done",
          "in progress": "open", "not started": "open", "stuck": "open",
          "blocked": "parked", "parked": "parked", "owner-only": "parked"}
CHECK = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")
STATUS_BULLET = re.compile(
    r"^\s*[-*]\s*(?:\*\*)?(done|complete|completed|in progress|not started|stuck|blocked|parked|owner-only)"
    r"(?:\*\*)?\s*[:—-]\s*(.+)$", re.I)
PROOF_COMMAND = re.compile(r"\b(test|check|verify|build|lint|pytest|jest|vitest|playwright|xcodebuild|assert|swift test|cargo test)\b", re.I)
PROOF_TEXT = re.compile(
    r"\b(?:evidence|screenshot|recording|frames?|observed|saw|shows|measured|visible|reproduced|"
    r"tester report|qa report|verification|proof|result|fps|within\s+\d|on build)\b", re.I)
ITEM_ID = re.compile(r"\bISC[- ](\d+(?:\.\d+)*)\b", re.I)
VERDICT = re.compile(r"\bISC[- ](\d+(?:\.\d+)*)\s*:\s*(PASS|FAIL|BLOCKED|PARK(?:ED)?)\b", re.I)
ALERT_LINE = re.compile(
    r"^(?:🚦\s*)?(?:WATCH STALLED\b|WATCH DONE\b|WATCH ERROR\b|"
    r"HOST\s+(?:load|disk|orphan process|large file):|"
    r"AGENT\s+.+?:|GHOST\s+BB child\b|LEDGER\s+ISC[- ]\d|OFF TRACK\b|"
    r"LOOP\b|REGRESSION\b|UNCLAIMED\b|PLATEAU\b|LEFTOVER\b|OPENCODE\b|"
    r"SIMULATOR\b|BRIEF\b|ALERT\b|FAIL\s+ISC[- ]\d)", re.I)
TASK_BOUND = re.compile(r"\b(?:scope|deliverable|acceptance|only change|do not change|don't change|report back|bounded|must not|should not)\b", re.I)
LEDGER_FILE = re.compile(r"(?:^|[/\\])(?:ISA|checklist)\.html$", re.I)
LEDGER_INVOKE = re.compile(r"\bpython\S*\s+(?:[^\s;&|]*/)?ledger\.py\s+([^\s;&|]+)", re.I)
EDIT_TOOLS = {"edit", "write", "apply_patch", "applypatch"}


def bb(*args):
    out = subprocess.run(["bb", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def event_text(event):
    data = event.get("data") or {}
    if event.get("type") == "client/turn/requested":
        return "\n".join(item.get("text") or "" for item in data.get("input") or [])
    item = data.get("item") or {}
    if event.get("type") == "item/completed" and item.get("type") == "agentMessage":
        return item.get("text") or ""
    return ""


def clip_tail(text, size):
    if len(text) <= size:
        return text
    marker = "…[trimmed]"
    return marker + text[-(size - len(marker)):]


def action(event):
    item = (event.get("data") or {}).get("item") or {}
    kind = item.get("type") or event.get("type") or "event"
    if kind == "agentMessage":
        text = item.get("text") or ""
    elif kind == "commandExecution":
        text = "command: " + str(item.get("command") or "") + " [" + str(item.get("status") or "") + "]"
    elif kind == "toolCall":
        text = str(item.get("tool") or "tool") + " " + json.dumps(item.get("arguments") or {}, ensure_ascii=False)
    elif kind == "delegation":
        text = "delegation " + json.dumps({"label": item.get("label"),
                                           "background": item.get("background"),
                                           "presentation": item.get("presentation")}, ensure_ascii=False)
    else:
        text = kind
    # Source event type and item status let consumers check, e.g., that a B4/B6 action is a start.
    return {"kind": kind, "text": clip_tail(redact(text), 1400), "eventId": event.get("id"),
            "eventType": event.get("type"), "status": item.get("status")}


def next_action_index(events, index):
    for j in range(index + 1, len(events)):
        item = (events[j].get("data") or {}).get("item") or {}
        if events[j].get("type") == "item/completed" and item.get("type") in (
                "agentMessage", "toolCall", "commandExecution", "delegation"):
            return j
    return None


def context(events, before, limit=1800, trigger=None, trigger_text=None):
    """Recent sanitized history before the action, with an explicit trigger kept in-bounds."""
    start = max(0, before - 90)
    messages = []
    for i in range(start, before):
        text = event_text(events[i]).strip()
        if text:
            messages.append((i, text))
    if trigger is not None and trigger < before:
        existing = next((j for j, (i, _) in enumerate(messages) if i == trigger), None)
        if existing is None:
            text = event_text(events[trigger]).strip()
            if text:
                messages.append((trigger, text))
                messages.sort(key=lambda pair: pair[0])
                existing = next(j for j, (i, _) in enumerate(messages) if i == trigger)
        if existing is not None and trigger_text:
            trigger_text = redact(trigger_text)
            current = messages[existing][1]
            if trigger_text not in current:
                messages[existing] = (trigger, current + "\n[trigger] " + trigger_text)
    messages = messages[-5:]
    if trigger is not None and trigger < before and not any(i == trigger for i, _ in messages):
        trigger_message = event_text(events[trigger]).strip()
        if trigger_message:
            if trigger_text:
                safe_trigger = redact(trigger_text)
                if safe_trigger not in trigger_message:
                    trigger_message += "\n[trigger] " + safe_trigger
            # Keep the trigger plus the four newest surrounding messages, even when old.
            messages = sorted(messages[-4:] + [(trigger, trigger_message)], key=lambda pair: pair[0])
    parts = []
    for i, text in messages:
        size = 700 if i == trigger else (250 if trigger is not None else 350)
        parts.append((i, clip_tail(redact(text), size)))
    while len(parts) > 1 and len("\n---\n".join(text for _, text in parts)) > limit:
        drop = next((j for j, (i, _) in enumerate(parts) if i != trigger), None)
        if drop is None:
            break
        parts.pop(drop)
    out = "\n---\n".join(text for _, text in parts)
    return clip_tail(out, limit)


def moment(run_id, week, behavior, event, ctx, next_action, fixed_check,
           item_id=None, trigger_event_id=None):
    row = {"runId": run_id, "week": week, "behavior": behavior,
           "eventId": event.get("id"), "context": ctx,
           "actualNextAction": next_action, "fixedCheck": fixed_check}
    if item_id:
        row["itemId"] = item_id
    if trigger_event_id:
        row["triggerEventId"] = trigger_event_id
    identity = json.dumps([run_id, behavior, row["eventId"], item_id,
                           trigger_event_id, fixed_check,
                           (next_action or {}).get("eventId")], sort_keys=True, ensure_ascii=False)
    row["momentId"] = hashlib.sha256(identity.encode()).hexdigest()[:20]
    return row


def status_rows(text):
    """Read explicit checklist bullets only; markdown status tables are summaries, not items."""
    rows = []
    for line in text.splitlines():
        match = CHECK.match(line)
        if match:
            rows.append({"item": match.group(2).strip(), "state": "done" if match.group(1).strip() else "open"})
            continue
        match = STATUS_BULLET.match(line)
        if match:
            state = STATUS[match.group(1).lower()]
            rows.append({"item": match.group(2).strip(), "state": state,
                         "reason": state == "parked" and bool(re.search(
                             r"\b(because|reason|waiting|until|blocked by|owner-only|unblock)\b",
                             match.group(2), re.I))})
    return rows


def open_state(prior_text):
    rows = status_rows(prior_text)
    if any(row["state"] == "open" for row in rows):
        return "open"
    if rows and all(row["state"] in ("done", "parked") for row in rows):
        return "closed"
    if re.search(r"\b(in progress|not started|stuck|blocked|open|remaining|todo|to do)\b", prior_text, re.I):
        return "open"
    if re.search(r"\b(done|completed|all items closed|watch done|parked|owner-only)\b", prior_text, re.I):
        return "closed"
    return "unknown"


def _field(value, names):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in names and isinstance(child, str):
                return child
        for child in value.values():
            found = _field(child, names)
            if found is not None:
                return found
    return None


def _ledger_path(path):
    return bool(path and LEDGER_FILE.search(str(path).strip().strip("'\"")))


def _changed(old, new):
    if "\n" not in old and "\n" not in new:
        after = []
        for tag, _, _, start, end in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
            if tag in ("insert", "replace"):
                after.append(new[start:end])
        return "\n".join(after)
    before, after = old.splitlines(), new.splitlines()
    return "\n".join(line for tag, _, _, start, end in difflib.SequenceMatcher(
        None, before, after, autojunk=False).get_opcodes()
                      if tag in ("insert", "replace") for line in after[start:end])


def _patch_additions(patch, fallback_target=False):
    additions, target = [], fallback_target
    for line in patch.splitlines():
        if line.startswith(("*** Update File:", "*** Add File:", "--- ", "+++ ")):
            target = _ledger_path(line.split(":", 1)[-1].strip()) if line.startswith("*** ") else _ledger_path(line[4:].strip())
        elif line.startswith("+") and not line.startswith("+++") and target:
            additions.append(line[1:])
    return "\n".join(additions)


def _checked_items(text):
    found = {}
    for match in re.finditer(r"\bid\s*=\s*(['\"])ISC[- ](\d+(?:\.\d+)*)\1", text, re.I):
        row = text[match.end():match.end() + 700].split("</li>", 1)[0]
        checkbox = re.search(r"<input\b[^>]*\bchecked(?:\s|>|=)", row, re.I)
        if checkbox:
            found["ISC-" + match.group(2)] = row.strip()
    for match in re.finditer(r"\[x\]\s*ISC[- ](\d+(?:\.\d+)*)", text, re.I):
        found["ISC-" + match.group(1)] = match.group(0)
    return found


def _decisions(added, old="", new=""):
    """Read item outcomes only from content proven to be newly written to the ledger."""
    found, seen = [], set()
    for match in VERDICT.finditer(added):
        item_id = "ISC-" + match.group(1)
        raw_state = match.group(2).lower()
        state = "parked" if raw_state.startswith("park") else raw_state
        key = (item_id, state)
        if key not in seen:
            start = max(0, added.rfind("\n", 0, match.start()) + 1)
            end = added.find("\n", match.end())
            line = added[start:end if end >= 0 else len(added)]
            found.append((item_id, state, line.strip(), state == "pass"))
            seen.add(key)

    before = _checked_items(old)
    after = _checked_items(new) if new else _checked_items(added)
    for item_id, line in after.items():
        if item_id not in before and (item_id, "tick") not in seen:
            found.append((item_id, "tick", line, True))
            seen.add((item_id, "tick"))
    return found


def _path_args(args):
    path = _field(args, {"path", "filepath", "file_path", "filename", "file"})
    if path and _ledger_path(path):
        return path
    patch = _field(args, {"patch", "patchtext"})
    match = re.search(r"(?m)^\*\*\* (?:Update|Add) File:\s*(.+)$", patch or "")
    return match.group(1).strip() if match and _ledger_path(match.group(1).strip()) else None


def _tool_decisions(item, files):
    tool = str(item.get("tool") or "").lower().rsplit(".", 1)[-1]
    args = item.get("arguments") or {}
    path = _path_args(args)
    if tool not in EDIT_TOOLS or not path:
        return []
    key = posixpath.normpath(path.strip().strip("'\""))
    old = _field(args, {"oldstring", "old_string", "oldtext", "old_text"}) or ""
    new = _field(args, {"newstring", "new_string", "newtext", "new_text"})
    if tool in ("apply_patch", "applypatch"):
        patch = _field(args, {"patch", "patchtext", "content", "text"}) or ""
        added = _patch_additions(patch, fallback_target=True)
        return _decisions(added)
    if new is None:
        new = _field(args, {"content", "contents", "text"})
    if new is None:
        return []
    prior = files.get(key)
    old = old or (prior if isinstance(prior, str) else "")
    if tool == "write" and not old and re.search(r"<(?:!doctype|html\b|section\b|table\b)", new, re.I):
        # A full ledger rewrite is not evidence that its old checked rows were newly added.
        files[key] = new
        return []
    added = _changed(old, new) if old else new
    files[key] = new
    return _decisions(added, old, new)


def _shell_vars(command):
    values = {}
    for match in re.finditer(r"(?:^|[;\s])([A-Z][A-Z0-9_]*)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)", command):
        values[match.group(1)] = match.group(2).strip("'\"")
    return values


def _shell_path(path, variables):
    path = path.strip().strip("'\"")
    for _ in range(4):
        path = re.sub(r"\$\{?([A-Z][A-Z0-9_]*)\}?", lambda m: variables.get(m.group(1), m.group(0)), path)
    return posixpath.normpath(path)


def _literal_strings(code):
    """Return string literals passed directly to print() in a Python stdin command."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    values, output = {}, []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = node.value.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    output.append(arg.value)
                elif isinstance(arg, ast.Name) and arg.id in values:
                    output.append(values[arg.id])
    return "\n".join(output)


def _command_files(command, files):
    variables = _shell_vars(command)
    # Unknown shell redirections invalidate an old cached value; never reuse stale rows.
    for match in re.finditer(r"(?<![<])(?:>>|>)\s*([^\s;|&]+)", command):
        path = _shell_path(match.group(1), variables)
        if path not in ("/dev/null", "&1", "&2"):
            files[path] = None
    heredoc = re.compile(r"\bcat\s+(?P<op>>>|>)\s*(?P<path>[^\s]+)\s+<<(?P<quote>['\"]?)(?P<tag>[A-Za-z_]\w*)(?P=quote)\s*\n(?P<body>.*?)\n\s*(?P=tag)(?=\s|$)", re.S)
    for match in heredoc.finditer(command):
        path = _shell_path(match.group("path"), variables)
        body = match.group("body")
        files[path] = (str(files.get(path) or "") + body) if match.group("op") == ">>" else body
    for match in re.finditer(r"\b(?:echo|printf)\s+((?:\"(?:\\.|[^\"])*\")|(?:'[^']*'))\s*(>>|>)\s*([^\s;|&]+)", command):
        try:
            value = shlex.split(match.group(1))[0]
        except (ValueError, IndexError):
            continue
        path = _shell_path(match.group(3), variables)
        files[path] = (str(files.get(path) or "") + value) if match.group(2) == ">>" else value


def _stdin_payload(command, invoke_start):
    prefix = command[:invoke_start]
    py = re.search(r"\bpython\S*\s+-\s+<<(['\"]?)([A-Za-z_]\w*)\1\s*\n(.*?)\n\s*\2(?=\s|$)", prefix, re.S)
    if py:
        return _literal_strings(py.group(3))
    values = []
    for match in re.finditer(r"\becho\s+((?:\"(?:\\.|[^\"])*\")|(?:'[^']*'))", prefix):
        try:
            values.append(shlex.split(match.group(1))[0])
        except (ValueError, IndexError):
            pass
    return "\n".join(values)


def _command_decisions(item, files):
    command = item.get("command") or ""
    variables = _shell_vars(command)
    _command_files(command, files)
    invoke = LEDGER_INVOKE.search(command)
    if invoke:
        source = invoke.group(1).strip("'\"")
        if source in ("/dev/stdin", "-"):
            payload = _stdin_payload(command, invoke.start())
        else:
            payload = files.get(_shell_path(source, variables))
        return _decisions(payload) if isinstance(payload, str) else []

    # Direct append or patch operations expose the actual added ledger text.
    patch = re.search(r"\bapply_patch\s+<<(['\"]?)([A-Za-z_]\w*)\1\s*\n(.*?)\n\s*\2(?=\s|$)", command, re.S)
    if patch:
        return _decisions(_patch_additions(patch.group(3)))
    for match in re.finditer(r"\bcat\s+(>>|>)\s*([^\s]+)\s+<<(['\"]?)([A-Za-z_]\w*)\3\s*\n(.*?)\n\s*\4(?=\s|$)", command, re.S):
        if _ledger_path(_shell_path(match.group(2), variables)) and match.group(1) == ">>":
            return _decisions(match.group(5))
    for match in re.finditer(r"\b(?:echo|printf)\s+((?:\"(?:\\.|[^\"])*\")|(?:'[^']*'))\s*(>>|>)\s*([^\s;|&]+)", command):
        if (_ledger_path(_shell_path(match.group(3), variables))
                and (match.group(2) == ">>" or re.search(r"ISC[- ]\d+\s*:", match.group(1), re.I))):
            try:
                return _decisions(shlex.split(match.group(1))[0])
            except (ValueError, IndexError):
                return []

    # A Python command must execute (not merely create) the code that writes the ledger.
    if not re.search(r"\bpython\S*\s+-\s+<<|\bpython\S*\s+-c\s+", command, re.I):
        return []
    code = command
    if not re.search(r"(?:ISA|checklist)\.html", code, re.I) or not re.search(r"(?:write_text|\.write\(|open\([^\n]*['\"]w)", code, re.I):
        return []
    result = []
    for match in re.finditer(r"\.replace\(\s*(['\"])(.*?)\1\s*,\s*(['\"])(.*?)\3\s*\)", code, re.S):
        try:
            old, new = ast.literal_eval(match.group(1) + match.group(2) + match.group(1)), ast.literal_eval(match.group(3) + match.group(4) + match.group(3))
        except (ValueError, SyntaxError):
            continue
        result.extend(_decisions(_changed(old, new), old, new))
    return result


def item_decisions(events, index, files=None):
    """Return decisions encoded by completed edits to an ISA/checklist ledger only."""
    event = events[index]
    item = (event.get("data") or {}).get("item") or {}
    if event.get("type") != "item/completed" or item.get("status") != "completed":
        return []
    if re.search(r"\b(?:refused|declined|denied)\b", str(item.get("approvalStatus") or ""), re.I):
        return []
    files = files if files is not None else {}
    if item.get("type") == "toolCall":
        return _tool_decisions(item, files)
    if item.get("type") == "commandExecution":
        return _command_decisions(item, files)
    return []


def proof_present(events, index, line, item_id):
    if PROOF_TEXT.search(line):
        return True
    # A successful check near the tick is useful only when the tick itself refers to proof/results.
    if re.search(r"\b(?:evidence|proof|result|report|verification|confirmed|observed|saw|shows)\b", line, re.I):
        return True
    for prior in events[max(0, index - 30):index]:
        item = (prior.get("data") or {}).get("item") or {}
        prior_text = event_text(prior)
        if item_id in prior_text and PROOF_TEXT.search(prior_text):
            return True
        if (prior.get("type") == "item/completed" and item.get("type") == "commandExecution"
                and item.get("status") == "completed" and item_id in (item.get("command") or "")
                and PROOF_COMMAND.search(item.get("command") or "")):
            return True
    return False


SPAWN_COMMAND = re.compile(r"\bbb\s+thread\s+spawn\b")


def is_delegation_action(event):
    """True only for the event that launches a worker; completions and reports never count."""
    if event.get("type") != "item/started":
        return False
    item = (event.get("data") or {}).get("item") or {}
    if item.get("type") == "delegation":
        return True
    if item.get("type") == "toolCall":
        return str(item.get("tool") or "").lower().rsplit(".", 1)[-1] in ("delegate", "subagent", "task")
    if item.get("type") == "commandExecution":
        command = item.get("command") or ""
        return bool(SPAWN_COMMAND.search(command)) and not re.search(r"(?:^|\s)(?:--help|-h)\b", command)
    return False


def watchdog_alerts(event):
    if event.get("type") != "client/turn/requested":
        return []
    text = event_text(event)
    if "[bb system]" in text.lower() or re.search(r"@thread:\S+\s+completed:", text):
        return []
    return [line.strip() for line in text.splitlines() if ALERT_LINE.match(line.strip())]


def extract_moments(run_id, week, events, invoked_at):
    events = sorted((e for e in events if (e.get("createdAt") or 0) >= invoked_at),
                    key=lambda e: (e.get("createdAt") or 0, e.get("seq") or 0))
    result = []

    # Behaviors 1–2: explicit per-item decision lines with a stable ledger identity.
    ledger_files = {}
    for i, event in enumerate(events):
        for item_id, state, line, completed in item_decisions(events, i, ledger_files):
            action_now = action(event)
            ctx = context(events, i)
            result.append(moment(run_id, week, 1, event, ctx, action_now,
                                 {"rule": "explicit per-item tick, park, retry or verdict",
                                  "label": state}, item_id=item_id))
            if completed and state in ("tick", "pass"):
                result.append(moment(run_id, week, 2, event, ctx, action_now,
                                      {"rule": "per-item tick has observable evidence or a recent item-specific successful check",
                                       "label": "proof_present" if proof_present(events, i, line, item_id) else "proof_not_detected"},
                                     item_id=item_id))

    # Behavior 3: long gaps are judged using only the state and context before the next action.
    activities = []
    for i, event in enumerate(events):
        if event.get("type") == "client/turn/requested":
            activities.append((i, event))
        elif event.get("type") == "item/completed":
            item = (event.get("data") or {}).get("item") or {}
            if item.get("type") in ("agentMessage", "toolCall", "commandExecution", "delegation"):
                activities.append((i, event))
    for (ai, before), (bi, after) in zip(activities, activities[1:]):
        elapsed = (after.get("createdAt") or 0) - (before.get("createdAt") or 0)
        if elapsed < GAP_MS:
            continue
        action_index = bi if after.get("type") == "item/completed" else next_action_index(events, bi)
        if action_index is None:
            continue
        action_event = events[action_index]
        prior = "\n".join(event_text(event) for event in events[max(0, ai - 90):ai + 1])
        state = open_state(prior)
        result.append(moment(run_id, week, 3, action_event,
                             context(events, action_index, trigger=ai), action(action_event),
                             {"rule": "orchestrator action gap exceeds 30 minutes; was work open?",
                              "gapMinutes": round(elapsed / 60000), "label": state},
                             trigger_event_id=before.get("id")))

    # Behaviors 4 and 6: only the launching event; context stops before it.
    for i, event in enumerate(events):
        if not is_delegation_action(event):
            continue
        summary = action(event)["text"]
        result.append(moment(run_id, week, 4, event, context(events, i), action(event),
                             {"rule": "orchestrator starts independent worker work",
                              "label": "parallel_start_detected"}))
        result.append(moment(run_id, week, 6, event, context(events, i), action(event),
                             {"rule": "delegation action includes bounded task details",
                              "label": "task_bounds_present" if TASK_BOUND.search(summary) else "task_bounds_not_detected"}))

    # Behavior 5: watchdog-authored incoming alerts only; preserve the alert in its action context.
    for i, event in enumerate(events):
        for line in watchdog_alerts(event):
            follow_index = next_action_index(events, i)
            follow = events[follow_index] if follow_index is not None else None
            alert = clip_tail(redact(line), 400)
            result.append(moment(run_id, week, 5, event,
                                 context(events, follow_index if follow_index is not None else i + 1,
                                         trigger=i, trigger_text=alert),
                                 action(follow) if follow else {"kind": "none", "text": "", "eventId": None,
                                                                  "eventType": None, "status": None},
                                 {"rule": "watchdog alert is followed by an orchestrator action",
                                  "alert": alert,
                                  "label": "follow_up_present" if follow else "no_follow_up"}))

    # Behavior 7: elapsed time and the provider's aggregate token counters; USD cost is not logged.
    final = next((e for e in reversed(events) if e.get("type") == "item/completed"
                  and ((e.get("data") or {}).get("item") or {}).get("type") == "agentMessage"), None)
    if final:
        duration = max(0, (final.get("createdAt") or invoked_at) - invoked_at)
        usage_event = next((e for e in reversed(events) if e.get("type") == "thread/tokenUsage/updated"), None)
        token_total = ((usage_event.get("data") or {}).get("tokenUsage") or {}).get("total") if usage_event else None
        usage = ({key: token_total.get(key) for key in ("inputTokens", "cachedInputTokens", "outputTokens",
                                                        "reasoningOutputTokens", "totalTokens")
                  if isinstance(token_total.get(key), (int, float))}
                 if isinstance(token_total, dict) else None)
        result.append(moment(run_id, week, 7, final, context(events, events.index(final)), action(final),
                             {"rule": "elapsed time and aggregate token use are recorded; provider USD cost is unavailable",
                              "durationMinutes": round(duration / 60000), "tokenUsage": usage,
                              "costUsd": None, "costStatus": "not provided by provider log",
                              "label": "duration_and_tokens_recorded"}))
    return result


def skill_commit(invoked_at):
    when = dt.datetime.fromtimestamp(invoked_at / 1000, tz=dt.timezone.utc).isoformat()
    result = subprocess.run(["git", "log", "-1", f"--before={when}", "--format=%H", "--",
                             ".agents/skills/hivecall"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.strip()
    return result or None


def skill_provenance(events):
    for event in events:
        item = (event.get("data") or {}).get("item") or {}
        args = item.get("arguments") or {}
        result = item.get("result") or ""
        if not isinstance(args, dict):
            continue
        if not isinstance(result, str):
            result = json.dumps(result, ensure_ascii=False)
        if item.get("type") != "toolCall" or item.get("tool") != "skill" or args.get("id") != "hivecall":
            continue
        match = re.search(r"Base directory for this skill:\s*([^\n]+)", result)
        base = match.group(1).strip() if match else ""
        if "/.config/opencode/skills/hivecall" in base or base.startswith("~/.config/opencode/skills/hivecall"):
            source = "global-config copy"
        elif ".agents/skills/hivecall" in base:
            source = "repository copy"
        elif base:
            source = "other loaded copy"
        else:
            source = None
        digest = hashlib.sha256(result.encode()).hexdigest() if result else None
        return {"skillPath": source, "skillPathSource": "loaded skill result" if source else "not visible in log",
                "skillContentSha256": digest,
                "method": "loaded path/content hash plus repository commit nearest invocation timestamp"}
    return {"skillPath": None, "skillPathSource": "not visible in log",
            "skillContentSha256": None,
            "method": "repository commit nearest invocation timestamp; loaded path not visible"}


def build_record(run, include_workers=True):
    events = bb("thread", "log", run["id"], "--json", "--all")
    invoked_at = run["invokedAt"]
    week = dt.datetime.fromtimestamp(invoked_at / 1000, tz=dt.timezone.utc).strftime("%G-W%V")
    moment_rows = extract_moments(run["id"], week, events, invoked_at)
    workers = []
    if include_workers:
        for child_id in run.get("children", []):
            try:
                child_events = bb("thread", "log", child_id, "--json", "--all")
            except Exception:
                workers.append({"id": child_id, "report": None, "readable": False})
                continue
            messages = [event_text(event) for event in child_events if event.get("type") == "item/completed"
                        and ((event.get("data") or {}).get("item") or {}).get("type") == "agentMessage"]
            report = redact(messages[-1]) if messages else ""
            workers.append({"id": child_id, "report": clip_tail(report, 350) if report else None,
                            "readable": True})
    provenance = skill_provenance(events)
    record = {"schemaVersion": 2, "recordType": "run", "runId": run["id"], "week": week,
              "invokedAt": invoked_at, "lastEvent": run.get("lastEvent"),
              "invocation": run["how"], "skillCommit": skill_commit(invoked_at),
              **provenance, "workers": workers, "moments": moment_rows}
    return redact_value(record)


def moment_key(moment_row):
    if moment_row.get("momentId"):
        return moment_row["momentId"]
    identity = json.dumps([moment_row.get("runId"), moment_row.get("behavior"),
                           moment_row.get("eventId"), moment_row.get("itemId"),
                           moment_row.get("triggerEventId"), moment_row.get("fixedCheck"),
                           (moment_row.get("actualNextAction") or {}).get("eventId")],
                          sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(identity.encode()).hexdigest()[:20]


def plan_appends(runs, existing_records, build=build_record, build_update=None):
    """Append new moments and changed worker reports without rewriting prior rows."""
    states = {}
    for row in existing_records:
        state = states.setdefault(row["runId"], {"lastEvent": 0, "moments": set(), "workers": {}})
        state["lastEvent"] = max(state["lastEvent"], row.get("lastEvent") or 0)
        state["moments"].update(moment_key(moment_row) for moment_row in row.get("moments", []))
        state["workers"].update((worker.get("id"), worker) for worker in row.get("workers", []) if worker.get("id"))
    pending = []
    for run in sorted(runs, key=lambda row: (row.get("invokedAt", 0), row["id"])):
        old = states.get(run["id"])
        if old is None:
            pending.append(build(run))
            continue
        record = (build_update or build)(run)
        new_moments = [m for m in record["moments"] if moment_key(m) not in old["moments"]]
        changed_workers = [worker for worker in record.get("workers", [])
                           if old["workers"].get(worker.get("id")) != worker]
        if new_moments or changed_workers:
            pending.append({key: value for key, value in record.items()
                            if key not in ("workers", "moments", "recordType")}
                           | {"recordType": "runUpdate", "moments": new_moments,
                              "workers": changed_workers})
    return pending


def build_update_record(run):
    return build_record(run, include_workers=True)


def dataset_counts(records):
    counts = {str(number): 0 for number in range(1, 8)}
    behavior1_with_item_id = 0
    alert_total = alert_contexts = 0
    run_ids = set()
    for record in records:
        run_ids.add(record["runId"])
        for m in record.get("moments", []):
            counts[str(m["behavior"])] += 1
            if m["behavior"] == 1 and m.get("itemId"):
                behavior1_with_item_id += 1
            if m["behavior"] == 5:
                alert_total += 1
                alert_contexts += int(bool(m.get("fixedCheck", {}).get("alert")
                                           and m["fixedCheck"]["alert"] in m.get("context", "")))
    return {"runs": len(run_ids), "momentsByBehavior": counts,
            "behavior1WithItemId": behavior1_with_item_id,
            "alertMoments": alert_total, "alertContextsContainingAlert": alert_contexts,
            "alertContextPercent": round(alert_contexts * 100 / alert_total, 1) if alert_total else 100.0}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(DEFAULT_OUT))
    o = p.parse_args()
    found = subprocess.run([sys.executable, str(HERE / "find-runs.py"), "--all"],
                           capture_output=True,
                           text=True, check=True)
    runs = json.loads(found.stdout)
    path = Path(o.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()] if path.exists() else []
    pending = plan_appends(runs["runs"], existing, build_update=build_update_record)
    encoded = [json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in pending]
    current = path.stat().st_size if path.exists() else 0
    added = sum(len(line.encode("utf-8")) for line in encoded)
    if added and current + added > MAX_BYTES:
        raise SystemExit(f"append would exceed {MAX_BYTES} byte dataset cap")
    if encoded:
        with path.open("a", encoding="utf-8") as out:
            out.writelines(encoded)
            out.flush()
            os.fsync(out.fileno())
    all_records = existing + [json.loads(line) for line in encoded]
    stats = dataset_counts(all_records)
    appended_moments = sum(len(row.get("moments", [])) for row in pending)
    print(json.dumps({"foundRuns": len(runs["runs"]), "appendedRecords": len(pending),
                      "appendedMoments": appended_moments, **stats,
                      "datasetBytes": current + added,
                      "unreadableRuns": len(runs.get("unreadable", [])), "dataset": str(path)}, indent=2))
    incomplete = [f"baseline incomplete: behavior {behavior} has only {stats['momentsByBehavior'][behavior]} moments"
                  for behavior in ("1", "2") if stats["momentsByBehavior"][behavior] < 10]
    if incomplete:
        raise SystemExit("\n".join(incomplete))


if __name__ == "__main__":
    main()
