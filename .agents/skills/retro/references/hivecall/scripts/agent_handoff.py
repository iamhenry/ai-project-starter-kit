#!/usr/bin/env python3
"""Small, local JSONL handoff/cache helpers for OpenCode-agent answers."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import textwrap


ID_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def cache_key(model, payload, identity=""):
    encoded = json.dumps({"model": model, "payload": payload, "identity": identity},
                         ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_cached_answer(cache_dir, answer_id):
    path = Path(cache_dir).expanduser() / f"{answer_id}.json"
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, None
    if isinstance(saved, dict) and saved.get("key") == answer_id and "result" in saved:
        return True, saved["result"]
    return False, None


def write_cached_answer(cache_dir, answer_id, answer, model="opencode-agent"):
    directory = Path(cache_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{answer_id}.json"
    found, _ = read_cached_answer(directory, answer_id)
    if found:
        return False
    encoded = json.dumps({"key": answer_id, "model": model, "result": answer},
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".answer-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def import_answers(cache_dir, answers_path):
    """Validate the entire answers file before adding any answers to the cache."""
    rows = []
    seen = set()
    for line_no, line in enumerate(Path(answers_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {answers_path}:{line_no}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"answer row at {answers_path}:{line_no} must be an object")
        answer_id, answer = row.get("id"), row.get("answer")
        if not isinstance(answer_id, str) or not ID_PATTERN.fullmatch(answer_id):
            raise ValueError(f"answer row at {answers_path}:{line_no} has an invalid id")
        if not isinstance(answer, str):
            raise ValueError(f"answer row at {answers_path}:{line_no} must contain raw answer text in `answer`")
        if answer_id in seen:
            raise ValueError(f"duplicate answer id at {answers_path}:{line_no}")
        seen.add(answer_id)
        rows.append((answer_id, answer))

    imported = skipped = 0
    for answer_id, answer in rows:
        if write_cached_answer(cache_dir, answer_id, answer):
            imported += 1
        else:
            skipped += 1
    return imported, skipped


def _write_atomic(path, content):
    fd, temporary = tempfile.mkstemp(prefix=".prompts-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _wrap_lines(text):
    return "\n".join(part for line in text.split("\n")
                     for part in (textwrap.wrap(line, width=1200, replace_whitespace=False,
                                                drop_whitespace=False, break_long_words=True,
                                                break_on_hyphens=False) or [""]))


def _code_block(text, language):
    runs = {char: max((len(run) for run in re.findall(re.escape(char) + r"+", text)), default=0)
            for char in ("`", "~")}
    delimiter = min(runs, key=runs.get)
    fence = delimiter * max(3, runs[delimiter] + 1)
    return f"{fence}{language}\n{_wrap_lines(text)}\n{fence}"


def _write_readable_batch(requests, path):
    systems, skills = {}, {}
    items = []
    for request in requests:
        system = request.get("system", "") or ""
        systems.setdefault(system, len(systems) + 1)
        prompt = request.get("prompt", "")
        skill_number = None
        if request.get("role") == "tested":
            match = re.search(r"<hivecall skill>\n([\s\S]*?)\n</hivecall skill>", prompt)
            if match:
                skill = match.group(1)
                skills.setdefault(skill, len(skills) + 1)
                skill_number = skills[skill]
                replacement = f"<hivecall skill>\n[See skill section {skill_number} above.]\n</hivecall skill>"
                prompt = prompt[:match.start()] + replacement + prompt[match.end():]
        items.append((request, systems[system], skill_number, prompt))

    role = requests[0].get("role", "unknown")
    lines = [f"# Agent-readable batch — {role}", "",
             "This Markdown twin is the agent input; use it instead of the machine JSONL batch.",
             "Apply each item's referenced system and skill sections as instructions, then answer its prompt. Return one importer-format answer line per item, preserving its ID.",
             "", "## System sections", ""]
    for system, number in systems.items():
        lines.extend([f"### System section {number}", "", _code_block(system, "text"), ""])
    if skills:
        lines.extend(["## Skill sections", ""])
        for skill, number in skills.items():
            lines.extend([f"### Skill section {number}", "", _code_block(skill, "markdown"), ""])
    lines.extend(["## Items", ""])
    for index, (request, system_number, skill_number, prompt) in enumerate(items, 1):
        lines.extend([f"### Item {index}", "", f"- ID: `{request['id']}`",
                      f"- Role: {request.get('role', 'unknown')}",
                      f"- System section: {system_number}",
                      f"- Skill section: {skill_number if skill_number is not None else 'none'}",
                      "", "#### Prompt", "", _code_block(prompt, "text"), ""])
    _write_atomic(path, "\n".join(lines).encode("utf-8"))


def write_prompt_batch(requests, output_path, batch_size):
    """Write one role's pending prompts in bounded, ordered batches."""
    if not requests:
        return None
    role = next((candidate for candidate in ("tested", "judge")
                 if any(request["role"] == candidate for request in requests)), requests[0]["role"])
    batch = [request for request in requests if request["role"] == role]
    batches = [batch[start:start + batch_size] for start in range(0, len(batch), batch_size)]
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    machine_paths = ([path] if len(batches) == 1 else
                     [path.with_name(f"{path.stem}.b{index:02d}.jsonl")
                      for index in range(1, len(batches) + 1)])
    outputs = []
    for output, prompts in zip(machine_paths, batches):
        encoded = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                          for row in prompts).encode("utf-8")
        _write_atomic(output, encoded)
        readable = output.with_suffix(".md")
        _write_readable_batch(prompts, readable)
        outputs.append((output, readable))
    return outputs, role, len(batch)
