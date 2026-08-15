from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class KickDecision:
    eligible: bool
    action: str
    reason: str


def evaluate_kick_eligibility(
    entitlement: dict,
    *,
    now: datetime | None = None,
    newer_active_exists: bool = False,
) -> KickDecision:
    """Pure kick policy. It never calls Telegram or changes persistence."""
    now = now or datetime.now(timezone.utc)
    state = str(entitlement.get("state") or "").upper()
    quality = str(entitlement.get("source_quality") or "").upper()
    group_code = entitlement.get("group_code")
    expires_at = entitlement.get("expires_at")

    if state == "CANCELLED":
        return KickDecision(False, "NOOP", "cancelled_entitlement")
    if state != "EXPIRED":
        return KickDecision(False, "REVIEW", "entitlement_not_expired")
    if quality != "VERIFIED":
        return KickDecision(False, "REVIEW", "unverified_source")
    if not group_code:
        return KickDecision(False, "REVIEW", "missing_group_code")
    if not expires_at:
        return KickDecision(False, "REVIEW", "missing_expiry")
    if newer_active_exists:
        return KickDecision(False, "BLOCK", "newer_active_entitlement")
    if hasattr(expires_at, "tzinfo"):
        expiry = expires_at
    else:
        try:
            expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        except ValueError:
            return KickDecision(False, "REVIEW", "invalid_expiry")
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry > now:
        return KickDecision(False, "REVIEW", "expiry_in_future")
    return KickDecision(True, "KICK", "expired_verified_entitlement")
