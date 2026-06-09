from bot_instance import bot
from database import db
from scheduler import now_local, parse_expire_datetime, plan_group_ids, user_active_group_ids
from supabase_store import supabase_store


def _normalize_chat_id(value):
    raw = str(value or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def support_event_time(event):
    return str((event or {}).get("created_at") or "")


def latest_event(events, event_type, user_id, order_id=None, chat_id=None):
    user_id = str(user_id or "")
    order_id = str(order_id or "") if order_id is not None else None
    chat_id = _normalize_chat_id(chat_id) if chat_id is not None else None
    matches = [
        event
        for event in events
        if event.get("event_type") == event_type
        and str(event.get("telegram_user_id") or "") == user_id
        and (order_id is None or str(event.get("order_id") or "") == order_id)
        and (chat_id is None or _normalize_chat_id(event.get("chat_id")) == chat_id)
    ]
    matches.sort(key=support_event_time, reverse=True)
    return matches[0] if matches else None


def support_event_error(event):
    raw_data = (event or {}).get("raw_data") or {}
    if isinstance(raw_data, dict):
        return str(raw_data.get("error") or raw_data.get("message") or "").strip()
    return str(raw_data or "").strip()


def member_status_value(member):
    raw_status = getattr(member, "status", "")
    return str(getattr(raw_status, "value", raw_status)).lower()


async def member_live_state(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
        status = member_status_value(member)
        present = status not in {"left", "kicked", "banned"}
        if hasattr(member, "is_member") and member.is_member is False:
            present = False
        return {"checked": True, "present": present, "status": status, "error": ""}
    except Exception as exc:
        text = str(exc)
        lower = text.lower()
        if "user not found" in lower or "participant_id_invalid" in lower:
            return {"checked": True, "present": False, "status": "left", "error": ""}
        return {"checked": True, "present": None, "status": "unknown", "error": text}


def order_display_name(order, support_events):
    user_id = str(order.get("telegram_user_id") or "")
    direct = str(order.get("full_name") or "").strip()
    if direct and direct != "-":
        return direct
    for event in support_events:
        if str(event.get("telegram_user_id") or "") != user_id:
            continue
        name = str(event.get("full_name") or event.get("username") or "").strip()
        if name and name != "-":
            return name
    return user_id


def group_label_for_chat_id(chat_id):
    target = _normalize_chat_id(chat_id)
    for group_no in range(1, 101):
        gid = _normalize_chat_id(db.get_config(f"ID_G{group_no}", ""))
        if gid and gid == target:
            return db.get_config(f"BTN_G{group_no}", f"G{group_no}")
    return target or "-"


async def build_vip_group_audit_rows(live=False, order_id_filter="", user_id_filter="", chat_id_filter=""):
    db.reload_config(force=True)
    now = now_local().replace(tzinfo=None)
    orders = supabase_store.list_scheduler_orders(limit=5000)
    users_data = [supabase_store.order_to_sheet_row(order) for order in orders]
    try:
        support_events = supabase_store.list_support_events(limit=5000)
    except Exception:
        support_events = []

    rows = []
    for order in orders:
        order_id = str(order.get("order_id") or "")
        user_id = str(order.get("telegram_user_id") or "")
        if order_id_filter and order_id != str(order_id_filter):
            continue
        if user_id_filter and user_id != str(user_id_filter):
            continue

        plan_name = str(order.get("plan_name") or "")
        display_name = order_display_name(order, support_events)
        raw_expire_at = order.get("expire_at")
        expire_at = parse_expire_datetime(raw_expire_at)
        if raw_expire_at and not expire_at:
            continue
        if not expire_at or expire_at > now:
            continue

        current_group_ids = [str(item) for item in plan_group_ids(plan_name)]
        active_group_ids = {str(item) for item in user_active_group_ids(user_id, order_id, users_data, now)}

        for gid in current_group_ids:
            normalized_gid = _normalize_chat_id(gid)
            if chat_id_filter and _normalize_chat_id(chat_id_filter) != normalized_gid:
                continue

            retained = normalized_gid in active_group_ids
            latest_order_kick = latest_event(support_events, "member_kicked", user_id, order_id, normalized_gid)
            latest_group_kick = latest_event(support_events, "member_kicked", user_id, None, normalized_gid)
            latest_kick = latest_order_kick or latest_group_kick

            live_state = {"checked": False, "present": None, "status": "", "error": ""}
            if live:
                live_state = await member_live_state(normalized_gid, user_id)

            status = "ACTIVE_RETAINED" if retained else "LEFT_GROUP" if live_state["present"] is False else "KICKED" if latest_kick else "WAITING_CHECK"
            status_label = (
                "Còn quyền active"
                if retained
                else "Đã out group"
                if live_state["present"] is False
                else "Đã kick"
                if latest_kick
                else "Chưa xác nhận"
            )

            rows.append({
                "audit_id": f"{order_id}:{normalized_gid}",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": order.get("expire_at"),
                "group_id": normalized_gid,
                "group_name": group_label_for_chat_id(normalized_gid),
                "status": status,
                "status_label": status_label,
                "needs_action": not retained and (live_state["present"] is False or not latest_kick),
                "latest_kick_at": (latest_kick or {}).get("created_at") or "",
                "latest_error": support_event_error(latest_event(support_events, "member_kick_failed", user_id, order_id, normalized_gid)),
                "live_checked": live_state["checked"],
                "live_status": live_state["status"],
                "live_present": live_state["present"],
                "order_active_group_ids": sorted(active_group_ids),
                "current_group_ids": current_group_ids,
            })

    priority = {"LEFT_GROUP": 0, "WAITING_CHECK": 1, "KICKED": 2, "ACTIVE_RETAINED": 3}
    rows.sort(key=lambda item: (priority.get(item["status"], 9), str(item.get("expire_at") or "")))
    return rows
