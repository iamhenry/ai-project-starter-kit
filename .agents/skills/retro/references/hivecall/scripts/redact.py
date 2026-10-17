#!/usr/bin/env python3
"""Local redaction shared by stored traces and cloud payloads."""
import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.I)
TOKEN_PREFIX = re.compile(r"\b(?:sk|pk|ghp|gho|ghs|github_pat|xox[baprs])[-_][\w-]{8,}\b", re.I)
BEARER = re.compile(r"\bBearer\s+[^\s,;]+", re.I)
SECRET_KEY = (r"[\"']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|token)"
              r"[\"']?\s*[:=]\s*")
QUOTED_SECRET = re.compile(SECRET_KEY + r"(?P<q>[\"'])(?:\\.|(?!\1).)*?\1", re.I | re.S)
ASSIGNED_SECRET = re.compile(SECRET_KEY + r"[^\s,;\"'}\]]+", re.I)
JWT = re.compile(r"\beyJ[\w-]*\.[\w-]+\.[\w-]+\b")
LONG_TOKEN = re.compile(r"\b[A-Za-z0-9+/_=-]{40,}\b")
UUID_LIKE = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){2,4}(?:-[0-9a-f]{1,12})?\b", re.I)
# Private-id families: an alphanumeric suffix (proj_abcd1234), or a suffix that also has
# underscores/hyphens and a digit (auto_7pyi__rzd54, arun_ct_qp73jk-y). Digit-free snake_case
# labels such as task_bounds_not_detected stay readable. thr_/evt_ are allowed record keys.
PRIVATE_ID = re.compile(
    # Known BB/OpenCode families: prefix plus any following id run, whatever its shape.
    r"(?<!\w)(?:proj|ses|auto|arun|msg|env|host|prt|call)_[A-Za-z0-9_-]+"
    r"|(?<!\w)(?!(?-i:thr_|evt_))[a-z]{2,6}_"
    r"(?:(?=[A-Za-z_-]*\d)[A-Za-z0-9_-]{5,}(?![\w-])|[A-Za-z0-9]{8,}(?!\w))", re.I)
ABS_PATH = re.compile(r"(?<![\w:])/(?:Users|home|private|Volumes|var|tmp|workspace|workspaces)/[^\s\"'<>),;]+")
WIN_PATH = re.compile(r"\b[A-Za-z]:\\Users\\[^\s\"'<>),;]+", re.I)
TILDE_PATH = re.compile(r"(?<!\w)~/(?:[^\s\"'<>),;]+)")
HOME_VAR_PATH = re.compile(r"\$HOME(?:/[^\s\"'<>),;]*)?")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
TAILNET_HOST = re.compile(r"(?i)(?:[a-z0-9-]+\.)+ts\.net\b")
PRIVATE_URL = re.compile(
    r"(?i)\b(?:https?://)?(?:[a-z0-9-]+\.)+ts\.net(?::\d+)?(?:/[^\s\"'<>]*)?"
    r"|\b(?:https?://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s\"'<>]*)?"
)


