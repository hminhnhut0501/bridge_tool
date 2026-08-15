from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from new_core.contract import normalize_contract_kick_state_alias


RENEWAL_KICK_REASON_CODES = {
    "no_group_map",
    "scheduler_expired",
    "kick_attempt",
    "kick_sent",
    "kick_failed",
    "stale_confirm_timeout",
    "active_order_retained",
    "confirm_unknown",
    "confirm_timeout",
    "retry_limit_reached",
    "group_unmapped",
    "active_order_retained",
    "bot_api_error",
    "telegram_rate_limited",
    "telegram_forbidden",
    "user_not_found",
    "chat_not_found",
    "manual_kick_detected",
    "already_kicked",
    "already_review_required",
    "legacy_ambiguous_state",
}

RENEWAL_KICK_STATE_ALIASES = {
    "review": "review_required",
    "needs_review": "review_required",
    "need_review": "review_required",
    "cần review": "review_required",
    "cần xử lý": "review_required",
    "review required": "review_required",
    "chờ kick": "queued",
    "đang kick": "processing",
    "đang chờ telegram xác nhận": "waiting_confirm",
    "chờ thử lại": "retry_scheduled",
    "bị giữ bởi đơn active khác": "blocked_active_order",
    "bị giữ lại": "retained",
    "không map được group": "unmapped",
}


def normalize_renewal_kick_state(value):
    raw = str(value or "").strip().lower()
    mapped = RENEWAL_KICK_STATE_ALIASES.get(raw, raw)
    return normalize_contract_kick_state_alias(mapped)


def normalize_renewal_kick_reason(value):
    raw = str(value or "").strip().lower().replace(" ", "_")
    return raw if raw in RENEWAL_KICK_REASON_CODES else raw


def parse_expire_datetime(value, *, timezone_name="Asia/Ho_Chi_Minh"):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            try:
                timezone = ZoneInfo(timezone_name or "Asia/Ho_Chi_Minh")
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_event_datetime(event, *, timezone_name="Asia/Ho_Chi_Minh"):
    return parse_expire_datetime((event or {}).get("created_at"), timezone_name=timezone_name)


def event_happened_after(candidate, reference, *, timezone_name="Asia/Ho_Chi_Minh"):
    candidate_at = parse_event_datetime(candidate, timezone_name=timezone_name)
    reference_at = parse_event_datetime(reference, timezone_name=timezone_name)
    return bool(candidate_at and reference_at and candidate_at >= reference_at)


def task_state_value(task):
    state = (task or {}).get("state")
    if state is None:
        state = (task or {}).get("task_state")
    return normalize_renewal_kick_state(state)


def group_task_state_value(task):
    state = (task or {}).get("group_state")
    if state is None:
        state = (task or {}).get("state")
    return normalize_renewal_kick_state(state)


def renewal_kick_group_key(order_id, user_id, group_id):
    return f"{str(order_id or '').strip()}:{str(user_id or '').strip()}:{str(group_id or '').strip()}"


def renewal_kick_v2_lock_expired(task, now, *, lock_minutes=5):
    locked_at = parse_expire_datetime((task or {}).get("locked_at"))
    if not locked_at:
        return True
    return now - locked_at >= timedelta(minutes=lock_minutes)


def renewal_kick_v2_task_age_minutes(task, now):
    for key in ("updated_at", "last_transition_at", "queued_at", "created_at", "due_at", "first_due_at"):
        parsed = parse_expire_datetime((task or {}).get(key))
        if parsed:
            return max(0, int((now - parsed).total_seconds() // 60))
    return None
