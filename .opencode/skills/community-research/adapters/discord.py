from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AdapterResult, BaseAdapter, ResearchItem


class DiscordAdapter(BaseAdapter):
    source_name = "discord"

    def fetch(
        self,
        query: str,
        source_config: Dict[str, Any],
        time_range: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AdapterResult:
        export_path = source_config.get("channel_export_path")
        if not export_path:
            return AdapterResult(items=[], errors=["discord adapter requires source_config.channel_export_path"])

        path = Path(export_path)
        if not path.exists():
            return AdapterResult(items=[], errors=[f"discord export not found: {path}"])

        data = json.loads(path.read_text())
        messages = data.get("messages") or []
        limit = int(source_config.get("limit") or limit or 10)
        query_terms = [term.lower() for term in query.split() if term.strip()]

        matches: List[ResearchItem] = []
        for message in messages:
            content = (message.get("content") or "").strip()
            if not content:
                continue
            haystack = content.lower()
            if query_terms and not any(term in haystack for term in query_terms):
                continue
            item = self.build_item(
                text=content,
                author=((message.get("author") or {}).get("name") or "unknown"),
                timestamp=message.get("timestamp"),
                engagement_score=len(message.get("reactions") or []),
                direct_url=message.get("link") or self._build_fallback_url(source_config, message),
                replies=[],
            )
            matches.append(item)
            if len(matches) >= limit:
                break

        return AdapterResult(items=matches)

    def _build_fallback_url(self, source_config: Dict[str, Any], message: Dict[str, Any]) -> str:
        guild_id = source_config.get("server_id") or "@me"
        channel_id = source_config.get("channel_id") or message.get("channel_id")
        message_id = message.get("id")
        if guild_id and channel_id and message_id:
            return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        return ""
