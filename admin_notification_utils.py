def admin_notification_from_support_event(event: dict):
    event_type = str(event.get("event_type") or "").strip()
    if event_type not in {"delivery_success", "support_ticket_created"}:
        return None

    telegram_user_id = str(event.get("telegram_user_id") or "").strip()
    full_name = str(event.get("full_name") or "").strip()
    plan_name = str(event.get("plan_name") or "").strip()
    order_id = str(event.get("order_id") or "").strip()
    raw_data = event.get("raw_data") or {}
    if not isinstance(raw_data, dict):
        raw_data = {}
    created_at = str(event.get("created_at") or "").strip()
    if event_type == "delivery_success":
        title = "Đơn auto-paid mới"
        detail_parts = [full_name or telegram_user_id, plan_name, order_id]
        kind = "order"
    else:
        title = "Tin nhắn riêng mới"
        ticket_no = str(raw_data.get("ticket_no") or "").strip()
        subject = order_id or str(raw_data.get("subject") or "").strip()
        detail_parts = [full_name or telegram_user_id, subject, ticket_no]
        kind = "message"

    detail = " • ".join([part for part in detail_parts if part]) or telegram_user_id or "-"
    return {
        "id": f"{event_type}:{event.get('id')}",
        "kind": kind,
        "title": title,
        "detail": detail,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name,
        "plan_name": plan_name,
        "order_id": order_id,
        "created_at": created_at,
        "raw_data": raw_data,
    }
