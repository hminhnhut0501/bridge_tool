from aiogram import Router
from aiogram.types import Message

from message_classifier_utils import classify_private_message
from supabase_store import supabase_store
from support_utils import (
    create_support_case_from_private_message,
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
