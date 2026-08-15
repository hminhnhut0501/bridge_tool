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

LEGACY_KICK_STATE_ALIASES = {
    "queued": "processing",
    "running": "processing",
    "pending": "processing",
    "selected": "processing",
    "pending_confirm": "processing",
    "retry_pending": "processing",
    "waiting_confirm": "processing",
    "retry_scheduled": "processing",
    "processing": "processing",
    "kicked": "done",
    "retained": "done",
    "blocked_active_order": "blocked",
    "unmapped": "processing",
    "review": "review_required",
    "needs_review": "review_required",
    "need_review": "review_required",
    "failed": "failed_terminal",
    "error": "failed_terminal",
    "failed_terminal": "failed_terminal",
}


def normalize_contract_order_state(value: str) -> str:
    state = str(value or "").strip().lower() or "unknown"
    return state if state in ORDER_STATE_CONTRACT else "unknown"


def normalize_contract_kick_state(value: str) -> str:
    state = str(value or "").strip().lower() or "none"
    return state if state in KICK_STATE_CONTRACT else "none"


def normalize_contract_kick_state_alias(value: str) -> str:
    state = str(value or "").strip().lower() or "none"
    return normalize_contract_kick_state(LEGACY_KICK_STATE_ALIASES.get(state, state))


def assert_contract_membership(state: str, contract: set[str], *, default: str):
    normalized = str(state or "").strip().lower() or default
    return normalized if normalized in contract else default
