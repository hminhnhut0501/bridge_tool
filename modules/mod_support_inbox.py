import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot_instance import bot
from helpers import create_background_task
from message_classifier_utils import classify_private_message
from supabase_store import supabase_store
from support_utils import (
    create_support_case_from_private_message,
    support_admin_presence_text,
    render_support_inbox_ready_text,
    support_inbox_connecting_text,
    support_inbox_status_enabled,
    support_inbox_status_frame_delay_ms,
    support_inbox_status_frame_list,
    support_inbox_status_total_ms,
    support_inbox_enabled,
)

router = Router()


def _message_text(message: Message) -> str:
    text = str(message.text or message.caption or "").strip()
    if text:
        return text
    if message.photo:
        return "[photo]"
    if message.document:
        return "[document]"
    if message.video:
        return "[video]"
    if message.voice:
        return "[voice]"
    if message.audio:
        return "[audio]"
    if message.sticker:
        return "[sticker]"
    return "[message]"


def _is_private_user_message(message: Message) -> bool:
    if message.chat.type != "private":
        return False
    if not message.from_user or message.from_user.is_bot:
        return False
    text = str(message.text or "").strip()
    if text.startswith("/"):
        return False
    return bool(text or message.caption or message.photo or message.document or message.video or message.voice or message.audio or message.sticker)


def _is_support_inbox_private_message(message: Message) -> bool:
    if not _is_private_user_message(message):
        return False
    if not support_inbox_enabled():
        return False
    if not supabase_store.enabled:
        return False
    classified = classify_private_message(message)
    if classified["kind"] in {"coupon", "hidden", "activation"}:
        print(f"ℹ️ support inbox skip kind={classified['kind']} user={message.from_user.id} reason={classified['reason']}")
        return False
    return classified["kind"] == "support"


def has_open_support_ticket(user_id):
    if not supabase_store.enabled:
        return False
    try:
        return bool(supabase_store.get_open_support_ticket_by_user(user_id))
    except Exception:
        return False


async def _play_support_inbox_status_effect(*, chat_id: int, message_id: int, ticket_no: str):
    frames = support_inbox_status_frame_list(support_inbox_connecting_text())
    if not frames:
        return

    delay_ms = support_inbox_status_frame_delay_ms()
    total_visible_ms = support_inbox_status_total_ms(len(frames))
    animation_window_ms = max(delay_ms, total_visible_ms)
    elapsed_ms = 0
    frame_index = 0

    while elapsed_ms < animation_window_ms:
        frame = frames[frame_index % len(frames)]
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=frame)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                return
        except Exception:
            return
        sleep_ms = min(delay_ms, animation_window_ms - elapsed_ms)
        await asyncio.sleep(sleep_ms / 1000.0)
        elapsed_ms += sleep_ms
        frame_index += 1

    final_text = f"{support_admin_presence_text(True)}\n{render_support_inbox_ready_text(staff_name='Admin', ticket_no=ticket_no)}"
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=final_text)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            return
    except Exception:
        return


@router.message(_is_support_inbox_private_message)
async def support_private_inbox(message: Message):
    try:
        ticket, ticket_error = await create_support_case_from_private_message(
            message,
            source="private_user_message",
            subject=_message_text(message) or "Tin nhắn hỗ trợ",
        )
        if ticket_error:
            print(f"⚠️ Không tạo được support ticket cho user {message.from_user.id}: {ticket_error}")
        if ticket:
            print(f"ℹ️ support inbox ticket={ticket.get('ticket_no', '')} user={message.from_user.id}")
    except Exception as exc:
        print(f"⚠️ Không xử lý support inbox cho user {message.from_user.id}: {exc}")


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def support_group_legacy_passthrough(message: Message):
    return
