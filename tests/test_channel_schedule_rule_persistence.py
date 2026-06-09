from supabase_store import SupabaseStore


def test_patch_channel_post_preserves_schedule_flags_from_payload(monkeypatch):
    store = SupabaseStore()
    synced = []

    def fake_request(method, table, params=None, json=None, prefer=None):
        assert method == "PATCH"
        assert table == "channel_posts"
        return [{
            "id": 13,
            "bot_key": "main",
            "target_chat_id": "-1002841272060",
            "title": "test",
            "status": "scheduled",
            "scheduled_at": json["scheduled_at"],
            "delete_at": json["delete_at"],
            "enabled": True,
        }]

    monkeypatch.setattr(store, "_request", fake_request)

    import helpers

    monkeypatch.setattr(helpers, "invalidate_channel_schedule_cache", lambda: None)
    monkeypatch.setattr(helpers, "recompute_bot_runtime_state", lambda: None)
    monkeypatch.setattr(helpers, "sync_bot_schedule_rule_from_post", lambda row: synced.append(row))

    store.patch_channel_post("13", {
        "status": "scheduled",
        "scheduled_at": "2026-06-09T23:10:00+07:00",
        "delete_at": "2026-06-09T23:15:00+07:00",
        "repeat_daily": True,
        "sync_bot_schedule": True,
    })

    assert synced
    assert synced[0]["repeat_daily"] is True
    assert synced[0]["sync_bot_schedule"] is True
    assert synced[0]["scheduled_at"] == "2026-06-09T23:10:00+07:00"
    assert synced[0]["delete_at"] == "2026-06-09T23:15:00+07:00"
