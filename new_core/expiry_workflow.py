from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .ports import Clock, KickTaskRepository, OrderRepository
from .state import normalize_order_state
from .state_machine import transition_order


@dataclass(frozen=True, slots=True)
class ExpiryRunResult:
    scanned: int = 0
    expired: int = 0
    reconciled: int = 0
    tasks_created: int = 0
    tasks_existing: int = 0
    skipped: int = 0
    invalid: int = 0


def reconcile_expired_orders(
    orders: OrderRepository,
    tasks: KickTaskRepository,
    clock: Clock,
    *,
    parser: Callable[[Any], datetime | None],
    plan_group_resolver: Callable[[str], list[str]] | None = None,
    limit: int = 5000,
) -> ExpiryRunResult:
    """Reconcile order expiry and enqueue one idempotent kick task per order.

    This workflow deliberately has no Telegram or legacy-event dependency. A
    separate kick worker owns membership actions after the task is persisted.
    """
    now = clock.now()
    candidates = list(orders.list_expiry_candidates(before=now, limit=limit))
    result = ExpiryRunResult(scanned=len(candidates))

    for order in candidates:
        normalized = normalize_order_state(order, now, parser=parser)
        if normalized.state != "expired":
            result = _replace(result, skipped=result.skipped + 1)
            continue

        order_id = str(order.get("order_id") or order.get("id") or "").strip()
        user_id = str(order.get("telegram_user_id") or order.get("user_id") or "").strip()
        if not order_id or not user_id:
            result = _replace(result, invalid=result.invalid + 1)
            continue

        storage_status = str(order.get("status") or "").strip().upper()
        if storage_status == "PAID":
            transition_order("active", "expired")
            orders.update_status(order_id, "EXPIRED", changed_at=now)
            result = _replace(result, reconciled=result.reconciled + 1)

        result = _replace(result, expired=result.expired + 1)
        existing = tasks.get_task(order_id, user_id)
        if existing:
            result = _replace(result, tasks_existing=result.tasks_existing + 1)
            continue

        parent_task = tasks.create_task(
            {
                "order_id": order_id,
                "telegram_user_id": user_id,
                "plan_name": str(order.get("plan_name") or ""),
                "task_state": "queued",
                "due_at": order.get("expire_at"),
                "last_transition_at": now,
                "metadata": {"source": "expiry_workflow"},
            }
        )
        if plan_group_resolver and hasattr(tasks, "create_group_task"):
            for group_id in plan_group_resolver(str(order.get("plan_name") or "")):
                tasks.create_group_task(
                    {
                        "task_id": parent_task.get("id"),
                        "order_id": order_id,
                        "telegram_user_id": user_id,
                        "group_id": str(group_id),
                        "group_name": str(group_id),
                        "plan_name": str(order.get("plan_name") or ""),
                        "group_state": "pending",
                        "first_due_at": order.get("expire_at"),
                        "next_retry_at": now,
                    }
                )
        result = _replace(result, tasks_created=result.tasks_created + 1)

    return result


def _replace(result: ExpiryRunResult, **changes: int) -> ExpiryRunResult:
    values = {
        "scanned": result.scanned,
        "expired": result.expired,
        "reconciled": result.reconciled,
        "tasks_created": result.tasks_created,
        "tasks_existing": result.tasks_existing,
        "skipped": result.skipped,
        "invalid": result.invalid,
    }
    values.update(changes)
    return ExpiryRunResult(**values)
