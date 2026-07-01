from types import SimpleNamespace

from database import Database


def test_get_config_forces_initial_reload(monkeypatch):
    db = Database()
    calls = []

    def fake_reload(force=False):
        calls.append(force)
        db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON"}
        db.last_config_reload_time = 123

    monkeypatch.setattr(db, "reload_config_cache", fake_reload)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == [True]


def test_get_config_refreshes_stale_cache(monkeypatch):
    db = Database()
    db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "OFF"}
    db.last_config_reload_time = 0
    calls = []

    def fake_reload(force=False):
        calls.append(force)
        db.cache_config["AUTO_PAYMENT_EN_RETURNING_ENABLED"] = "ON"
        db.last_config_reload_time = 9999999999

    monkeypatch.setattr(db, "reload_config_cache", fake_reload)
    monkeypatch.setattr("database.time.time", lambda: 61)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == [False]


def test_get_config_keeps_recent_cache_without_reload(monkeypatch):
    db = Database()
    db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON"}
    db.last_config_reload_time = 50
    calls = []

    monkeypatch.setattr(db, "reload_config_cache", lambda force=False: calls.append(force))
    monkeypatch.setattr("database.time.time", lambda: 80)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == []


def test_get_config_resolves_alias_keys():
    db = Database()
    db.cache_config = {"PRICE_ALL_ACCESS_LIFE": "499000"}
    db.last_config_reload_time = 9999999999

    assert db.get_config("PRICE_ALL_ACCESS_LIFE", "0") == "499000"
    assert db.get_config("PRICE_SVIP_LIFE", "0") == "499000"


def test_set_config_mirrors_alias_keys(monkeypatch):
    db = Database()
    db.backend = "supabase"
    writes = []

    def fake_set_configs(items):
        writes.append([dict(item) for item in items])
        return items

    monkeypatch.setattr("database.supabase_store", SimpleNamespace(enabled=True, set_configs=fake_set_configs))

    db.set_config("PRICE_SVIP_LIFE", "499000")

    assert writes
    written_keys = {item["key"] for item in writes[0]}
    assert "PRICE_ALL_ACCESS_LIFE" in written_keys
    assert "PRICE_SVIP_LIFE" in written_keys


def test_get_config_refreshes_only_config_cache_when_stale(monkeypatch):
    db = Database()
    db.cache_config = {"AUTO_PAYMENT_EN_RETURNING_ENABLED": "OFF"}
    db.pages_cache = {"main_menu": {"text": "cached"}}
    db.sales_cache = [{"sale_id": "cached"}]
    db.last_config_reload_time = 0
    db.last_pages_reload_time = 9999999999
    db.last_sales_reload_time = 9999999999
    calls = {"config": 0, "pages": 0, "sales": 0}

    def fake_reload_config_cache(force=False):
        calls["config"] += 1
        db.cache_config["AUTO_PAYMENT_EN_RETURNING_ENABLED"] = "ON"
        db.last_config_reload_time = 9999999999

    def fake_reload_pages_cache(force=False):
        calls["pages"] += 1

    def fake_reload_sales_cache(force=False):
        calls["sales"] += 1

    monkeypatch.setattr(db, "reload_config_cache", fake_reload_config_cache)
    monkeypatch.setattr(db, "reload_pages_cache", fake_reload_pages_cache)
    monkeypatch.setattr(db, "reload_sales_cache", fake_reload_sales_cache)
    monkeypatch.setattr("database.time.time", lambda: 61)

    assert db.get_config("AUTO_PAYMENT_EN_RETURNING_ENABLED", "OFF") == "ON"
    assert calls == {"config": 1, "pages": 0, "sales": 0}
