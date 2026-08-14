from __future__ import annotations

ORDER_STATE_CONTRACT = {
    "active",
    "expired",
    "unknown",
}

KICK_STATE_CONTRACT = {
    "none",
    "processing",
    "done",
    "blocked",
    "review_required",
    "failed_terminal",
}


def normalize_contract_order_state(value: str) -> str:
    state = str(value or "").strip().lower() or "unknown"
    return state if state in ORDER_STATE_CONTRACT else "unknown"


def normalize_contract_kick_state(value: str) -> str:
    state = str(value or "").strip().lower() or "none"
    return state if state in KICK_STATE_CONTRACT else "none"


def assert_contract_membership(state: str, contract: set[str], *, default: str):
    normalized = str(state or "").strip().lower() or default
    return normalized if normalized in contract else default
