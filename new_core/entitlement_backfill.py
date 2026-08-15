from __future__ import annotations

from datetime import datetime, timezone


def _parse(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def build_backfill_rows(rows: list[dict], *, now: datetime | None = None) -> list[dict]:
    """Return only high-confidence rows safe for Phase B insertion."""
    now = now or datetime.now(timezone.utc)
    result = []
    for row in rows:
        status = str(row.get("status") or "").upper()
        family = str(row.get("canonical_plan_family") or "").upper()
        duration = str(row.get("canonical_duration") or "").upper()
        group_code = str(row.get("canonical_group_code") or "").upper()
        expiry = _parse(row.get("expire_at"))
        if status not in {"PAID", "EXPIRED"}:
            continue
        if family in {"", "UNSUPPORTED"} or duration in {"", "REVIEW"} or not group_code:
            continue
        lifetime = duration == "LIFETIME"
        if not lifetime and expiry is None:
            continue
        state = "ACTIVE" if lifetime or (status == "PAID" and expiry and expiry > now) else "EXPIRED"
        result.append({
            "source_order_id": str(row.get("order_id")),
            "telegram_user_id": str(row.get("telegram_user_id")),
            "group_code": group_code,
            "group_id": None,
            "starts_at": row.get("paid_at") or row.get("created_at"),
            "expires_at": row.get("expire_at"),
            "is_lifetime": lifetime,
            "state": state,
            "source_quality": "VERIFIED",
        })
    return result
