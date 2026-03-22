from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ResearchItem:
    text: str
    author: str
    timestamp: Optional[str]
    engagementScore: int
    directUrl: str
    source: str
    replies: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdapterResult:
    items: List[ResearchItem]
    errors: List[str] = field(default_factory=list)


class BaseAdapter(ABC):
    source_name: str = "base"

    @abstractmethod
    def fetch(
        self,
        query: str,
        source_config: Dict[str, Any],
        time_range: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AdapterResult:
        raise NotImplementedError

    def normalize_timestamp(self, value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(value, str):
            return value
        return str(value)

    def build_item(
        self,
        *,
        text: Any,
        author: Any,
        timestamp: Any,
        engagement_score: Any,
        direct_url: Any,
        replies: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> ResearchItem:
        return ResearchItem(
            text=(text or "").strip(),
            author=(author or "unknown").strip(),
            timestamp=self.normalize_timestamp(timestamp),
            engagementScore=int(engagement_score or 0),
            directUrl=(direct_url or "").strip(),
            source=self.source_name,
            replies=list(replies or []),
        )
