"""Admin renewal mutations with explicit gates and audit records."""

from __future__ import annotations

from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _store():
    import scheduler

    return scheduler.supabase_store


def _audit(action, key, actor, status, payload, error=None):
    return _store()._request(
        "POST",
        "renewal_admin_mutation_audit",
        json={
            "action": action,
            "idempotency_key": key,
            "actor": actor,
            "status": status,
            "payload": payload or {},
            "error": error,
            "created_at": _now(),
        },
        prefer="return=representation",
    )


def _gate(body, *, action):
    if str(body.get("idempotency_key") or "").strip() == "":
        raise ValueError("Thiếu idempotency_key.")
    if body.get("confirm") is not True:
        raise ValueError("Mutation yêu cầu confirm=true.")
    if action not in {"SEND_REMINDER", "RETRY_KICK"}:
        raise ValueError("Mutation không hợp lệ.")


async def send_reminder(body, actor):
    _gate(body, action="SEND_REMINDER")
    key = str(body["idempotency_key"]).strip()
    order_id = str(body.get("order_id") or "").strip()
    user_id = str(body.get("telegram_user_id") or "").strip()
    if not order_id or not user_id:
        raise ValueError("Thiếu order_id hoặc telegram_user_id.")
    existing = _store()._request("GET", "renewal_admin_mutation_audit", params={"select": "*", "idempotency_key": f"eq.{key}", "limit": "1"})
    if existing:
        return {"status": "IDEMPOTENT_REPLAY", "audit": existing[0]}
    payload = {
        "order_id": order_id,
        "telegram_user_id": user_id,
        "reminder_type": "RENEWAL_REMINDER",
        "status": "PENDING",
        "attempts": 0,
    }
    try:
        event = _store()._request("POST", "renewal_reminder_events", json=payload, prefer="return=representation")
        audit = _audit("SEND_REMINDER", key, actor, "QUEUED", payload)
        return {"status": "QUEUED", "event": event, "audit": audit}
    except Exception as exc:
        _audit("SEND_REMINDER", key, actor, "FAILED", payload, str(exc))
        raise


async def retry_kick(body, actor):
    _gate(body, action="RETRY_KICK")
    key = str(body["idempotency_key"]).strip()
    existing = _store()._request("GET", "renewal_admin_mutation_audit", params={"select": "*", "idempotency_key": f"eq.{key}", "limit": "1"})
    if existing:
        return {"status": "IDEMPOTENT_REPLAY", "audit": existing[0]}
    from renewal_admin_review_service import review_renewal_task_v2

    payload = {**body, "action": "requeue", "reason": body.get("reason") or "admin_retry_kick"}
    try:
        result = await review_renewal_task_v2(payload)
        audit = _audit("RETRY_KICK", key, actor, "QUEUED", payload)
        return {"status": "QUEUED", "task": result, "audit": audit}
    except Exception as exc:
        _audit("RETRY_KICK", key, actor, "FAILED", payload, str(exc))
        raise
