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


def support_group_enabled():
    return str(db.get_config("SUPPORT_GROUP_ENABLED", "OFF")).strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def support_group_id():
    return normalize_chat_id(db.get_config("SUPPORT_GROUP_ID", ""))


def support_group_name():
    return db.get_config("SUPPORT_GROUP_NAME", "Nhóm hỗ trợ")


def support_group_grace_days():
    try:
        return max(0, int(float(str(db.get_config("SUPPORT_GROUP_GRACE_DAYS", "14")).strip())))
    except (TypeError, ValueError):
        return 14

def support_group_mute_enabled():
    return str(db.get_config("SUPPORT_GROUP_MUTE_ENABLED", "ON")).strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}

def record_support_event(event_type, telegram_user_id=None, **kwargs):
    if not supabase_store.enabled:
        return
    try:
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
        invite = await bot.create_chat_invite_link(
            chat_id=gid,
            member_limit=1,
            creates_join_request=False,
            name=f"support-{user_id}",
        )
        return invite.invite_link, ""
    except Exception as exc:
        return None, str(exc)


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
