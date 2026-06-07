from web_backend import parse_manual_expire_at


def test_parse_manual_expire_at_iso_datetime_local():
    parsed = parse_manual_expire_at("2026-06-07T12:30")

    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 6
    assert parsed.day == 7
    assert parsed.hour == 12
    assert parsed.minute == 30
    assert parsed.tzinfo is not None


def test_parse_manual_expire_at_slash_format():
    parsed = parse_manual_expire_at("07/06/2026 12:30")

    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 6
    assert parsed.day == 7
    assert parsed.hour == 12
    assert parsed.minute == 30
