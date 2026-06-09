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
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-05T08:00:00+00:00",
        "delete_at": "2026-06-05T10:00:00+00:00",
    }

    assert asyncio.run(channel_publisher.delete_channel_post(row))
    assert any("repeat_rescheduled" == item[1] for item in events)
    scheduled_patch = next(item[1] for item in patches if item[1].get("status") == "scheduled")
    assert scheduled_patch["repeat_daily"] is True
    assert scheduled_patch["sync_bot_schedule"] is True


def test_publish_channel_post_preserves_schedule_flags(monkeypatch):
    events = []
    patches = []

    class FakeStore:
        def patch_channel_post(self, post_id, raw, status=None):
            patches.append((post_id, raw, status))
            return [raw | {"id": post_id}]

        def record_channel_post_event(self, post_id, event_type, message, details=None, bot_key="main"):
            events.append((post_id, event_type, message, details or {}))

    class FakeBot:
        async def send_message(self, **kwargs):
            return SimpleNamespace(message_id=777, **kwargs)

    monkeypatch.setattr(channel_publisher, "supabase_store", FakeStore())
    monkeypatch.setitem(sys.modules, "bot_instance", SimpleNamespace(bot=FakeBot()))

    row = {
        "id": 11,
        "target_chat_id": "-1001",
        "content": "Hello world",
        "buttons_text": "",
        "status": "scheduled",
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-05T08:00:00+00:00",
        "delete_at": "2026-06-05T10:00:00+00:00",
    }

    assert asyncio.run(channel_publisher.publish_channel_post(row))
    sent_patch = next(item[1] for item in patches if item[1].get("status") == "delete_scheduled")
    assert sent_patch["repeat_daily"] is True
    assert sent_patch["sync_bot_schedule"] is True


def test_publish_channel_post_uses_photo_caption_when_image_ref_exists(monkeypatch):
    events = []
    patches = []

    class FakeStore:
        def patch_channel_post(self, post_id, raw, status=None):
            patches.append((post_id, raw, status))
            return [raw | {"id": post_id}]

        def record_channel_post_event(self, post_id, event_type, message, details=None, bot_key="main"):
            events.append((post_id, event_type, message, details or {}))

    class FakeBot:
        async def send_photo(self, **kwargs):
            return SimpleNamespace(message_id=555, **kwargs)

    monkeypatch.setattr(channel_publisher, "supabase_store", FakeStore())
    monkeypatch.setitem(sys.modules, "bot_instance", SimpleNamespace(bot=FakeBot()))

    row = {
        "id": 9,
        "target_chat_id": "-1001",
        "content": "Hello <b>world</b>",
        "image_ref": "AgACAgQAAxkBAAIB",
        "buttons_text": "Xem | https://example.com",
        "status": "scheduled",
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "enabled": True,
    }

    assert asyncio.run(channel_publisher.publish_channel_post(row))
    assert any(item[1] == "send_succeeded" for item in events)
    assert any(item[1].get("status") == "sent" for item in patches)


def test_delete_channel_post_uses_notes_flags_when_columns_missing(monkeypatch):
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
        "id": 12,
        "target_chat_id": "-1001",
        "sent_message_id": "321",
        "status": "sent",
        "scheduled_at": "2026-06-05T08:00:00+00:00",
        "delete_at": "2026-06-05T10:00:00+00:00",
        "notes": "[[cp_flags:repeat_daily=1,sync_bot_schedule=1]]",
    }

    assert asyncio.run(channel_publisher.delete_channel_post(row))
    assert any(item[1].get("repeat_daily") is True for item in patches)
    assert any(item[1].get("sync_bot_schedule") is True for item in patches)
