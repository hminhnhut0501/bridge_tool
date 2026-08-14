from __future__ import annotations

from .expiry import is_order_expired
from .state import normalize_kick_state


def classify_kick_state(*, renewal_task=None, group_task=None, support_event_state="none"):
    return normalize_kick_state(
        renewal_task=renewal_task,
        group_task=group_task,
        support_event_state=support_event_state,
    )


def should_queue_kick(order, now, *, parser) -> bool:
    return is_order_expired(order, now, parser=parser)
