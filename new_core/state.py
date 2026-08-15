from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contract import (
    KICK_STATE_CONTRACT,
    ORDER_STATE_CONTRACT,
    assert_contract_membership,
)
from .expiry import is_order_active, is_order_expired

ORDER_STATES = {
    "active",
    "expired",
    "queued",
    "processing",
    "waiting_confirm",
    "done",
    "blocked",
    "review_required",
    "failed_terminal",
    "unknown",
}

KICK_STATES = {
    "none",
    "queued",
    "processing",
    "waiting_confirm",
    "done",
    "blocked",
    "review_required",
    "failed_terminal",
    "unknown",
}

KICK_STATE_TASK_ALIASES = {
    "queued": "processing",
    "running": "processing",
    "pending_confirm": "processing",
    "retry_pending": "processing",
    "waiting_confirm": "processing",
    "retry_scheduled": "processing",
    "processing": "processing",
    "done": "done",
    "kicked": "done",
    "retained": "done",
    "blocked": "blocked",
    "blocked_active_order": "blocked",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
    "error": "failed_terminal",
}

KICK_STATE_GROUP_ALIASES = {
    "pending": "processing",
    "selected": "processing",
    "processing": "processing",
    "waiting_confirm": "processing",
    "retry_scheduled": "processing",
    "unmapped": "processing",
    "kicked": "done",
    "retained": "done",
    "blocked_active_order": "blocked",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
}


@dataclass(frozen=True, slots=True)
class NormalizedOrderState:
    state: str
    reason: str = ""
    source: str = ""


def normalize_order_state(order: dict[str, Any] | None, now, *, parser) -> NormalizedOrderState:
    if not order:
        return NormalizedOrderState(state=assert_contract_membership("unknown", ORDER_STATE_CONTRACT, default="unknown"), reason="missing_order", source="contract")

    status = str(order.get("status") or "").strip().upper()
    if status == "EXPIRED":
        return NormalizedOrderState(state=assert_contract_membership("expired", ORDER_STATE_CONTRACT, default="unknown"), reason="status_expired", source="status")
    if is_order_expired(order, now, parser=parser):
        return NormalizedOrderState(state=assert_contract_membership("expired", ORDER_STATE_CONTRACT, default="unknown"), reason="expiring_by_datetime", source="expiry")
    if status == "PAID" and is_order_active(order, now, parser=parser):
        return NormalizedOrderState(state=assert_contract_membership("active", ORDER_STATE_CONTRACT, default="unknown"), reason="paid_active", source="expiry")
    if status == "PAID":
        return NormalizedOrderState(state=assert_contract_membership("unknown", ORDER_STATE_CONTRACT, default="unknown"), reason="paid_unknown_expiry", source="expiry")
    return NormalizedOrderState(state=assert_contract_membership("unknown", ORDER_STATE_CONTRACT, default="unknown"), reason=f"status_{status.lower() or 'empty'}", source="status")


def normalize_kick_state(*, renewal_task=None, group_task=None, support_event_state="none") -> str:
    if renewal_task:
        state = str(renewal_task.get("task_state") or "").strip().lower()
        mapped = KICK_STATE_TASK_ALIASES.get(state)
        if mapped:
            return assert_contract_membership(mapped, KICK_STATE_CONTRACT, default="none")
    if group_task:
        state = str(group_task.get("group_state") or "").strip().lower()
        mapped = KICK_STATE_GROUP_ALIASES.get(state)
        if mapped:
            return assert_contract_membership(mapped, KICK_STATE_CONTRACT, default="none")
    return "none"
