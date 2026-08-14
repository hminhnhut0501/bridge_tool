from __future__ import annotations

from support_event_read_model import build_support_events_read_model


LEGACY_SUPPORT_EVENT_TYPES = {
    "manual_order_created",
    "manual_activation_link_generated",
    "manual_activation_link_failed",
    "activation_link_cleanup_done",
    "activation_link_cleanup_failed",
    "expired_notice_sent",
    "renewal_reminder_sent",
    "member_kicked",
    "member_kick_failed",
    "member_kick_closed",
    "member_unmuted",
    "member_muted",
    "support_joined",
    "support_left",
    "vip_joined",
    "vip_left",
    "vip_kicked",
    "vip_unmuted",
    "vip_restricted_changed",
    "license_delivery_notified",
    "auto_payment_schedule_toggled",
    "auto_payment_redirect",
    "order_deleted",
    "admin_reply_failed",
    "admin_reply_sent",
}


def is_legacy_support_event_type(event_type: str) -> bool:
    return str(event_type or "").strip() in LEGACY_SUPPORT_EVENT_TYPES


def record_support_event_legacy(supabase_store, event_type, telegram_user_id=None, **kwargs):
    if not getattr(supabase_store, "enabled", False):
        return

    if not is_legacy_support_event_type(event_type):
        print(f"⚠️ Bỏ qua support event legacy chưa nằm trong contract: {event_type}")
        return

    if telegram_user_id and (not kwargs.get("full_name") or not kwargs.get("username")):
        try:
            identity = supabase_store.get_user_identity(telegram_user_id)
        except Exception:
            identity = None
        if identity:
            kwargs.setdefault("username", identity.get("username") or "")
            kwargs.setdefault("full_name", identity.get("full_name") or "")
            if not kwargs.get("username") and identity.get("username"):
                kwargs["username"] = identity.get("username")
            if not kwargs.get("full_name") and identity.get("full_name"):
                kwargs["full_name"] = identity.get("full_name")

    supabase_store.record_support_event(event_type, telegram_user_id, **kwargs)


def read_support_events_legacy(supabase_store, *, limit: int = 1000, updated_after: str | None = None, query: str = ""):
    safe_limit = max(1, min(int(limit or 1000), 2000))
    rows = supabase_store.list_support_events(limit=max(100, safe_limit * 2), updated_after=updated_after)
    return build_support_events_read_model(rows, limit=safe_limit, updated_after=updated_after, query=query)
