from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from aiogram import BaseMiddleware
from datetime import datetime, time as datetime_time
import re
from html import unescape
import os
import time
from zoneinfo import ZoneInfo

from database import db
from bot_instance import bot, is_spamming
from i18n import t
from supabase_store import supabase_store

ADMIN_ID = 887869657  # Nhớ thay bằng ID Telegram của bạn nếu chưa đổi nhé
user_welcome_msgs = {}
_bio_link_cache = {}
_channel_schedule_cache = {"loaded_at": 0.0, "rows": []}
_bot_runtime_state_cache = {"loaded_at": 0.0, "row": None}
CHANNEL_SCHEDULE_CACHE_SECONDS = 60
BOT_RUNTIME_STATE_CACHE_SECONDS = 5


def invalidate_channel_schedule_cache():
    _channel_schedule_cache["loaded_at"] = 0.0
    _channel_schedule_cache["rows"] = []


def invalidate_bot_runtime_state_cache():
    _bot_runtime_state_cache["loaded_at"] = 0.0
    _bot_runtime_state_cache["row"] = None


def configured_admin_ids():
    raw = str(db.get_config("ADMIN_IDS", os.getenv("ADMIN_IDS", str(ADMIN_ID))) or "").strip()
    values = {str(ADMIN_ID)}
    for item in raw.replace(";", ",").split(","):
        item = item.strip()
        if item:
            values.add(item)
    return values


def is_admin_user(user_id):
    return str(user_id) in configured_admin_ids()

def config_enabled(key, default="OFF"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ"}

def config_int(key, default):
    try:
        return int(float(str(db.get_config(key, str(default)) or default).strip()))
    except Exception:
        return default

def bot_timezone():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")

def parse_active_hours(raw):
    windows = []
    for item in str(raw or "").replace("\n", ",").split(","):
        item = item.strip()
        if not item or "-" not in item:
            continue
        start_raw, end_raw = [part.strip() for part in item.split("-", 1)]
        try:
            start = datetime_time.fromisoformat(start_raw)
            end = datetime_time.fromisoformat(end_raw)
        except ValueError:
            continue
        windows.append((start, end))
    return windows

def time_in_active_window(current_time, start, end):
    if start == end:
        return True
    if start < end:
        return start <= current_time < end
    return current_time >= start or current_time < end

def truthy_value(value):
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}

def bot_schedule_active(now=None):
    return bool(bot_runtime_state(now).get("active"))

