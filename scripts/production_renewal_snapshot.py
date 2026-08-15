from __future__ import annotations

import json
import os
import sys
import urllib.parse
from collections import Counter
from datetime import datetime, timedelta, timezone
from scripts.readonly_http import get_json


PAGE_SIZE = 1000


def read_page(base_url: str, key: str, table: str, params: dict[str, str], offset: int):
    query = dict(params)
    query.update({"limit": str(PAGE_SIZE), "offset": str(offset)})
    url = f"{base_url.rstrip('/')}/rest/v1/{table}?{urllib.parse.urlencode(query)}"
    return get_json(url, headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=30, retries=3)


def read_all(base_url: str, key: str, table: str, params: dict[str, str]):
    rows = []
    offset = 0
    while True:
        page = read_page(base_url, key, table, params, offset)
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def count_values(rows, field, *, upper=False):
    values = []
    for row in rows:
        value = str(row.get(field) or "UNKNOWN")
        values.append(value.upper() if upper else value.lower())
    return dict(Counter(values))


def build_snapshot(base_url: str, key: str, *, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    event_since = (now - timedelta(days=14)).isoformat()
    orders = read_all(base_url, key, "orders", {"select": "order_id,status,expire_at,telegram_user_id,plan_name", "status": "in.(PAID,EXPIRED)"})
    tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "id,order_id,telegram_user_id,task_state,updated_at,locked_at,resolved_at"})
    groups = read_all(base_url, key, "renewal_kick_group_tasks_v2", {"select": "id,task_id,order_id,telegram_user_id,group_id,group_state,updated_at,locked_at,resolved_at"})
    attempts = read_all(base_url, key, "renewal_kick_attempts_v2", {"select": "id,task_id,group_task_id,order_id,attempt_state,started_at"})
    events = read_all(base_url, key, "support_events", {"select": "event_type,created_at", "created_at": f"gte.{event_since}"})

    task_ids = {str(row.get("id")) for row in tasks if row.get("id")}
    group_ids = {str(row.get("id")) for row in groups if row.get("id")}
    order_ids = {str(row.get("order_id")) for row in orders if row.get("order_id")}
    task_order_ids = {str(row.get("order_id")) for row in tasks if row.get("order_id")}
    group_task_ids = {str(row.get("task_id")) for row in groups if row.get("task_id")}

    return {
        "snapshot_at": now.isoformat(),
        "event_window_start": event_since,
        "counts": {
            "orders": len(orders),
            "tasks": len(tasks),
            "group_tasks": len(groups),
            "attempts": len(attempts),
            "support_events": len(events),
        },
        "orders_by_status": count_values(orders, "status", upper=True),
        "tasks_by_state": count_values(tasks, "task_state"),
        "groups_by_state": count_values(groups, "group_state"),
        "attempts_by_state": count_values(attempts, "attempt_state"),
        "support_events_by_type": count_values(events, "event_type"),
        "integrity": {
            "orders_without_task": len(order_ids - task_order_ids),
            "expired_orders_without_task": sum(
                1 for row in orders
                if str(row.get("status") or "").upper() == "EXPIRED"
                and str(row.get("order_id") or "") not in task_order_ids
            ),
            "paid_orders_without_task": sum(
                1 for row in orders
                if str(row.get("status") or "").upper() == "PAID"
                and str(row.get("order_id") or "") not in task_order_ids
            ),
            "tasks_without_order": len(task_order_ids - order_ids),
            "groups_without_parent": len(group_task_ids - task_ids),
            "duplicate_task_keys": _duplicate_count(tasks, ("order_id", "telegram_user_id")),
            "duplicate_group_keys": _duplicate_count(groups, ("task_id", "group_id")),
            "stale_locked_tasks": sum(1 for row in tasks + groups if row.get("locked_at") and not row.get("resolved_at")),
            "review_required": sum(1 for row in tasks + groups if str(row.get("task_state") or row.get("group_state") or "").lower() == "review_required"),
        },
    }


def _duplicate_count(rows, fields):
    keys = [tuple(str(row.get(field) or "") for field in fields) for row in rows]
    return len(keys) - len(set(keys))


def main():
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        print(json.dumps(build_snapshot(base_url, key), ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"snapshot failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
