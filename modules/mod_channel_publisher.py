import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from supabase_store import _now_iso, supabase_store


LOGGER = logging.getLogger(__name__)


def parse_channel_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def is_channel_due(value, now=None):
    parsed = parse_channel_datetime(value)
    return bool(parsed and parsed <= (now or datetime.now(timezone.utc)))


def next_daily_pair(scheduled_at, delete_at, now=None):
    scheduled = parse_channel_datetime(scheduled_at)
    delete = parse_channel_datetime(delete_at)
    if not scheduled or not delete:
        return None, None
    current = now or datetime.now(timezone.utc)
    while scheduled <= current:
        scheduled += timedelta(days=1)
        delete += timedelta(days=1)
    return scheduled.isoformat(), delete.isoformat()


def _valid_url(value):
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme in {"http", "https", "tg"} and bool(parsed.netloc or parsed.scheme == "tg")


def parse_channel_buttons(raw_buttons):
    text = str(raw_buttons or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
            rows = []
            for row in data:
                if not isinstance(row, list):
                    continue
                buttons = []
                for item in row:
                    if not isinstance(item, dict):
                        continue
                    label = str(item.get("text") or item.get("label") or "").strip()
                    url = str(item.get("url") or "").strip()
                    if label and _valid_url(url):
                        buttons.append((label, url))
                if buttons:
                    rows.append(buttons)
            return rows
        except Exception:
            LOGGER.warning("Invalid channel button JSON.")
            return []

    rows = []
    for line in text.splitlines():
        button_row = []
        for chunk in line.strip().split("||"):
            parts = [part.strip() for part in chunk.split("|", 1)]
            if len(parts) == 2 and parts[0] and _valid_url(parts[1]):
                button_row.append((parts[0], parts[1]))
        if button_row:
            rows.append(button_row)
    return rows


def build_channel_markup(raw_buttons):
    rows = parse_channel_buttons(raw_buttons)
    if not rows:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, url=url) for label, url in row]
            for row in rows
        ]
    )


def channel_error_code(exc):
    text = str(exc).lower()
    if "not enough rights" in text or "administrator" in text or "can't remove" in text:
        return "missing_permission"
    if "chat not found" in text:
        return "chat_not_found"
    if "message to delete not found" in text:
        return "message_not_found"
    if "button" in text and "url" in text:
        return "invalid_button_url"
    return "telegram_error"


def _safe_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def _truthy(value):
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


async def publish_channel_post(row):
    row_id = row.get("id")
    chat_id = str(row.get("target_chat_id") or "").strip()
    content = str(row.get("content") or "").strip()
    original_status = str(row.get("status") or "draft").strip().lower()
    if not row_id or not chat_id or not content:
        return False

    claimed = supabase_store.patch_channel_post(
        row_id,
        {
            "status": "sending",
            "error": None,
            "error_code": None,
            "last_attempt_at": _now_iso(),
            "attempt_count": _safe_int(row.get("attempt_count")) + 1,
        },
        status=original_status,
    )
    if not claimed:
        return False

    supabase_store.record_channel_post_event(row_id, "send_started", "Bot bắt đầu gửi bài.")
    parse_mode = str(row.get("parse_mode") or "HTML").strip().upper()
    if parse_mode == "NONE":
        parse_mode = None
    try:
        from bot_instance import bot

        image_ref = str(row.get("image_ref") or "").strip()
        if image_ref:
            sent = await bot.send_photo(
                chat_id=chat_id,
                photo=image_ref,
                caption=content,
                parse_mode=parse_mode,
                reply_markup=build_channel_markup(row.get("buttons_text")),
            )
        else:
            sent = await bot.send_message(
                chat_id=chat_id,
                text=content,
                parse_mode=parse_mode,
                reply_markup=build_channel_markup(row.get("buttons_text")),
                disable_web_page_preview=bool(row.get("disable_web_page_preview")),
            )
        next_status = "delete_scheduled" if row.get("delete_at") else "sent"
        supabase_store.patch_channel_post(
            row_id,
            {
                "status": next_status,
                "sent_message_id": str(sent.message_id),
                "sent_at": _now_iso(),
                "error": None,
                "error_code": None,
            },
        )
        supabase_store.record_channel_post_event(row_id, "send_succeeded", "Telegram đã nhận bài.", {"message_id": sent.message_id})
        return True
    except (TelegramBadRequest, TelegramForbiddenError, Exception) as exc:
        supabase_store.patch_channel_post(
            row_id,
            {"status": "failed", "error": str(exc)[:1000], "error_code": channel_error_code(exc)},
        )
        supabase_store.record_channel_post_event(row_id, "send_failed", "Không gửi được bài.", {"error": str(exc)})
        LOGGER.warning("Cannot publish channel post %s to %s: %s", row_id, chat_id, exc)
        return False


