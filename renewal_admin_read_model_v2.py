from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone


def _customer_map(orders):
    return {str(row.get("order_id")): row for row in orders}


def build_renewal_read_model(entitlements, jobs, orders, membership_snapshots=None, reminder_events=None, *, now=None, tab="expiring-soon"):
    now = now or datetime.now(timezone.utc)
    order_by_id = _customer_map(orders)
    job_by_entitlement = {str(row.get("entitlement_id")): row for row in jobs}
    membership_by_key = {(str(row.get("telegram_user_id")), str(row.get("group_id"))): row for row in (membership_snapshots or [])}
    reminders_by_order = {}
    for event in reminder_events or []:
        key = str(event.get("order_id") or "")
        if key and key not in reminders_by_order:
            reminders_by_order[key] = event
    rows = []
    for entitlement in entitlements:
        state = str(entitlement.get("state") or "").upper()
        expiry = entitlement.get("expires_at")
        expiry_dt = None
        if expiry:
            try:
                expiry_dt = datetime.fromisoformat(str(expiry).replace("Z", "+00:00"))
                if expiry_dt.tzinfo is None:
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        if tab == "expiring-soon" and not (state == "ACTIVE" and expiry_dt and expiry_dt > now and not entitlement.get("is_lifetime")):
            continue
        if tab == "expired" and state != "EXPIRED":
            continue
        order = order_by_id.get(str(entitlement.get("source_order_id")), {})
        job = job_by_entitlement.get(str(entitlement.get("id")), {})
        reminder = reminders_by_order.get(str(entitlement.get("source_order_id")), {})
        reminder_sent = reminder.get("sent_at") or order.get("expired_notice_at") or order.get("last_reminder_date")
        reminder_failed = str(reminder.get("status") or "").upper() == "FAILED"
        snapshot = membership_by_key.get((str(entitlement.get("telegram_user_id") or ""), str(entitlement.get("group_id") or "")), {})
        kick_status = str(job.get("status") or ("NOT_DUE" if tab == "expiring-soon" else "REVIEW")).upper()
        rows.append({
            "customer": {"name": order.get("full_name"), "telegramUserId": str(entitlement.get("telegram_user_id") or "")},
            "entitlement": {"orderId": str(entitlement.get("source_order_id") or ""), "planName": order.get("plan_name") or "", "planFamily": entitlement.get("plan_family") or "", "groupCode": entitlement.get("group_code") or "", "groupId": entitlement.get("group_id"), "expiresAt": expiry, "isLifetime": bool(entitlement.get("is_lifetime"))},
            "reminder": {"status": "FAILED" if reminder_failed else ("SENT" if reminder_sent else "NOT_SENT"), "sentAt": reminder_sent, "attempts": int(reminder.get("attempts") or (1 if reminder_sent else 0)), "lastError": reminder.get("last_error")},
            "membership": str(snapshot.get("membership_status") or "UNKNOWN").upper(),
            "kick": {"status": kick_status, "attempts": int(job.get("attempts") or 0), "lastError": job.get("last_error"), "updatedAt": job.get("updated_at")},
        })
    summary = Counter()
    for row in rows:
        if tab == "expiring-soon":
            summary["expiringSoon"] += 1
            if row["reminder"]["status"] == "NOT_SENT": summary["reminderNotSent"] += 1
        else:
            summary["expired"] += 1
            if row["kick"]["status"] in {"PENDING", "PROCESSING", "RETRY"}: summary["pendingKick"] += 1
            if row["kick"]["status"] == "DONE": summary["kicked"] += 1
            if row["kick"]["status"] == "RETAINED": summary["retained"] += 1
            if row["kick"]["status"] == "REVIEW": summary["review"] += 1
    return {"tab": tab, "rows": rows, "summary": dict(summary), "loading": False, "error": None, "source": "API"}
