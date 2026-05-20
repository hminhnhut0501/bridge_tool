from database import db
from supabase_store import supabase_store

DEFAULT_LANGUAGE = "vi"
SUPPORTED_LANGUAGES = {"vi", "en"}
_language_cache = {}


def user_language_config_key(user_key):
    return f"USER_LANGUAGE_{str(user_key or '').strip()}"


def is_missing_user_preferences_error(exc):
    text = str(exc)
    return "user_preferences" in text and ("PGRST205" in text or "Could not find the table" in text)


def normalize_language(value):
    lang = str(value or "").strip().lower()
    if lang in {"english", "eng", "gb", "us"}:
        return "en"
    if lang in {"vietnamese", "viet", "vn"}:
        return "vi"
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def default_language():
    return normalize_language(db.get_config("BOT_DEFAULT_LANGUAGE", DEFAULT_LANGUAGE))


def get_user_language(user_id):
    user_key = str(user_id or "").strip()
    if not user_key:
        return default_language()
    if user_key in _language_cache:
        return _language_cache[user_key]

    lang = default_language()
    has_user_pref = False
    if supabase_store.enabled:
        try:
            pref = supabase_store.get_user_preference(user_key)
            if pref:
                lang = normalize_language(pref.get("language") or lang)
                has_user_pref = True
        except Exception as exc:
            if not is_missing_user_preferences_error(exc):
                print(f"⚠️ Không đọc được language preference user {user_key}: {exc}")
    fallback_lang = db.get_config(user_language_config_key(user_key), "") if not has_user_pref else ""
    if fallback_lang:
        lang = normalize_language(fallback_lang)
    _language_cache[user_key] = lang
    return lang


def set_user_language(user_id, language):
    user_key = str(user_id or "").strip()
    lang = normalize_language(language)
    if not user_key:
        return lang
    _language_cache[user_key] = lang
    if supabase_store.enabled:
        try:
            supabase_store.upsert_user_preference(user_key, lang)
        except Exception as exc:
            if not is_missing_user_preferences_error(exc):
                print(f"⚠️ Không lưu được language preference user {user_key}: {exc}")
            try:
                db.set_config(user_language_config_key(user_key), lang)
            except Exception as config_exc:
                print(f"⚠️ Không lưu được fallback language preference user {user_key}: {config_exc}")
    return lang


def localized_key(key, language):
    lang = normalize_language(language)
    if lang == "en":
        return f"{key}_EN"
    if lang == "vi":
        return f"{key}_VI"
    return key


def t_for_lang(language, key, default=""):
    lang = normalize_language(language)
    if lang != DEFAULT_LANGUAGE:
        translated = db.get_config(localized_key(key, lang), "")
        if str(translated).strip():
            return translated
    default_lang_value = db.get_config(localized_key(key, DEFAULT_LANGUAGE), "")
    if str(default_lang_value).strip():
        return default_lang_value
    return db.get_config(key, default)


def t(user_or_id, key, default=""):
    user_id = getattr(user_or_id, "id", user_or_id)
    return t_for_lang(get_user_language(user_id), key, default)


def localize_page_id(page_id, language):
    lang = normalize_language(language)
    base = str(page_id or "").strip()
    if lang == DEFAULT_LANGUAGE:
        return base
    candidate = f"{base}_{lang}"
    return candidate if db.get_page(candidate) else base


def language_switch_text(language):
    lang = normalize_language(language)
    if lang == "en":
        return t_for_lang("en", "BTN_LANGUAGE_SWITCH_TO_VI", "🇻🇳 Tiếng Việt")
    return t_for_lang("vi", "BTN_LANGUAGE_SWITCH_TO_EN", "🇬🇧 English")


def language_switch_target(language):
    return "vi" if normalize_language(language) == "en" else "en"
