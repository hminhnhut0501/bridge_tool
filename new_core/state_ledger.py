from __future__ import annotations

from collections import Counter
from typing import Any

from .contract import normalize_contract_kick_state, normalize_contract_kick_state_alias, normalize_contract_order_state


def _key(row: dict[str, Any], field: str) -> str:
    return str(row.get(field) or "").strip()


def build_state_ledger(*, orders: list[dict[str, Any]], tasks: list[dict[str, Any]], groups: list[dict[str, Any]], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    order_ids = {_key(row, "order_id") for row in orders if _key(row, "order_id")}
    task_ids = {_key(row, "id") for row in tasks if _key(row, "id")}
    task_order_ids = {_key(row, "order_id") for row in tasks if _key(row, "order_id")}
    group_task_ids = {_key(row, "task_id") for row in groups if _key(row, "task_id")}

    return {
        "contract": "renewal_state_ledger_v1",
        "source": "orders/renewal_kick_tasks_v2/renewal_kick_group_tasks_v2/renewal_kick_attempts_v2",
        "support_events_used": False,
        "counts": {
            "orders": len(orders),
            "tasks": len(tasks),
            "group_tasks": len(groups),
            "attempts": len(attempts),
        },
        "orders_by_state": dict(Counter(normalize_contract_order_state(row.get("status")) for row in orders)),
        "tasks_by_state": dict(Counter(normalize_contract_kick_state_alias(row.get("task_state")) for row in tasks)),
        "groups_by_state": dict(Counter(normalize_contract_kick_state_alias(row.get("group_state")) for row in groups)),
        "integrity": {
            "orders_without_task": sorted(order_ids - task_order_ids),
            "tasks_without_order": sorted(task_order_ids - order_ids),
            "groups_without_parent": sorted(group_task_ids - task_ids),
            "duplicate_task_keys": _duplicate_keys(tasks, ("order_id", "telegram_user_id")),
            "duplicate_group_keys": _duplicate_keys(groups, ("task_id", "group_id")),
            "stale_locked_tasks": [
                row.get("id") for row in tasks + groups
                if row.get("locked_at") and not row.get("resolved_at")
            ],
        },
        "attempts_by_state": dict(Counter(normalize_contract_kick_state_alias(row.get("attempt_state")) for row in attempts)),
    }


def _duplicate_keys(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, ...], int] = {}
    for row in rows:
        key = tuple(_key(row, field) for field in fields)
        seen[key] = seen.get(key, 0) + 1
    return [{"key": list(key), "count": count} for key, count in seen.items() if count > 1]
