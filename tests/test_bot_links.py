from bot_links import normalize_bot_link_template


def test_normalize_bot_link_template_rewrites_legacy_bot_username(monkeypatch):
    monkeypatch.setenv("BOT_USERNAME", "hangcuvipbot")

    normalized = normalize_bot_link_template("https://t.me/hangcuprivebot?start={code}")

    assert normalized == "https://t.me/hangcuvipbot?start=act_{code}"


def test_normalize_bot_link_template_rewrites_legacy_placeholder(monkeypatch):
    monkeypatch.setenv("BOT_USERNAME", "hangcuvipbot")

    normalized = normalize_bot_link_template("t.me/your_bot_username")

    assert normalized == "https://t.me/hangcuvipbot?start=act_{code}"


def test_normalize_bot_link_template_preserves_license_payload(monkeypatch):
    monkeypatch.setenv("BOT_USERNAME", "hangcuvipbot")

    normalized = normalize_bot_link_template(
        "https://t.me/your_bot_username?start={code}",
        default_payload="lic_{code}",
    )

    assert normalized == "https://t.me/hangcuvipbot?start=lic_{code}"
