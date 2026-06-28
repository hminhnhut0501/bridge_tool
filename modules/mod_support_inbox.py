from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot_instance import bot
from helpers import is_admin_user
from support_utils import (
    create_support_ticket_for_user,
    post_support_ticket_to_group,
    is_support_group,
    record_support_event,
    record_support_message,
    support_delete_enabled,
    support_group_enabled,
    support_group_name,
)
from supabase_store import supabase_store

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


def _ticket_status_label(status: str) -> str:
    normalized = str(status or "").strip().lower()
    return {
        "open": "OPEN",
        "closed": "CLOSED",
        "pending": "PENDING",
        "resolved": "RESOLVED",
    }.get(normalized, normalized.upper() or "UNKNOWN")


def _resolve_ticket_from_group_message(message: Message):
    if not supabase_store.enabled:
        return None
    ticket = None
    try:
        if message.reply_to_message:
            ticket = supabase_store.get_support_ticket_by_manager_group_message_id(message.reply_to_message.message_id)
    except Exception as exc:
        print(f"⚠️ Không đọc được ticket theo group message id: {exc}")
    if not ticket and getattr(message, "message_thread_id", None):
        try:
            ticket = supabase_store.get_support_ticket_by_topic_thread_id(message.message_thread_id)
        except Exception as exc:
            print(f"⚠️ Không đọc được ticket theo thread id: {exc}")
    return ticket


def _resolve_support_message_for_delete(message: Message):
    if not supabase_store.enabled:
        return None, None
    if message.reply_to_message:
        try:
            row = supabase_store.get_support_message_by_manager_group_message_id(message.reply_to_message.message_id)
            if row:
                ticket = supabase_store.get_support_ticket_by_id(row.get("ticket_id"))
                return row, ticket
        except Exception as exc:
            print(f"⚠️ Không đọc được support message theo reply target: {exc}")
    if getattr(message, "message_thread_id", None):
        try:
            ticket = supabase_store.get_support_ticket_by_topic_thread_id(message.message_thread_id)
            if ticket:
                return None, ticket
        except Exception as exc:
            print(f"⚠️ Không đọc được ticket theo thread id khi delete: {exc}")
    return None, None


def _is_private_user_message(message: Message) -> bool:
    if message.chat.type != "private":
        return False
    if not message.from_user:
        return False
    if message.from_user.is_bot:
        return False
    text = str(message.text or "").strip()
    if text.startswith("/"):
        return False
    return bool(
        text
        or message.caption
        or message.photo
        or message.document
        or message.video
        or message.voice
        or message.audio
        or message.sticker
    )


async def _forward_private_message_to_group(message: Message):
    if not support_group_enabled():
        return
    if not supabase_store.enabled:
        return

    subject = _message_text(message)
    ticket, ticket_error = await create_support_ticket_for_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
        subject=subject,
        source="private_user_message",
        raw_data={
            "message_id": message.message_id,
            "chat_type": message.chat.type,
            "kind": "private_message",
        },
    )
    if not ticket:
        print(f"⚠️ Không tạo được ticket cho user {message.from_user.id}: {ticket_error}")
        return

    ticket_text = (
        f"📩 <b>Tin nhắn từ khách</b>\n"
        f"Ticket: <code>{ticket.get('ticket_no', '')}</code>\n"
        f"Khách: <b>{message.from_user.full_name}</b>\n"
        f"ID: <code>{message.from_user.id}</code>\n\n"
        f"{_message_text(message)}"
    )
    try:
        sent = await post_support_ticket_to_group(ticket, message_text=ticket_text)
    except Exception as exc:
        print(f"⚠️ Không forward ticket lên group: {exc}")
        return

    if sent:
        try:
            supabase_store.update_support_ticket(
                ticket["id"],
                {
                    "manager_group_message_id": sent.message_id,
                    "last_message_at": sent.date.isoformat() if getattr(sent, "date", None) else None,
                    "updated_at": sent.date.isoformat() if getattr(sent, "date", None) else None,
                },
            )
        except Exception as exc:
            print(f"⚠️ Không cập nhật ticket group message id: {exc}")
        try:
            await record_support_message(
                ticket["id"],
                "user_to_support",
                telegram_message_id=message.message_id,
                manager_group_message_id=sent.message_id,
                text=_message_text(message),
                payload={
                    "chat_id": str(message.chat.id),
                    "chat_type": message.chat.type,
                    "source": "private_user_message",
                },
            )
        except Exception as exc:
            print(f"⚠️ Không lưu support message private->group: {exc}")

    try:
        record_support_event(
            "support_ticket_created",
            message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or "",
            chat_id=str(message.chat.id),
            chat_title="private",
            order_id=str(ticket.get("subject") or ""),
            plan_name=str(ticket.get("source") or ""),
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "source": "private_user_message",
            },
        )
    except Exception:
        pass

    try:
        await message.answer(
            f"✅ Đã chuyển tin nhắn của bạn sang {support_group_name()}.\n"
            f"Ticket: <code>{ticket.get('ticket_no', '')}</code>",
        )
    except Exception:
        pass