def bot_schedule_status(now=None):
    local_now = now or datetime.now(bot_timezone())
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip() or "Asia/Ho_Chi_Minh"
    maintenance_mode = config_enabled("MAINTENANCE_MODE", "OFF")
    fixed_schedule_enabled = config_enabled("BOT_SCHEDULE_ENABLED", "OFF")
    active_hours_raw = db.get_config("BOT_ACTIVE_HOURS", "08:00-23:00") or "08:00-23:00"
    windows = parse_active_hours(active_hours_raw)
    current_time = local_now.time().replace(tzinfo=None)
    linked_rows = channel_schedule_rows()
    has_linked_rows = bool(linked_rows)
    active_linked_post = None
    for row in linked_rows:
        scheduled_at = row.get("scheduled_at")
        delete_at = row.get("delete_at")
        if not scheduled_at or not delete_at:
            continue
        try:
            start = datetime.fromisoformat(str(scheduled_at).replace("Z", "+00:00")).astimezone(bot_timezone()).time().replace(tzinfo=None)
            end = datetime.fromisoformat(str(delete_at).replace("Z", "+00:00")).astimezone(bot_timezone()).time().replace(tzinfo=None)
        except ValueError:
            continue
        if time_in_active_window(current_time, start, end):
            active_linked_post = row
            break
    active_fixed_window = None
    if not active_linked_post and not has_linked_rows and fixed_schedule_enabled and windows:
        active_fixed_window = next((window for window in windows if time_in_active_window(current_time, window[0], window[1])), None)
    if active_linked_post:
        return {
            "source": "channel",
            "active": True,
            "sourcePostId": str(active_linked_post.get("id") or ""),
            "sourcePostTitle": active_linked_post.get("title") or f"Bài #{active_linked_post.get('id')}",
            "title": active_linked_post.get("title") or f"Bài #{active_linked_post.get('id')}",
            "window": f"{active_linked_post.get('scheduled_at')} → {active_linked_post.get('delete_at')}",
            "windowStart": active_linked_post.get("scheduled_at") or "",
            "windowEnd": active_linked_post.get("delete_at") or "",
            "detail": "Bài liên kết đang giữ bot online." + (" Bảo trì thủ công đang bị override." if maintenance_mode else ""),
            "timezone": timezone_name,
            "linkedCount": len(linked_rows),
            "maintenanceMode": maintenance_mode,
            "maintenanceOverride": maintenance_mode,
            "fixedScheduleEnabled": fixed_schedule_enabled,
            "activeHours": active_hours_raw,
        }
    if maintenance_mode:
        return {
            "source": "maintenance",
            "active": False,
            "sourcePostId": "",
            "sourcePostTitle": "Bảo trì thủ công",
            "title": "Bảo trì thủ công",
            "window": "Bot đang bị khóa thủ công",
            "windowStart": "",
            "windowEnd": "",
            "detail": "Không có bài liên kết nào đang active.",
            "timezone": timezone_name,
            "linkedCount": len(linked_rows),
            "maintenanceMode": maintenance_mode,
            "maintenanceOverride": False,
            "fixedScheduleEnabled": fixed_schedule_enabled,
            "activeHours": active_hours_raw,
        }
    if has_linked_rows:
        return {
            "source": "channel",
            "active": False,
            "sourcePostId": "",
            "sourcePostTitle": "Ngoài khung giờ bài liên kết",
            "title": "Ngoài khung giờ bài liên kết",
            "window": "Chưa có bài đăng liên kết đang active",
            "windowStart": "",
            "windowEnd": "",
            "detail": "Bot đang chờ khung giờ của bài đăng liên kết.",
            "timezone": timezone_name,
            "linkedCount": len(linked_rows),
            "maintenanceMode": maintenance_mode,
            "maintenanceOverride": False,
            "fixedScheduleEnabled": fixed_schedule_enabled,
            "activeHours": active_hours_raw,
        }
    if fixed_schedule_enabled and windows:
        window_text = next((f"{start.isoformat(timespec='minutes')} - {end.isoformat(timespec='minutes')}" for start, end in windows if time_in_active_window(current_time, start, end)), None)
        return {
            "source": "fixed",
            "active": bool(active_fixed_window),
            "sourcePostId": "",
            "sourcePostTitle": "BOT_ACTIVE_HOURS",
            "title": f"Khung giờ {window_text}" if window_text else "Ngoài khung giờ",
            "window": window_text or ", ".join(f"{start.isoformat(timespec='minutes')}-{end.isoformat(timespec='minutes')}" for start, end in windows),
            "windowStart": "",
            "windowEnd": "",
            "detail": "Bot chạy theo BOT_ACTIVE_HOURS.",
            "timezone": timezone_name,
            "linkedCount": len(linked_rows),
            "maintenanceMode": maintenance_mode,
            "maintenanceOverride": False,
            "fixedScheduleEnabled": fixed_schedule_enabled,
            "activeHours": active_hours_raw,
        }
    return {
        "source": "always",
        "active": True,
        "sourcePostId": "",
        "sourcePostTitle": "Luôn hoạt động",
        "title": "Luôn hoạt động",
        "window": "Không dùng lịch bot cố định",
        "windowStart": "",
        "windowEnd": "",
        "detail": "Không bật bảo trì và không có lịch bài liên kết.",
        "timezone": timezone_name,
        "linkedCount": len(linked_rows),
        "maintenanceMode": maintenance_mode,
        "maintenanceOverride": False,
        "fixedScheduleEnabled": fixed_schedule_enabled,
        "activeHours": active_hours_raw,
    }


