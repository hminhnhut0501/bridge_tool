"""Populate Phase 8 read models without sending reminders or mutating Telegram membership."""

from __future__ import annotations

import os
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _rest(base: str, key: str, table: str, *, params=None, method="GET", payload=None):
    request_headers = _headers(key)
    if table == "renewal_membership_snapshots" and method == "POST":
        request_headers["Prefer"] = "resolution=merge-duplicates"
        params = {**(params or {}), "on_conflict": "telegram_user_id,group_id"}
    response = requests.request(
        method,
        f"{base}/rest/v1/{table}",
        headers=request_headers,
        params=params,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json() if response.content else []


def _telegram_membership(token: str, group_id: str, user_id: str) -> tuple[str, str | None]:
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getChatMember",
            params={"chat_id": group_id, "user_id": user_id},
            timeout=2,
        )
    except requests.RequestException as exc:
        return "UNKNOWN", f"Telegram read timeout/error: {exc.__class__.__name__}"
    body = response.json()
    if not response.ok or not body.get("ok"):
        description = str(body.get("description") or f"HTTP {response.status_code}")
        if "user not found" in description.lower() or "participant_id_invalid" in description.lower():
            return "ABSENT", description
        return "UNKNOWN", description
    status = str((body.get("result") or {}).get("status") or "").lower()
    if status in {"left", "kicked"}:
        return "ABSENT", None
    if status in {"member", "administrator", "creator", "restricted"}:
        return "PRESENT", None
    return "UNKNOWN", f"Unsupported Telegram status: {status or 'empty'}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    token = os.environ["BOT_TOKEN"]
    now = datetime.now(timezone.utc).isoformat()

    entitlements = _rest(base, key, "customer_entitlements_v2", params={"select": "*", "offset": args.offset, "limit": args.limit, "order": "id.asc"})
    orders = _rest(
        base,
        key,
        "orders",
        params={"select": "order_id,telegram_user_id,last_reminder_date,expired_notice_at", "limit": "5000"},
    )
    order_by_id = {str(row.get("order_id")): row for row in orders}

    membership_rows = []
    counts = Counter()
    seen = set()
    candidates = []
    for entitlement in entitlements:
        user_id = str(entitlement.get("telegram_user_id") or "")
        group_id = str(entitlement.get("group_id") or "")
        if not user_id or not group_id or (user_id, group_id) in seen:
            continue
        seen.add((user_id, group_id))
        candidates.append((user_id, group_id))

    def check(candidate):
        user_id, group_id = candidate
        return user_id, group_id, _telegram_membership(token, group_id, user_id)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = [executor.submit(check, candidate) for candidate in candidates]
        for index, future in enumerate(as_completed(futures), 1):
            user_id, group_id, (status, error) = future.result()
            
            counts[status] += 1
            membership_rows.append({
                "telegram_user_id": user_id,
                "group_id": group_id,
                "membership_status": status,
                "source": "telegram_read",
                "checked_at": now,
                "last_error": error,
            })
            if index % args.batch_size == 0 or index == len(candidates):
                print(f"membership progress: {index}/{len(candidates)}", flush=True)

            if len(membership_rows) >= args.batch_size:
                _rest(base, key, "renewal_membership_snapshots", method="POST", payload=membership_rows)
                print(f"membership batch written: {index}/{len(candidates)}", flush=True)
                membership_rows = []

    if membership_rows:
        _rest(base, key, "renewal_membership_snapshots", method="POST", payload=membership_rows)
        print(f"membership final batch written: {len(candidates)}/{len(candidates)}", flush=True)

    reminder_rows = []
    for order in orders:
        order_id = str(order.get("order_id") or "")
        sent_at = order.get("expired_notice_at") or order.get("last_reminder_date")
        if not order_id or not sent_at:
            continue
        reminder_rows.append({
            "order_id": order_id,
            "telegram_user_id": str(order.get("telegram_user_id") or ""),
            "reminder_type": "EXPIRY_NOTICE" if order.get("expired_notice_at") else "RENEWAL_REMINDER",
            "status": "SENT",
            "sent_at": sent_at,
            "attempts": 1,
            "last_error": None,
        })
    if reminder_rows:
        _rest(base, key, "renewal_reminder_events", method="POST", payload=reminder_rows)

    print({"entitlements": len(entitlements), "membership_rows": len(membership_rows), "membership_counts": dict(counts), "reminder_rows": len(reminder_rows), "telegram_mutations": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
