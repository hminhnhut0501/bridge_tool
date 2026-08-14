from __future__ import annotations

import logging
from datetime import timedelta

from supabase_store import supabase_store


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


async def enqueue_expired_renewal_kick_tasks_v2(user_id, order_id, plan_name, expire_str, now, *, plan_group_cache=None):
    scheduler = _scheduler()
    current_group_ids = scheduler.cached_plan_group_ids(plan_name, plan_group_cache)
    if not supabase_store.enabled:
        return []
    logging.info("⏭ Bỏ qua legacy renewal_kick_tasks cho order=%s; chỉ ghi v2.", order_id)
    task_rows = []
    try:
        no_group_map = not current_group_ids
        parent_rows = supabase_store.upsert_renewal_kick_task_v2({
            "order_id": order_id,
            "telegram_user_id": user_id,
            "plan_name": plan_name,
            "task_state": "review_required" if no_group_map else "queued",
            "priority": -100 if no_group_map else 0,
            "due_at": expire_str,
            "last_transition_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "total_groups": len(current_group_ids),
            "pending_groups": len(current_group_ids),
            "review_groups": 1 if no_group_map else 0,
            "review_reason": "no_group_map" if no_group_map else "",
            "last_reason": "no_group_map" if no_group_map else "",
            "last_error": "no_group_map" if no_group_map else "",
            "metadata": {
                "source": "scheduler_expired",
                "queued_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "plan_name_raw": plan_name,
                "reason": "no_group_map" if no_group_map else "scheduler_expired",
            },
        }) or []
        parent_task_id = parent_rows[0]["id"] if parent_rows else None
        if parent_task_id:
            if current_group_ids:
                for gid in current_group_ids:
                    group_rows = supabase_store.upsert_renewal_kick_group_task_v2({
                        "task_id": parent_task_id,
                        "order_id": order_id,
                        "telegram_user_id": user_id,
                        "group_id": gid,
                        "group_name": gid,
                        "group_no": gid,
                        "plan_name": plan_name,
                        "group_state": "pending",
                        "attempt_count": 0,
                        "confirm_count": 0,
                        "first_due_at": expire_str,
                        "next_retry_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "last_transition_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "metadata": {
                            "source": "scheduler_expired",
                            "queued_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "plan_name_raw": plan_name,
                        },
                    }) or []
                    if group_rows:
                        supabase_store.upsert_renewal_kick_legacy_map_v2({
                            "legacy_key": scheduler.renewal_kick_group_key(order_id, user_id, gid),
                            "task_id": parent_task_id,
                            "group_task_id": group_rows[0]["id"],
                            "legacy_source": "scheduler",
                            "legacy_ref": order_id,
                            "metadata": {"plan_name": plan_name, "group_id": gid},
                        })
            else:
                supabase_store.upsert_renewal_kick_legacy_map_v2({
                    "legacy_key": scheduler.renewal_kick_group_key(order_id, user_id, "__NO_GROUP_MAP__"),
                    "task_id": parent_task_id,
                    "group_task_id": None,
                    "legacy_source": "scheduler",
                    "legacy_ref": order_id,
                    "metadata": {"plan_name": plan_name, "group_id": "", "reason": "no_group_map"},
                })
    except Exception as exc:
        logging.warning("⚠️ Không enqueue được renewal_kick_tasks_v2 order=%s: %s", order_id, exc)
    return task_rows