def _bot_runtime_state_payload(now=None):
    status = bot_schedule_status(now)
    return {
        "id": "main",
        "effective_mode": status.get("source") or "always",
        "source": status.get("source") or "always",
        "active": bool(status.get("active")),
        "title": status.get("title") or "",
        "window": status.get("window") or "",
        "detail": status.get("detail") or "",
        "timezone": status.get("timezone") or "Asia/Ho_Chi_Minh",
        "linked_count": int(status.get("linkedCount") or 0),
        "maintenance_mode": bool(status.get("maintenanceMode")),
        "maintenance_override": bool(status.get("maintenanceOverride")),
        "fixed_schedule_enabled": bool(status.get("fixedScheduleEnabled")),
        "active_hours": status.get("activeHours") or "",
        "source_post_id": str(status.get("sourcePostId") or ""),
        "source_post_title": status.get("sourcePostTitle") or status.get("title") or "",
        "window_start": status.get("windowStart") or "",
        "window_end": status.get("windowEnd") or "",
        "raw_data": status,
    }


def bot_runtime_state(now=None):
    if not supabase_store.enabled:
        return _bot_runtime_state_payload(now)
    current_ts = time.time()
    cached_row = _bot_runtime_state_cache.get("row")
    if cached_row and current_ts - float(_bot_runtime_state_cache.get("loaded_at") or 0) <= BOT_RUNTIME_STATE_CACHE_SECONDS:
        return cached_row
    try:
        row = supabase_store.get_bot_runtime_state()
        if row:
            _bot_runtime_state_cache["row"] = row
            _bot_runtime_state_cache["loaded_at"] = current_ts
            return row
    except Exception as exc:
        print(f"⚠️ Không đọc được bot_runtime_state: {exc}")
    return _bot_runtime_state_payload(now)


def recompute_bot_runtime_state(now=None):
    payload = _bot_runtime_state_payload(now)
    if supabase_store.enabled:
        try:
            rows = supabase_store.upsert_bot_runtime_state(payload)
            invalidate_bot_runtime_state_cache()
            return rows[0] if rows else payload
        except Exception as exc:
            print(f"⚠️ Không ghi được bot_runtime_state: {exc}")
    invalidate_bot_runtime_state_cache()
    return payload

def _load_channel_schedule_rows():
    if not supabase_store.enabled:
        return []
    current_ts = time.time()
    if current_ts - float(_channel_schedule_cache.get("loaded_at") or 0) > CHANNEL_SCHEDULE_CACHE_SECONDS:
        _channel_schedule_cache["rows"] = supabase_store.list_bot_schedule_channel_posts(limit=200)
        _channel_schedule_cache["loaded_at"] = current_ts
    return _channel_schedule_cache.get("rows") or []

def channel_schedule_rows():
    try:
        return [
            row
            for row in _load_channel_schedule_rows()
            if truthy_value(row.get("enabled", True))
            and truthy_value(row.get("sync_bot_schedule"))
            and truthy_value(row.get("repeat_daily"))
        ]
    except Exception as exc:
        print(f"⚠️ Không đọc được lịch bot từ channel_posts: {exc}")
        return []

def channel_schedule_active(now=None, rows=None):
    local_now = now or datetime.now(bot_timezone())
    current_time = local_now.time().replace(tzinfo=None)
    posts = rows if rows is not None else channel_schedule_rows()
    for row in posts or []:
        scheduled_at = row.get("scheduled_at")
        delete_at = row.get("delete_at")
        if not scheduled_at or not delete_at:
            continue
        try:
            start = datetime.fromisoformat(str(scheduled_at).replace("Z", "+00:00")).astimezone(bot_timezone()).time().replace(tzinfo=None)
            end = datetime.fromisoformat(str(delete_at).replace("Z", "+00:00")).astimezone(bot_timezone()).time().replace(tzinfo=None)
        except ValueError:
            continue
        if time_in_active_window(current_time, start, end):
            return True
    return False