def _config(*args):
    try:
        return subprocess.run(["git", "config", *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


@lru_cache(maxsize=1)
def machine_denylist():
    """Known machine, owner and BB project identifiers; no name guessing."""
    names = [os.environ.get("USER", ""), _config("user.name")]
    names.extend(n.strip() for n in re.split(r"[,;\n]", os.environ.get("HIVECALL_REDACT_NAMES", "")))
    paths = [os.path.expanduser("~")]
    try:
        projects = json.loads(subprocess.run(
            ["bb", "project", "list", "--include-personal", "--json"],
            capture_output=True, text=True, check=True).stdout)
        for project in projects:
            names.append(project.get("name", ""))
            paths.extend(source.get("path", "") for source in project.get("sources", []))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    clean_names = {n.strip() for n in names if n and n.strip()}
    # Git owner names can occur as a full name or a component; never guess from capitalization.
    for name in tuple(clean_names):
        if name == _config("user.name"):
            clean_names.update(part for part in re.split(r"\s+", name) if len(part) >= 3)
    clean_paths = {str(Path(p).expanduser()) for p in paths if p and p.strip()}
    return (tuple(sorted(clean_names, key=len, reverse=True)),
            tuple(sorted(clean_paths, key=len, reverse=True)))


def _is_private_ip(value):
    parts = [int(part) for part in value.split(".")]
    return (parts[0] in (10, 100) or parts[:2] == [192, 168]
            or (parts[0] == 172 and 16 <= parts[1] <= 31))


def _redact_ip(match):
    return "[private-ip]" if _is_private_ip(match.group(0)) else match.group(0)


def _boundary_replace(text, value, replacement):
    if not value:
        return text
    left = r"(?<![\w])" if value[0].isalnum() else r""
    right = r"(?![\w])" if value[-1].isalnum() else r""
    return re.sub(left + re.escape(value) + right, replacement, text, flags=re.I)


def redact(text):
    text = str(text)
    # Replace whole private URLs before their hosts, so URL paths are not retained.
    text = PRIVATE_URL.sub("[private-url]", text)
    text = IPV4.sub(_redact_ip, text)
    text = TAILNET_HOST.sub("[private-host]", text)
    text = EMAIL.sub("[email]", text)
    text = TOKEN_PREFIX.sub("[secret]", text)
    text = BEARER.sub("Bearer [secret]", text)
    text = QUOTED_SECRET.sub(lambda m: m.group(0)[:m.start("q") - m.start()]
                             + m.group("q") + "[secret]" + m.group("q"), text)
    text = ASSIGNED_SECRET.sub(lambda m: m.group(0).rsplit("=", 1)[0] + "=[secret]"
                               if "=" in m.group(0) else m.group(0).rsplit(":", 1)[0] + ":[secret]", text)
    text = JWT.sub("[token]", text)
    text = PRIVATE_ID.sub("[private-id]", text)
    text = UUID_LIKE.sub("[private-id]", text)
    text = LONG_TOKEN.sub("[long-token]", text)
    names, paths = machine_denylist()
    for path in paths:
        text = _boundary_replace(text, path, "[path]")
    text = ABS_PATH.sub("[path]", text)
    text = WIN_PATH.sub("[path]", text)
    text = TILDE_PATH.sub("[path]", text)
    text = HOME_VAR_PATH.sub("[path]", text)
    for name in names:
        text = _boundary_replace(text, name, "[name]")
    return text


def _secret_key(key):
    return bool(re.fullmatch(r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|token)",
                             str(key).strip(), re.I))


def redact_value(value, key=""):
    if _secret_key(key):
        return "[secret]"
    if key in ("skillCommit", "skillContentSha256"):
        return value
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {k: redact_value(item, k) for k, item in value.items()}
    return value


def scan(path):
    text = Path(path).read_text(encoding="utf-8")

    def strings(value, key=""):
        if isinstance(value, str):
            yield key, value
        elif isinstance(value, list):
            for item in value:
                yield from strings(item, key)
        elif isinstance(value, dict):
            for k, item in value.items():
                yield from strings(item, k)

    try:
        values = list(strings(json.loads(text)))
    except json.JSONDecodeError:
        try:
            values = [pair for line in text.splitlines() if line.strip()
                      for pair in strings(json.loads(line))]
        except json.JSONDecodeError:
            values = [("", text)]
    names, paths = machine_denylist()
    hits = {"paths": 0, "emails": 0, "personal_names": 0,
            "private_identifiers": 0, "private_network": 0, "key_token_patterns": 0}
    for key, value in values:
        hits["paths"] += len(ABS_PATH.findall(value)) + len(WIN_PATH.findall(value))
        hits["paths"] += len(TILDE_PATH.findall(value)) + len(HOME_VAR_PATH.findall(value))
        hits["paths"] += sum(value.count(p) for p in paths if p)
        hits["emails"] += len(EMAIL.findall(value))
        hits["personal_names"] += sum(len(re.findall(r"(?<!\w)" + re.escape(n) + r"(?!\w)", value, re.I))
                                       for n in names)
        hits["private_network"] += len(TAILNET_HOST.findall(value))
        hits["private_network"] += sum(1 for ip in IPV4.findall(value) if _is_private_ip(ip))
        hits["private_identifiers"] += len(UUID_LIKE.findall(value)) + len(PRIVATE_ID.findall(value))
        token_patterns = (TOKEN_PREFIX, BEARER, QUOTED_SECRET, ASSIGNED_SECRET, JWT)
        hits["key_token_patterns"] += sum(len(p.findall(value)) for p in token_patterns)
        if key not in ("skillCommit", "skillContentSha256"):
            hits["key_token_patterns"] += len(LONG_TOKEN.findall(value))
    print(json.dumps(hits, indent=2))
    return any(hits.values())


def self_test():
    old = os.environ.get("HIVECALL_REDACT_NAMES")
    os.environ["HIVECALL_REDACT_NAMES"] = "Fixture Owner"
    machine_denylist.cache_clear()
    try:
        fake_home = "/Users/fixture-owner/project"
        private_ids = ("proj_abcd123456 ses_abcdefghijk auto_abcdefghij msg_abcdefghij "
                       "env_abcdefghij host_abcdefghij prt_abcdefghij call_abcdefghij "
                       "auto_7pyi__rzd54 arun_ct_qp73jk-y proj_ab_cd-1234 ses_abcdefghijk-based "
                       "ses_alpha_beta auto_abcdefgh_ijkl")
        sample = ('{"api_key":"planted-short-secret"} Fixture Owner ' + fake_home
                  + " https://fixture.tailnet.ts.net/private/report 100.101.2.3 "
                  + "3A909B83-74E2-4D15-81A3-01D7122A1C33 " + private_ids
                  + " thr_safeid123 evt_safeid123 task_bounds_not_detected")
        preview = redact(sample)
        forbidden = ("planted-short-secret", "Fixture Owner", fake_home,
                     "fixture.tailnet.ts.net", "100.101.2.3", "3A909B83-74E2-4D15-81A3-01D7122A1C33",
                     *(v.removesuffix("-based") for v in private_ids.split()))
        if any(value in preview for value in forbidden):
            raise SystemExit("redaction self-test failed: " + preview)
        if '"api_key":"[secret]"' not in preview:
            raise SystemExit("quoted JSON secret key self-test failed: " + preview)
        if ("thr_safeid123" not in preview or "evt_safeid123" not in preview
                or "task_bounds_not_detected" not in preview):
            raise SystemExit("record-key allowlist self-test failed: " + preview)
        print(json.dumps({"preview": preview, "removed": ["quoted secret", "home/project path",
                                                              "owner name", "tailnet URL", "private IP",
                                                              "device-like identifier", "BB/OpenCode IDs"],
                         "preserved": ["thr_", "evt_"]}, indent=2))
    finally:
        if old is None:
            os.environ.pop("HIVECALL_REDACT_NAMES", None)
        else:
            os.environ["HIVECALL_REDACT_NAMES"] = old
        machine_denylist.cache_clear()


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 3 and sys.argv[1] == "--scan":
        raise SystemExit(1 if scan(sys.argv[2]) else 0)
    else:
        print(redact(sys.stdin.read()))
