from __future__ import annotations

import re
from dataclasses import dataclass


LIFETIME_DAYS = 3650
DEFAULT_DURATION_DAYS = 30
SUPPORTED_DURATION_KEYS = ("1M", "365D", "LIFE")


@dataclass(frozen=True)
class DurationSpec:
    key: str
    days: int | None
    label_vi: str
    label_en: str
    is_lifetime: bool = False


def normalize_duration_key(value) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return "1M"
    if text in {"1", "1M", "30", "30D", "30DAY", "30DAYS", "MONTH", "MONTHLY"}:
        return "1M"
    if text in {"365", "365D", "365DAY", "365DAYS", "YEAR", "ANNUAL", "ANNUALLY"}:
        return "365D"
    if text in {"LIFE", "LIFETIME", "TRONDOI", "TRỌN ĐỜI", "VĨNH VIỄN", "VINHVIEN"}:
        return "LIFE"
    if text.endswith("_1M"):
        return "1M"
    if text.endswith("_365D"):
        return "365D"
    if text.endswith("_LIFE"):
        return "LIFE"
    return text if text in SUPPORTED_DURATION_KEYS else "1M"


def duration_days_from_key(value) -> int:
    key = normalize_duration_key(value)
    if key == "LIFE":
        return LIFETIME_DAYS
    if key == "365D":
        return 365
    return DEFAULT_DURATION_DAYS


def duration_label(key, *, language: str = "vi") -> str:
    normalized = normalize_duration_key(key)
    if normalized == "LIFE":
        return "Trọn Đời" if language == "vi" else "Lifetime"
    if normalized == "365D":
        return "365 Ngày" if language == "vi" else "365 Days"
    return "30 Ngày" if language == "vi" else "30 Days"


def duration_spec(key) -> DurationSpec:
    normalized = normalize_duration_key(key)
    days = duration_days_from_key(normalized)
    if normalized == "LIFE":
        return DurationSpec(normalized, days, "Trọn Đời", "Lifetime", True)
    if normalized == "365D":
        return DurationSpec(normalized, days, "365 Ngày", "365 Days", False)
    return DurationSpec(normalized, days, "30 Ngày", "30 Days", False)


def is_lifetime_key(value) -> bool:
    return normalize_duration_key(value) == "LIFE"


def plan_key_for_duration(base_key: str, duration_key) -> str:
    normalized = normalize_duration_key(duration_key)
    base = str(base_key or "").strip().upper()
    if base.endswith(("_1M", "_365D", "_LIFE")):
        return re.sub(r"_(1M|365D|LIFE)$", f"_{normalized}", base)
    return f"{base}_{normalized}" if base else normalized

