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

def bot_schedule_active(now=None):
    if not config_enabled("BOT_SCHEDULE_ENABLED", "OFF"):
        return True
    windows = parse_active_hours(db.get_config("BOT_ACTIVE_HOURS", "08:00-23:00"))
    if not windows:
        return True
    local_now = now or datetime.now(bot_timezone())
    return any(time_in_active_window(local_now.time().replace(tzinfo=None), start, end) for start, end in windows)

def bot_unavailable_reason(now=None):
    if config_enabled("MAINTENANCE_MODE", "OFF"):
        return "maintenance"
    if not bot_schedule_active(now):
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
