from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence

from .ports import Clock, KickTaskRepository, MembershipGateway
from .state_machine import transition_kick_group


@dataclass(frozen=True, slots=True)
class KickRunResult:
    scanned: int = 0
    processed: int = 0
    kicked: int = 0
    blocked: int = 0
    retry_scheduled: int = 0
    review_required: int = 0
    failed: int = 0
    skipped: int = 0


async def process_due_kick_groups(
    tasks: KickTaskRepository,
    membership: MembershipGateway,
    clock: Clock,
    *,
    active_order_check: Callable[[str, str, str], bool],
    limit: int = 300,
) -> KickRunResult:
    """Execute due group kick tasks without depending on scheduler/web_backend."""
    now = clock.now()
    rows: Sequence[dict] = tasks.list_due_group_tasks(before=now, limit=limit)
    result = KickRunResult(scanned=len(rows))
    for row in rows:
        state = str(row.get("group_state") or "pending").strip().lower()
        if state not in {"pending", "retry_scheduled", "processing", "waiting_confirm"}:
            result = _replace(result, skipped=result.skipped + 1)
            continue

        task_id = str(row.get("id") or "").strip()
        order_id = str(row.get("order_id") or "").strip()
        user_id = str(row.get("telegram_user_id") or "").strip()
        group_id = str(row.get("group_id") or "").strip()
        if not task_id or not order_id or not user_id or not group_id:
            result = _replace(result, skipped=result.skipped + 1)
            continue

        if active_order_check(user_id, order_id, group_id):
            transition_kick_group(state, "blocked_active_order")
            tasks.update_group_task(task_id, {"group_state": "blocked_active_order", "last_reason": "active_order_retained"})
            result = _replace(result, blocked=result.blocked + 1, processed=result.processed + 1)
            continue

        if state in {"processing", "waiting_confirm"}:
            presence = await membership.is_present(group_id, user_id)
            if presence is False:
                transition_kick_group(state, "kicked")
                tasks.update_group_task(task_id, {"group_state": "kicked", "last_reason": "kick_confirmed", "resolved_at": now})
                result = _replace(result, kicked=result.kicked + 1, processed=result.processed + 1)
                continue
            if presence is None:
                transition_kick_group(state, "review_required")
                tasks.update_group_task(task_id, {"group_state": "review_required", "last_reason": "confirm_unknown"})
                result = _replace(result, review_required=result.review_required + 1, processed=result.processed + 1)
                continue

        transition_kick_group(state, "processing")
        tasks.update_group_task(task_id, {"group_state": "processing", "last_transition_at": now})
        try:
            kick_result = await membership.kick(group_id, user_id)
        except Exception as exc:
            transition_kick_group("processing", "retry_scheduled")
            tasks.update_group_task(task_id, {"group_state": "retry_scheduled", "last_error": str(exc), "last_reason": "kick_exception"})
            result = _replace(result, retry_scheduled=result.retry_scheduled + 1, processed=result.processed + 1)
            continue

        if kick_result.ok:
            transition_kick_group("processing", "waiting_confirm")
            tasks.update_group_task(task_id, {"group_state": "waiting_confirm", "last_reason": "kick_sent", "next_retry_at": now})
            result = _replace(result, kicked=result.kicked + 1, processed=result.processed + 1)
        else:
            transition_kick_group("processing", "retry_scheduled")
            tasks.update_group_task(task_id, {"group_state": "retry_scheduled", "last_reason": kick_result.reason or "kick_failed"})
            result = _replace(result, retry_scheduled=result.retry_scheduled + 1, processed=result.processed + 1)
    return result


def _replace(result: KickRunResult, **changes: int) -> KickRunResult:
    values = {
        "scanned": result.scanned,
        "processed": result.processed,
        "kicked": result.kicked,
        "blocked": result.blocked,
        "retry_scheduled": result.retry_scheduled,
        "review_required": result.review_required,
        "failed": result.failed,
        "skipped": result.skipped,
    }
    values.update(changes)
    return KickRunResult(**values)
