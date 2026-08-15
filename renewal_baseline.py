from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def build_renewal_baseline(*, orders: Iterable[dict[str, Any]], tasks: Iterable[dict[str, Any]], group_tasks: Iterable[dict[str, Any]], support_events: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    """Build a read-only migration snapshot from already-fetched rows."""
    order_rows = list(orders)
    task_rows = list(tasks)
    group_rows = list(group_tasks)
    event_rows = list(support_events)
    return {
        "orders_by_status": dict(Counter(str(row.get("status") or "UNKNOWN").upper() for row in order_rows)),
        "tasks_by_state": dict(Counter(str(row.get("task_state") or "UNKNOWN").lower() for row in task_rows)),
        "groups_by_state": dict(Counter(str(row.get("group_state") or "UNKNOWN").lower() for row in group_rows)),
        "stale_lock_count": sum(1 for row in task_rows + group_rows if row.get("locked_at") and not row.get("resolved_at")),
        "review_required_count": sum(1 for row in task_rows + group_rows if str(row.get("task_state") or row.get("group_state") or "").lower() == "review_required"),
        "support_events_by_type": dict(Counter(str(row.get("event_type") or "UNKNOWN") for row in event_rows)),
        "totals": {"orders": len(order_rows), "tasks": len(task_rows), "group_tasks": len(group_rows), "support_events": len(event_rows)},
    }
