from __future__ import annotations

from datetime import datetime


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
    return bool(expire_at and expire_at >= now)


def days_until_expire(order, now: datetime, *, parser, expire_field: str = "expire_at") -> int:
    expire_at = parser(order.get(expire_field)) if order else None
    if not expire_at:
        return 999999
    return int((expire_at - now).total_seconds() // 86400)
