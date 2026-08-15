from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any


TERMINAL_STATES = {"kicked", "blocked_active_order", "review_required", "failed_terminal"}


def idempotency_key(row: dict[str, Any]) -> str:
    raw = "|".join(str(row.get(field) or "") for field in ("order_id", "group_id", "telegram_user_id"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def claim_group_task(row: dict[str, Any], now: datetime, *, lease_minutes: int = 10) -> dict[str, Any] | None:
    state = str(row.get("group_state") or "pending").strip().lower()
    locked_at = row.get("locked_at")
    if state in TERMINAL_STATES:
        return None
    if locked_at and not _lease_expired(locked_at, now, lease_minutes):
        return None
    return {
        "group_state": "processing",
        "locked_at": now,
        "lock_expires_at": now + timedelta(minutes=lease_minutes),
        "idempotency_key": idempotency_key(row),
        "last_transition_at": now,
    }


def finalize_group_task(row: dict[str, Any], now: datetime, *, outcome: str, reason: str = "", max_attempts: int = 3) -> dict[str, Any]:
    attempt_count = int(row.get("attempt_count") or 0)
    payload: dict[str, Any] = {
        "last_reason": reason or outcome,
        "last_transition_at": now,
        "attempt_count": attempt_count,
        "locked_at": None,
        "lock_expires_at": None,
    }
    if outcome in {"kicked", "blocked_active_order", "review_required"}:
        payload["group_state"] = outcome
        payload["resolved_at"] = now if outcome != "review_required" else None
    elif outcome in {"kick_failed", "kick_exception"}:
        payload["attempt_count"] = attempt_count + 1
        if payload["attempt_count"] >= max_attempts:
            payload["group_state"] = "failed_terminal"
            payload["resolved_at"] = now
        else:
            payload["group_state"] = "retry_scheduled"
    else:
        payload["group_state"] = "review_required"
    return payload


def _lease_expired(value: Any, now: datetime, lease_minutes: int) -> bool:
    if isinstance(value, datetime):
        return value + timedelta(minutes=lease_minutes) <= now
    return True
