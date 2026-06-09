from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

import helpers


@pytest.fixture(autouse=True)
def stub_bot_runtime_state_io(monkeypatch):
    monkeypatch.setattr(helpers.supabase_store, "get_bot_runtime_state", lambda: None, raising=False)
    monkeypatch.setattr(helpers.supabase_store, "upsert_bot_runtime_state", lambda raw: [raw], raising=False)


def local_datetime(hour, minute=0):
    return datetime(2026, 6, 4, hour, minute, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))


def test_parse_active_hours_accepts_multiple_windows_and_skips_invalid_values():
    windows = helpers.parse_active_hours("08:00-12:00, invalid, 13:30-23:00")

    assert len(windows) == 2
    assert windows[0][0].isoformat() == "08:00:00"
    assert windows[1][1].isoformat() == "23:00:00"


def test_time_in_active_window_supports_normal_and_overnight_windows():
    normal, overnight = helpers.parse_active_hours("08:00-12:00,20:00-02:00")

    assert helpers.time_in_active_window(local_datetime(9).time(), *normal)
    assert not helpers.time_in_active_window(local_datetime(12).time(), *normal)
    assert helpers.time_in_active_window(local_datetime(23).time(), *overnight)
    assert helpers.time_in_active_window(local_datetime(1).time(), *overnight)
    assert not helpers.time_in_active_window(local_datetime(3).time(), *overnight)


def test_bot_schedule_uses_configured_vietnam_hours(monkeypatch):
    values = {
        "BOT_SCHEDULE_ENABLED": "ON",
        "BOT_ACTIVE_HOURS": "08:00-12:00,13:30-23:00",
    }
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))

    assert helpers.bot_schedule_active(local_datetime(9))
    assert not helpers.bot_schedule_active(local_datetime(12, 30))
    assert helpers.bot_schedule_active(local_datetime(22, 59))
    assert not helpers.bot_schedule_active(local_datetime(23))


def test_invalid_or_disabled_schedule_fails_open(monkeypatch):
    values = {"BOT_SCHEDULE_ENABLED": "OFF", "BOT_ACTIVE_HOURS": "invalid"}
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))
    assert helpers.bot_schedule_active(local_datetime(3))

    values["BOT_SCHEDULE_ENABLED"] = "ON"
    assert helpers.bot_schedule_active(local_datetime(3))


