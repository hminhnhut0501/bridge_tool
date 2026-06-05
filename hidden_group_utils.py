import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import config_utils
import database
from supabase_store import supabase_store

REQUIREMENT_NONE = "NONE"
REQUIREMENT_SVIP_ACTIVE = "SVIP_ACTIVE"
REQUIREMENT_SVIP_LIFETIME = "SVIP_LIFETIME"
REQUIREMENT_PLAN_TOKEN_ACTIVE = "PLAN_TOKEN_ACTIVE"
REQUIREMENT_PLAN_TOKEN_LIFETIME = "PLAN_TOKEN_LIFETIME"

PLAN_TOKEN_PREFIX = "HG:"
PLAN_TOKEN_TAG_PREFIX = "[PT:"
DEFAULT_HIDDEN_1M_DAYS = 30
DEFAULT_HIDDEN_LIFETIME_DAYS = 3650


def _timezone():
    timezone_name = str(_db().get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def now_local():
    return datetime.now(_timezone()).replace(tzinfo=None)


def normalize_text(value):
    return str(value or "").strip()


def normalize_key_text(value):
    return normalize_text(value).upper()


def normalize_chat_id(value):
    raw = normalize_text(value)
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def parse_int(value, default=0):
    try:
        raw = normalize_text(value).replace(",", ".")
        return int(float(raw)) if raw else default
    except Exception:
        return default


def parse_number(value, default=0):
    try:
        raw = normalize_text(value).replace(",", ".")
        number = float(raw)
        return int(number) if number.is_integer() else round(number, 2)
    except Exception:
        return default


def parse_bool(value, default=False):
    raw = normalize_key_text(value)
    if not raw:
        return default
    return raw in {"ON", "TRUE", "YES", "1", "ACTIVE", "BẬT", "BAT"}


def parse_datetime(value):
    raw = normalize_text(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            parsed = parsed.astimezone(_timezone()).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _db():
    return getattr(config_utils, "db", None) or getattr(database, "db")


def ensure_hidden_supabase_enabled():
    if not supabase_store.enabled:
        raise RuntimeError("Hidden groups yêu cầu Supabase. Hãy chạy migration SQL mới nhất và cấu hình SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.")


def main_group_matches_plan(group_no, plan_name):
    btn_name = _db().get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")
    plan_upper = normalize_key_text(plan_name)
    if "FULL" in plan_upper or "SVIP" in plan_upper:
        return True
    if f"G{group_no}" in plan_upper:
        return True
    plan_text = normalize_match_text(plan_name)
    btn_text = normalize_match_text(btn_name)
    if btn_text and (btn_text in plan_text or plan_text in btn_text):
        return True
    plan_tokens = set(significant_group_tokens(plan_name))
    btn_tokens = set(significant_group_tokens(btn_name))
    return bool(btn_tokens and btn_tokens.issubset(plan_tokens)) or bool(plan_tokens and plan_tokens.issubset(btn_tokens))


def normalize_match_text(value):
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def significant_group_tokens(value):
    ignored = {
        "vip", "svip", "full", "goi", "nhom", "group", "ngay", "thang",
        "tron", "doi", "prive", "plus", "premium", "signature", "hang", "cu",
    }
    return [token for token in normalize_match_text(value).split() if token and token not in ignored and not token.isdigit()]


def build_hidden_plan_token(hidden_group_id, duration_key):
    duration = "LIFE" if normalize_key_text(duration_key) == "LIFE" else "1M"
    return f"{PLAN_TOKEN_PREFIX}{normalize_text(hidden_group_id)}:{duration}"


def embed_plan_token(plan_name, plan_token):
    clean_name = strip_plan_token(plan_name)
    token = normalize_text(plan_token)
    if not token:
        return clean_name
    return f"{clean_name} {PLAN_TOKEN_TAG_PREFIX}{token}]".strip()


def extract_plan_token(plan_name, explicit_plan_token=""):
    token = normalize_text(explicit_plan_token)
    if token:
        return token
    name = normalize_text(plan_name)
    start = name.rfind(PLAN_TOKEN_TAG_PREFIX)
    if start == -1 or not name.endswith("]"):
        return ""
    return normalize_text(name[start + len(PLAN_TOKEN_TAG_PREFIX):-1])


def strip_plan_token(plan_name):
    name = normalize_text(plan_name)
    start = name.rfind(PLAN_TOKEN_TAG_PREFIX)
    if start == -1 or not name.endswith("]"):
        return name
    return name[:start].rstrip()


def display_plan_name(plan_name):
    return strip_plan_token(plan_name)


def hidden_plan_duration_key(plan_token):
    token = normalize_key_text(plan_token)
    if not token.startswith(PLAN_TOKEN_PREFIX):
        return ""
    parts = token.split(":")
    return parts[-1] if len(parts) >= 3 else ""


def hidden_plan_group_id(plan_token):
    token = normalize_text(plan_token)
    if not normalize_key_text(token).startswith(PLAN_TOKEN_PREFIX):
        return ""
    parts = token.split(":")
    return normalize_text(parts[1]) if len(parts) >= 3 else ""


def is_hidden_plan_token(plan_token):
    return normalize_key_text(plan_token).startswith(PLAN_TOKEN_PREFIX)


def _normalize_hidden_group(item):
    group_id = normalize_text(item.get("id") or item.get("group_id") or item.get("slug"))
    name = normalize_text(item.get("name") or item.get("title"))
    return {
        "id": group_id,
        "name": name,
        "description": normalize_text(item.get("description")),
        "chat_id": normalize_chat_id(item.get("chat_id") or item.get("group_chat_id")),
        "price_1m_vnd": parse_number(item.get("price_1m_vnd"), 0),
        "price_life_vnd": parse_number(item.get("price_life_vnd"), 0),
        "price_1m_usd": parse_number(item.get("price_1m_usd"), 0),
        "price_life_usd": parse_number(item.get("price_life_usd"), 0),
        "duration_1m_days": max(1, parse_int(item.get("duration_1m_days"), DEFAULT_HIDDEN_1M_DAYS)),
        "lifetime_days": max(3650, parse_int(item.get("lifetime_days"), DEFAULT_HIDDEN_LIFETIME_DAYS)),
        "image_url": normalize_text(item.get("image_url")),
        "requirement_type": normalize_key_text(item.get("requirement_type") or REQUIREMENT_NONE) or REQUIREMENT_NONE,
        "requirement_value": normalize_text(item.get("requirement_value")),
        "sort_order": parse_int(item.get("sort_order"), 0),
        "is_active": bool(item.get("is_active")) if isinstance(item.get("is_active"), bool) else parse_bool(item.get("is_active"), True),
        "created_at": normalize_text(item.get("created_at")),
        "updated_at": normalize_text(item.get("updated_at")),
    }


def _normalize_hidden_code(item):
    raw_group_ids = item.get("group_ids") or item.get("visible_group_ids") or []
    if isinstance(raw_group_ids, str):
        try:
            parsed = json.loads(raw_group_ids)
            raw_group_ids = parsed if isinstance(parsed, list) else []
        except Exception:
            raw_group_ids = [part.strip() for part in raw_group_ids.split(",") if part.strip()]
    return {
        "code": normalize_key_text(item.get("code") or item.get("Code")),
        "name": normalize_text(item.get("name")),
        "description": normalize_text(item.get("description")),
        "scope_type": normalize_key_text(item.get("scope_type") or "SELECTED_GROUPS") or "SELECTED_GROUPS",
        "group_ids": [normalize_text(group_id) for group_id in raw_group_ids if normalize_text(group_id)],
        "requirement_type": normalize_key_text(item.get("requirement_type") or ""),
        "requirement_value": normalize_text(item.get("requirement_value")),
        "max_uses": parse_int(item.get("max_uses"), 0),
        "used_count": parse_int(item.get("used_count"), 0),
        "valid_from": normalize_text(item.get("valid_from")),
        "valid_until": normalize_text(item.get("valid_until")),
        "is_active": bool(item.get("is_active")) if isinstance(item.get("is_active"), bool) else parse_bool(item.get("is_active"), True),
        "created_at": normalize_text(item.get("created_at")),
        "updated_at": normalize_text(item.get("updated_at")),
    }


def _normalize_hidden_redemption(item):
    return {
        "id": normalize_text(item.get("id")),
        "code": normalize_key_text(item.get("code")),
        "telegram_user_id": normalize_text(item.get("telegram_user_id")),
        "full_name": normalize_text(item.get("full_name")),
        "username": normalize_text(item.get("username")),
        "revealed_group_ids": list(item.get("revealed_group_ids") or []),
        "created_at": normalize_text(item.get("created_at")),
    }


def list_hidden_groups(include_inactive=True):
    ensure_hidden_supabase_enabled()
    groups = [_normalize_hidden_group(item) for item in supabase_store.list_hidden_groups()]
    groups.sort(key=lambda item: (item.get("sort_order", 0), item.get("name", "")))
    if include_inactive:
        return groups
    return [item for item in groups if item.get("is_active")]


def get_hidden_group(hidden_group_id):
    target = normalize_text(hidden_group_id)
    if not target:
        return None
    for item in list_hidden_groups(include_inactive=True):
        if item.get("id") == target:
            return item
    return None


def upsert_hidden_group(raw):
    ensure_hidden_supabase_enabled()
    item = _normalize_hidden_group(raw or {})
    if not item["id"]:
        raise ValueError("Thiếu id hidden group.")
    if not item["name"]:
        raise ValueError("Thiếu tên hidden group.")
    if not item["chat_id"]:
        raise ValueError("Thiếu chat_id hidden group.")
    return supabase_store.upsert_hidden_group(item)


def delete_hidden_group(hidden_group_id):
    ensure_hidden_supabase_enabled()
    target = normalize_text(hidden_group_id)
    if not target:
        return []
    return supabase_store.delete_hidden_group(target)


def list_hidden_codes(include_inactive=True):
    ensure_hidden_supabase_enabled()
    codes = [_normalize_hidden_code(item) for item in supabase_store.list_hidden_codes()]
    codes.sort(key=lambda item: (item.get("code", ""), item.get("name", "")))
    if include_inactive:
        return codes
    return [item for item in codes if item.get("is_active")]


def get_hidden_code(code):
    target = normalize_key_text(code)
    if not target:
        return None
    for item in list_hidden_codes(include_inactive=True):
        if item.get("code") == target:
            return item
    return None


def upsert_hidden_code(raw):
    ensure_hidden_supabase_enabled()
    item = _normalize_hidden_code(raw or {})
    if not item["code"]:
        raise ValueError("Thiếu mã hidden code.")
    return supabase_store.upsert_hidden_code(item)


def mark_hidden_code_used(code):
    hidden_code = get_hidden_code(code)
    if not hidden_code:
        return []
    hidden_code["used_count"] = parse_int(hidden_code.get("used_count"), 0) + 1
    return upsert_hidden_code(hidden_code)


def delete_hidden_code(code):
    ensure_hidden_supabase_enabled()
    target = normalize_key_text(code)
    if not target:
        return []
    return supabase_store.delete_hidden_code(target)


def list_hidden_redemptions(limit=500):
    ensure_hidden_supabase_enabled()
    rows = [_normalize_hidden_redemption(item) for item in supabase_store.list_hidden_code_redemptions(limit=limit)]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[:limit]


def record_hidden_code_redemption(code, telegram_user_id, full_name="", username="", revealed_group_ids=None):
    ensure_hidden_supabase_enabled()
    payload = {
        "code": normalize_key_text(code),
        "telegram_user_id": normalize_text(telegram_user_id),
        "full_name": normalize_text(full_name),
        "username": normalize_text(username),
        "revealed_group_ids": [normalize_text(group_id) for group_id in (revealed_group_ids or []) if normalize_text(group_id)],
        "created_at": now_local().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return supabase_store.record_hidden_code_redemption(payload)


def hidden_code_available_groups(hidden_code):
    if not hidden_code:
        return []
    groups = list_hidden_groups(include_inactive=False)
    if hidden_code.get("scope_type") == "ALL_ACTIVE_HIDDEN_GROUPS":
        return groups
    allowed = set(hidden_code.get("group_ids") or [])
    return [item for item in groups if item.get("id") in allowed]


def hidden_code_requirement(hidden_code, hidden_group=None):
    requirement_type = normalize_key_text((hidden_code or {}).get("requirement_type"))
    requirement_value = normalize_text((hidden_code or {}).get("requirement_value"))
    if requirement_type:
        return requirement_type, requirement_value
    if hidden_group:
        return normalize_key_text(hidden_group.get("requirement_type") or REQUIREMENT_NONE), normalize_text(hidden_group.get("requirement_value"))
    return REQUIREMENT_NONE, ""


def is_lifetime_order(plan_name="", plan_token=""):
    token = extract_plan_token(plan_name, plan_token)
    if token:
        if normalize_key_text(token).endswith(":LIFE"):
            return True
        if normalize_key_text(token) == "FULL_LIFE":
            return True
    upper = normalize_key_text(strip_plan_token(plan_name))
    return "TRỌN ĐỜI" in upper or "LIFE" in upper


def is_svip_order(plan_name="", plan_token=""):
    token = normalize_key_text(extract_plan_token(plan_name, plan_token))
    if token.startswith(PLAN_TOKEN_PREFIX):
        return False
    if token.startswith("FULL_"):
        return True
    upper = normalize_key_text(strip_plan_token(plan_name))
    return "FULL" in upper or "SVIP" in upper


def order_is_active(status, expire_at, plan_name="", plan_token="", now=None):
    if normalize_key_text(status) != "PAID":
        return False
    if is_lifetime_order(plan_name, plan_token):
        return True
    expire_date = parse_datetime(expire_at)
    if expire_date:
        return expire_date > (now or now_local())
    return bool(normalize_text(expire_at))


def _orders_for_user(user_id):
    if supabase_store.enabled:
        return supabase_store.list_paid_orders_for_user(user_id, limit=500)
    current_db = _db()
    if hasattr(current_db, "connect"):
        current_db.connect()
    rows = current_db.users_sheet.get_all_values()
    items = []
    for row in rows[1:]:
        if len(row) < 8:
            continue
        items.append({
            "order_id": row[0],
            "telegram_user_id": row[1],
            "full_name": row[2],
            "plan_name": row[3],
            "amount": row[4],
            "status": row[5],
            "paid_at": row[6],
            "expire_at": row[7],
            "sale_id": row[8] if len(row) > 8 else "",
            "original_amount": row[9] if len(row) > 9 else "",
        })
    return [item for item in items if normalize_text(item.get("telegram_user_id")) == normalize_text(user_id)]


def user_has_requirement(user_id, requirement_type, requirement_value=""):
    rule = normalize_key_text(requirement_type or REQUIREMENT_NONE) or REQUIREMENT_NONE
    if rule == REQUIREMENT_NONE:
        return True
    now = now_local()
    token_target = normalize_key_text(requirement_value)
    for order in _orders_for_user(user_id):
        plan_name = order.get("plan_name", "")
        plan_token = order.get("plan_token", "")
        if not order_is_active(order.get("status", ""), order.get("expire_at"), plan_name, plan_token, now):
            continue
        token = normalize_key_text(extract_plan_token(plan_name, plan_token))
        if rule == REQUIREMENT_SVIP_ACTIVE and is_svip_order(plan_name, plan_token):
            return True
        if rule == REQUIREMENT_SVIP_LIFETIME and is_svip_order(plan_name, plan_token) and is_lifetime_order(plan_name, plan_token):
            return True
        if rule == REQUIREMENT_PLAN_TOKEN_ACTIVE and token and token == token_target:
            return True
        if rule == REQUIREMENT_PLAN_TOKEN_LIFETIME and token and token == token_target and is_lifetime_order(plan_name, plan_token):
            return True
    return False


def validate_hidden_code_for_user(code, user_id):
    hidden_code = get_hidden_code(code)
    if not hidden_code:
        return None, "Mã không tồn tại."
    if not hidden_code.get("is_active"):
        return None, "Mã này đang tắt."
    now = now_local()
    valid_from = parse_datetime(hidden_code.get("valid_from"))
    valid_until = parse_datetime(hidden_code.get("valid_until"))
    if valid_from and now < valid_from:
        return None, "Mã này chưa đến thời gian mở."
    if valid_until and now > valid_until:
        return None, "Mã này đã hết hạn."
    max_uses = parse_int(hidden_code.get("max_uses"), 0)
    used_count = parse_int(hidden_code.get("used_count"), 0)
    if max_uses > 0 and used_count >= max_uses:
        return None, "Mã này đã hết lượt dùng."
    groups = hidden_code_available_groups(hidden_code)
    if not groups:
        return None, "Mã hợp lệ nhưng chưa có hidden group nào đang bật."
    requirement_type, requirement_value = hidden_code_requirement(hidden_code)
    if not user_has_requirement(user_id, requirement_type, requirement_value):
        if requirement_type == REQUIREMENT_SVIP_LIFETIME:
            return None, "Bạn cần có gói SVIP trọn đời để mở mã này."
        if requirement_type == REQUIREMENT_SVIP_ACTIVE:
            return None, "Bạn cần có gói SVIP còn hạn để mở mã này."
        return None, "Tài khoản của bạn chưa đủ điều kiện để mở mã này."
    return hidden_code, ""


def hidden_duration_price(hidden_group, duration_key, currency="VND"):
    duration = normalize_key_text(duration_key)
    if normalize_key_text(currency) == "USD":
        return parse_number(hidden_group.get("price_life_usd" if duration == "LIFE" else "price_1m_usd"), 0)
    return parse_number(hidden_group.get("price_life_vnd" if duration == "LIFE" else "price_1m_vnd"), 0)


def hidden_duration_days(hidden_group, duration_key):
    return parse_int(hidden_group.get("lifetime_days" if normalize_key_text(duration_key) == "LIFE" else "duration_1m_days"), DEFAULT_HIDDEN_LIFETIME_DAYS if normalize_key_text(duration_key) == "LIFE" else DEFAULT_HIDDEN_1M_DAYS)


def build_hidden_plan_name(hidden_group, duration_key):
    duration_label = "Trọn Đời" if normalize_key_text(duration_key) == "LIFE" else f"{hidden_duration_days(hidden_group, duration_key)} Ngày"
    base_name = f"Hidden - {hidden_group.get('name')} - {duration_label}"
    return embed_plan_token(base_name, build_hidden_plan_token(hidden_group.get("id"), duration_key))


def resolve_plan_groups(plan_name, plan_token=""):
    token = extract_plan_token(plan_name, plan_token)
    if is_hidden_plan_token(token):
        hidden_group = get_hidden_group(hidden_plan_group_id(token))
        if hidden_group and hidden_group.get("chat_id"):
            return [(hidden_group.get("chat_id"), hidden_group.get("name"))]
        return []
    groups = []
    for group_no in config_utils.group_numbers():
        if not main_group_matches_plan(group_no, plan_name):
            continue
        gid = normalize_chat_id(_db().get_config(f"ID_G{group_no}"))
        if gid:
            groups.append((gid, _db().get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")))
    return groups