async def process_due_renewal_kick_group_tasks_v2(now, *, run_kick_cache=None, run_presence_cache=None, user_cache=None, plan_group_cache=None, limit=300):
    scheduler = _scheduler()
    if not supabase_store.enabled:
        return {"queued": 0, "processing": 0, "done": 0, "blocked": 0, "error": 0, "review": 0}
    try:
        tasks = supabase_store.list_due_renewal_kick_group_tasks_v2(limit=limit)
    except Exception as exc:
        if "renewal_kick_group_tasks_v2" in str(exc).lower():
            return {"queued": 0, "processing": 0, "done": 0, "blocked": 0, "error": 0, "review": 0}
        raise

    summary = {"queued": 0, "processing": 0, "done": 0, "blocked": 0, "error": 0, "review": 0}
    for task in tasks:
        state = scheduler.group_task_state_value(task)
        next_retry_at = scheduler.parse_expire_datetime(task.get("next_retry_at"))
        if state not in {"pending", "selected", "retry_scheduled", "processing", "waiting_confirm"}:
            continue
        age_minutes = scheduler.renewal_kick_v2_task_age_minutes(task, now)
        stale_confirm = age_minutes is not None and age_minutes >= scheduler.RENEWAL_KICK_V2_STALE_CONFIRM_MINUTES
        if state in {"waiting_confirm", "processing"} and stale_confirm:
            try:
                supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                    "group_state": "review_required",
                    "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_error": "stale_confirm_timeout",
                    "review_reason": "stale_confirm_timeout",
                    "metadata": {**(task.get("metadata") or {}), "reason": "stale_confirm_timeout"},
                })
                summary["review"] += 1
            except Exception:
                summary["error"] += 1
            continue
        locked_by = str(task.get("locked_by") or "").strip()
        if locked_by and locked_by != "scheduler_v2" and not scheduler.renewal_kick_v2_lock_expired(task, now):
            continue
        stale_queue = age_minutes is not None and age_minutes >= scheduler.RENEWAL_KICK_V2_STALE_QUEUE_MINUTES
        if next_retry_at and next_retry_at > now and not stale_queue:
            continue
        order_id = str(task.get("order_id") or "")
        user_id = str(task.get("telegram_user_id") or "")
        group_id = str(task.get("group_id") or "")
        plan_name = str(task.get("plan_name") or "")
        if not order_id or not user_id or not group_id:
            continue
        if user_cache and user_id in user_cache:
            active_group_ids = set(user_cache[user_id].get("active_group_ids") or set())
        else:
            active_group_ids = scheduler.user_active_group_ids(user_id, order_id, [], now, plan_group_cache=plan_group_cache)
        if group_id in active_group_ids:
            try:
                supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                    "group_state": "blocked_active_order",
                    "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_reason": "active_order_retained",
                    "metadata": {**(task.get("metadata") or {}), "reason": "active_order_retained"},
                })
                summary["blocked"] += 1
            except Exception:
                summary["error"] += 1
            continue

        if state in {"waiting_confirm", "processing"}:
            try:
                member = await scheduler.member_is_present(group_id, user_id)
                if member is False:
                    supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                        "group_state": "kicked",
                        "completed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "last_reason": "kick_confirmed",
                        "metadata": {**(task.get("metadata") or {}), "reason": "kick_confirmed"},
                    })
                    summary["done"] += 1
                elif member is True:
                    retry_count = int(task.get("attempt_count") or 0)
                    next_state = "retry_scheduled" if retry_count < scheduler.KICK_MAX_ATTEMPTS else "review_required"
                    supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                        "group_state": next_state,
                        "confirm_count": int(task.get("confirm_count") or 0) + 1,
                        "next_retry_at": (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S") if next_state == "retry_scheduled" else None,
                        "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S") if next_state == "review_required" else None,
                        "review_reason": "still_present_after_confirm" if next_state == "review_required" else "",
                        "metadata": {**(task.get("metadata") or {}), "reason": "still_present_after_confirm"},
                    })
                    summary["queued"] += 1
                else:
                    confirm_count = int(task.get("confirm_count") or 0) + 1
                    next_state = "retry_scheduled" if confirm_count < scheduler.KICK_CONFIRM_MAX_ATTEMPTS else "review_required"
                    supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                        "group_state": next_state,
                        "confirm_count": confirm_count,
                        "next_retry_at": (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S") if next_state == "retry_scheduled" else None,
                        "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S") if next_state == "review_required" else None,
                        "last_error": "confirm_unknown" if next_state != "review_required" else "confirm_unknown_max_attempts",
                        "review_reason": "confirm_unknown" if next_state == "review_required" else "",
                        "metadata": {**(task.get("metadata") or {}), "reason": "confirm_unknown"},
                    })
                    summary["queued"] += 1 if next_state == "retry_scheduled" else 0
                    summary["review"] += 1 if next_state == "review_required" else 0
            except Exception as exc:
                confirm_count = int(task.get("confirm_count") or 0) + 1
                next_state = "retry_scheduled" if confirm_count < scheduler.KICK_CONFIRM_MAX_ATTEMPTS else "review_required"
                supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                    "group_state": next_state,
                    "confirm_count": confirm_count,
                    "next_retry_at": (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S") if next_state == "retry_scheduled" else None,
                    "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S") if next_state == "review_required" else None,
                    "last_error": str(exc),
                    "review_reason": "confirm_exception" if next_state == "review_required" else "",
                    "metadata": {**(task.get("metadata") or {}), "reason": "confirm_failed"},
                })
                summary["error"] += 1
            continue

        try:
            supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                "group_state": "processing",
                "locked_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "locked_by": "scheduler_v2",
                "attempt_count": int(task.get("attempt_count") or 0) + 1,
                "last_transition_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "metadata": {**(task.get("metadata") or {}), "reason": "kick_attempt"},
            })
            supabase_store.insert_renewal_kick_attempt_v2({
                "task_id": task.get("task_id"),
                "group_task_id": task.get("id"),
                "order_id": order_id,
                "telegram_user_id": user_id,
                "group_id": group_id,
                "group_name": str(task.get("group_name") or group_id),
                "attempt_no": int(task.get("attempt_count") or 0) + 1,
                "attempt_state": "claimed",
                "action": "kick",
                "actor": "worker_v2",
                "reason_code": "kick_attempt",
                "metadata": {"source": "worker_v2"},
            })
        except Exception:
            summary["error"] += 1
            continue

        ok = await scheduler.ensure_member_kicked(
            group_id,
            user_id,
            order_id,
            plan_name,
            "renewal_due_v2",
            raw_data={
                "expire_at": task.get("first_due_at") or "",
                "task_id": task.get("task_id"),
                "group_task_id": task.get("id"),
                "kick_task_state": "processing",
                "source": "v2",
            },
            run_kick_cache=run_kick_cache,
            run_presence_cache=run_presence_cache,
        )
        try:
            if ok:
                try:
                    supabase_store.insert_renewal_kick_attempt_v2({
                        "task_id": task.get("task_id"),
                        "group_task_id": task.get("id"),
                        "order_id": order_id,
                        "telegram_user_id": user_id,
                        "group_id": group_id,
                        "group_name": str(task.get("group_name") or group_id),
                        "attempt_no": int(task.get("attempt_count") or 0) + 1,
                        "attempt_state": "kick_sent",
                        "action": "kick",
                        "actor": "worker_v2",
                        "reason_code": "kick_sent",
                        "metadata": {"source": "worker_v2", "result": "ok"},
                    })
                except Exception:
                    pass
                supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                    "group_state": "waiting_confirm",
                    "confirm_count": int(task.get("confirm_count") or 0),
                    "next_retry_at": (now + timedelta(seconds=scheduler.KICK_CONFIRMATION_DELAY_SECONDS)).strftime("%Y-%m-%d %H:%M:%S"),
                    "last_reason": "kick_sent",
                    "metadata": {**(task.get("metadata") or {}), "reason": "kick_sent"},
                })
                summary["processing"] += 1
            else:
                try:
                    supabase_store.insert_renewal_kick_attempt_v2({
                        "task_id": task.get("task_id"),
                        "group_task_id": task.get("id"),
                        "order_id": order_id,
                        "telegram_user_id": user_id,
                        "group_id": group_id,
                        "group_name": str(task.get("group_name") or group_id),
                        "attempt_no": int(task.get("attempt_count") or 0) + 1,
                        "attempt_state": "failed_exception",
                        "action": "kick",
                        "actor": "worker_v2",
                        "reason_code": "bot_api_error",
                        "error_message": "kick_failed",
                        "metadata": {"source": "worker_v2", "result": "failed"},
                    })
                except Exception:
                    pass
                supabase_store.update_renewal_kick_group_task_v2(task["id"], {
                    "group_state": "retry_scheduled",
                    "attempt_count": int(task.get("attempt_count") or 0) + 1,
                    "next_retry_at": (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                    "last_error": "kick_failed",
                    "last_reason": "kick_failed",
                    "metadata": {**(task.get("metadata") or {}), "reason": "kick_failed"},
                })
                summary["error"] += 1
        except Exception:
            summary["error"] += 1
    return summary


async def process_due_renewal_kick_finalizer_v2(now, *, limit=300):
    scheduler = _scheduler()
    if not supabase_store.enabled:
        return {"finalized": 0, "review": 0, "done": 0, "blocked": 0, "partial_done": 0, "error": 0}
    try:
        tasks = supabase_store.list_renewal_kick_tasks_v2(limit=limit)
        group_rows = supabase_store.list_due_renewal_kick_group_tasks_v2(limit=1000)
    except Exception as exc:
        if "renewal_kick_tasks_v2" in str(exc).lower():
            return {"finalized": 0, "review": 0, "done": 0, "blocked": 0, "partial_done": 0, "error": 0}
        raise

    summary = {"finalized": 0, "review": 0, "done": 0, "blocked": 0, "partial_done": 0, "error": 0}
    active_states = {"queued", "running", "waiting_confirm", "retry_scheduled", "partial_done", "review_required"}
    for task in tasks:
        state = scheduler.task_state_value(task)
        if state not in active_states:
            continue
        task_id = task.get("id")
        if not task_id:
            continue
        try:
            related_groups = [item for item in group_rows if str(item.get("task_id") or "") == str(task_id)]
            if not related_groups:
                continue
            next_state, payload = scheduler.finalize_renewal_kick_task_v2_from_groups(task, related_groups, now)
            supabase_store.update_renewal_kick_task_v2(task_id, payload)
            summary["finalized"] += 1
            if next_state == "done":
                summary["done"] += 1
            elif next_state == "blocked":
                summary["blocked"] += 1
            elif next_state == "partial_done":
                summary["partial_done"] += 1
            elif next_state == "review_required":
                summary["review"] += 1
        except Exception as exc:
            logging.warning("⚠️ Không finalize được renewal_kick_tasks_v2 %s: %s", task_id, exc)
            summary["error"] += 1
    return summary