def test_manual_maintenance_is_ignored_when_schedule_is_active(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "ON",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    linked_posts = [{
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-04T08:00:00+07:00",
        "delete_at": "2026-06-04T23:59:00+07:00",
    }]
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", lambda limit=200: linked_posts)
    helpers._channel_schedule_cache["loaded_at"] = 0
    helpers._channel_schedule_cache["rows"] = []

    assert helpers.bot_unavailable_reason(local_datetime(9)) == ""


def test_linked_schedule_overrides_manual_maintenance(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "ON",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    linked_posts = [{
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-04T08:00:00+07:00",
        "delete_at": "2026-06-04T23:00:00+07:00",
    }]
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", lambda limit=200: linked_posts)
    helpers._channel_schedule_cache["loaded_at"] = 0
    helpers._channel_schedule_cache["rows"] = []

    assert helpers.bot_unavailable_reason(local_datetime(12)) == ""
    status = helpers.bot_schedule_status(local_datetime(12))
    assert status["source"] == "channel"
    assert status["active"] is True
    assert status["maintenanceOverride"] is True


def test_channel_linked_schedule_overrides_built_in_hours(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "OFF",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    linked_posts = [{
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-04T08:00:00+07:00",
        "delete_at": "2026-06-04T23:00:00+07:00",
    }]
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", lambda limit=200: linked_posts)
    helpers._channel_schedule_cache["loaded_at"] = 0
    helpers._channel_schedule_cache["rows"] = []

    assert helpers.bot_schedule_active(local_datetime(12))
    assert not helpers.bot_schedule_active(local_datetime(23))


def test_manual_maintenance_wins_when_no_active_linked_schedule(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "ON",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    linked_posts = [{
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-04T08:00:00+07:00",
        "delete_at": "2026-06-04T10:00:00+07:00",
    }]
    monkeypatch.setattr(helpers.db, "get_config", lambda key, default="": values.get(key, default))
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", lambda limit=200: linked_posts)
    helpers._channel_schedule_cache["loaded_at"] = 0
    helpers._channel_schedule_cache["rows"] = []

    status = helpers.bot_schedule_status(local_datetime(12))
    assert status["source"] == "maintenance"
    assert status["active"] is False


def test_channel_schedule_cache_can_be_invalidated(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "OFF",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    calls = []
    linked_posts = [{
        "enabled": True,
        "repeat_daily": True,
        "sync_bot_schedule": True,
        "scheduled_at": "2026-06-04T08:00:00+07:00",
        "delete_at": "2026-06-04T23:00:00+07:00",
    }]

    def fake_get_config(key, default=""):
        return values.get(key, default)

    def fake_list_bot_schedule_rules(limit=200):
        calls.append(limit)
        return linked_posts

    monkeypatch.setattr(helpers.db, "get_config", fake_get_config)
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", fake_list_bot_schedule_rules)
    helpers._channel_schedule_cache["loaded_at"] = 0
    helpers._channel_schedule_cache["rows"] = []

    assert helpers.bot_schedule_active(local_datetime(12))
    assert calls == [200]

    helpers.invalidate_channel_schedule_cache()
    assert helpers.bot_schedule_active(local_datetime(12))
    assert calls == [200, 200]


def test_recompute_bot_runtime_state_writes_payload(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "OFF",
        "BOT_SCHEDULE_ENABLED": "ON",
        "BOT_ACTIVE_HOURS": "08:00-12:00",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    writes = []

    def fake_get_config(key, default=""):
        return values.get(key, default)

    def fake_list_bot_schedule_rules(limit=200):
        return [{
            "id": 99,
            "bot_key": "main",
            "enabled": True,
            "repeat_daily": True,
            "sync_bot_schedule": True,
            "active_from": "2026-06-04T08:00:00+07:00",
            "active_to": "2026-06-04T23:00:00+07:00",
            "title": "Bài giữ bot",
        }]

    def fake_upsert_bot_runtime_state(raw):
        writes.append(raw)
        return [raw]

    monkeypatch.setattr(helpers.db, "get_config", fake_get_config)
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", fake_list_bot_schedule_rules)
    monkeypatch.setattr(helpers.supabase_store, "upsert_bot_runtime_state", fake_upsert_bot_runtime_state)
    helpers.invalidate_bot_runtime_state_cache()

    state = helpers.recompute_bot_runtime_state(local_datetime(9))
    assert state["active"] is True
    assert state["source"] == "channel"
    assert state["effective_mode"] == "channel"
    assert writes and writes[0]["active"] is True


def test_bot_runtime_state_self_heals_stale_inactive_row(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "OFF",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }
    writes = []

    def fake_get_config(key, default=""):
        return values.get(key, default)

    def fake_list_bot_schedule_rules(limit=200):
        return [{
            "id": 100,
            "bot_key": "main",
            "enabled": True,
            "repeat_daily": True,
            "sync_bot_schedule": True,
            "active_from": "2026-06-04T08:00:00+07:00",
            "active_to": "2026-06-04T23:00:00+07:00",
            "title": "Bài giữ bot",
        }]

    def fake_get_bot_runtime_state():
        return {
            "id": "main",
            "effective_mode": "maintenance",
            "source": "maintenance",
            "active": False,
            "title": "Bảo trì thủ công",
            "window": "Bot đang bị khóa thủ công",
            "detail": "Stale row",
            "timezone": "Asia/Ho_Chi_Minh",
            "linked_count": 0,
            "maintenance_mode": True,
            "maintenance_override": False,
            "fixed_schedule_enabled": False,
            "active_hours": "08:00-23:00",
            "source_post_id": "",
            "source_post_title": "Bảo trì thủ công",
            "window_start": "",
            "window_end": "",
            "updated_at": "2026-06-04T00:00:00+00:00",
        }

    def fake_upsert_bot_runtime_state(raw):
        writes.append(raw)
        return [raw]

    monkeypatch.setattr(helpers.db, "get_config", fake_get_config)
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(helpers.supabase_store, "list_bot_schedule_rules", fake_list_bot_schedule_rules)
    monkeypatch.setattr(helpers.supabase_store, "get_bot_runtime_state", fake_get_bot_runtime_state)
    monkeypatch.setattr(helpers.supabase_store, "upsert_bot_runtime_state", fake_upsert_bot_runtime_state)
    helpers.invalidate_bot_runtime_state_cache()

    state = helpers.bot_runtime_state(local_datetime(9))
    assert state["active"] is True
    assert state["source"] == "channel"
    assert state["effective_mode"] == "channel"
    assert writes and writes[0]["active"] is True


def test_channel_schedule_rows_use_bot_schedule_rules_table(monkeypatch):
    values = {
        "MAINTENANCE_MODE": "OFF",
        "BOT_SCHEDULE_ENABLED": "OFF",
        "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
    }

    def fake_get_config(key, default=""):
        return values.get(key, default)

    monkeypatch.setattr(helpers.db, "get_config", fake_get_config)
    monkeypatch.setattr(helpers.supabase_store, "url", "https://example.supabase.co")
    monkeypatch.setattr(helpers.supabase_store, "key", "service-role")
    monkeypatch.setattr(
        helpers.supabase_store,
        "list_bot_schedule_rules",
        lambda limit=200: [{
            "id": 101,
            "bot_key": "main",
            "enabled": True,
            "repeat_daily": True,
            "sync_bot_schedule": True,
            "active_from": "2026-06-04T08:00:00+07:00",
            "active_to": "2026-06-04T23:00:00+07:00",
            "source_post_title": "Bài giữ bot",
        }],
    )
    helpers.invalidate_channel_schedule_cache()
    rows = helpers.channel_schedule_rows()
    assert len(rows) == 1
    state = helpers.bot_schedule_status(local_datetime(9))
    assert state["source"] == "channel"
    assert state["active"] is True