def bot_unavailable_reason(now=None):
    status = bot_runtime_state(now)
    if status.get("active"):
        return ""
    if str(status.get("effective_mode") or status.get("source") or "").strip().lower() == "maintenance":
        return "maintenance"
    if str(status.get("effective_mode") or status.get("source") or "").strip().lower() in {"channel", "fixed"}:
        return "schedule"
    return ""

def bio_link_patterns():
    raw = db.get_config("SELLER_BIO_LINK_PATTERNS", "http://,https://,t.me/,telegram.me/,linktr.ee,beacons.ai")
    return [item.strip().lower() for item in str(raw or "").replace("\n", ",").split(",") if item.strip()]

def text_has_blocked_link(text):
    lowered = str(text or "").lower()
    if not lowered:
        return False
    return any(pattern in lowered for pattern in bio_link_patterns())

async def blacklist_entry_for_user(user):
    if not config_enabled("BLACKLIST_ENABLED", "ON") or is_admin_user(user.id):
        return None

    if supabase_store.enabled:
        try:
            entry = supabase_store.get_blacklist_entry(user.id)
            if entry:
                return entry
        except Exception as exc:
            print(f"⚠️ Không đọc được blacklist Supabase: {exc}")

    if not config_enabled("SELLER_BIO_LINK_BLOCK_ENABLED", "OFF"):
        return None

    now_ts = time.time()
    ttl = max(config_int("BIO_LINK_CHECK_TTL_SECONDS", 86400), 60)
    last_checked = _bio_link_cache.get(user.id, 0)
    if now_ts - last_checked < ttl:
        return None
    _bio_link_cache[user.id] = now_ts

    try:
        chat = await bot.get_chat(user.id)
        bio = (
            getattr(chat, "bio", None)
            or getattr(chat, "about", None)
            or getattr(chat, "description", None)
            or ""
        )
    except Exception as exc:
        print(f"⚠️ Không đọc được bio user {user.id}: {exc}")
        return None

    if not text_has_blocked_link(bio):
        return None

    entry = {
        "telegram_user_id": str(user.id),
        "username": user.username or "",
        "full_name": user.full_name or "",
        "reason": "Bio có link seller bị chặn",
        "source": "bio_link",
        "is_active": True,
        "raw_data": {"bio": str(bio or "")[:500]},
    }
    if supabase_store.enabled:
        try:
            saved = supabase_store.upsert_blacklist(entry)
            if saved:
                return saved[0]
        except Exception as exc:
            print(f"⚠️ Không lưu được blacklist bio link: {exc}")
    return entry

def strip_html_tags(text):
    return unescape(re.sub(r"<[^>]*>", "", str(text or "")))

async def cleanup_welcome(user_id, chat_id):
    """Giữ tương thích code cũ, không xoá tin nhắn trong group."""
    user_welcome_msgs.pop(user_id, None)

async def safe_delete_private_message(message):
    """Chỉ xoá tin trong private chat, tuyệt đối không xoá message trong group."""
    if not message or getattr(message.chat, "type", None) != "private":
        return False

    try:
        await message.delete()
        return True
    except Exception:
        return False

