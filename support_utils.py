from datetime import datetime

from aiogram.types import ChatPermissions, InlineKeyboardButton

from bot_instance import bot
from database import db
from i18n import t
from supabase_store import supabase_store


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


def explain_support_invite_error(error, gid):
    err = str(error or "")
    lower = err.lower()
    if "chat not found" in lower:
        return (
            f"{err}. Kiểm tra SUPPORT_GROUP_ID={mask_chat_id(gid)}: phải là chat_id thật của group/supergroup "
            "dạng -100..., bot phải đang ở trong đúng group hỗ trợ."
        )
    if "not enough rights" in lower or "administrator" in lower or "can't invite" in lower:
        return (
            f"{err}. Bot cần được đặt làm admin trong group hỗ trợ và có quyền tạo link mời/thêm thành viên."
        )
    return err


def support_group_enabled():
    raw = str(db.get_config("SUPPORT_GROUP_ENABLED", "OFF") or "OFF").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_group_id():
    return normalize_chat_id(db.get_config("SUPPORT_GROUP_ID", ""))


def support_group_name():
    return db.get_config("SUPPORT_GROUP_NAME", "Chăm sóc khách hàng")


def support_group_grace_days():
    try:
        return max(0, int(float(str(db.get_config("SUPPORT_GROUP_GRACE_DAYS", "14")).strip())))
    except (TypeError, ValueError):
        return 14

def support_group_mute_enabled():
    raw = str(db.get_config("SUPPORT_GROUP_MUTE_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_mode():
    raw = str(db.get_config("SUPPORT_INBOX_MODE", "group") or "group").strip().lower()
    return raw if raw in {"group", "forum"} else "group"


def support_delete_enabled():
    raw = str(db.get_config("SUPPORT_DELETE_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


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
        return None, "SUPABASE chưa bật."

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
            "manager_chat_id": support_group_id(),
            "status": "open",
            "subject": str(subject or ""),
            "source": str(source or "bot"),
            "last_message_at": datetime.now().isoformat(),
            "raw_data": raw_data or {},
        }
        created = supabase_store.create_support_ticket(payload)
        return created[0] if created else None, ""
    except Exception as exc:
        print(f"⚠️ Không tạo được support ticket cho user {telegram_user_id}: {exc}")
        return None, str(exc)


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


def _render_template(template: str, context: dict[str, object], default_text: str):
    text = str(template or "").strip() or default_text
    for key, value in context.items():
        text = text.replace(f"{{{key}}}", str(value or ""))
    return text


def render_support_group_message(ticket, message_text="", *, template_key="SUPPORT_INBOX_GROUP_TEMPLATE"):
    context = {
        "ticket_no": ticket.get("ticket_no", ""),
        "full_name": ticket.get("full_name", ""),
        "telegram_user_id": ticket.get("telegram_user_id", ""),
        "username": ticket.get("username", ""),
        "subject": ticket.get("subject", ""),
        "status": ticket.get("status", ""),
        "message": message_text,
    }
    default_text = (
        "📩 <b>Tin nhắn từ khách</b>\n"
        "Ticket: <code>{ticket_no}</code>\n"
        "Khách: <b>{full_name}</b>\n"
        "ID: <code>{telegram_user_id}</code>\n\n"
        "{message}"
    )
    return _render_template(db.get_config(template_key, default_text), context, default_text)


def render_support_reply_message(ticket, message_text="", admin_name="", admin_username=""):
    context = {
        "ticket_no": ticket.get("ticket_no", ""),
        "full_name": ticket.get("full_name", ""),
        "telegram_user_id": ticket.get("telegram_user_id", ""),
        "subject": ticket.get("subject", ""),
        "status": ticket.get("status", ""),
        "admin_name": admin_name,
        "admin_username": admin_username,
        "message": message_text,
    }
    default_text = (
        "💬 <b>Phản hồi từ hỗ trợ</b>\n"
        "Ticket: <code>{ticket_no}</code>\n"
        "{admin_name}{admin_username}\n\n"
        "{message}"
    )
    return _render_template(db.get_config("SUPPORT_INBOX_REPLY_TEMPLATE", default_text), context, default_text)


def support_admin_online_text():
    return str(db.get_config("SUPPORT_ADMIN_ONLINE_TEXT", "🟢 Admin đang online") or "🟢 Admin đang online").strip()


def support_admin_offline_text():
    return str(db.get_config("SUPPORT_ADMIN_OFFLINE_TEXT", "⚪ Admin đang offline") or "⚪ Admin đang offline").strip()


async def post_support_ticket_to_group(ticket, message_text="", join_link=""):
    if not ticket or not support_group_enabled() or not is_support_group(ticket.get("manager_chat_id") or support_group_id()):
        return None

    header = support_ticket_header(ticket)
    body = []
    if message_text:
        body.append(escape_html(message_text.strip()))
    if join_link:
        body.append(f"🔗 {escape_html(join_link)}")
    text = "\n\n".join([header] + body)
    sent = await bot.send_message(
        chat_id=support_group_id(),
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    return sent


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

        gid = support_group_id()
        if gid and normalize_chat_id(kwargs.get("chat_id")) == gid and not kwargs.get("chat_title"):
            kwargs["chat_title"] = support_group_name()

        supabase_store.record_support_event(event_type, telegram_user_id, **kwargs)
    except Exception as exc:
        print(f"⚠️ Không ghi được support event {event_type}: {exc}")


def is_lifetime_plan(plan_name):
    upper = str(plan_name or "").upper()
    return "TRỌN ĐỜI" in upper or "LIFE" in upper


def is_support_group(chat_id):
    gid = support_group_id()
    return bool(gid and normalize_chat_id(chat_id) == gid)


async def create_support_invite_link(user_id):
    if not support_group_enabled():
        return None, ""

    gid = support_group_id()
    if not gid:
        return None, "Nhóm hỗ trợ chưa cấu hình group ID."

    try:
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
        print(f"⚠️ Không tạo được support invite link group={mask_chat_id(gid)} user={user_id}: {exc}")
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
        keyboard_builder.row(InlineKeyboardButton(
            text=t(user_id, "SUPPORT_GROUP_BUTTON_TEXT", "💬 Join nhóm hỗ trợ"),
            url=link,
        ))
        return ""
    if error:
        template = t(user_id, "MSG_SUPPORT_LINK_ERROR", "\n💬 <b>{group}</b>: <i>Không tạo được link hỗ trợ ({error})</i>\n")
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
