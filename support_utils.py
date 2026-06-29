from datetime import datetime
import re

from aiogram.types import ChatPermissions, InlineKeyboardButton

from bot_instance import bot
from database import db
from i18n import t
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
            f"{err}. Kiểm tra {config_key}={mask_chat_id(gid)}: phải là chat_id thật của group/supergroup "
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
    return db.get_config("SUPPORT_GROUP_NAME", "Nhóm VIP")


def support_group_grace_days():
    try:
        return max(0, int(float(str(db.get_config("SUPPORT_GROUP_GRACE_DAYS", "14")).strip())))
    except (TypeError, ValueError):
        return 14

def support_group_mute_enabled():
    raw = str(db.get_config("SUPPORT_GROUP_MUTE_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_group_id():
    return normalize_chat_id(db.get_config("SUPPORT_INBOX_GROUP_ID", ""))


def support_inbox_group_name():
    return db.get_config("SUPPORT_INBOX_GROUP_NAME", "Nhóm hỗ trợ")


def support_inbox_mode():
    raw = str(db.get_config("SUPPORT_INBOX_MODE", "group") or "group").strip().lower()
    return raw if raw in {"group", "forum"} else "group"


def support_inbox_status_enabled():
    raw = str(db.get_config("SUPPORT_INBOX_STATUS_ENABLED", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_status_style():
    raw = str(db.get_config("SUPPORT_INBOX_STATUS_STYLE", "pulse") or "pulse").strip().lower()
    return raw if raw in {"pulse", "dots", "blink", "wave"} else "pulse"


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


def support_inbox_status_min_visible_ms():
    # Keep the transition visible long enough so users can perceive the handoff.
    return max(1200, support_inbox_status_frame_delay_ms() * 3 + support_inbox_status_final_hold_ms())


def support_inbox_connecting_text():
    return str(db.get_config("SUPPORT_INBOX_CONNECTING_TEXT", "Đang kết nối") or "Đang kết nối").strip()


def support_inbox_ready_text():
    return str(db.get_config("SUPPORT_INBOX_READY_TEXT", "{staff_name} đã sẵn sàng hỗ trợ 🤗") or "{staff_name} đã sẵn sàng hỗ trợ 🤗").strip()


def support_inbox_staff_name():
    configured = str(db.get_config("SUPPORT_INBOX_STAFF_NAME", "") or "").strip()
    if configured:
        return configured
    for names in support_inbox_staff_map().values():
        if names:
            return names[0]
    return ""


def support_inbox_reply_show_username():
    raw = str(db.get_config("SUPPORT_INBOX_REPLY_SHOW_USERNAME", "ON") or "ON").strip()
    return raw.upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_inbox_staff_map():
    raw = str(db.get_config("SUPPORT_INBOX_STAFF_MAP", "") or "").strip()
    mapping = {}
    if not raw:
        return mapping

    for line in raw.splitlines():
        row = str(line or "").strip()
        if not row or row.startswith("#"):
            continue
        if "|" in row:
            admin_id, names_raw = row.split("|", 1)
        elif ":" in row:
            admin_id, names_raw = row.split(":", 1)
        else:
            continue
        admin_key = normalize_chat_id(admin_id)
        if not admin_key:
            continue
        names = [name.strip() for name in re.split(r"[;,/]+", names_raw) if name.strip()]
        if not names:
            continue
        mapping.setdefault(admin_key, []).extend(names)
    return mapping


def support_inbox_staff_names_for_admin(admin_id):
    admin_key = normalize_chat_id(admin_id)
    if not admin_key:
        return []
    return list(support_inbox_staff_map().get(admin_key, []))


def support_inbox_staff_name_for_admin(admin_id, fallback=""):
    names = support_inbox_staff_names_for_admin(admin_id)
    if names:
        return names[0]
    configured = str(db.get_config("SUPPORT_INBOX_STAFF_NAME", "") or "").strip()
    if configured:
        return configured
    return str(fallback or "").strip()


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
    return support_admin_online_text() if online else support_admin_offline_text()


def support_inbox_status_frame_list(base_message=""):
    message = str(base_message or support_inbox_connecting_text()).strip() or "Đang kết nối"
    raw_frames = support_inbox_status_frames()
    if raw_frames:
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
        return None, ""

    try:
        existing = supabase_store.get_support_ticket_by_user(telegram_user_id)
        if existing:
            ticket = existing
            inbox_gid = support_inbox_group_id()
            if inbox_gid and normalize_chat_id(ticket.get("manager_chat_id") or "") != inbox_gid:
                try:
                    updated_ticket = supabase_store.update_support_ticket(ticket["id"], {"manager_chat_id": inbox_gid, "updated_at": datetime.now().isoformat()})
                    if updated_ticket:
                        ticket = updated_ticket[0]
                except Exception as exc:
                    print(f"⚠️ Không cập nhật manager_chat_id cho support ticket cũ {telegram_user_id}: {exc}")
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
            "manager_chat_id": support_inbox_group_id(),
            "status": "open",
            "subject": str(subject or ""),
            "source": str(source or "bot"),
            "raw_data": raw_data or {},
        }
        created = supabase_store.create_support_ticket(payload)
        return created[0] if created else None, ""
    except Exception as exc:
        print(f"⚠️ Không tạo được support ticket cho user {telegram_user_id}: {exc}")
        return None, str(exc)


async def create_support_case_from_private_message(message, *, source="private_user_message", subject=None):
    if not supabase_store.enabled or not message or not getattr(message, "from_user", None):
        return None, ""

    message_text = str(getattr(message, "text", "") or getattr(message, "caption", "") or "").strip()
    ticket_subject = str(subject or message_text or "").strip() or "Tin nhắn hỗ trợ"
    ticket, ticket_error = await create_support_ticket_for_user(
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

    ticket_text = render_support_group_message(ticket, message_text)
    try:
        sent = await post_support_ticket_to_group(ticket, message_text=ticket_text)
    except Exception as exc:
        sent = None
        print(f"⚠️ Không forward ticket lên group: {exc}")

    if sent:
        try:
            supabase_store.update_support_ticket(
                ticket["id"],
                {
                    "manager_group_message_id": sent.message_id,
                    "updated_at": sent.date.isoformat() if getattr(sent, "date", None) else None,
                },
            )
        except Exception as exc:
            print(f"⚠️ Không cập nhật ticket group message id: {exc}")
        try:
            await record_support_message(
                ticket["id"],
                "user_to_support",
                telegram_message_id=getattr(message, "message_id", None),
                manager_group_message_id=sent.message_id,
                text=message_text or "",
                payload={
                    "chat_id": str(getattr(message.chat, "id", "")),
                    "chat_type": getattr(message.chat, "type", ""),
                    "source": source,
                },
            )
        except Exception as exc:
            print(f"⚠️ Không lưu support message private->group: {exc}")
    elif ticket:
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
                    "forward_status": "failed",
                },
            )
        except Exception as exc:
            print(f"⚠️ Không lưu support message fallback: {exc}")

    try:
        record_support_event(
            "support_ticket_created",
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


def render_support_reply_message(ticket, message_text="", admin_name="", admin_username="", admin_status_text="", admin_id=None, show_username=None):
    display_name = str(admin_name or "").strip()
    if not display_name:
        display_name = support_inbox_staff_name_for_admin(admin_id, fallback="")
    if not display_name:
        display_name = "Admin"

    show_username = support_inbox_reply_show_username() if show_username is None else bool(show_username)
    username_suffix = ""
    if show_username:
        raw_username = str(admin_username or "").strip().lstrip("@")
        if raw_username:
            username_suffix = f" @{raw_username}"

    context = {
        "ticket_no": ticket.get("ticket_no", ""),
        "full_name": ticket.get("full_name", ""),
        "telegram_user_id": ticket.get("telegram_user_id", ""),
        "subject": ticket.get("subject", ""),
        "status": ticket.get("status", ""),
        "admin_name": display_name,
        "admin_username": username_suffix,
        "admin_status": admin_status_text or support_admin_online_text(),
        "message": message_text,
    }
    default_text = (
        "💬 <b>Phản hồi từ hỗ trợ</b>\n"
        "Ticket: <code>{ticket_no}</code>\n"
        "{admin_status}\n"
        "{admin_name}{admin_username}\n\n"
        "{message}"
    )
    return _render_template(db.get_config("SUPPORT_INBOX_REPLY_TEMPLATE", default_text), context, default_text)


def support_admin_online_text():
    return str(db.get_config("SUPPORT_ADMIN_ONLINE_TEXT", "🟢 Admin đang online") or "🟢 Admin đang online").strip()


def support_admin_offline_text():
    return str(db.get_config("SUPPORT_ADMIN_OFFLINE_TEXT", "⚪ Admin đang offline") or "⚪ Admin đang offline").strip()


async def post_support_ticket_to_group(ticket, message_text="", join_link=""):
    manager_chat_id = normalize_chat_id(ticket.get("manager_chat_id") or support_inbox_group_id())
    if not ticket or not manager_chat_id:
        return None
    if normalize_chat_id(ticket.get("manager_chat_id") or "") and normalize_chat_id(ticket.get("manager_chat_id") or "") != manager_chat_id:
        manager_chat_id = normalize_chat_id(ticket.get("manager_chat_id") or "")
    ticket = await ensure_support_ticket_topic(ticket)

    header = support_ticket_header(ticket)
    body = []
    if message_text:
        body.append(escape_html(message_text.strip()))
    if join_link:
        body.append(f"🔗 {escape_html(join_link)}")
    text = "\n\n".join([header] + body)
    send_kwargs = {
        "chat_id": manager_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    thread_id = ticket.get("manager_topic_thread_id")
    if support_inbox_mode() == "forum" and thread_id:
        send_kwargs["message_thread_id"] = int(thread_id)
    sent = await bot.send_message(**send_kwargs)
    return sent


def support_topic_title(ticket):
    ticket_no = str(ticket.get("ticket_no") or "").strip()
    full_name = str(ticket.get("full_name") or ticket.get("username") or ticket.get("telegram_user_id") or "Khách").strip()
    title = f"{full_name} - {ticket_no}" if ticket_no else full_name
    return title[:120]


async def ensure_support_ticket_topic(ticket):
    if not ticket or support_inbox_mode() != "forum":
        return ticket

    manager_chat_id = normalize_chat_id(ticket.get("manager_chat_id") or support_inbox_group_id())
    if not manager_chat_id:
        return ticket

    existing_thread_id = str(ticket.get("manager_topic_thread_id") or "").strip()
    if existing_thread_id:
        return ticket

    try:
        topic = await bot.create_forum_topic(
            chat_id=manager_chat_id,
            name=support_topic_title(ticket),
        )
        payload = {
            "manager_chat_id": manager_chat_id,
            "manager_topic_thread_id": getattr(topic, "message_thread_id", None),
            "manager_topic_name": getattr(topic, "name", "") or support_topic_title(ticket),
            "updated_at": datetime.now().isoformat(),
        }
        updated = supabase_store.update_support_ticket(ticket["id"], payload) if supabase_store.enabled else []
        if updated:
            return updated[0]
        ticket.update(payload)
        return ticket
    except Exception as exc:
        print(f"⚠️ Không tạo được topic support cho ticket {ticket.get('ticket_no', '')}: {exc}")
        return ticket


async def send_support_connecting_status(message, ticket, *, delete_source_message=False):
    try:
        status_message = await message.answer(
            f"{support_admin_presence_text(False)}\n{support_inbox_connecting_text()}",
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
                    await asyncio.sleep(support_inbox_status_min_visible_ms() / 1000.0)
                    await status_message.edit_text(
                        f"{support_admin_presence_text(True)}\n"
                        f"{render_support_inbox_ready_text(staff_name=support_inbox_staff_name() or 'Admin', ticket_no=str(ticket.get('ticket_no', '')))}"
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
                await asyncio.sleep(support_inbox_status_min_visible_ms() / 1000.0)
                await status_message.edit_text(
                    f"{support_admin_presence_text(True)}\n"
                    f"{render_support_inbox_ready_text(staff_name=support_inbox_staff_name() or 'Admin', ticket_no=str(ticket.get('ticket_no', '')))}"
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
                f"✅ Đã chuyển tin nhắn của bạn sang {support_inbox_group_name()}.\n"
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
