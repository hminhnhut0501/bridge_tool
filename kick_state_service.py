from __future__ import annotations

import logging

from supabase_store import supabase_store


def _latest_renewal_kick_v2_task(order_id, user_id=None):
    if not supabase_store.enabled:
        return None
    try:
        task = supabase_store.get_renewal_kick_task_v2(order_id, user_id)
    except Exception as exc:
        logging.warning("⚠️ Không đọc được renewal_kick_task_v2 order=%s user=%s: %s", order_id, user_id, exc)
        task = None
    return task


def _latest_renewal_kick_v2_group_task(order_id, user_id, chat_id):
    if not supabase_store.enabled:
        return None
    try:
        group_tasks = supabase_store.list_due_renewal_kick_group_tasks_v2(limit=1000)
    except Exception as exc:
        logging.warning("⚠️ Không đọc được renewal_kick_group_tasks_v2 order=%s user=%s chat=%s: %s", order_id, user_id, chat_id, exc)
        group_tasks = []
    for group_task in group_tasks:
        if str(group_task.get("order_id") or "") != str(order_id):
            continue
        if str(group_task.get("telegram_user_id") or "") != str(user_id):
            continue
        if str(group_task.get("group_id") or "") != str(chat_id):
            continue
        return group_task
    return None


def renewal_kick_state_v2(user_id, order_id, chat_id):
    task = _latest_renewal_kick_v2_task(order_id, user_id)
    if task:
        task_state = str(task.get("task_state") or "").strip().lower()
        if task_state in {"done"}:
            return "done", task
        if task_state in {"failed_terminal", "error"}:
            return "error", task
        if task_state in {"blocked", "blocked_active_order"}:
            return "blocked", task
        if task_state in {"review_required"}:
            return "review_required", task
        if task_state in {"queued", "running", "waiting_confirm", "retry_scheduled", "pending_confirm", "retry_pending", "processing"}:
            return "processing", task

    group_task = _latest_renewal_kick_v2_group_task(order_id, user_id, chat_id)
    if group_task:
        state = str(group_task.get("group_state") or "").strip().lower()
        if state in {"kicked", "retained"}:
            return "done", group_task
        if state in {"failed_terminal"}:
            return "error", group_task
        if state in {"blocked_active_order"}:
            return "blocked", group_task
        if state in {"review_required"}:
            return "review_required", group_task
        if state in {"pending", "selected", "processing", "waiting_confirm", "retry_scheduled", "unmapped"}:
            return "processing", group_task
    return "none", None


def is_kick_finalized(user_id, order_id, chat_id):
    kick_state, _ = renewal_kick_state_v2(user_id, order_id, chat_id)
    return kick_state == "done"
