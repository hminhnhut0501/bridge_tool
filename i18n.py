from database import db
from supabase_store import supabase_store

DEFAULT_LANGUAGE = "vi"
SUPPORTED_LANGUAGES = {"vi", "en"}
_language_cache = {}


def normalize_language(value):
    language = str(value or "").strip().lower()
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def default_language():
    return normalize_language(db.get_config("DEFAULT_LANGUAGE", DEFAULT_LANGUAGE))


def _language_from_paid_orders(user_id):
    if not supabase_store.enabled:
        return ""
    try:
        orders = supabase_store.list_paid_orders_for_user(user_id, limit=20)
    except Exception as exc:
        print(f"⚠️ Không đọc được orders để suy ra ngôn ngữ user {user_id}: {exc}")
        return ""
    if not orders:
        return ""
    for order in orders:
        metadata = order.get("metadata") if isinstance(order.get("metadata"), dict) else {}
        language = str(metadata.get("language") or "").strip().lower()
        if language in SUPPORTED_LANGUAGES:
            return language
        currency = str(order.get("payment_currency") or metadata.get("payment_currency") or "").strip().upper()
        provider = str(order.get("payment_provider") or metadata.get("payment_provider") or "").strip().upper()
        if currency == "USD" or provider in {"PAYPAL", "NOWPAYMENTS", "TRON_USDT", "BINANCE_PAY"}:
            return "en"
        if currency == "VND" or provider == "PAYOS":
            return "vi"
    return ""


def get_user_language(user_id):
    key = str(user_id or "").strip()
    if not key:
        return default_language()
    if key in _language_cache:
        return _language_cache[key]
    language = default_language()
    if supabase_store.enabled:
        try:
            preference = supabase_store.get_user_preference(key)
            language = normalize_language((preference or {}).get("language"))
        except Exception as exc:
            print(f"⚠️ Không đọc được language preference user {key}: {exc}")
    if language != "en":
        order_language = _language_from_paid_orders(key)
        if order_language == "en":
            language = "en"
    _language_cache[key] = language
    return language


def set_user_language(user_id, language):
    key = str(user_id or "").strip()
    normalized = normalize_language(language)
    if key:
        _language_cache[key] = normalized
        if supabase_store.enabled:
            try:
                supabase_store.upsert_user_preference(key, normalized)
            except Exception as exc:
                print(f"⚠️ Không lưu được language preference user {key}: {exc}")
    return normalized


def localized_key(key, language):
    return f"{key}_{normalize_language(language).upper()}"


def t_for_lang(language, key, default=""):
    language = normalize_language(language)
    localized_value = db.get_config(localized_key(key, language), "")
    if str(localized_value).strip():
        return localized_value
    base_value = db.get_config(key, "")
    if str(base_value).strip():
        return base_value
    return default


def t(user_or_id, key, default=""):
    user_id = getattr(user_or_id, "id", user_or_id)
    return t_for_lang(get_user_language(user_id), key, default)


def localize_page_id(page_id, language):
    page_id = str(page_id or "").strip()
    language = normalize_language(language)
    if not page_id or language == "vi":
        return page_id[:-3] if page_id.endswith("_en") else page_id
    if page_id.endswith("_en"):
        return page_id
    candidate = f"{page_id}_en"
    return candidate if db.get_page(candidate) else page_id
