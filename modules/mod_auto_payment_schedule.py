import asyncio
import logging
import re
from datetime import datetime, time as datetime_time
from zoneinfo import ZoneInfo

from aiogram import Router

from database import db
from supabase_store import supabase_store

router = Router()


def bot_timezone():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def config_enabled(key, default="OFF"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ", "BẬT", "BAT"}


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


def auto_payment_schedule_active(now=None):
    if not config_enabled("AUTO_PAYMENT_SCHEDULE_ENABLED", "ON"):
        return False
    windows = parse_windows(db.get_config("AUTO_PAYMENT_SCHEDULE_WINDOWS", "22:00-06:00"))
    if not windows:
        return False
    local_now = now or datetime.now(bot_timezone())
    current_time = local_now.time().replace(tzinfo=None)
    return any(time_in_window(current_time, start, end) for start, end in windows)


def apply_auto_payment_schedule(now=None):
    active = auto_payment_schedule_active(now)
    desired = "ON" if active else "OFF"
    keys = (
        "NEW_CUSTOMER_AUTO_PAYMENT_ENABLED",
        "RETURNING_CUSTOMER_AUTO_PAYMENT_ENABLED",
    )
    changed = []
    for key in keys:
        current = str(db.get_config(key, "OFF") or "OFF").strip().upper()
        if current != desired:
            db.set_config(key, desired)
            changed.append(key)
    audit_now = (now or datetime.now(bot_timezone())).strftime("%Y-%m-%d %H:%M:%S")
    audit_payload = {
        "AUTO_PAYMENT_SCHEDULE_LAST_TOGGLED_AT": audit_now,
        "AUTO_PAYMENT_SCHEDULE_LAST_TOGGLED_TO": desired,
        "AUTO_PAYMENT_SCHEDULE_LAST_TOGGLED_REASON": "AUTO_WINDOW_ACTIVE" if active else "AUTO_WINDOW_INACTIVE",
    }
    for key, value in audit_payload.items():
        db.set_config(key, value)
    if supabase_store.enabled:
        try:
            supabase_store.record_support_event(
                "auto_payment_schedule_toggled",
                None,
                raw_data={
                    "active": active,
                    "desired": desired,
                    "changed": changed,
                    "scheduled_at": audit_now,
                    "window": db.get_config("AUTO_PAYMENT_SCHEDULE_WINDOWS", "22:00-06:00"),
                },
            )
        except Exception as exc:
            logging.warning("⚠️ Không ghi được audit auto payment schedule: %s", exc)
    return {"active": active, "desired": desired, "changed": changed}


async def auto_payment_schedule_worker():
    logging.info("⏰ Auto payment schedule worker đã khởi động.")
    apply_auto_payment_schedule()
    while True:
        try:
            result = apply_auto_payment_schedule()
            if result["changed"]:
                logging.info(
                    "🔁 Auto payment schedule đã đổi %s -> %s cho %s",
                    "ON" if result["active"] else "OFF",
                    result["desired"],
                    ", ".join(result["changed"]),
                )
        except Exception as exc:
            logging.error("❌ Auto payment schedule worker lỗi: %s", exc)
        await asyncio.sleep(30)
