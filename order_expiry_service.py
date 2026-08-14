from __future__ import annotations

from datetime import datetime

from new_core.expiry import days_until_expire as core_days_until_expire
from new_core.expiry import is_order_active as core_is_order_active
from new_core.expiry import is_order_expired as core_is_order_expired


def parse_order_expire_at(value, parser):
    return parser(value)


def order_is_lifetime(plan_name: str | None, *, plan_token: str = "") -> bool:
    text = f"{plan_name or ''} {plan_token or ''}".upper()
    return any(token in text for token in ("TRỌN ĐỜI", "TRON DOI", "LIFETIME", "LIFE", "SVIP"))


def order_is_expired(order, now, *, parser, status_field: str = "status", expire_field: str = "expire_at") -> bool:
    return core_is_order_expired(order, now, parser=parser, status_field=status_field, expire_field=expire_field)


def order_is_active(order, now, *, parser, status_field: str = "status", expire_field: str = "expire_at") -> bool:
    return core_is_order_active(order, now, parser=parser, status_field=status_field, expire_field=expire_field)


def days_until_order_expire(order, now, *, parser, expire_field: str = "expire_at") -> int:
    return core_days_until_expire(order, now, parser=parser, expire_field=expire_field)


def reconcile_expired_paid_orders(orders, now, *, parser, mark_expired, limit=5000):
    reconciled = []
    for order in orders or []:
        if len(reconciled) >= limit:
            break
        if not order_is_expired(order, now, parser=parser):
            continue
        order_id = str(order.get("order_id") or "").strip()
        if not order_id:
            continue
        if str(order.get("status") or "").strip().upper() != "PAID":
            continue
        try:
            mark_expired(order_id, expired_notice_at=order.get("expired_notice_at") or None)
            reconciled.append(order_id)
        except Exception:
            continue
    return reconciled
