import asyncio
import logging
import re
from datetime import datetime, time as datetime_time
from zoneinfo import ZoneInfo

from aiogram import Router

from database import db
from supabase_store import supabase_store
router = Router()
_LAST_SCHEDULE_STATE = {"new": None, "returning": None}


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


def payment_tier_enabled(tier: str):
    prefix = tier_prefix(tier)
    default = "ON" if prefix == "RETURNING" else "OFF"
    return config_enabled(f"AUTO_PAYMENT_{prefix}_ENABLED", default)


def payment_tier_schedule_enabled(tier: str):
    prefix = tier_prefix(tier)
    return config_enabled(f"AUTO_PAYMENT_{prefix}_SCHEDULE_ENABLED", "ON")


def payment_tier_windows(tier: str):
    prefix = tier_prefix(tier)
    return db.get_config(f"AUTO_PAYMENT_{prefix}_WINDOWS", "22:00-06:00")


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


def auto_payment_schedule_active_for_tier(tier: str, now=None):
    if not payment_tier_enabled(tier):
        return False
    if not payment_tier_schedule_enabled(tier):
        return False
    windows = parse_windows(payment_tier_windows(tier))
    if not windows:
        return False
    local_now = now or datetime.now(bot_timezone())
    current_time = local_now.time().replace(tzinfo=None)
    return any(time_in_window(current_time, start, end) for start, end in windows)


def auto_payment_schedule_active(now=None):
    return auto_payment_schedule_active_for_tier("new", now)


def auto_payment_allowed_for_user(user_id, now=None):
    from modules.mod_payment import has_prior_paid_vip_order

    tier = "returning" if str(user_id).strip() and has_prior_paid_vip_order(user_id) else "new"
    return auto_payment_schedule_active_for_tier(tier, now)


def apply_auto_payment_schedule(now=None):
    new_active = auto_payment_schedule_active_for_tier("new", now)
    returning_active = auto_payment_schedule_active_for_tier("returning", now)
    audit_now = (now or datetime.now(bot_timezone())).strftime("%Y-%m-%d %H:%M:%S")
    audit_payload = {
        "AUTO_PAYMENT_NEW_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_NEW_LAST_CHECK_RESULT": "ON" if new_active else "OFF",
        "AUTO_PAYMENT_RETURNING_LAST_CHECK_AT": audit_now,
        "AUTO_PAYMENT_RETURNING_LAST_CHECK_RESULT": "ON" if returning_active else "OFF",
    }
    for key, value in audit_payload.items():
        db.set_config(key, value)
    state_changed = _LAST_SCHEDULE_STATE["new"] != new_active or _LAST_SCHEDULE_STATE["returning"] != returning_active
    _LAST_SCHEDULE_STATE["new"] = new_active
    _LAST_SCHEDULE_STATE["returning"] = returning_active
    if supabase_store.enabled and state_changed:
        try:
            supabase_store.record_support_event(
                "auto_payment_schedule_toggled",
                None,
                raw_data={
                    "new_active": new_active,
                    "returning_active": returning_active,
                    "scheduled_at": audit_now,
                    "new_window": payment_tier_windows("new"),
                    "returning_window": payment_tier_windows("returning"),
                },
            )
        except Exception as exc:
            logging.warning("⚠️ Không ghi được audit auto payment schedule: %s", exc)
    return {
        "new_active": new_active,
        "returning_active": returning_active,
        "state_changed": state_changed,
    }


async def auto_payment_schedule_worker():
    logging.info("⏰ Auto payment schedule worker đã khởi động.")
    while True:
        try:
            result = apply_auto_payment_schedule()
            if result["state_changed"]:
                logging.info(
                    "🔁 Auto payment schedule new=%s returning=%s",
                    "ON" if result["new_active"] else "OFF",
                    "ON" if result["returning_active"] else "OFF",
                )
        except Exception as exc:
            logging.error("❌ Auto payment schedule worker lỗi: %s", exc)
        await asyncio.sleep(poll_interval_seconds())
