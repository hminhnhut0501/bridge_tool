import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from fastapi import FastAPI

from bot_links import bot_base_url
from supabase_store import supabase_store

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REMINDER_INTERVAL_SECONDS = int(float(os.getenv("REMINDER_INTERVAL_SECONDS", "10800")))
REMINDER_DAYS_DEFAULT = int(float(os.getenv("REMINDER_DAYS", "3")))
TIMEZONE_NAME = os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh")
BOT_NEW_URL = os.getenv("BOT_NEW_URL", "").strip() or bot_base_url()
WEBHOOK_DELETE_RETRIES = max(1, int(float(os.getenv("WEBHOOK_DELETE_RETRIES", "5"))))
WEBHOOK_DELETE_BACKOFF_SECONDS = max(1.0, float(os.getenv("WEBHOOK_DELETE_BACKOFF_SECONDS", "1.5")))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def now_local() -> datetime:
    try:
        tz = ZoneInfo(TIMEZONE_NAME)
    except Exception:
        tz = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime.now(tz).replace(tzinfo=None)


def parse_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed.astimezone(ZoneInfo(TIMEZONE_NAME)).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def link_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔁 Mở bot mới", url=BOT_NEW_URL))
    return kb.as_markup()


def reminder_text(plan_name: str, days_remaining: int, expire_at: str) -> str:
    return (
        f"⏰ Gói <b>{plan_name}</b> của bạn sẽ hết hạn sau <b>{days_remaining} ngày</b> nữa.\n\n"
        f"Vui lòng bấm nút bên dưới để chuyển sang bot mới và tiếp tục gia hạn.\n"
        f"Thời điểm hết hạn: <b>{expire_at or '-'}</b>"
    )


def expired_text(plan_name: str, expire_at: str) -> str:
    return (
        f"⚠️ Gói <b>{plan_name}</b> của bạn đã hết hạn.\n\n"
        "Bạn có thể bấm nút bên dưới để sang bot mới và gia hạn tiếp.\n"
        f"Thời điểm hết hạn: <b>{expire_at or '-'}</b>"
    )


@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "Chào bạn, đây là bot điều hướng và nhắc gia hạn cho hệ thống cũ.\n\n"
        "Bấm nút bên dưới để sang bot mới và tiếp tục sử dụng."
    )
    await message.answer(text, reply_markup=link_keyboard())


async def send_html_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=link_keyboard(), parse_mode="HTML")
    except Exception:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=link_keyboard(), parse_mode=None)


async def reminder_worker():
    if not supabase_store.enabled:
        logging.warning("Supabase chưa cấu hình, bridge tool chỉ chạy phần bot.")
        return
    while True:
        try:
            await run_reminders_once()
        except Exception as exc:
            logging.exception("Reminder worker lỗi: %s", exc)
        await asyncio.sleep(max(600, REMINDER_INTERVAL_SECONDS))


async def ensure_webhook_deleted():
    last_error = None
    for attempt in range(1, WEBHOOK_DELETE_RETRIES + 1):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logging.info("Webhook cũ đã được xóa trước khi polling.")
            return
        except Exception as exc:
            last_error = exc
            logging.warning("Không xóa được webhook ở lần %s/%s: %s", attempt, WEBHOOK_DELETE_RETRIES, exc)
            if attempt < WEBHOOK_DELETE_RETRIES:
                await asyncio.sleep(WEBHOOK_DELETE_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"Failed to delete webhook after {WEBHOOK_DELETE_RETRIES} retries: {last_error}")


async def run_reminders_once():
    now = now_local()
    today_str = now.strftime("%Y-%m-%d")
    reminder_days = max(0, int(REMINDER_DAYS_DEFAULT))
    limit = int(os.getenv("SCHEDULER_ORDER_LIMIT", "2000"))
    orders = supabase_store.list_scheduler_due_orders(now + timedelta(days=reminder_days), limit=limit)
    logging.info("Bridge scan %s đơn", len(orders))
    for order in orders:
        user_id = str(order.get("telegram_user_id") or "").strip()
        if not user_id:
            continue
        plan_name = str(order.get("plan_name") or "").strip() or "gói của bạn"
        status = str(order.get("status") or "").strip().upper()
        expire_at_raw = str(order.get("expire_at") or "").strip()
        expire_at = parse_datetime(expire_at_raw)
        if not expire_at:
            continue

        days_remaining = (expire_at.date() - now.date()).days
        last_reminder = str(order.get("last_reminder_date") or "").strip()
        if status == "PAID" and 0 <= days_remaining <= reminder_days and last_reminder != today_str:
            text = reminder_text(plan_name, days_remaining, expire_at_raw)
            try:
                await send_html_message(user_id, text)
                supabase_store.mark_reminder_sent(order["order_id"], today_str)
            except Exception as exc:
                logging.warning("Không gửi được reminder cho %s: %s", user_id, exc)
            continue

        if status == "EXPIRED" or expire_at <= now:
            expired_notice_at = str(order.get("expired_notice_at") or "").strip()
            if expired_notice_at:
                continue
            text = expired_text(plan_name, expire_at_raw)
            try:
                await send_html_message(user_id, text)
                supabase_store.mark_order_expired(order["order_id"], expired_notice_at=now.strftime("%Y-%m-%d %H:%M:%S"))
            except Exception as exc:
                logging.warning("Không gửi được expired notice cho %s: %s", user_id, exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN")
    bot_info = await bot.get_me()
    logging.info("Bridge bot ready: @%s", bot_info.username)
    await ensure_webhook_deleted()
    task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()), name="bridge_polling")
    reminder_task = asyncio.create_task(reminder_worker(), name="bridge_reminder_worker")
    try:
        yield
    finally:
        for current in (task, reminder_task):
            current.cancel()
        await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "supabase": supabase_store.enabled, "bot_new_url": BOT_NEW_URL}


@app.get("/")
async def root():
    return {"ok": True}
