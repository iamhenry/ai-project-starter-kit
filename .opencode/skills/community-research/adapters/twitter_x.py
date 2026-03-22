from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests

from .base import AdapterResult, BaseAdapter, ResearchItem


class TwitterXAdapter(BaseAdapter):
    source_name = "twitter_x"
    search_url = "https://api.x.com/2/tweets/search/recent"

    def fetch(
        self,
        query: str,
        source_config: Dict[str, Any],
        time_range: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AdapterResult:
        token = os.getenv("X_BEARER_TOKEN")
        if not token:
            return AdapterResult(items=[], errors=["twitter_x adapter requires X_BEARER_TOKEN"])

        search_term = source_config.get("search_term") or query
        limit = int(source_config.get("limit") or limit or 10)
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "query": search_term,
            "max_results": min(max(limit, 10), 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,name",
        }

        start_time = self._time_range_to_start(source_config.get("time_range") or time_range)
        if start_time:
            params["start_time"] = start_time

        response = requests.get(self.search_url, headers=headers, params=params, timeout=30)
        if response.status_code >= 400:
            return AdapterResult(items=[], errors=[f"twitter_x adapter request failed: {response.status_code} {response.text}"])

        payload = response.json()
        users = {user.get("id"): user for user in payload.get("includes", {}).get("users", [])}
        items: List[ResearchItem] = []
        for tweet in payload.get("data", [])[:limit]:
            metrics = tweet.get("public_metrics") or {}
            user = users.get(tweet.get("author_id"), {})
            username = user.get("username") or tweet.get("author_id") or "unknown"
            item = self.build_item(
                text=tweet.get("text") or "",
                author=username,
                timestamp=tweet.get("created_at"),
                engagement_score=(metrics.get("like_count") or 0) + (metrics.get("retweet_count") or 0) + (metrics.get("reply_count") or 0),
                direct_url=f"https://x.com/{username}/status/{tweet.get('id')}",
                replies=[],
            )
            items.append(item)

        return AdapterResult(items=items)

    def _time_range_to_start(self, time_range: Optional[str]) -> Optional[str]:
        if not time_range:
            return None
        now = datetime.now(timezone.utc)
        mapping = {
            "day": now - timedelta(days=1),
            "7d": now - timedelta(days=7),
            "week": now - timedelta(days=7),
            "30d": now - timedelta(days=30),
            "month": now - timedelta(days=30),
        }
        dt = mapping.get(str(time_range).lower())
        if not dt:
            return None
        return dt.isoformat().replace("+00:00", "Z")
