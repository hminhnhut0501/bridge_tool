from __future__ import annotations

from datetime import datetime, timezone


def _parse(value):
    if not value:
        return None
    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def _is_active(row: dict, now: datetime) -> bool:
    if str(row.get("state") or "").upper() != "ACTIVE":
        return False
    if row.get("is_lifetime"):
        return True
    expiry = _parse(row.get("expires_at"))
    return expiry is not None and expiry > now


def resolve_customer_group(
    entitlements: list[dict],
    *,
    telegram_user_id: str,
    group_code: str,
    now: datetime | None = None,
) -> dict:
    """Resolve one customer's current entitlement for one canonical group."""
    now = now or datetime.now(timezone.utc)
    user = str(telegram_user_id)
    group = str(group_code).upper()
    rows = [
        row for row in entitlements
        if str(row.get("telegram_user_id")) == user
        and str(row.get("group_code") or "").upper() == group
    ]
    active = [row for row in rows if _is_active(row, now)]
    if active:
        active.sort(key=lambda row: (
            bool(row.get("is_lifetime")),
            _parse(row.get("expires_at")) or datetime.min.replace(tzinfo=timezone.utc),
        ), reverse=True)
        winner = dict(active[0])
        winner["resolution"] = "ACTIVE"
        winner["active_count"] = len(active)
        return winner

    return {
        "telegram_user_id": telegram_user_id,
        "group_code": group,
        "resolution": "NO_ACTIVE_ENTITLEMENT",
        "active_count": 0,
        "historical_count": len(rows),
    }


def has_newer_active_entitlement(
    entitlements: list[dict],
    *,
    telegram_user_id: str,
    group_code: str,
    source_order_id: str,
    now: datetime | None = None,
) -> bool:
    resolved = resolve_customer_group(
        entitlements,
        telegram_user_id=telegram_user_id,
        group_code=group_code,
        now=now,
    )
    return (
        resolved.get("resolution") == "ACTIVE"
        and str(resolved.get("source_order_id")) != str(source_order_id)
    )
