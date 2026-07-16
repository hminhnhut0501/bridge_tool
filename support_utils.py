from datetime import datetime
from aiogram.types import ChatPermissions, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from bot_instance import bot
from database import db
from i18n import t
from i18n import get_user_language
from supabase_store import supabase_store
from helpers import safe_delete_private_message


def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def normalize_chat_id(value):
    raw = str(value or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def mask_chat_id(value):
    raw = normalize_chat_id(value)
    if len(raw) <= 8:
        return raw
    return f"{raw[:5]}...{raw[-4:]}"


def explain_support_invite_error(error, gid, config_key="SUPPORT_GROUP_ID"):
    err = str(error or "")
    lower = err.lower()
    if "chat not found" in lower:
        return (
            f"{err}. Kiểm tra {config_key}={mask_chat_id(gid)}: phải là chat_id thật của group/channel "
            "dạng -100..., bot phải đang ở trong đúng nơi hỗ trợ."
        )
    if "not enough rights" in lower or "administrator" in lower or "can't invite" in lower:
        return (
            f"{err}. Bot cần được đặt làm admin trong khu vực hỗ trợ và có quyền tạo link mời/thêm thành viên."
        )
    return err


def support_group_enabled():
    raw = str(db.get_config("SUPPORT_GROUP_ENABLED", "OFF") or "OFF").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_group_mode():
    raw = str(db.get_config("SUPPORT_GROUP_MODE", "group") or "group").strip().lower()
    return raw if raw in {"group", "channel"} else "group"


def support_group_id():
    return normalize_chat_id(db.get_config("SUPPORT_GROUP_ID", ""))


def support_group_name():
    default_name = "Kênh hỗ trợ" if support_group_mode() == "channel" else "Nhóm hỗ trợ"
    return db.get_config("SUPPORT_GROUP_NAME", default_name)


def support_group_grace_days():
    try:
        return max(0, int(float(str(db.get_config("SUPPORT_GROUP_GRACE_DAYS", "14")).strip())))
    except (TypeError, ValueError):
        return 14

def support_group_mute_enabled():
    raw = str(db.get_config("SUPPORT_GROUP_MUTE_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def is_support_group(chat_id):
    gid = support_group_id()
    return bool(gid and normalize_chat_id(chat_id) == gid)


def support_inbox_enabled():
    raw = str(db.get_config("SUPPORT_INBOX_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_status_enabled():
    raw = str(db.get_config("SUPPORT_INBOX_STATUS_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_status_style():
    raw = str(db.get_config("SUPPORT_INBOX_STATUS_STYLE", "pulse") or "pulse").strip().lower()
    return raw if raw in {"pulse", "dots", "blink", "wave", "custom"} else "pulse"


def support_inbox_status_frames():
    return str(db.get_config("SUPPORT_INBOX_STATUS_FRAMES", "") or "").strip()


def support_inbox_status_frame_delay_ms():
    try:
        return max(120, int(float(str(db.get_config("SUPPORT_INBOX_STATUS_FRAME_DELAY_MS", "420")).strip())))
    except (TypeError, ValueError):
        return 420


def support_inbox_status_final_hold_ms():
    try:
        return max(0, int(float(str(db.get_config("SUPPORT_INBOX_STATUS_FINAL_HOLD_MS", "800")).strip())))
    except (TypeError, ValueError):
        return 800


def support_inbox_status_total_ms(frame_count=None):
    configured = str(db.get_config("SUPPORT_INBOX_STATUS_TOTAL_MS", "") or "").strip()
    if configured:
        try:
            return max(1200, int(float(configured)))
        except (TypeError, ValueError):
            pass
    # Fallback for older data: keep the transition visible long enough for at least two full frame cycles.
    safe_frame_count = max(1, int(frame_count or 0) or 1)
    return max(1200, support_inbox_status_frame_delay_ms() * safe_frame_count * 2 + support_inbox_status_final_hold_ms())


def support_inbox_connecting_text():
    return str(db.get_config("SUPPORT_INBOX_CONNECTING_TEXT", "Đang kết nối") or "Đang kết nối").strip()


def support_inbox_ready_text():
    return str(db.get_config("SUPPORT_INBOX_READY_TEXT", "{staff_name} đã sẵn sàng hỗ trợ 🤗") or "{staff_name} đã sẵn sàng hỗ trợ 🤗").strip()


def render_support_inbox_ready_text(*, staff_name="Admin", admin_name="", admin_username="", ticket_no=""):
    text = support_inbox_ready_text()
    replacements = {
        "{staff_name}": str(staff_name or "Admin"),
        "{admin_name}": str(admin_name or ""),
        "{admin_username}": str(admin_username or ""),
        "{ticket_no}": str(ticket_no or ""),
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def support_admin_presence_text(online=True):
    return "🟢 Admin đang online" if online else "⚪ Admin đang offline"


def support_inbox_status_frame_list(base_message=""):
    message = str(base_message or support_inbox_connecting_text()).strip() or "Đang kết nối"
    raw_frames = support_inbox_status_frames()
    if support_inbox_status_style() == "custom" and raw_frames:
        frames = [line.strip() for line in raw_frames.splitlines() if line.strip()]
        return [frame.replace("{message}", message) for frame in frames] or [message]

    style = support_inbox_status_style()
    if style == "dots":
        return [message, f"{message}.", f"{message}..", f"{message}..."]
    if style == "blink":
        return [f"● {message}", f"○ {message}", f"● {message}"]
    if style == "wave":
        return [message, f"{message} ~", f"{message} ~~", f"{message} ~~~"]
    return [f"{message} ·", f"{message} ··", f"{message} ···"]


def support_ticket_prefix():
    return str(db.get_config("SUPPORT_TICKET_PREFIX", "SUP") or "SUP").strip().upper()[:6] or "SUP"


def support_case_id(ticket):
    if not ticket:
        return ""
    ticket_no = str(ticket.get("ticket_no") or "").strip()
    user_id = str(ticket.get("telegram_user_id") or "").strip()
    return ticket_no or (f"U{user_id}" if user_id else "")


def support_ticket_subject_from_action(action="", provider="", plan_name=""):
    parts = []
    if action:
        parts.append(str(action).strip())
    if provider:
        parts.append(str(provider).strip().upper())
    if plan_name:
        parts.append(str(plan_name).strip())
    return " | ".join([part for part in parts if part])[:120]


def build_support_ticket_no():
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{support_ticket_prefix()}{stamp}"


async def create_support_ticket_for_user(*, telegram_user_id, chat_id=None, username="", full_name="", subject="", source="auto_payment_off", raw_data=None):
    if not supabase_store.enabled:
        return None, ""

    try:
        existing = supabase_store.get_support_ticket_by_user(telegram_user_id)
        if existing:
            ticket = existing
            if subject and not str(ticket.get("subject") or "").strip():
                ticket = supabase_store.update_support_ticket(ticket["id"], {"subject": subject, "updated_at": datetime.now().isoformat()})[0]
            return ticket, ""

        user_id = str(telegram_user_id)
        payload = {
            "ticket_no": build_support_ticket_no(),
            "telegram_user_id": user_id,
            "chat_id": str(chat_id or ""),
            "username": str(username or ""),
            "full_name": str(full_name or ""),
            "status": "open",
            "subject": str(subject or ""),
            "source": str(source or "bot"),
            "raw_data": raw_data or {},
        }
        created = supabase_store.create_support_ticket(payload)
        try:
            supabase_store.record_customer_identity_history(
                user_id,
                username=payload["username"],
                full_name=payload["full_name"],
                source_event_type="support_ticket_created",
                source_chat_id=payload["chat_id"],
                raw_data={
                    "source": payload["source"],
                    "subject": payload["subject"],
                    "ticket_no": payload["ticket_no"],
                },
            )
        except Exception as exc:
            print(f"⚠️ Không ghi được customer identity history cho {telegram_user_id}: {exc}")
        return created[0] if created else None, ""
    except Exception as exc:
        print(f"⚠️ Không tạo được support ticket cho user {telegram_user_id}: {exc}")
        return None, str(exc)


async def get_or_create_support_ticket_for_user(*, telegram_user_id, chat_id=None, username="", full_name="", subject="", source="private_user_message", raw_data=None):
    if not supabase_store.enabled:
        return None, False, "Supabase support is disabled."

    try:
        existing = supabase_store.get_open_support_ticket_by_user(telegram_user_id)
        if existing:
            ticket = existing
            updates = {"updated_at": datetime.now().isoformat()}
            if subject and not str(ticket.get("subject") or "").strip():
                updates["subject"] = subject
            if len(updates) > 1:
                try:
                    updated_ticket = supabase_store.update_support_ticket(ticket["id"], updates)
                    if updated_ticket:
                        ticket = updated_ticket[0]
                except Exception as exc:
                    print(f"⚠️ Không cập nhật support ticket đang mở cho {telegram_user_id}: {exc}")
            return ticket, False, ""

        ticket, error = await create_support_ticket_for_user(
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            username=username,
            full_name=full_name,
            subject=subject,
            source=source,
            raw_data=raw_data,
        )
        return ticket, True, error
    except Exception as exc:
        print(f"⚠️ Không lấy/tạo support ticket cho user {telegram_user_id}: {exc}")
        return None, False, str(exc)


async def create_support_case_from_private_message(message, *, source="private_user_message", subject=None):
    if not supabase_store.enabled or not message or not getattr(message, "from_user", None):
        return None, ""

    message_text = str(getattr(message, "text", "") or getattr(message, "caption", "") or "").strip()
    ticket_subject = str(subject or message_text or "").strip() or "Tin nhắn hỗ trợ"
    ticket, created_new, ticket_error = await get_or_create_support_ticket_for_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
        subject=ticket_subject,
        source=source,
        raw_data={
            "message_id": getattr(message, "message_id", None),
            "chat_type": getattr(message.chat, "type", ""),
            "kind": "private_message",
            "message_text": message_text,
        },
    )
    if not ticket:
        return None, ticket_error or "Không tạo được ticket hỗ trợ."

    try:
        await record_support_message(
            ticket["id"],
            "user_to_support",
            telegram_message_id=getattr(message, "message_id", None),
            text=message_text or "",
            payload={
                "chat_id": str(getattr(message.chat, "id", "")),
                "chat_type": getattr(message.chat, "type", ""),
                "source": source,
                "content_type": "media" if getattr(message, "photo", None) or getattr(message, "video", None) or getattr(message, "document", None) or getattr(message, "voice", None) or getattr(message, "audio", None) or getattr(message, "sticker", None) else "text",
            },
        )
    except Exception as exc:
        print(f"⚠️ Không lưu support message private->internal: {exc}")

    event_type = "support_ticket_created" if created_new else "support_ticket_reused"
    try:
        record_support_event(
            event_type,
            message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or "",
            chat_id=str(getattr(message.chat, "id", "")),
            chat_title="private",
            order_id=str(ticket.get("subject") or ""),
            plan_name=str(ticket.get("source") or ""),
            raw_data={
                "ticket_id": ticket.get("id", ""),
                "ticket_no": ticket.get("ticket_no", ""),
                "source": source,
            },
        )
    except Exception:
        pass

    await send_support_connecting_status(message, ticket, delete_source_message=True)

    return ticket, ""


def support_ticket_header(ticket):
    if not ticket:
        return ""
    ticket_no = support_case_id(ticket)
    full_name = str(ticket.get("full_name") or "").strip() or "Khách"
    telegram_user_id = str(ticket.get("telegram_user_id") or "").strip()
    subject = str(ticket.get("subject") or "").strip()
    status = str(ticket.get("status") or "").strip().upper()
    lines = [
        f"🎫 <b>{ticket_no}</b> - {escape_html(full_name)}",
        f"ID: <code>{escape_html(telegram_user_id)}</code>",
    ]
    if subject:
        lines.append(f"🔎 {escape_html(subject)}")
    lines.append(f"Trạng thái: <b>{escape_html(status)}</b>")
    return "\n".join(lines)


def support_ticket_context(ticket, message_text=""):
    return {
        "ticket_no": escape_html(ticket.get("ticket_no", "")),
        "full_name": escape_html(ticket.get("full_name", "")),
        "telegram_user_id": escape_html(ticket.get("telegram_user_id", "")),
        "username": escape_html(ticket.get("username", "")),
        "subject": escape_html(ticket.get("subject", "")),
        "status": escape_html(ticket.get("status", "")),
        "message": escape_html(message_text),
    }


def _render_template(template: str, context: dict[str, object], default_text: str):
    text = str(template or "").strip() or default_text
    for key, value in context.items():
        text = text.replace(f"{{{key}}}", str(value or ""))
    return text


async def send_support_connecting_status(message, ticket, *, delete_source_message=False):
    try:
        initial_frames = support_inbox_status_frame_list(support_inbox_connecting_text())
        initial_text = initial_frames[0] if initial_frames else support_inbox_connecting_text()
        status_message = await message.answer(
            initial_text,
        )
        if delete_source_message:
            await safe_delete_private_message(message)
        if support_inbox_status_enabled():
            try:
                from modules.mod_support_inbox import _play_support_inbox_status_effect
            except Exception as exc:
                print(f"⚠️ Không nạp được effect support inbox: {exc}")
                _play_support_inbox_status_effect = None

            if _play_support_inbox_status_effect:
                from helpers import create_background_task

                create_background_task(
                    _play_support_inbox_status_effect(
                        chat_id=message.chat.id,
                        message_id=status_message.message_id,
                        ticket_no=str(ticket.get("ticket_no", "")),
                    ),
                    name=f"support_inbox_status_{ticket.get('ticket_no', '')}",
                    context="support_inbox",
                )
            else:
                from helpers import create_background_task
                import asyncio

                async def _finalize_support_status():
                    await asyncio.sleep(support_inbox_status_total_ms(len(initial_frames)) / 1000.0)
                    await status_message.edit_text(
                        f"{support_admin_presence_text(True)}\n"
                        f"{render_support_inbox_ready_text(staff_name='Admin', ticket_no=str(ticket.get('ticket_no', '')))}"
                    )

                create_background_task(
                    _finalize_support_status(),
                    name=f"support_inbox_status_fallback_{ticket.get('ticket_no', '')}",
                    context="support_inbox",
                )
        else:
            from helpers import create_background_task
            import asyncio

            async def _finalize_support_status():
                await asyncio.sleep(support_inbox_status_total_ms(len(initial_frames)) / 1000.0)
                await status_message.edit_text(
                    f"{support_admin_presence_text(True)}\n"
                    f"{render_support_inbox_ready_text(staff_name='Admin', ticket_no=str(ticket.get('ticket_no', '')))}"
                )

            create_background_task(
                _finalize_support_status(),
                name=f"support_inbox_status_disabled_{ticket.get('ticket_no', '')}",
                context="support_inbox",
            )
    except Exception:
        try:
            if delete_source_message:
                await safe_delete_private_message(message)
            await message.answer(
                "✅ Đã ghi nhận tin nhắn hỗ trợ.\n"
                f"Ticket: <code>{ticket.get('ticket_no', '')}</code>",
            )
        except Exception:
            pass


async def record_support_message(ticket_id, direction, *, telegram_message_id=None, manager_group_message_id=None, manager_topic_message_id=None, reply_to_manager_message_id=None, text="", payload=None):
    if not supabase_store.enabled:
        return None
    data = {
        "ticket_id": str(ticket_id),
        "direction": str(direction or "").strip().lower(),
        "telegram_message_id": telegram_message_id,
        "manager_group_message_id": manager_group_message_id,
        "manager_topic_message_id": manager_topic_message_id,
        "reply_to_manager_message_id": reply_to_manager_message_id,
        "text": str(text or ""),
        "payload": payload or {},
    }
    return supabase_store.create_support_message(data)

def record_support_event(event_type, telegram_user_id=None, **kwargs):
    if not supabase_store.enabled:
        return
    try:
        if telegram_user_id and (not kwargs.get("full_name") or not kwargs.get("username")):
            identity = supabase_store.get_user_identity(telegram_user_id)
            if identity:
                kwargs.setdefault("username", identity.get("username") or "")
                kwargs.setdefault("full_name", identity.get("full_name") or "")
                if not kwargs.get("username") and identity.get("username"):
                    kwargs["username"] = identity.get("username")
                if not kwargs.get("full_name") and identity.get("full_name"):
                    kwargs["full_name"] = identity.get("full_name")

        supabase_store.record_support_event(event_type, telegram_user_id, **kwargs)
    except Exception as exc:
        print(f"⚠️ Không ghi được support event {event_type}: {exc}")


def is_lifetime_plan(plan_name):
    upper = str(plan_name or "").upper()
    return "TRỌN ĐỜI" in upper or "LIFE" in upper


async def create_support_invite_link(user_id):
    if not support_group_enabled():
        return None, ""

    gid = support_group_id()
    if not gid:
        return None, "Nhóm hỗ trợ chưa cấu hình group ID."

    try:
        if support_group_mode() != "channel":
            try:
                await bot.unban_chat_member(chat_id=gid, user_id=int(user_id), only_if_banned=True)
            except Exception:
                pass
            try:
                await unmute_member(gid, user_id)
            except Exception:
                pass
        invite = await bot.create_chat_invite_link(
            chat_id=gid,
            member_limit=1,
            creates_join_request=False,
            name=f"support-{user_id}",
        )
        return invite.invite_link, ""
    except Exception as exc:
        print(f"⚠️ Không tạo được support invite link mode={support_group_mode()} target={mask_chat_id(gid)} user={user_id}: {exc}")
        return None, explain_support_invite_error(exc, gid)


async def revoke_support_invite_link(chat_id, invite_link):
    gid = normalize_chat_id(chat_id)
    link = str(invite_link or "").strip()
    if not gid or not link:
        return False, "Thiếu chat_id hoặc invite_link."
    try:
        await bot.revoke_chat_invite_link(chat_id=gid, invite_link=link)
        return True, ""
    except Exception as exc:
        print(f"⚠️ Không revoke được support invite link group={mask_chat_id(gid)}: {exc}")
        return False, explain_support_invite_error(exc, gid)


async def add_support_join_button(keyboard_builder, user_id):
    link, error = await create_support_invite_link(user_id)
    if link:
        language = get_user_language(user_id)
        default_label = "💬 Join support group" if language == "en" else "💬 Join nhóm hỗ trợ"
        keyboard_builder.row(InlineKeyboardButton(
            text=t(user_id, "SUPPORT_GROUP_BUTTON_TEXT", default_label),
            url=link,
        ))
        return ""
    if error:
        language = get_user_language(user_id)
        default_error = (
            "\n💬 <b>{group}</b>: <i>Unable to create support link ({error})</i>\n"
            if language == "en"
            else "\n💬 <b>{group}</b>: <i>Không tạo được link hỗ trợ ({error})</i>\n"
        )
        template = t(user_id, "MSG_SUPPORT_LINK_ERROR", default_error)
        return template.replace("{group}", escape_html(support_group_name())).replace("{error}", escape_html(error))
    return ""


async def mute_member(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=int(user_id),
        permissions=ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        ),
    )


async def unmute_member(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=int(user_id),
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        ),
    )
