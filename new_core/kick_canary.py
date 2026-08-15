from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .entitlement_resolver import has_newer_active_entitlement
from .kick_policy import evaluate_kick_eligibility


async def run_read_only_canary(
    jobs: list[dict],
    entitlements: list[dict],
    membership_reader,
    *,
    now: datetime | None = None,
    limit: int = 20,
) -> dict:
    """Read membership and produce decisions without calling kick()."""
    now = now or datetime.now(timezone.utc)
    due = [
        job for job in jobs
        if str(job.get("status") or "").upper() in {"PENDING", "RETRY"}
        and str(job.get("run_at") or "") <= now.isoformat()
    ][:max(1, min(limit, 20))]
    decisions = []
    for job in due:
        user_id = str(job.get("telegram_user_id") or "")
        group_id = str(job.get("group_id") or "")
        group_code = str(job.get("group_code") or "")
        order_id = str(job.get("source_order_id") or "")
        rows = [
            row for row in entitlements
            if str(row.get("telegram_user_id")) == user_id
            and str(row.get("group_code") or "") == group_code
        ]
        entitlement = next((row for row in rows if str(row.get("source_order_id")) == order_id), None)
        newer = has_newer_active_entitlement(rows, telegram_user_id=user_id, group_code=group_code, source_order_id=order_id, now=now)
        policy = evaluate_kick_eligibility(entitlement or {}, now=now, newer_active_exists=newer)
        if policy.action == "BLOCK":
            action = "RETAINED"
            reason = policy.reason
        elif not policy.eligible:
            action = "REVIEW"
            reason = policy.reason
        else:
            presence = await membership_reader.is_present(group_id, user_id)
            if presence is True:
                action, reason = "WOULD_KICK", "member_present"
            elif presence is False:
                action, reason = "ALREADY_ABSENT", "member_absent"
            else:
                action, reason = "REVIEW", "membership_unknown"
        decisions.append({"job_id": job.get("id"), "source_order_id": order_id, "telegram_user_id": user_id, "group_id": group_id, "action": action, "reason": reason})
    return {
        "contract": "renewal_kick_canary_v1",
        "mode": "read_only",
        "scanned": len(decisions),
        "action_counts": dict(Counter(row["action"] for row in decisions)),
        "decisions": decisions,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }
