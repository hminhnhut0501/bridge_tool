from aiogram import Router
from aiogram.types import ChatMemberUpdated

from support_utils import is_support_group, record_support_event

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

    event_type = ""
    if old_status in {"left", "kicked"} and new_status in {"member", "restricted"}:
        event_type = "support_joined"
    elif new_status in {"left", "kicked"}:
        event_type = "support_left"

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