@router.message(F.chat.type == "private")
async def support_private_inbox(message: Message):
    if not _is_private_user_message(message):
        return
    await _forward_private_message_to_group(message)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def support_group_reply(message: Message):
    if not is_support_group(message.chat.id):
        return
    if not message.reply_to_message:
        return
    if not message.from_user or not is_admin_user(message.from_user.id):
        return
    ticket = _resolve_ticket_from_group_message(message)
    if not ticket:
        return

    telegram_user_id = str(ticket.get("telegram_user_id") or "").strip()
    if not telegram_user_id:
        return

    body = _message_text(message)
    admin_name = message.from_user.full_name if message.from_user else "Admin"
    admin_username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else ""
    outgoing = f"💬 <b>Phản hồi từ hỗ trợ</b>\nTicket: <code>{ticket.get('ticket_no', '')}</code>\n{admin_name}"
    if admin_username:
        outgoing += f" ({admin_username})"
    outgoing += f"\n\n{body}"

    try:
        sent = await bot.send_message(
            chat_id=int(telegram_user_id),
            text=outgoing,
            disable_web_page_preview=True,
        )
    except Exception as exc:
        print(f"⚠️ Không gửi được phản hồi support tới user {telegram_user_id}: {exc}")
        try:
            record_support_event(
                "support_reply_failed",
                telegram_user_id,
                username=ticket.get("username") or "",
                full_name=ticket.get("full_name") or "",
                chat_id=str(message.chat.id),
                chat_title=message.chat.title or "",
                order_id=str(ticket.get("subject") or ""),
                plan_name=str(ticket.get("source") or ""),
                raw_data={
                    "ticket_id": ticket.get("id", ""),
                    "ticket_no": ticket.get("ticket_no", ""),
                    "error": str(exc),
                },
            )
        except Exception:
            pass
        return

    try:
        await record_support_message(
            ticket.get("id"),
            "support_to_user",
            telegram_message_id=sent.message_id,
            manager_group_message_id=message.message_id,
            reply_to_manager_message_id=message.reply_to_message.message_id,
            text=body,
            payload={
                "admin_name": admin_name,
                "admin_username": message.from_user.username if message.from_user else "",
                "source_chat_id": str(message.chat.id),
            },
        )
    except Exception as exc:
        print(f"⚠️ Không ghi được support_message reply: {exc}")

    try:
        supabase_store.update_support_ticket(
            ticket["id"],
            {
                "last_message_at": sent.date.isoformat() if getattr(sent, "date", None) else None,
                "updated_at": sent.date.isoformat() if getattr(sent, "date", None) else None,
            },
        )
    except Exception:
        pass

    try:
        record_support_event(
            "support_reply_sent",
            telegram_user_id,
            username=ticket.get("username") or "",
            full_name=ticket.get("full_name") or "",
            chat_id=str(message.chat.id),
            chat_title=message.chat.title or "",
            order_id=str(ticket.get("subject") or ""),
            plan_name=str(ticket.get("source") or ""),
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "reply_message_id": message.message_id,
            },
        )
    except Exception:
        pass


@router.message(Command("close"))
async def support_close_ticket(message: Message):
    if not is_support_group(message.chat.id):
        return
    if not message.from_user or not is_admin_user(message.from_user.id):
        return
    ticket = _resolve_ticket_from_group_message(message)
    if not ticket:
        await message.reply("⚠️ Không tìm thấy ticket để đóng. Hãy reply vào tin ticket hoặc ở đúng topic.")
        return
    if not supabase_store.enabled:
        await message.reply("⚠️ Supabase chưa sẵn sàng.")
        return

    try:
        updated = supabase_store.update_support_ticket(
            ticket["id"],
            {
                "status": "closed",
                "closed_at": message.date.isoformat() if getattr(message, "date", None) else None,
                "updated_at": message.date.isoformat() if getattr(message, "date", None) else None,
            },
        )
        ticket = updated[0] if updated else ticket
    except Exception as exc:
        print(f"⚠️ Không close được ticket {ticket.get('ticket_no')}: {exc}")
        await message.reply("⚠️ Không đóng được ticket, thử lại sau.")
        return

    try:
        await record_support_message(
            ticket["id"],
            "support_action",
            manager_group_message_id=message.message_id,
            text="/close",
            payload={
                "action": "close",
                "admin_name": message.from_user.full_name if message.from_user else "",
            },
        )
    except Exception:
        pass

    try:
        record_support_event(
            "support_ticket_closed",
            ticket.get("telegram_user_id") or "",
            username=ticket.get("username") or "",
            full_name=ticket.get("full_name") or "",
            chat_id=str(message.chat.id),
            chat_title=message.chat.title or "",
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "closed_by": message.from_user.id if message.from_user else None,
            },
        )
    except Exception:
        pass

    await message.reply(f"✅ Đã đóng ticket <code>{ticket.get('ticket_no', '')}</code>.")


