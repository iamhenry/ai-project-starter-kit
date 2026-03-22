from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import AdapterResult, BaseAdapter, ResearchItem


class RedditAdapter(BaseAdapter):
    source_name = "reddit"

    def fetch(
        self,
        query: str,
        source_config: Dict[str, Any],
        time_range: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AdapterResult:
        subreddit = source_config.get("subreddit")
        if not subreddit:
            return AdapterResult(items=[], errors=["reddit adapter requires source_config.subreddit"])

        try:
            from scrapi_reddit import RedditScraper  # type: ignore
        except Exception as exc:  # pragma: no cover - import path depends on environment
            return AdapterResult(items=[], errors=[f"failed to import scrapi_reddit: {exc}"])

        limit = int(source_config.get("limit") or limit or 10)
        time_range = source_config.get("time_range") or time_range or "month"

        scraper = RedditScraper()
        raw_items = self._run_search(scraper, subreddit=subreddit, query=query, time_range=time_range, limit=limit)

        items: List[ResearchItem] = []
        for raw in raw_items:
            item = self.build_item(
                text=raw.get("selftext") or raw.get("body") or raw.get("title") or "",
                author=raw.get("author") or "unknown",
                timestamp=raw.get("created_utc") or raw.get("createdAt"),
                engagement_score=(raw.get("score") or 0) + (raw.get("num_comments") or 0),
                direct_url=raw.get("url") or raw.get("permalink"),
                replies=raw.get("replies") or [],
            )
            items.append(item)

        return AdapterResult(items=items)

    def _run_search(
        self,
        scraper: Any,
        *,
        subreddit: str,
        query: str,
        time_range: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if hasattr(scraper, "search_subreddit"):
            return list(scraper.search_subreddit(subreddit=subreddit, query=query, time=time_range, limit=limit))
        if hasattr(scraper, "search"):
            return list(scraper.search(subreddit=subreddit, query=query, time=time_range, limit=limit))
        raise RuntimeError("scrapi_reddit scraper does not expose a supported search method")
