from __future__ import annotations

from datetime import datetime

from legacy_support_boundary import read_support_events_legacy
from renewal_admin_audit_service import build_kick_audit_rows
from renewal_admin_review_service import review_renewal_task_v2
from renewal_admin_view_service import build_renewal_admin_view


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def _store():
    return _scheduler().supabase_store


async def get_blacklist(limit: int = 500):
    return {"data": _store().list_blacklist(limit=limit)}


async def upsert_blacklist(body: dict):
    return {"data": _store().upsert_blacklist(body)}


async def delete_blacklist(telegram_user_id: str):
    return {"data": _store().delete_blacklist(telegram_user_id)}


async def support_events(limit: int = 1000, updated_after: str | None = None, query: str = ""):
    return read_support_events_legacy(_store(), limit=limit, updated_after=updated_after, query=query)


async def customer_identity_history(telegram_user_id: str, limit: int = 50):
    safe_limit = max(1, min(int(limit or 50), 500))
    return {"data": _store().get_customer_identity_history(telegram_user_id, limit=safe_limit)}


async def support_cases(query: str = "", limit: int = 20, status: str = "", message_limit: int = 20, updated_after: str | None = None):
    safe_limit = max(1, min(int(limit or 20), 50))
    safe_message_limit = max(1, min(int(message_limit or 20), 200))
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in {"open", "closed"}:
        normalized_status = ""
    rows = (
        _store().search_support_tickets(query, limit=safe_limit)
        if str(query or "").strip()
        else _store().list_support_tickets(limit=safe_limit, status=normalized_status or None, updated_after=updated_after)
    )
    if normalized_status and str(query or "").strip():
        rows = [row for row in rows if str(row.get("status") or "").strip().lower() == normalized_status]
    message_rows = _store().list_support_messages_for_tickets([row.get("id") for row in rows], limit=safe_message_limit)
    messages_by_ticket = {}
    for message in message_rows:
        messages_by_ticket.setdefault(str(message.get("ticket_id") or ""), []).append(message)
    data = [{"ticket": row, "messages": messages_by_ticket.get(str(row.get("id") or ""), [])[-safe_message_limit:]} for row in rows]
    return {"data": data}


async def update_support_case(ticket_id: str, body: dict):
    status = str(body.get("status") or "").strip().lower()
    if status not in {"open", "closed"}:
        raise ValueError("Trạng thái ticket không hợp lệ.")
    payload = {
        "status": status,
        "updated_at": datetime.now().isoformat(),
        "closed_at": datetime.now().isoformat() if status == "closed" else None,
    }
    updated = _store().update_support_ticket(ticket_id, payload)
    return {"data": updated[0] if updated else None}


async def kick_audit(live: bool = False, updated_after: str | None = None):
    return {"data": await build_kick_audit_rows(live=live, updated_after=updated_after)}


async def group_membership_audit_preview(group_id: str, csv_text: str, *, group_name: str = "", live: bool = False):
    from web_backend import build_group_membership_audit_rows

    return {"data": await build_group_membership_audit_rows(group_id, csv_text, group_name=group_name, live=live)}


async def renewal_kick_v2(updated_after: str | None = None):
    scheduler = _scheduler()
    store = _store()
    try:
        tasks = store.list_renewal_kick_tasks_v2(limit=5000)
    except Exception:
        tasks = []
    try:
        group_tasks = store.list_due_renewal_kick_group_tasks_v2(limit=5000)
    except Exception:
        group_tasks = []
    try:
        attempts = store._request("GET", "renewal_kick_attempts_v2", params={"select": "*", "order": "started_at.desc", "limit": "2000"})
    except Exception:
        attempts = []
    if updated_after:
        tasks = [row for row in tasks if str(row.get("updated_at") or row.get("last_transition_at") or "") >= updated_after]
        group_tasks = [row for row in group_tasks if str(row.get("updated_at") or row.get("last_transition_at") or "") >= updated_after]
        attempts = [row for row in attempts if str(row.get("started_at") or "") >= updated_after]
    from scheduler import parse_expire_datetime
    orders = store.list_scheduler_orders(limit=5000, updated_after=updated_after) if hasattr(store, "list_scheduler_orders") else []
    view = build_renewal_admin_view(orders, tasks, group_tasks, attempts, scheduler.now_local_naive(), parser=parse_expire_datetime)
    return {"data": tasks, "group_tasks": group_tasks, "attempts": attempts, "view": view}


async def renewal_kick_v2_review(body: dict):
    return {"data": await review_renewal_task_v2(body)}


async def vip_group_audit(live: bool = False, updated_after: str | None = None):
    from web_backend import build_vip_group_audit_rows
    return {"data": await build_vip_group_audit_rows(live=live, updated_after=updated_after)}


async def vip_member_audit(live: bool = False, risk_type: str = "ALL", updated_after: str | None = None):
    from web_backend import build_vip_member_risk_rows
    return {"data": await build_vip_member_risk_rows(live=live, risk_type_filter=risk_type, updated_after=updated_after)}