@router.message(Command("reopen"))
async def support_reopen_ticket(message: Message):
    if not is_support_group(message.chat.id):
        return
    if not message.from_user or not is_admin_user(message.from_user.id):
        return
    ticket = _resolve_ticket_from_group_message(message)
    if not ticket:
        await message.reply("⚠️ Không tìm thấy ticket để mở lại. Hãy reply vào tin ticket hoặc ở đúng topic.")
        return
    if not supabase_store.enabled:
        await message.reply("⚠️ Supabase chưa sẵn sàng.")
        return

    try:
        updated = supabase_store.update_support_ticket(
            ticket["id"],
            {
                "status": "open",
                "closed_at": None,
                "updated_at": message.date.isoformat() if getattr(message, "date", None) else None,
            },
        )
        ticket = updated[0] if updated else ticket
    except Exception as exc:
        print(f"⚠️ Không reopen được ticket {ticket.get('ticket_no')}: {exc}")
        await message.reply("⚠️ Không mở lại được ticket, thử lại sau.")
        return

    try:
        await record_support_message(
            ticket["id"],
            "support_action",
            manager_group_message_id=message.message_id,
            text="/reopen",
            payload={
                "action": "reopen",
                "admin_name": message.from_user.full_name if message.from_user else "",
            },
        )
    except Exception:
        pass

    try:
        record_support_event(
            "support_ticket_reopened",
            ticket.get("telegram_user_id") or "",
            username=ticket.get("username") or "",
            full_name=ticket.get("full_name") or "",
            chat_id=str(message.chat.id),
            chat_title=message.chat.title or "",
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "reopened_by": message.from_user.id if message.from_user else None,
            },
        )
    except Exception:
        pass

    await message.reply(f"✅ Đã mở lại ticket <code>{ticket.get('ticket_no', '')}</code>.")


@router.message(Command("delete"))
async def support_delete_message(message: Message):
    if not is_support_group(message.chat.id):
        return
    if not message.from_user or not is_admin_user(message.from_user.id):
        return
    if not support_delete_enabled():
        await message.reply("⚠️ Chức năng delete đang tắt trong config.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Hãy reply vào tin nhắn cần xoá rồi dùng /delete.")
        return
    if not supabase_store.enabled:
        await message.reply("⚠️ Supabase chưa sẵn sàng.")
        return

    support_message, ticket = _resolve_support_message_for_delete(message)
    if not ticket:
        ticket = _resolve_ticket_from_group_message(message)
    if not ticket:
        await message.reply("⚠️ Không tìm thấy case hỗ trợ tương ứng.")
        return

    telegram_user_id = str(ticket.get("telegram_user_id") or "").strip()
    target_user_message_id = None
    if support_message and support_message.get("telegram_message_id"):
        target_user_message_id = int(support_message["telegram_message_id"])
    elif support_message and support_message.get("reply_to_manager_message_id"):
        try:
            row = supabase_store.get_support_message_by_manager_group_message_id(support_message["reply_to_manager_message_id"])
            target_user_message_id = int(row["telegram_message_id"]) if row and row.get("telegram_message_id") else None
        except Exception:
            target_user_message_id = None

    if not telegram_user_id or not target_user_message_id:
        await message.reply("⚠️ Không xác định được tin nhắn user cần xoá.")
        return

    try:
        await bot.delete_message(chat_id=int(telegram_user_id), message_id=target_user_message_id)
    except Exception as exc:
        print(f"⚠️ Không xoá được message user {telegram_user_id}/{target_user_message_id}: {exc}")
        await message.reply("⚠️ Không xoá được tin nhắn ở phía user.")
        return

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
    except Exception:
        pass

    try:
        await record_support_message(
            ticket["id"],
            "support_action",
            manager_group_message_id=message.message_id,
            reply_to_manager_message_id=message.reply_to_message.message_id,
            text="/delete",
            payload={
                "action": "delete",
                "deleted_user_message_id": target_user_message_id,
                "admin_name": message.from_user.full_name if message.from_user else "",
            },
        )
    except Exception:
        pass

    try:
        record_support_event(
            "support_message_deleted",
            telegram_user_id,
            username=ticket.get("username") or "",
            full_name=ticket.get("full_name") or "",
            chat_id=str(message.chat.id),
            chat_title=message.chat.title or "",
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "deleted_user_message_id": target_user_message_id,
                "deleted_by": message.from_user.id if message.from_user else None,
            },
        )
    except Exception:
        pass

    await message.reply(f"🗑️ Đã xoá tin nhắn của user trong case <code>{ticket.get('ticket_no', '')}</code>.")
