from __future__ import annotations

from dataclasses import dataclass


class InvalidStateTransition(ValueError):
    """Raised when a workflow attempts an unsafe state transition."""


ORDER_STATES = frozenset({"active", "expired", "unknown"})
KICK_TASK_STATES = frozenset(
    {
        "queued",
        "processing",
        "waiting_confirm",
        "retry_scheduled",
        "done",
        "partial_done",
        "blocked_active_order",
        "review_required",
        "failed_terminal",
    }
)
KICK_GROUP_STATES = frozenset(
    {
        "pending",
        "processing",
        "waiting_confirm",
        "retry_scheduled",
        "kicked",
        "retained",
        "blocked_active_order",
        "review_required",
        "failed_terminal",
        "unmapped",
    }
)

ORDER_TRANSITIONS = {
    "unknown": frozenset({"active", "expired", "unknown"}),
    "active": frozenset({"active", "expired", "unknown"}),
    "expired": frozenset({"expired", "active", "unknown"}),
}

KICK_TASK_TRANSITIONS = {
    "queued": frozenset({"queued", "processing", "blocked_active_order", "review_required"}),
    "processing": frozenset({"processing", "waiting_confirm", "retry_scheduled", "done", "partial_done", "review_required", "failed_terminal", "blocked_active_order"}),
    "waiting_confirm": frozenset({"waiting_confirm", "done", "retry_scheduled", "review_required", "failed_terminal"}),
    "retry_scheduled": frozenset({"retry_scheduled", "processing", "review_required", "failed_terminal"}),
    "done": frozenset({"done", "partial_done"}),
    "partial_done": frozenset({"partial_done", "done", "review_required"}),
    "blocked_active_order": frozenset({"blocked_active_order", "queued", "done"}),
    "review_required": frozenset({"review_required", "queued", "processing", "done", "failed_terminal"}),
    "failed_terminal": frozenset({"failed_terminal", "review_required"}),
}

KICK_GROUP_TRANSITIONS = {
    "pending": frozenset({"pending", "processing", "blocked_active_order", "unmapped", "review_required"}),
    "processing": frozenset({"processing", "waiting_confirm", "kicked", "retry_scheduled", "review_required", "failed_terminal", "blocked_active_order"}),
    "waiting_confirm": frozenset({"waiting_confirm", "kicked", "retry_scheduled", "review_required", "failed_terminal"}),
    "retry_scheduled": frozenset({"retry_scheduled", "processing", "review_required", "failed_terminal"}),
    "kicked": frozenset({"kicked"}),
    "retained": frozenset({"retained", "processing"}),
    "blocked_active_order": frozenset({"blocked_active_order", "pending", "retained"}),
    "review_required": frozenset({"review_required", "pending", "processing", "kicked", "failed_terminal"}),
    "failed_terminal": frozenset({"failed_terminal", "review_required"}),
    "unmapped": frozenset({"unmapped", "review_required", "pending"}),
}


@dataclass(frozen=True, slots=True)
class StateTransition:
    entity: str
    previous: str
    next: str


def _validate(value: str, allowed: frozenset[str], *, field: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in allowed:
        raise InvalidStateTransition(f"Unknown {field}: {value!r}")
    return normalized


def transition_order(previous: str, next_state: str) -> StateTransition:
    previous = _validate(previous, ORDER_STATES, field="order state")
    next_state = _validate(next_state, ORDER_STATES, field="order state")
    if next_state not in ORDER_TRANSITIONS[previous]:
        raise InvalidStateTransition(f"Order transition {previous!r} -> {next_state!r} is not allowed")
    return StateTransition("order", previous, next_state)


def transition_kick_task(previous: str, next_state: str) -> StateTransition:
    previous = _validate(previous, KICK_TASK_STATES, field="kick task state")
    next_state = _validate(next_state, KICK_TASK_STATES, field="kick task state")
    if next_state not in KICK_TASK_TRANSITIONS[previous]:
        raise InvalidStateTransition(f"Kick task transition {previous!r} -> {next_state!r} is not allowed")
    return StateTransition("kick_task", previous, next_state)


def transition_kick_group(previous: str, next_state: str) -> StateTransition:
    previous = _validate(previous, KICK_GROUP_STATES, field="kick group state")
    next_state = _validate(next_state, KICK_GROUP_STATES, field="kick group state")
    if next_state not in KICK_GROUP_TRANSITIONS[previous]:
        raise InvalidStateTransition(f"Kick group transition {previous!r} -> {next_state!r} is not allowed")
    return StateTransition("kick_group", previous, next_state)
