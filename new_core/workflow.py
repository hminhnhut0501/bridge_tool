from __future__ import annotations

from .state import normalize_order_state


def plan_expired_order_actions(order, now, *, parser):
    normalized = normalize_order_state(order, now, parser=parser)
    if normalized.state != "expired":
        return {"queue_kick": False, "reconcile": False, "reason": "not_expired"}
    return {"queue_kick": True, "reconcile": True, "reason": "expired"}