async def delete_channel_post(row):
    row_id = row.get("id")
    chat_id = str(row.get("target_chat_id") or "").strip()
    message_id = _safe_int(row.get("sent_message_id"))
    original_status = str(row.get("status") or "").strip().lower()
    if not row_id or not chat_id or not message_id:
        return False

    claimed = supabase_store.patch_channel_post(
        row_id,
        {"status": "deleting", "error": None, "error_code": None},
        status=original_status,
    )
    if not claimed:
        return False

    supabase_store.record_channel_post_event(row_id, "delete_started", "Bot bắt đầu xóa bài.")
    try:
        from bot_instance import bot

        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        repeat_daily = _truthy(row.get("repeat_daily"))
        next_scheduled_at, next_delete_at = next_daily_pair(row.get("scheduled_at"), row.get("delete_at")) if repeat_daily else (None, None)
        if repeat_daily and next_scheduled_at and next_delete_at:
            supabase_store.patch_channel_post(
                row_id,
                {
                    "status": "scheduled",
                    "scheduled_at": next_scheduled_at,
                "delete_at": next_delete_at,
                "sent_message_id": None,
                "sent_at": None,
                "image_ref": row.get("image_ref") or None,
                "deleted_at": _now_iso(),
                "error": None,
                "error_code": None,
            },
        )
            supabase_store.record_channel_post_event(
                row_id,
                "repeat_rescheduled",
                "Đã lên lịch lại cho ngày kế tiếp.",
                {"scheduled_at": next_scheduled_at, "delete_at": next_delete_at},
            )
        else:
            supabase_store.patch_channel_post(
                row_id,
                {"status": "deleted", "deleted_at": _now_iso(), "error": None, "error_code": None},
            )
        supabase_store.record_channel_post_event(row_id, "delete_succeeded", "Đã xóa bài khỏi Telegram.")
        return True
    except (TelegramBadRequest, TelegramForbiddenError, Exception) as exc:
        supabase_store.patch_channel_post(
            row_id,
            {"status": "delete_failed", "error": str(exc)[:1000], "error_code": channel_error_code(exc)},
        )
        supabase_store.record_channel_post_event(row_id, "delete_failed", "Không xóa được bài.", {"error": str(exc)})
        LOGGER.warning("Cannot delete channel post %s from %s: %s", row_id, chat_id, exc)
        return False


async def channel_publisher_worker():
    logging.info("📮 Channel publisher worker đã khởi động.")
    await asyncio.sleep(10)
    while True:
        if not supabase_store.enabled:
            await asyncio.sleep(30)
            continue
        try:
            posts = supabase_store.list_channel_posts(limit=200)
            for row in posts:
                if not _truthy(row.get("enabled", True)):
                    continue
                status = str(row.get("status") or "draft").strip().lower()
                if status in {"pending", "queued"} or (status == "scheduled" and is_channel_due(row.get("scheduled_at"))):
                    await publish_channel_post(row)
                elif status in {"sent", "delete_scheduled"} and row.get("delete_at") and is_channel_due(row.get("delete_at")):
                    await delete_channel_post(row)
            await asyncio.sleep(5)
        except Exception as exc:
            logging.error("❌ Channel publisher worker lỗi: %s", exc)
            await asyncio.sleep(15)
