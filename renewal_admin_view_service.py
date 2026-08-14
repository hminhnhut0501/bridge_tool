from __future__ import annotations

from collections import defaultdict

from new_core.contract import assert_contract_membership, KICK_STATE_CONTRACT, ORDER_STATE_CONTRACT
from new_core.state import normalize_kick_state, normalize_order_state


def build_renewal_admin_view(orders, tasks, group_tasks, attempts, now, *, parser):
    tasks_by_order = {}
    for task in tasks or []:
        order_id = str(task.get("order_id") or "").strip()
        if not order_id:
            continue
        current = tasks_by_order.get(order_id)
        if not current or str(task.get("updated_at") or task.get("last_transition_at") or "") >= str(current.get("updated_at") or current.get("last_transition_at") or ""):
            tasks_by_order[order_id] = task

    groups_by_order = defaultdict(list)
    for group_task in group_tasks or []:
        order_id = str(group_task.get("order_id") or "").strip()
        if order_id:
            groups_by_order[order_id].append(group_task)

    attempts_by_order = defaultdict(list)
    for attempt in attempts or []:
        order_id = str(attempt.get("order_id") or "").strip()
        if order_id:
            attempts_by_order[order_id].append(attempt)

    rows = []
    for order in orders or []:
        order_id = str(order.get("order_id") or "").strip()
        user_id = str(order.get("telegram_user_id") or "").strip()
        normalized = normalize_order_state(order, now, parser=parser)
        if assert_contract_membership(normalized.state, ORDER_STATE_CONTRACT, default="unknown") != "expired":
            continue
        task = tasks_by_order.get(order_id)
        groups = groups_by_order.get(order_id, [])
        task_state = str((task or {}).get("task_state") or "").strip().lower()
        kick_state = normalize_kick_state(renewal_task=task, support_event_state="none")
        group_states = [normalize_kick_state(group_task=group, support_event_state="none") for group in groups]
        kicked = sum(1 for state in group_states if state == "done")
        blocked = sum(1 for state in group_states if state == "blocked")
        review = sum(1 for state in group_states if state == "review_required")
        processing = sum(1 for state in group_states if state == "processing")
        pending = len(groups) - kicked - blocked - review - processing
        needs_action = kick_state not in {"done", "failed_terminal"} or blocked > 0 or review > 0 or pending > 0
        status = (
            "DONE" if kick_state == "done" and pending == 0 and review == 0 and blocked == 0
            else "REVIEW_REQUIRED" if review > 0 or kick_state == "review_required"
            else "BLOCKED" if blocked > 0 or kick_state == "blocked"
            else "PROCESSING" if processing > 0 or kick_state == "processing"
            else "FAILED" if kick_state == "failed_terminal"
            else "WAITING"
        )
        rows.append({
            "order_id": order_id,
            "telegram_user_id": user_id,
            "customer_name": str(order.get("full_name") or user_id or order_id or "-"),
            "plan_name": str(order.get("plan_name") or ""),
            "expire_at": str(order.get("expire_at") or ""),
            "task_state": task_state or "none",
            "kick_state": kick_state,
            "status": status,
            "status_label": {
                "DONE": "Đã kick xong",
                "REVIEW_REQUIRED": "Cần review",
                "BLOCKED": "Bị giữ bởi đơn active khác",
                "PROCESSING": "Đang kick",
                "FAILED": "Lỗi kick",
                "WAITING": "Chờ kick",
            }[status],
            "needs_action": needs_action,
            "task_id": str((task or {}).get("id") or ""),
            "group_count": len(groups),
            "kicked_count": kicked,
            "blocked_count": blocked,
            "review_count": review,
            "pending_count": pending,
            "latest_kick_at": str((task or {}).get("updated_at") or (task or {}).get("last_transition_at") or ""),
            "latest_error": str((task or {}).get("last_error") or (task or {}).get("review_reason") or ""),
            "groups": [
                {
                    "group_id": str(group.get("group_id") or ""),
                    "group_name": str(group.get("group_name") or group.get("group_id") or ""),
                    "group_state": str(group.get("group_state") or ""),
                    "status": normalize_kick_state(group_task=group, support_event_state="none"),
                    "latest_error": str(group.get("last_error") or group.get("review_reason") or ""),
                }
                for group in groups
            ],
            "attempt_count": len(attempts_by_order.get(order_id, [])),
            "reason": normalized.reason,
        })

    rows.sort(key=lambda item: (item["status"] != "REVIEW_REQUIRED", item["status"] != "BLOCKED", item["status"] != "PROCESSING", item["customer_name"]))
    return {
        "rows": rows,
        "summary": {
            "total": len(rows),
            "needs_action": sum(1 for row in rows if row["needs_action"]),
            "done": sum(1 for row in rows if row["status"] == "DONE"),
            "review": sum(1 for row in rows if row["status"] == "REVIEW_REQUIRED"),
            "blocked": sum(1 for row in rows if row["status"] == "BLOCKED"),
            "processing": sum(1 for row in rows if row["status"] == "PROCESSING"),
        },
    }
