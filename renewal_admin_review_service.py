from __future__ import annotations

from datetime import datetime

def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def _supabase_store():
    return _scheduler().supabase_store


def _group_tasks_for_task(group_tasks, task_id):
    return [row for row in group_tasks or [] if str(row.get("task_id") or "") == str(task_id)]


def _find_task(tasks, task_id="", order_id="", telegram_user_id=""):
    task = None
    if task_id:
        task = next((row for row in tasks if str(row.get("id") or "") == task_id), None)
    if not task and order_id:
        task = next((row for row in tasks if str(row.get("order_id") or "") == order_id and (not telegram_user_id or str(row.get("telegram_user_id") or "") == telegram_user_id)), None)
    if not task and order_id and telegram_user_id:
        task = next((row for row in tasks if str(row.get("order_id") or "") == telegram_user_id and str(row.get("telegram_user_id") or "") == order_id), None)
    return task


def _get_group_tasks():
    try:
        return _supabase_store()._request(
            "GET",
            "renewal_kick_group_tasks_v2",
            params={"select": "*", "order": "updated_at.desc", "limit": "5000"},
        )
    except Exception:
        return []


async def review_renewal_task_v2(body):
    scheduler = _scheduler()
    task_id = str(body.get("task_id") or "").strip()
    order_id = str(body.get("order_id") or "").strip()
    telegram_user_id = str(body.get("telegram_user_id") or "").strip()
    action = str(body.get("action") or "requeue").strip().lower()
    if action not in {"requeue", "close", "kick_now"}:
        raise ValueError("Hành động review không hợp lệ.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    store = _supabase_store()
    tasks = store.list_renewal_kick_tasks_v2(limit=5000)
    group_tasks = _get_group_tasks()

    task = _find_task(tasks, task_id=task_id, order_id=order_id, telegram_user_id=telegram_user_id)
    bootstrapped = False
    if not task and order_id:
        bootstrap_order = store.get_order(order_id)
        if bootstrap_order and (not telegram_user_id or str(bootstrap_order.get("telegram_user_id") or "") == telegram_user_id):
            bootstrap_user_id = str(bootstrap_order.get("telegram_user_id") or telegram_user_id or "").strip()
            bootstrap_plan_name = str(bootstrap_order.get("plan_name") or "").strip()
            bootstrap_group_ids = [str(item).strip() for item in scheduler.plan_group_ids(bootstrap_plan_name) if str(item).strip()]
            if bootstrap_group_ids:
                created_rows = store.upsert_renewal_kick_task_v2({
                    "order_id": order_id,
                    "telegram_user_id": bootstrap_user_id,
                    "plan_name": bootstrap_plan_name,
                    "task_state": "queued",
                    "priority": -100 if action == "kick_now" else 0,
                    "due_at": bootstrap_order.get("expire_at") or bootstrap_order.get("paid_at") or now,
                    "last_transition_at": now,
                    "resolved_at": None,
                    "metadata": {
                        "source": "admin_review_bootstrap",
                        "bootstrapped_from": "review_api",
                        "review_action": action,
                        "reason": str(body.get("reason") or ""),
                    },
                }) or []
                task = created_rows[0] if created_rows else None
                if task and task.get("id"):
                    for group_id in bootstrap_group_ids:
                        try:
                            group_rows = store.upsert_renewal_kick_group_task_v2({
                                "task_id": task.get("id"),
                                "order_id": order_id,
                                "telegram_user_id": bootstrap_user_id,
                                "group_id": group_id,
                                "group_name": group_id,
                                "group_no": group_id,
                                "plan_name": bootstrap_plan_name,
                                "group_state": "pending",
                                "attempt_count": 0,
                                "confirm_count": 0,
                                "first_due_at": bootstrap_order.get("expire_at") or bootstrap_order.get("paid_at") or now,
                                "next_retry_at": now,
                                "last_transition_at": now,
                                "metadata": {
                                    "source": "admin_review_bootstrap",
                                    "bootstrapped_from": "review_api",
                                },
                            }) or []
                            if group_rows:
                                bootstrapped = True
                        except Exception:
                            continue

    if not task:
        raise LookupError(
            {
                "task_id": task_id,
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "task_count": len(tasks),
                "bootstrapped": bootstrapped,
            }
        )

    related_groups = _group_tasks_for_task(group_tasks, task.get("id"))
    if action == "close":
        updated_task = store.update_renewal_kick_task_v2(str(task.get("id")), {
            "task_state": "failed_terminal",
            "resolved_at": now,
            "review_reason": str(body.get("reason") or "closed_by_admin"),
            "metadata": {**(task.get("metadata") or {}), "reason": "closed_by_admin", "review_action": "close"},
        })
        return updated_task[0] if isinstance(updated_task, list) and updated_task else updated_task

    if action == "kick_now":
        for group in related_groups:
            current_state = str(group.get("group_state") or "").strip().lower()
            if current_state in {"kicked", "retained", "blocked_active_order"}:
                continue
            try:
                store.update_renewal_kick_group_task_v2(str(group.get("id")), {
                    "group_state": "pending",
                    "locked_at": None,
                    "locked_by": None,
                    "next_retry_at": now,
                    "resolved_at": None,
                    "review_reason": "",
                    "last_reason": "kick_now",
                    "metadata": {**(group.get("metadata") or {}), "reason": "kick_now", "review_action": "kick_now"},
                })
            except Exception:
                continue

        updated_task = store.update_renewal_kick_task_v2(str(task.get("id")), {
            "task_state": "queued",
            "priority": -100,
            "review_reason": "",
            "last_reason": "kick_now",
            "last_transition_at": now,
            "resolved_at": None,
            "metadata": {**(task.get("metadata") or {}), "reason": "kick_now", "review_action": "kick_now", "priority": "urgent"},
        })
        return updated_task[0] if isinstance(updated_task, list) and updated_task else updated_task

    for group in related_groups:
        current_state = str(group.get("group_state") or "").strip().lower()
        if current_state in {"kicked", "retained", "blocked_active_order"}:
            continue
        try:
            store.update_renewal_kick_group_task_v2(str(group.get("id")), {
                "group_state": "retry_scheduled",
                "next_retry_at": now,
                "resolved_at": None,
                "review_reason": str(body.get("reason") or "review_requeue"),
                "metadata": {**(group.get("metadata") or {}), "reason": "review_requeue"},
            })
        except Exception:
            continue

    updated_task = store.update_renewal_kick_task_v2(str(task.get("id")), {
        "task_state": "queued",
        "review_reason": "",
        "last_reason": "review_requeued",
        "last_transition_at": now,
        "resolved_at": None,
        "metadata": {**(task.get("metadata") or {}), "reason": "review_requeued", "review_action": "requeue"},
    })
    return updated_task[0] if isinstance(updated_task, list) and updated_task else updated_task
