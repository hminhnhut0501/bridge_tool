import asyncio
import logging
import re
from datetime import datetime, time as datetime_time
from zoneinfo import ZoneInfo

from aiogram import Router

from database import db
from supabase_store import supabase_store
router = Router()
_LAST_SCHEDULE_STATE = {"vi": {"new": None, "returning": None}, "en": {"new": None, "returning": None}}


def bot_timezone():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def config_enabled(key, default="OFF"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ", "BẬT", "BAT"}


def tier_key(tier: str):
    normalized = str(tier or "").strip().lower()
    return "returning" if normalized in {"returning", "old", "existing", "customer_cu"} else "new"


def tier_prefix(tier: str):
    return "RETURNING" if tier_key(tier) == "returning" else "NEW"


def customer_segment_key(user_id=None, preferred_language=None):
    try:
        from i18n import get_user_language

        language = str(preferred_language or "").strip().lower()
        if language in {"vi", "en"}:
            return "en" if language == "en" else "vi"
        return "en" if get_user_language(user_id) == "en" else "vi"
    except Exception:
        return "vi"


def segment_prefix(segment: str):
    return "EN" if str(segment or "").strip().lower() == "en" else "VI"


def legacy_tier_enabled_key(tier: str):
    return f"AUTO_PAYMENT_{tier_prefix(tier)}_ENABLED"


def legacy_tier_schedule_key(tier: str):
    return f"AUTO_PAYMENT_{tier_prefix(tier)}_SCHEDULE_ENABLED"


def legacy_tier_windows_key(tier: str):
    return f"AUTO_PAYMENT_{tier_prefix(tier)}_WINDOWS"


def _payment_tier_enabled(segment: str, tier: str):
    prefix = tier_prefix(tier)
    segment_key = f"AUTO_PAYMENT_{segment_prefix(segment)}_{prefix}_ENABLED"
    default = "ON" if prefix == "RETURNING" else "OFF"
    value = db.get_config(segment_key, "")
    if str(value).strip() != "":
        return config_enabled(segment_key, default)
    return config_enabled(legacy_tier_enabled_key(tier), default)


def _payment_tier_schedule_enabled(segment: str, tier: str):
    segment_key = f"AUTO_PAYMENT_{segment_prefix(segment)}_{tier_prefix(tier)}_SCHEDULE_ENABLED"
    value = db.get_config(segment_key, "")
    if str(value).strip() != "":
        return config_enabled(segment_key, "ON")
    return config_enabled(legacy_tier_schedule_key(tier), "ON")


def _payment_tier_windows(segment: str, tier: str):
    segment_key = f"AUTO_PAYMENT_{segment_prefix(segment)}_{tier_prefix(tier)}_WINDOWS"
    value = db.get_config(segment_key, "")
    if str(value).strip() != "":
        return value
    return db.get_config(legacy_tier_windows_key(tier), "22:00-06:00")


def payment_tier_enabled_for_user(user_id, tier: str):
    return _payment_tier_enabled(customer_segment_key(user_id), tier)


def payment_tier_schedule_enabled_for_user(user_id, tier: str):
    return _payment_tier_schedule_enabled(customer_segment_key(user_id), tier)


def payment_tier_windows_for_user(user_id, tier: str):
    return _payment_tier_windows(customer_segment_key(user_id), tier)


def payment_tier_enabled_vi(tier: str):
    return _payment_tier_enabled("vi", tier)


def payment_tier_schedule_enabled_vi(tier: str):
    return _payment_tier_schedule_enabled("vi", tier)


def payment_tier_windows_vi(tier: str):
    return _payment_tier_windows("vi", tier)


def payment_tier_enabled_en(tier: str):
    return _payment_tier_enabled("en", tier)


def payment_tier_schedule_enabled_en(tier: str):
    return _payment_tier_schedule_enabled("en", tier)


def payment_tier_windows_en(tier: str):
    return _payment_tier_windows("en", tier)


def payment_tier_enabled(tier: str):
    return payment_tier_enabled_vi(tier)


def poll_interval_seconds():
    try:
        value = int(str(db.get_config("AUTO_PAYMENT_SCHEDULE_POLL_SECONDS", "60") or "60").strip())
        return max(value, 30)
    except Exception:
        return 60


def parse_windows(raw):
    windows = []
    for item in re.split(r"[\n,]+", str(raw or "")):
        item = item.strip()
        if not item or "-" not in item:
            continue
        start_raw, end_raw = [part.strip() for part in item.split("-", 1)]
        try:
            windows.append((datetime_time.fromisoformat(start_raw), datetime_time.fromisoformat(end_raw)))
        except ValueError:
            continue
    return windows


def time_in_window(current_time, start, end):
    if start == end:
        return True
    if start < end:
        return start <= current_time < end
    return current_time >= start or current_time < end


def auto_payment_schedule_active_for_tier(tier: str, now=None, segment="vi"):
    if not _payment_tier_enabled(segment, tier):
        return False
    if not _payment_tier_schedule_enabled(segment, tier):
        return True
    windows = parse_windows(_payment_tier_windows(segment, tier))
    if not windows:
        return False
    local_now = now or datetime.now(bot_timezone())
    current_time = local_now.time().replace(tzinfo=None)
    return any(time_in_window(current_time, start, end) for start, end in windows)


def auto_payment_schedule_active(now=None):
    return auto_payment_schedule_active_for_tier("new", now)


def auto_payment_gate_snapshot_for_user(user_id, now=None, preferred_language=None):
    from modules.mod_payment import has_prior_paid_vip_order

    tier = "returning" if str(user_id).strip() and has_prior_paid_vip_order(user_id) else "new"
    segment = customer_segment_key(user_id, preferred_language=preferred_language)
    enabled = _payment_tier_enabled(segment, tier)
    schedule_enabled = _payment_tier_schedule_enabled(segment, tier)
    windows_raw = str(_payment_tier_windows(segment, tier) or "").strip()
    windows = parse_windows(windows_raw)
    local_now = now or datetime.now(bot_timezone())
    current_time = local_now.time().replace(tzinfo=None)
    in_window = any(time_in_window(current_time, start, end) for start, end in windows) if windows else False

    if not enabled:
        allowed = False
        reason = "tier_disabled"
    elif not schedule_enabled:
        allowed = True
        reason = "schedule_bypassed"
    elif not windows:
        allowed = False
        reason = "window_missing"
    elif not in_window:
        allowed = False
        reason = "outside_window"
    else:
        allowed = True
        reason = "inside_window"

    return {
        "allowed": allowed,
        "reason": reason,
        "segment": segment,
        "tier": tier,
        "enabled": enabled,
        "schedule_enabled": schedule_enabled,
        "windows": windows_raw,
        "now": local_now.strftime("%Y-%m-%d %H:%M:%S"),
    }


def auto_payment_allowed_for_user(user_id, now=None, preferred_language=None):
    snapshot = auto_payment_gate_snapshot_for_user(user_id, now=now, preferred_language=preferred_language)
    if not snapshot["allowed"]:
        logging.warning(
            "AUTO_PAY gate block user=%s segment=%s tier=%s main=%s schedule=%s windows=%s reason=%s now=%s",
            str(user_id),
            snapshot["segment"],
            snapshot["tier"],
            "ON" if snapshot["enabled"] else "OFF",
            "ON" if snapshot["schedule_enabled"] else "OFF",
            snapshot["windows"] or "-",
            snapshot["reason"],
            snapshot["now"],
        )
    return snapshot["allowed"]


def apply_auto_payment_schedule(now=None):
    vi_new_active = auto_payment_schedule_active_for_tier("new", now, segment="vi")
    vi_returning_active = auto_payment_schedule_active_for_tier("returning", now, segment="vi")
    en_new_active = auto_payment_schedule_active_for_tier("new", now, segment="en")
    en_returning_active = auto_payment_schedule_active_for_tier("returning", now, segment="en")
    audit_now = (now or datetime.now(bot_timezone())).strftime("%Y-%m-%d %H:%M:%S")
    audit_payload = {
        "AUTO_PAYMENT_VI_NEW_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_VI_NEW_LAST_CHECK_RESULT": "ON" if vi_new_active else "OFF",
        "AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_RESULT": "ON" if vi_returning_active else "OFF",
        "AUTO_PAYMENT_EN_NEW_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_EN_NEW_LAST_CHECK_RESULT": "ON" if en_new_active else "OFF",
        "AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_RESULT": "ON" if en_returning_active else "OFF",
        "AUTO_PAYMENT_NEW_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_NEW_LAST_CHECK_RESULT": "ON" if vi_new_active else "OFF",
        "AUTO_PAYMENT_RETURNING_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_RETURNING_LAST_CHECK_RESULT": "ON" if vi_returning_active else "OFF",
    }
    for key, value in audit_payload.items():
        db.set_config(key, value)
    state_changed = (
        _LAST_SCHEDULE_STATE["vi"]["new"] != vi_new_active
        or _LAST_SCHEDULE_STATE["vi"]["returning"] != vi_returning_active
        or _LAST_SCHEDULE_STATE["en"]["new"] != en_new_active
        or _LAST_SCHEDULE_STATE["en"]["returning"] != en_returning_active
    )
    _LAST_SCHEDULE_STATE["vi"]["new"] = vi_new_active
    _LAST_SCHEDULE_STATE["vi"]["returning"] = vi_returning_active
    _LAST_SCHEDULE_STATE["en"]["new"] = en_new_active
    _LAST_SCHEDULE_STATE["en"]["returning"] = en_returning_active
    if supabase_store.enabled and state_changed:
        try:
            supabase_store.record_support_event(
                "auto_payment_schedule_toggled",
                None,
                raw_data={
                    "vi_new_active": vi_new_active,
                    "vi_returning_active": vi_returning_active,
                    "en_new_active": en_new_active,
                    "en_returning_active": en_returning_active,
                    "scheduled_at": audit_now,
                    "vi_new_window": _payment_tier_windows("vi", "new"),
                    "vi_returning_window": _payment_tier_windows("vi", "returning"),
                    "en_new_window": _payment_tier_windows("en", "new"),
                    "en_returning_window": _payment_tier_windows("en", "returning"),
                },
            )
        except Exception as exc:
            logging.warning("⚠️ Không ghi được audit auto payment schedule: %s", exc)
    return {
        "vi_new_active": vi_new_active,
        "vi_returning_active": vi_returning_active,
        "en_new_active": en_new_active,
        "en_returning_active": en_returning_active,
        "new_active": vi_new_active,
        "returning_active": vi_returning_active,
        "state_changed": state_changed,
    }


async def auto_payment_schedule_worker():
    logging.info("⏰ Auto payment schedule worker đã khởi động.")
    while True:
        try:
            result = apply_auto_payment_schedule()
            if result["state_changed"]:
                logging.info(
                    "🔁 Auto payment schedule vi(new=%s returning=%s) en(new=%s returning=%s)",
                    "ON" if result["vi_new_active"] else "OFF",
                    "ON" if result["vi_returning_active"] else "OFF",
                    "ON" if result["en_new_active"] else "OFF",
                    "ON" if result["en_returning_active"] else "OFF",
                )
        except Exception as exc:
            logging.error("❌ Auto payment schedule worker lỗi: %s", exc)
        await asyncio.sleep(poll_interval_seconds())
