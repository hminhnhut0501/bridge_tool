from datetime import datetime, timedelta, timezone
import asyncio
import sys
from types import SimpleNamespace

import modules.mod_channel_publisher as channel_publisher

from modules.mod_channel_publisher import is_channel_due, parse_channel_buttons


def test_parse_channel_buttons_text_rows():
    rows = parse_channel_buttons("Xem ngay | https://example.com\nA | https://a.test || B | tg://resolve?domain=test")
    assert rows == [
        [("Xem ngay", "https://example.com")],
        [("A", "https://a.test"), ("B", "tg://resolve?domain=test")],
    ]


def test_parse_channel_buttons_skips_invalid_urls():
    rows = parse_channel_buttons("Sai | javascript:alert(1)\nĐúng | https://example.com")
    assert rows == [[("Đúng", "https://example.com")]]


def test_parse_channel_buttons_json():
    rows = parse_channel_buttons('[[{"text":"Join","url":"https://t.me/test"}]]')
    assert rows == [[("Join", "https://t.me/test")]]


def test_channel_due_uses_utc_iso_values():
    now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    assert is_channel_due((now - timedelta(seconds=1)).isoformat(), now=now)
    assert not is_channel_due((now + timedelta(seconds=1)).isoformat(), now=now)


def test_next_daily_pair_moves_to_next_day():
    now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    scheduled, deleted = channel_publisher.next_daily_pair(
        "2026-06-05T08:00:00+00:00",
        "2026-06-05T10:00:00+00:00",
        now=now,
    )

    assert scheduled.startswith("2026-06-06T08:00:00")
    assert deleted.startswith("2026-06-06T10:00:00")


def test_delete_channel_post_reschedules_daily_post(monkeypatch):
    events = []
    patches = []

    class FakeStore:
        def patch_channel_post(self, post_id, raw, status=None):
            patches.append((post_id, raw, status))
            return [raw | {"id": post_id}]

        def record_channel_post_event(self, post_id, event_type, message, details=None, bot_key="main"):
            events.append((post_id, event_type, message, details or {}))

    class FakeBot:
        async def delete_message(self, chat_id, message_id):
            return None

    monkeypatch.setattr(channel_publisher, "supabase_store", FakeStore())
    monkeypatch.setitem(sys.modules, "bot_instance", SimpleNamespace(bot=FakeBot()))

    row = {
        "id": 7,
        "target_chat_id": "-1001",
        "sent_message_id": "123",
        "status": "sent",
        "repeat_daily": True,
        "scheduled_at": "2026-06-05T08:00:00+00:00",
        "delete_at": "2026-06-05T10:00:00+00:00",
    }

    assert asyncio.run(channel_publisher.delete_channel_post(row))
    assert any("repeat_rescheduled" == item[1] for item in events)
    assert any(item[1].get("status") == "scheduled" for item in patches)
