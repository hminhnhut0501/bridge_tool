from aiogram import Router
from aiogram.types import ChatMemberUpdated

from support_utils import is_support_group, record_support_event
from database import db

router = Router()


def member_status(member):
    raw = str(getattr(member, "status", "") or "").lower()
    return raw.rsplit(".", 1)[-1]


def member_can_send(member):
    if member is None:
        return None
    permissions = getattr(member, "permissions", None)
    if permissions is None:
        return None
    can_send = getattr(permissions, "can_send_messages", None)
    if can_send is not None:
        return bool(can_send)
    restricted = getattr(member, "is_member", None)
    if restricted is False:
        return False
    return None


def vip_group_ids():
    ids = set()
    for group_no in range(1, 101):
        gid = str(db.get_config(f"ID_G{group_no}", "") or "").strip()
        if gid and not is_support_group(gid):
            ids.add(gid)
    return ids


def event_payload(old_status, new_status, old_member, new_member):
    payload = {"old_status": old_status, "new_status": new_status}
    old_can_send = member_can_send(old_member)
    new_can_send = member_can_send(new_member)
    if old_can_send is not None:
        payload["old_can_send_messages"] = old_can_send
    if new_can_send is not None:
        payload["new_can_send_messages"] = new_can_send
    return payload


@router.chat_member()
async def vip_group_member_update(event: ChatMemberUpdated):
    if str(event.chat.id).strip() not in vip_group_ids():
        return

    user = event.new_chat_member.user
    old_status = member_status(event.old_chat_member)
    new_status = member_status(event.new_chat_member)
    if old_status == new_status:
        return

    old_can_send = member_can_send(event.old_chat_member)
    new_can_send = member_can_send(event.new_chat_member)
    event_type = ""

    if new_status in {"left", "kicked"}:
        event_type = "vip_kicked" if new_status == "kicked" else "vip_left"
    elif old_status in {"left", "kicked"} and new_status in {"member", "restricted"}:
        if new_status == "restricted" and new_can_send is False:
            event_type = "vip_muted"
        else:
            event_type = "vip_joined"
    elif new_status == "restricted":
        if new_can_send is False:
            event_type = "vip_muted"
        elif old_status == "restricted" and old_can_send is False and new_can_send is not False:
            event_type = "vip_unmuted"
        elif old_status in {"member", "administrator", "creator"}:
            event_type = "vip_muted"
    elif old_status == "restricted" and old_can_send is False and new_can_send is not False:
        event_type = "vip_unmuted"
    elif old_status in {"member", "restricted", "administrator"} and new_status in {"administrator", "creator"}:
        event_type = "vip_promoted"
    elif old_status in {"administrator", "creator"} and new_status in {"member", "restricted"}:
        event_type = "vip_demoted"

    if not event_type:
        return

    record_support_event(
        event_type,
        user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        chat_id=str(event.chat.id),
        chat_title=event.chat.title or "",
        raw_data=event_payload(old_status, new_status, event.old_chat_member, event.new_chat_member),
    )
