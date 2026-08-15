from __future__ import annotations

from datetime import datetime, timezone


ACTIVE_ORDER_STATUSES = {"PAID"}


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def project_order(row: dict, *, now: datetime | None = None) -> dict:
    """Project one order into the read-only entitlement contract."""
    now = now or datetime.now(timezone.utc)
    status = str(row.get("status") or "").strip().upper()
    family = str(row.get("canonical_plan_family") or "").strip().upper() or None
    duration = str(row.get("canonical_duration") or "").strip().upper() or None
    group_code = str(row.get("canonical_group_code") or "").strip().upper() or None
    expires_at = parse_datetime(row.get("expire_at"))

    if status == "CANCELLED":
        state = "CANCELLED"
        reason = "order_cancelled"
    elif status == "REFUNDED":
        state = "CANCELLED"
        reason = "order_refunded"
    elif family == "UNSUPPORTED" or duration == "REVIEW" or not family or not group_code:
        state = "REVIEW"
        reason = "canonical_mapping_incomplete"
    elif status in ACTIVE_ORDER_STATUSES and duration == "LIFETIME":
        state = "ACTIVE"
        reason = "lifetime_order"
    elif status in ACTIVE_ORDER_STATUSES and expires_at and expires_at > now:
        state = "ACTIVE"
        reason = "future_expiry"
    elif status == "EXPIRED" or (status == "PAID" and expires_at and expires_at <= now):
        state = "EXPIRED"
        reason = "expiry_reached"
    elif status == "PAID" and not expires_at:
        state = "REVIEW"
        reason = "missing_expiry"
    else:
        state = "REVIEW"
        reason = "unsupported_order_state"

    return {
        "source_order_id": row.get("order_id"),
        "telegram_user_id": row.get("telegram_user_id"),
        "plan_family": family,
        "group_code": group_code,
        "starts_at": row.get("paid_at") or row.get("created_at"),
        "expires_at": row.get("expire_at"),
        "is_lifetime": duration == "LIFETIME",
        "state": state,
        "state_reason": reason,
        "source_quality": "VERIFIED" if family and group_code and duration else "REVIEW",
    }


def project_orders(rows: list[dict], *, now: datetime | None = None) -> list[dict]:
    return [project_order(row, now=now) for row in rows]
