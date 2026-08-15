from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .state import normalize_kick_state, normalize_order_state


@dataclass(frozen=True, slots=True)
class RenewalSummary:
    total: int = 0
    queued: int = 0
    processing: int = 0
    done: int = 0
    blocked: int = 0
    review_required: int = 0
    failed_terminal: int = 0


@dataclass(frozen=True, slots=True)
class RenewalRow:
    order_id: str
    telegram_user_id: str
    customer_name: str
    plan_name: str
    expire_at: Any
    order_state: str
    task_state: str
    group_summary: dict[str, int]
    next_action: str
    blocked_reason: str
    last_attempt: dict[str, Any] | None
    last_error: str
    updated_at: Any


def build_renewal_view_model(
    orders: Iterable[dict[str, Any]],
    tasks: Iterable[dict[str, Any]],
    group_tasks: Iterable[dict[str, Any]],
    attempts: Iterable[dict[str, Any]],
    *,
    now,
    parser,
) -> dict[str, Any]:
    task_by_order = {str(row.get("order_id") or ""): row for row in tasks if row.get("order_id")}
    groups_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in group_tasks:
        groups_by_task[str(row.get("task_id") or "")].append(row)
    attempts_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempts:
        attempts_by_group[str(row.get("group_task_id") or "")].append(row)

    rows: list[RenewalRow] = []
    for order in orders:
        order_id = str(order.get("order_id") or order.get("id") or "")
        if not order_id:
            continue
        task = task_by_order.get(order_id) or {}
        order_state = normalize_order_state(order, now, parser=parser).state
        task_state = normalize_kick_state(renewal_task=task)
        related_groups = groups_by_task[str(task.get("id") or "")]
        group_states = [normalize_kick_state(group_task=group) for group in related_groups]
        group_summary = {state: group_states.count(state) for state in ("processing", "done", "blocked", "review_required", "failed_terminal")}
        last_attempt = _latest_attempt(related_groups, attempts_by_group)
        next_action, blocked_reason = _next_action(order_state, task_state, group_summary, task)
        rows.append(
            RenewalRow(
                order_id=order_id,
                telegram_user_id=str(order.get("telegram_user_id") or order.get("user_id") or ""),
                customer_name=str(order.get("full_name") or order.get("customer_name") or ""),
                plan_name=str(order.get("plan_name") or ""),
                expire_at=order.get("expire_at"),
                order_state=order_state,
                task_state=task_state,
                group_summary=group_summary,
                next_action=next_action,
                blocked_reason=blocked_reason,
                last_attempt=last_attempt,
                last_error=str(task.get("last_error") or ""),
                updated_at=task.get("updated_at") or order.get("updated_at"),
            )
        )

    summary = RenewalSummary(total=len(rows))
    for row in rows:
        summary = _increment_summary(summary, row.task_state)
    return {"summary": asdict(summary), "rows": [asdict(row) for row in rows], "schema_version": 1}


def _latest_attempt(groups, attempts_by_group):
    attempts = [attempt for group in groups for attempt in attempts_by_group.get(str(group.get("id") or ""), [])]
    return max(attempts, key=lambda item: str(item.get("started_at") or item.get("created_at") or ""), default=None)


def _next_action(order_state, task_state, group_summary, task):
    if order_state == "active":
        return "retain", "active_order"
    if task_state == "none":
        return "queue", ""
    if task_state == "blocked":
        return "retain", str(task.get("last_reason") or "active_order_retained")
    if task_state == "review_required":
        return "review", str(task.get("review_reason") or "manual_review")
    if task_state == "failed_terminal":
        return "review", str(task.get("terminal_reason") or "terminal_failure")
    if task_state == "done":
        return "none", ""
    if group_summary.get("processing", 0):
        return "monitor", ""
    return "kick", ""


def _increment_summary(summary: RenewalSummary, state: str) -> RenewalSummary:
    values = {"total": summary.total, "queued": summary.queued, "processing": summary.processing, "done": summary.done, "blocked": summary.blocked, "review_required": summary.review_required, "failed_terminal": summary.failed_terminal}
    key = "processing" if state == "processing" else state
    if key in values:
        values[key] += 1
    return RenewalSummary(**values)