async def check_protection(event):
    """Lớp khiên bảo vệ: Chống Spam click và Khóa Bot khi Bảo trì"""
    user_id = event.from_user.id
    unavailable_reason = bot_unavailable_reason()

    if unavailable_reason and not is_admin_user(user_id):
        if unavailable_reason == "schedule":
            msg = t(user_id, "MSG_OUTSIDE_ACTIVE_HOURS", "🛠 <b>BOT ĐANG NGOÀI GIỜ HOẠT ĐỘNG</b>\n\nBot hiện ở chế độ bảo trì. Vui lòng quay lại trong khung giờ hoạt động.").replace("\\n", "\n")
        else:
            msg = t(user_id, "MSG_MAINTENANCE", "🛠 <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nAdmin đang nâng cấp hệ thống. Bạn vui lòng quay lại sau ít phút nhé!").replace("\\n", "\n")
        alert_main = t(user_id, "ALERT_MAINTENANCE", "🛠 Bot đang bảo trì, vui lòng quay lại sau...")
        if isinstance(event, Message): 
            await event.answer(msg, parse_mode="HTML")
        else: 
            await event.answer(alert_main, show_alert=True)
        return False
        
    if is_spamming(user_id) and not is_admin_user(user_id):
        alert_spam = t(user_id, "ALERT_SPAM", "⏳ Vui lòng thao tác chậm lại!")
        if isinstance(event, CallbackQuery):
            await event.answer(alert_spam, show_alert=False)
        return False

    blocked = await blacklist_entry_for_user(event.from_user)
    if blocked:
        msg = t(
            user_id,
            "MSG_BLACKLIST_BLOCKED",
            "⛔ Tài khoản của bạn đang bị chặn sử dụng bot. Vui lòng liên hệ admin nếu cần hỗ trợ.",
        ).replace("\\n", "\n")
        alert = strip_html_tags(msg)[:180] or "Tài khoản của bạn đang bị chặn."
        if isinstance(event, CallbackQuery):
            await event.answer(alert, show_alert=True)
        elif config_enabled("BLACKLIST_NOTIFY_USER", "ON"):
            await event.answer(msg, parse_mode="HTML")
        return False
        
    return True

def is_private_interaction(event):
    if isinstance(event, Message):
        return getattr(event.chat, "type", None) == "private"
    if isinstance(event, CallbackQuery):
        message = getattr(event, "message", None)
        return getattr(getattr(message, "chat", None), "type", None) == "private"
    return False

class BotAvailabilityMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and is_private_interaction(event) and bot_unavailable_reason() and not is_admin_user(user.id):
            await check_protection(event)
            return None
        return await handler(event, data)

def setup_bot_availability(dp):
    middleware = BotAvailabilityMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)

def format_currency(amount):
    """Định dạng tiền hiển thị. Số tiền gửi PayOS vẫn luôn là VND integer ở payment flow."""
    try:
        value = float(amount)
        style = str(db.get_config("DISPLAY_CURRENCY_STYLE", "VND_LOWER")).strip().upper()
        suffix = str(db.get_config("DISPLAY_CURRENCY_SUFFIX", "đ"))
        compact_decimals = int(float(str(db.get_config("DISPLAY_CURRENCY_COMPACT_DECIMALS", "0")).strip()))
        if style == "VND_TEXT":
            return "{:,.0f} VNĐ".format(value).replace(",", ".")
        if style == "COMPACT_K":
            compact = value / 1000
            return f"{compact:,.{compact_decimals}f}K".replace(",", ".")
        if style == "CUSTOM_SUFFIX":
            return "{:,.0f} {}".format(value, suffix).replace(",", ".")
        return "{:,.0f}đ".format(value).replace(",", ".")
    except Exception:
        return f"{amount}Đ"

async def smart_display(event, text, reply_markup, img=None):
    """Hàm xuất giao diện thông minh (Giữ lại để phục vụ cho trang /me)"""
    msg_updating = db.get_config("MSG_UPDATING", "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>")
    final_text = str(text).strip() if text else msg_updating
    final_img = str(img).strip() if img else None

    try:
        if isinstance(event, Message):
            if final_img and len(final_img) > 10:
                await event.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await event.answer(text=final_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await safe_delete_private_message(event.message)
            
            if final_img and len(final_img) > 10:
                await event.message.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await event.message.answer(text=final_text, reply_markup=reply_markup, parse_mode="HTML")
            await event.answer()
                
    except TelegramBadRequest as e:
        if "parse entities" in str(e).lower() or "can't parse entities" in str(e).lower() or "tag" in str(e).lower():
            fallback_text = strip_html_tags(final_text)
            if isinstance(event, Message):
                await event.answer(fallback_text, reply_markup=reply_markup, parse_mode=None)
            else:
                await event.message.answer(fallback_text, reply_markup=reply_markup, parse_mode=None)
                await event.answer()
        else:
            print(f"❌ Lỗi xuất giao diện: {e}")
    except Exception as e:
        print(f"❌ Lỗi xuất giao diện: {e}")
