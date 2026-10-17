#!/usr/bin/env python3
"""Send an explicit prompt to Ollama Cloud without local agent context or tools."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


ENDPOINT = "https://ollama.com/v1/chat/completions"


def judge(system: str, user: str, model: str) -> str:
    """Return one chat completion's text; callers own prompt redaction and parsing."""
    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        try:
            auth = json.loads((Path.home() / ".local/share/opencode/auth.json").read_text(encoding="utf-8"))
            key = auth.get("ollama-cloud", {}).get("key")
        except (OSError, ValueError, AttributeError):
            key = None
    if not isinstance(key, str) or not key:
        raise RuntimeError("Ollama Cloud API key is unavailable")

    messages = ([{"role": "system", "content": system}] if system else [])
    messages.append({"role": "user", "content": user})
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama Cloud returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise RuntimeError(f"Ollama Cloud request failed: {type(exc).__name__}") from None

    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return content if isinstance(content, str) else ""
