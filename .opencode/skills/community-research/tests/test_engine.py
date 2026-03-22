from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from adapters.base import BaseAdapter
from adapters.discord import DiscordAdapter
from scripts.research import build_output, dedupe_items


class DummyAdapter(BaseAdapter):
    source_name = "dummy"

    def fetch(self, query, source_config, time_range=None, limit=None):  # pragma: no cover - not used directly
        raise NotImplementedError


class EngineTests(unittest.TestCase):
    def test_build_item_normalizes_shape(self):
        adapter = DummyAdapter()
        item = adapter.build_item(
            text=" hello ",
            author=" tester ",
            timestamp=None,
            engagement_score=5,
            direct_url="https://example.com/post/1",
            replies=[{"text": "reply"}],
        )
        self.assertEqual(item.text, "hello")
        self.assertEqual(item.author, "tester")
        self.assertEqual(item.engagementScore, 5)
        self.assertEqual(item.directUrl, "https://example.com/post/1")
        self.assertEqual(item.source, "dummy")

    def test_dedupe_prefers_higher_engagement_and_filters_missing_urls(self):
        items = [
            {"text": "Same idea", "engagementScore": 1, "directUrl": "https://a", "source": "reddit"},
            {"text": "same   idea", "engagementScore": 9, "directUrl": "https://b", "source": "twitter_x"},
            {"text": "missing url", "engagementScore": 99, "directUrl": "", "source": "discord"},
        ]
        deduped = dedupe_items(items)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["directUrl"], "https://b")

    def test_discord_adapter_can_build_fallback_message_link(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.json"
            path.write_text(json.dumps({
                "messages": [
                    {
                        "id": "999",
                        "channel_id": "222",
                        "timestamp": "2026-03-22T10:00:00Z",
                        "content": "People keep relapsing on weekends",
                        "author": {"name": "alex"},
                        "reactions": [{"emoji": ":("}]
                    }
                ]
            }))
            adapter = DiscordAdapter()
            result = adapter.fetch(
                query="relapsing weekends",
                source_config={
                    "channel_export_path": str(path),
                    "server_id": "111",
                    "channel_id": "222",
                    "limit": 5,
                },
            )
            self.assertEqual(result.errors, [])
            self.assertEqual(result.items[0].directUrl, "https://discord.com/channels/111/222/999")

    def test_build_output_aggregates_parallel_sources(self):
        from scripts import research

        original_adapters = research.ADAPTERS.copy()

        class AdapterOne:
            def fetch(self, query, source_config, time_range=None, limit=None):
                dummy = DummyAdapter()
                return type("Result", (), {
                    "items": [dummy.build_item(text="one", author="a", timestamp=None, engagement_score=1, direct_url="https://1")],
                    "errors": []
                })

        class AdapterTwo:
            def fetch(self, query, source_config, time_range=None, limit=None):
                dummy = DummyAdapter()
                return type("Result", (), {
                    "items": [dummy.build_item(text="two", author="b", timestamp=None, engagement_score=2, direct_url="https://2")],
                    "errors": []
                })

        try:
            research.ADAPTERS = {"one": AdapterOne, "two": AdapterTwo}
            output = build_output("test", [{"type": "one"}, {"type": "two"}], None, None)
            self.assertEqual(len(output["items"]), 2)
            self.assertEqual(output["errors"], [])
        finally:
            research.ADAPTERS = original_adapters


if __name__ == "__main__":
    unittest.main()
