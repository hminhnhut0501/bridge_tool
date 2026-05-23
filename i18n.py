from database import db

DEFAULT_LANGUAGE = "vi"


def normalize_language(value):
    return DEFAULT_LANGUAGE


def default_language():
    return DEFAULT_LANGUAGE


def get_user_language(user_id):
    return DEFAULT_LANGUAGE


def set_user_language(user_id, language):
    return DEFAULT_LANGUAGE


def localized_key(key, language):
    return f"{key}_VI"


def t_for_lang(language, key, default=""):
    vi_value = db.get_config(localized_key(key, DEFAULT_LANGUAGE), "")
    if str(vi_value).strip():
        return vi_value
    return db.get_config(key, default)


def t(user_or_id, key, default=""):
    return t_for_lang(DEFAULT_LANGUAGE, key, default)


def localize_page_id(page_id, language):
    return str(page_id or "").strip()
