from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_parent_group_reconciliation(*, orders: list[dict[str, Any]], tasks: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[str, Any]:
    orders_by_id = {str(row.get("order_id")): row for row in orders if row.get("order_id")}
    tasks_by_id = {str(row.get("id")): row for row in tasks if row.get("id")}
    groups_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in groups:
        groups_by_task[str(row.get("task_id") or "")].append(row)

    parent_rows = []
    for task_id, task in tasks_by_id.items():
        order_id = str(task.get("order_id") or "")
        group_rows = groups_by_task.get(task_id, [])
        parent_rows.append({
            "task_id": task_id,
            "order_id": order_id,
            "telegram_user_id": task.get("telegram_user_id"),
            "task_state": task.get("task_state"),
            "order_exists": order_id in orders_by_id,
            "group_count": len(group_rows),
            "group_ids": [row.get("group_id") for row in group_rows],
            "group_task_ids": [row.get("id") for row in group_rows],
        })

    orphan_groups = [
        row for row in groups
        if str(row.get("task_id") or "") not in tasks_by_id
    ]
    tasks_without_groups = [row for row in parent_rows if row["group_count"] == 0]
    mismatched_users = [
        row for row in groups
        if str(row.get("task_id") or "") in tasks_by_id
        and str(row.get("telegram_user_id") or "") != str(tasks_by_id[str(row.get("task_id"))].get("telegram_user_id") or "")
    ]
    duplicate_groups = []
    seen: dict[tuple[str, str], int] = defaultdict(int)
    for row in groups:
        key = (str(row.get("task_id") or ""), str(row.get("group_id") or ""))
        seen[key] += 1
    duplicate_groups = [{"task_id": key[0], "group_id": key[1], "count": count} for key, count in seen.items() if count > 1]

    return {
        "contract": "renewal_parent_group_reconciliation_v1",
        "mode": "read_only",
        "counts": {"orders": len(orders), "tasks": len(tasks), "group_tasks": len(groups)},
        "parents": parent_rows,
        "orphan_group_tasks": orphan_groups,
        "tasks_without_groups": tasks_without_groups,
        "mismatched_group_users": mismatched_users,
        "duplicate_group_keys": duplicate_groups,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }
