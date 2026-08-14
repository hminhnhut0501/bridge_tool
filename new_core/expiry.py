from __future__ import annotations

from datetime import datetime


def _compareable_datetimes(left: datetime, right: datetime) -> tuple[datetime, datetime]:
    if left.tzinfo and not right.tzinfo:
        return left.replace(tzinfo=None), right
    if right.tzinfo and not left.tzinfo:
        return left, right.replace(tzinfo=None)
    return left, right


def _is_lifetime(plan_name: str | None, plan_token: str = "") -> bool:
    text = f"{plan_name or ''} {plan_token or ''}".upper()
    return any(token in text for token in ("TRỌN ĐỜI", "TRON DOI", "LIFETIME", "LIFE", "SVIP"))


def is_order_expired(order, now: datetime, *, parser, status_field: str = "status", expire_field: str = "expire_at") -> bool:
    if not order:
        return False
    status = str(order.get(status_field) or "").strip().upper()
    if status == "EXPIRED":
        return True
    if status != "PAID":
        return False
    plan_name = str(order.get("plan_name") or "").strip()
    plan_token = str(order.get("plan_token") or "").strip()
    if _is_lifetime(plan_name, plan_token):
        return False
    expire_at = parser(order.get(expire_field))
    if expire_at and expire_at.tzinfo and not now.tzinfo:
        now = now.replace(tzinfo=expire_at.tzinfo)
    elif expire_at and not expire_at.tzinfo and now.tzinfo:
        expire_at = expire_at.replace(tzinfo=now.tzinfo)
    elif expire_at:
        expire_at, now = _compareable_datetimes(expire_at, now)
    return bool(expire_at and expire_at < now)


def is_order_active(order, now: datetime, *, parser, status_field: str = "status", expire_field: str = "expire_at") -> bool:
    if not order:
        return False
    status = str(order.get(status_field) or "").strip().upper()
    if status != "PAID":
        return False
    plan_name = str(order.get("plan_name") or "").strip()
    plan_token = str(order.get("plan_token") or "").strip()
    if _is_lifetime(plan_name, plan_token):
        return True
    expire_at = parser(order.get(expire_field))
    if expire_at and expire_at.tzinfo and not now.tzinfo:
        now = now.replace(tzinfo=expire_at.tzinfo)
    elif expire_at and not expire_at.tzinfo and now.tzinfo:
        expire_at = expire_at.replace(tzinfo=now.tzinfo)
    elif expire_at:
        expire_at, now = _compareable_datetimes(expire_at, now)
    return bool(expire_at and expire_at >= now)


def days_until_expire(order, now: datetime, *, parser, expire_field: str = "expire_at") -> int:
    expire_at = parser(order.get(expire_field)) if order else None
    if not expire_at:
        return 999999
    if expire_at.tzinfo and not now.tzinfo:
        now = now.replace(tzinfo=expire_at.tzinfo)
    elif expire_at and not expire_at.tzinfo and now.tzinfo:
        expire_at = expire_at.replace(tzinfo=now.tzinfo)
    elif expire_at:
        expire_at, now = _compareable_datetimes(expire_at, now)
    return int((expire_at - now).total_seconds() // 86400)
