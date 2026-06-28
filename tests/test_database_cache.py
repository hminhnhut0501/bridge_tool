from database import Database


def test_get_config_forces_initial_reload(monkeypatch):
    db = Database()
    calls = []

    def fake_reload(force=False):
        calls.append(force)
        db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON"}
        db.last_reload_time = 123

    monkeypatch.setattr(db, "reload_config", fake_reload)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == [True]


def test_get_config_refreshes_stale_cache(monkeypatch):
    db = Database()
    db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "OFF"}
    db.last_reload_time = 0
    calls = []

    def fake_reload(force=False):
        calls.append(force)
        db.cache_config["AUTO_PAYMENT_EN_RETURNING_ENABLED"] = "ON"
        db.last_reload_time = 9999999999

    monkeypatch.setattr(db, "reload_config", fake_reload)
    monkeypatch.setattr("database.time.time", lambda: 61)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == [False]


def test_get_config_keeps_recent_cache_without_reload(monkeypatch):
    db = Database()
    db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON"}
    db.last_reload_time = 50
    calls = []

    monkeypatch.setattr(db, "reload_config", lambda force=False: calls.append(force))
    monkeypatch.setattr("database.time.time", lambda: 80)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == []
