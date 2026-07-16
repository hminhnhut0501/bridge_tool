from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated

from bot_instance import bot
from support_utils import is_support_group, record_support_event
from scheduler import evaluate_group_join_access

router = Router()


def member_status(member):
    raw = str(getattr(member, "status", "") or "").lower()
    return raw.rsplit(".", 1)[-1]


@router.chat_member()
async def support_group_member_update(event: ChatMemberUpdated):
    if not is_support_group(event.chat.id):
        return

    user = event.new_chat_member.user
    old_status = member_status(event.old_chat_member)
    new_status = member_status(event.new_chat_member)
    if old_status == new_status:
        return

    if old_status in {"left", "kicked"} and new_status in {"member", "restricted"}:
        access = await evaluate_group_join_access(
            event.chat.id,
            user.id,
            chat_title=event.chat.title or "",
            chat_member=event.new_chat_member,
        )
        if not access["allowed"]:
            try:
                await bot.ban_chat_member(chat_id=event.chat.id, user_id=int(user.id))
                await bot.unban_chat_member(chat_id=event.chat.id, user_id=int(user.id))
                record_support_event(
                    "member_kicked",
                    user.id,
                    username=user.username or "",
                    full_name=user.full_name or "",
                    chat_id=str(event.chat.id),
                    chat_title=event.chat.title or "",
                    raw_data={
                        "reason": access["reason"],
                        "source": "join_guard",
                        "old_status": old_status,
                        "new_status": new_status,
                        **(access.get("details") or {}),
                    },
                )
            except TelegramBadRequest as exc:
                record_support_event(
                    "member_kick_failed",
                    user.id,
                    username=user.username or "",
                    full_name=user.full_name or "",
                    chat_id=str(event.chat.id),
                    chat_title=event.chat.title or "",
                    raw_data={
                        "reason": access["reason"],
                        "source": "join_guard",
                        "error": str(exc),
                        "old_status": old_status,
                        "new_status": new_status,
                        **(access.get("details") or {}),
                    },
                )
            except Exception as exc:
                record_support_event(
                    "member_kick_failed",
                    user.id,
                    username=user.username or "",
                    full_name=user.full_name or "",
                    chat_id=str(event.chat.id),
                    chat_title=event.chat.title or "",
                    raw_data={
                        "reason": access["reason"],
                        "source": "join_guard",
                        "error": str(exc),
                        "old_status": old_status,
                        "new_status": new_status,
                        **(access.get("details") or {}),
                    },
                )
            return

        record_support_event(
            "support_joined",
            user.id,
            username=user.username or "",
            full_name=user.full_name or "",
            chat_id=str(event.chat.id),
            chat_title=event.chat.title or "",
            raw_data={
                "old_status": old_status,
                "new_status": new_status,
                "source": "join_guard",
                **(access.get("details") or {}),
            },
        )
        return

    if new_status in {"left", "kicked"}:
        event_type = "support_left"
    else:
        event_type = ""

    if not event_type:
        return

    record_support_event(
        event_type,
        user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        chat_id=str(event.chat.id),
        chat_title=event.chat.title or "",
        raw_data={"old_status": old_status, "new_status": new_status},
    )
