import re
from collections import OrderedDict


def normalize_config_key(value):
    return re.sub(r"[\u200b-\u200d\ufeff]", "", str(value or "")).strip().upper()


EXPLICIT_KEY_ALIASES = {
    "PLAN_FULL_1M": "PLAN_ALL_ACCESS_30D",
    "PLAN_FULL_LIFE": "PLAN_ALL_ACCESS_LIFE",
    "PLAN_UPSELL_FULL": "PLAN_UPSELL_ALL_ACCESS",
    "PRICE_SVIP_30D": "PRICE_ALL_ACCESS_30D",
    "PRICE_SVIP_LIFE": "PRICE_ALL_ACCESS_LIFE",
    "PRICE_SVIP_30D_USD": "PRICE_ALL_ACCESS_30D_USD",
    "PRICE_SVIP_LIFE_USD": "PRICE_ALL_ACCESS_LIFE_USD",
    "BTN_VIEW_SVIP_PAGE": "BTN_VIEW_ALL_ACCESS_PAGE",
    "BTN_UPGRADE_SVIP": "BTN_UPGRADE_ALL_ACCESS",
    "BTN_BUY_SVIP_LIFE": "BTN_BUY_ALL_ACCESS_LIFE",
    "BTN_BUY_SVIP_30D": "BTN_BUY_ALL_ACCESS_30D",
    "TXT_SVIP_DESCRIPTION": "TXT_ALL_ACCESS_DESCRIPTION",
    "IMG_SVIP_PAGE": "IMG_ALL_ACCESS_PAGE",
    "PLAN_G_1M": "PLAN_COLLECTION_30D",
    "PLAN_G_LIFE": "PLAN_COLLECTION_LIFE",
    "PLAN_UPSELL_G": "PLAN_UPSELL_COLLECTION",
    "BTN_BUY_1M": "BTN_BUY_COLLECTION_30D",
    "BTN_BUY_LIFE": "BTN_BUY_COLLECTION_LIFE",
}


_LEGACY_PATTERN_ALIASES = (
    (re.compile(r"^BTN_G(\d+)$"), lambda m: f"BTN_COLLECTION_G{m.group(1)}"),
    (re.compile(r"^BTN_G(\d+)_EN$"), lambda m: f"BTN_COLLECTION_G{m.group(1)}_EN"),
    (re.compile(r"^ID_G(\d+)$"), lambda m: f"ID_COLLECTION_G{m.group(1)}"),
    (re.compile(r"^DESC_G(\d+)$"), lambda m: f"DESC_COLLECTION_G{m.group(1)}"),
    (re.compile(r"^DESC_G(\d+)_EN$"), lambda m: f"DESC_COLLECTION_G{m.group(1)}_EN"),
    (re.compile(r"^PRICE_G(\d+)_(1M|LIFE)$"), lambda m: f"PRICE_COLLECTION_G{m.group(1)}_{'30D' if m.group(2) == '1M' else 'LIFE'}"),
    (re.compile(r"^PRICE_G(\d+)_(1M|LIFE)_USD$"), lambda m: f"PRICE_COLLECTION_G{m.group(1)}_{'30D' if m.group(2) == '1M' else 'LIFE'}_USD"),
)


def canonical_config_key(key):
    normalized = normalize_config_key(key)
    if not normalized:
        return ""
    if normalized in EXPLICIT_KEY_ALIASES:
        return EXPLICIT_KEY_ALIASES[normalized]
    for pattern, transform in _LEGACY_PATTERN_ALIASES:
        match = pattern.match(normalized)
        if match:
            return transform(match)
    return normalized


def legacy_config_keys(key):
    canonical = canonical_config_key(key)
    if not canonical:
        return []
    legacy_keys = [legacy for legacy, new in EXPLICIT_KEY_ALIASES.items() if new == canonical]
    for pattern, transform in (
        (re.compile(r"^BTN_COLLECTION_G(\d+)$"), lambda m: f"BTN_G{m.group(1)}"),
        (re.compile(r"^BTN_COLLECTION_G(\d+)_EN$"), lambda m: f"BTN_G{m.group(1)}_EN"),
        (re.compile(r"^ID_COLLECTION_G(\d+)$"), lambda m: f"ID_G{m.group(1)}"),
        (re.compile(r"^DESC_COLLECTION_G(\d+)$"), lambda m: f"DESC_G{m.group(1)}"),
        (re.compile(r"^DESC_COLLECTION_G(\d+)_EN$"), lambda m: f"DESC_G{m.group(1)}_EN"),
        (re.compile(r"^PRICE_COLLECTION_G(\d+)_(30D|LIFE)$"), lambda m: f"PRICE_G{m.group(1)}_{'1M' if m.group(2) == '30D' else 'LIFE'}"),
        (re.compile(r"^PRICE_COLLECTION_G(\d+)_(30D|LIFE)_USD$"), lambda m: f"PRICE_G{m.group(1)}_{'1M' if m.group(2) == '30D' else 'LIFE'}_USD"),
    ):
        match = pattern.match(canonical)
        if match:
            legacy_keys.append(transform(match))
            break
    return legacy_keys


def config_lookup_keys(key):
    canonical = canonical_config_key(key)
    requested = normalize_config_key(key)
    keys = []
    for candidate in (canonical, requested):
        if candidate and candidate not in keys:
            keys.append(candidate)
    for legacy_key in legacy_config_keys(canonical):
        if legacy_key and legacy_key not in keys:
            keys.append(legacy_key)
    return keys


def canonicalize_config_row(row):
    item = dict(row or {})
    key = canonical_config_key(item.get("key"))
    if not key:
        return None
    item["key"] = key
    return item


def canonicalize_config_rows(rows):
    grouped = OrderedDict()
    for row in rows or []:
        item = canonicalize_config_row(row)
        if not item:
            continue
        key = item["key"]
        source_key = normalize_config_key((row or {}).get("key"))
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = item
            continue
        if source_key == key and normalize_config_key(existing.get("key")) != key:
            grouped[key] = item
    return list(grouped.values())


def config_write_items(key, value):
    canonical = canonical_config_key(key)
    if not canonical:
        raise ValueError("Config key không hợp lệ")
    items = []
    seen = set()
    for candidate in [canonical, *legacy_config_keys(canonical)]:
        candidate = normalize_config_key(candidate)
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        items.append({"key": candidate, "value": value})
    return items
