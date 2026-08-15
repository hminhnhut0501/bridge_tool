from __future__ import annotations

import logging

from new_core.state import normalize_kick_state


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def _supabase_store():
    return _scheduler().supabase_store


def _latest_renewal_kick_v2_task(order_id, user_id=None):
    store = _supabase_store()
    if not store.enabled:
        return None
    try:
        task = store.get_renewal_kick_task_v2(order_id, user_id)
    except Exception as exc:
        logging.warning("⚠️ Không đọc được renewal_kick_task_v2 order=%s user=%s: %s", order_id, user_id, exc)
        task = None
    return task


def _latest_renewal_kick_v2_group_task(order_id, user_id, chat_id):
    store = _supabase_store()
    if not store.enabled:
        return None
    try:
        group_tasks = store.list_due_renewal_kick_group_tasks_v2(limit=1000)
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
        state = normalize_kick_state(renewal_task=task)
        if state == "done":
            return "done", task
        if state == "failed_terminal":
            return "error", task
        if state == "blocked":
            return "blocked", task
        if state == "review_required":
            return "review_required", task
        if state == "processing":
            return "processing", task

    group_task = _latest_renewal_kick_v2_group_task(order_id, user_id, chat_id)
    if group_task:
        state = normalize_kick_state(group_task=group_task)
        if state == "done":
            return "done", group_task
        if state == "failed_terminal":
            return "error", group_task
        if state == "blocked":
            return "blocked", group_task
        if state == "review_required":
            return "review_required", group_task
        if state == "processing":
            return "processing", group_task
    return "none", None


def is_kick_finalized(user_id, order_id, chat_id):
    kick_state, _ = renewal_kick_state_v2(user_id, order_id, chat_id)
    return kick_state == "done"
