from __future__ import annotations

import json
import os
import sys
from collections import Counter

from hidden_group_utils import resolve_plan_groups
from scripts.production_renewal_snapshot import read_all
from scripts.stale_task_membership_audit import telegram_get_member


def plan_groups(plan_name: str):
    try:
        return {str(group_id) for group_id, _name in resolve_plan_groups(plan_name)}
    except Exception:
        return set()


def build_dry_run(tasks, orders, token: str):
    orders_by_user = {}
    for order in orders:
        if str(order.get("status") or "").upper() != "PAID":
            continue
        orders_by_user.setdefault(str(order.get("telegram_user_id") or ""), []).append(order)

    outcomes = Counter()
    guards = Counter()
    planned_rows = []
    for task in tasks:
        user_id = str(task.get("telegram_user_id") or "")
        group_id = str(task.get("group_id") or "")
        plan_name = str(task.get("plan_name") or "")
        if not user_id or not group_id:
            outcomes["review_invalid_identity"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "review_invalid_identity"})
            continue
        active_order = False
        mapping_available = True
        for order in orders_by_user.get(user_id, []):
            expected = plan_groups(str(order.get("plan_name") or ""))
            if not expected:
                mapping_available = False
            if group_id in expected:
                active_order = True
        if not mapping_available:
            guards["active_order_mapping_unavailable"] += 1
            outcomes["review_mapping_unavailable"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "review_mapping_unavailable"})
            continue
        if active_order:
            guards["active_order"] += 1
            outcomes["retain_active_order"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "retain_active_order"})
            continue
        presence, reason = telegram_get_member(token, group_id, user_id)
        if presence == "absent":
            outcomes["confirm_done"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "confirm_done", "reason": reason})
        elif presence == "present":
            outcomes["would_kick"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "would_kick", "reason": reason})
        else:
            outcomes["review_unknown_membership"] += 1
            planned_rows.append({"task_id": task.get("id"), "outcome": "review_unknown_membership", "reason": reason})
    return {
        "mode": "dry_run",
        "scanned": len(tasks),
        "outcomes": dict(outcomes),
        "guards": dict(guards),
        "planned_rows": planned_rows,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }


def main():
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    token = os.getenv("BOT_TOKEN")
    if not base_url or not key or not token:
        print("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and BOT_TOKEN are required", file=sys.stderr)
        return 2
    try:
        tasks = read_all(base_url, key, "renewal_kick_group_tasks_v2", {"select": "telegram_user_id,group_id,plan_name,group_state", "group_state": "eq.processing"})
        orders = read_all(base_url, key, "orders", {"select": "telegram_user_id,status,plan_name", "status": "eq.PAID"})
        print(json.dumps(build_dry_run(tasks, orders, token), ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"worker dry-run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
