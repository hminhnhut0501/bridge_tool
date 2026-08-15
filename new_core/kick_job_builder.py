from __future__ import annotations


def build_kick_job(entitlement: dict) -> dict | None:
    """Build one delayed job only from a complete verified entitlement."""
    if str(entitlement.get("source_quality") or "").upper() != "VERIFIED":
        return None
    if str(entitlement.get("state") or "").upper() not in {"ACTIVE", "EXPIRED"}:
        return None
    if entitlement.get("is_lifetime") or not entitlement.get("expires_at"):
        return None
    if not entitlement.get("group_id"):
        return None
    return {
        "entitlement_id": entitlement.get("id"),
        "source_order_id": entitlement.get("source_order_id"),
        "telegram_user_id": entitlement.get("telegram_user_id"),
        "group_code": entitlement.get("group_code"),
        "group_id": entitlement.get("group_id"),
        "run_at": entitlement.get("expires_at"),
        "status": "PENDING",
        "attempts": 0,
    }


def build_kick_jobs(entitlements: list[dict]) -> list[dict]:
    return [job for row in entitlements if (job := build_kick_job(row)) is not None]
