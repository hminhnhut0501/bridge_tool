from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .entitlement_resolver import has_newer_active_entitlement
from .kick_policy import evaluate_kick_eligibility


def evaluate_dry_run(entitlements: list[dict], *, now: datetime | None = None) -> dict:
    """Evaluate expired entitlements without persistence or Telegram mutation."""
    now = now or datetime.now(timezone.utc)
    decisions = []
    for entitlement in entitlements:
        if str(entitlement.get("state") or "").upper() != "EXPIRED":
            continue
        user_id = str(entitlement.get("telegram_user_id") or "")
        group_code = str(entitlement.get("group_code") or "")
        newer_active = has_newer_active_entitlement(
            entitlements,
            telegram_user_id=user_id,
            group_code=group_code,
            source_order_id=str(entitlement.get("source_order_id") or ""),
            now=now,
        )
        decision = evaluate_kick_eligibility(
            entitlement,
            now=now,
            newer_active_exists=newer_active,
        )
        decisions.append({
            "source_order_id": entitlement.get("source_order_id"),
            "telegram_user_id": entitlement.get("telegram_user_id"),
            "group_code": entitlement.get("group_code"),
            "action": decision.action,
            "reason": decision.reason,
            "eligible": decision.eligible,
        })
    counts = Counter(row["action"] for row in decisions)
    return {
        "contract": "renewal_kick_dry_run_v1",
        "mode": "read_only",
        "generated_at": now.isoformat(),
        "scanned": len(decisions),
        "action_counts": dict(counts),
        "decisions": decisions,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }
