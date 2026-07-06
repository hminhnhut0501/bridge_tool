from modules import mod_engine


def test_language_switch_is_enabled_by_default(monkeypatch):
    monkeypatch.setattr(mod_engine.db, "get_config", lambda key, default="": default)

    assert mod_engine.menu_action_enabled("set_lang:en")
    assert mod_engine.should_add_language_switch("main_menu")


def test_language_switch_toggle_hides_automatic_and_menu_builder_buttons(monkeypatch):
    values = {"LANGUAGE_SWITCH_ENABLED": "OFF"}
    monkeypatch.setattr(mod_engine.db, "get_config", lambda key, default="": values.get(key, default))

    assert mod_engine.menu_action_enabled("set_lang:en")
    assert mod_engine.menu_action_enabled("set_lang:vi")
    assert not mod_engine.should_add_language_switch("main_menu")


def test_language_switch_is_added_automatically_on_main_menu_and_en_page(monkeypatch):
    values = {"LANGUAGE_SWITCH_ENABLED": "ON"}
    monkeypatch.setattr(mod_engine.db, "get_config", lambda key, default="": values.get(key, default))

    assert not mod_engine.should_add_language_switch("policy_page")
    assert mod_engine.should_add_language_switch("main_menu")
    assert mod_engine.should_add_language_switch("main_menu_en")
