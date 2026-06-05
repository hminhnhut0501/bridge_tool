from datetime import datetime, timedelta, timezone

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
