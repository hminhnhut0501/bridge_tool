from __future__ import annotations

from datetime import datetime, timezone


def _store():
    import scheduler
    return scheduler.supabase_store


def get_config():
    rows = _store()._request("GET", "renewal_worker_config", params={"select": "*", "worker_name": "eq.entitlement_kick", "limit": "1"})
    return rows[0] if rows else {"worker_name": "entitlement_kick", "enabled": False, "interval_seconds": 300, "batch_limit": 5, "halted": False, "halt_reason": None, "last_batch": {}}


def update_config(body, actor):
    enabled = bool(body.get("enabled", False))
    emergency_stop = bool(body.get("emergency_stop", False))
    interval = max(300, int(body.get("interval_seconds", 300)))
    batch = min(5, max(1, int(body.get("batch_limit", 5))))
    halted = emergency_stop or bool(body.get("halted", False))
    reason = str(body.get("halt_reason") or ("emergency_stop" if emergency_stop else "")) or None
    payload = {"enabled": enabled and not halted, "interval_seconds": interval, "batch_limit": batch, "halted": halted, "halt_reason": reason, "updated_by": actor, "updated_at": datetime.now(timezone.utc).isoformat()}
    result = _store()._request("PATCH", "renewal_worker_config", params={"worker_name": "eq.entitlement_kick"}, json=payload, prefer="return=representation")
    _store()._request("POST", "renewal_worker_config_audit", json={"worker_name": "entitlement_kick", "action": "UPDATE", "payload": payload, "actor": actor}, prefer="return=minimal")
    return result[0] if result else payload
