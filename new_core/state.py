from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contract import KICK_STATE_CONTRACT, ORDER_STATE_CONTRACT, assert_contract_membership
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
        if state in {"done"}:
            return assert_contract_membership("done", KICK_STATE_CONTRACT, default="none")
        if state in {"processing", "queued", "waiting_confirm", "retry_scheduled", "pending_confirm", "retry_pending", "running"}:
            return assert_contract_membership("processing", KICK_STATE_CONTRACT, default="none")
        if state in {"review_required"}:
            return assert_contract_membership("review_required", KICK_STATE_CONTRACT, default="none")
        if state in {"blocked", "blocked_active_order"}:
            return assert_contract_membership("blocked", KICK_STATE_CONTRACT, default="none")
        if state in {"failed_terminal", "error"}:
            return assert_contract_membership("failed_terminal", KICK_STATE_CONTRACT, default="none")
    if group_task:
        state = str(group_task.get("group_state") or "").strip().lower()
        if state in {"kicked", "retained"}:
            return assert_contract_membership("done", KICK_STATE_CONTRACT, default="none")
        if state in {"processing", "pending", "selected", "waiting_confirm", "retry_scheduled", "unmapped"}:
            return assert_contract_membership("processing", KICK_STATE_CONTRACT, default="none")
        if state in {"review_required"}:
            return assert_contract_membership("review_required", KICK_STATE_CONTRACT, default="none")
        if state in {"blocked_active_order"}:
            return assert_contract_membership("blocked", KICK_STATE_CONTRACT, default="none")
        if state in {"failed_terminal"}:
            return assert_contract_membership("failed_terminal", KICK_STATE_CONTRACT, default="none")
    return "none"
