from __future__ import annotations


def resolve_order_display_label(order):
    direct = str(order.get("full_name") or "").strip()
    if direct and direct != "-":
        return direct
    username = str(order.get("username") or "").strip()
    if username and username != "-":
        return username
    user_id = str(order.get("telegram_user_id") or "").strip()
    return user_id or "-"


def order_display_name(order):
    return resolve_order_display_label(order)
