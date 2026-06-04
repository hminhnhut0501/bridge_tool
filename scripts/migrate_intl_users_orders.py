"""Safely migrate real intl orders and optional language preferences.

Existing Supabase orders are never overwritten. Pending orders are excluded by
default because they are abandoned checkout attempts, not customer purchases.
"""

import argparse
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


LOCAL_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def normalize_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if not parsed:
        raise ValueError(f"Invalid datetime: {raw}")
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
    return parsed.isoformat()


def request(method, table, *, params=None, payload=None, prefer=None):
    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    response = requests.request(
        method,
        f"{url}/rest/v1/{table}",
        params=params,
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json() if response.text else []


def order_payload(row):
    keys = (
        "order_id",
        "telegram_user_id",
        "full_name",
        "plan_name",
        "amount",
        "status",
        "sale_id",
        "original_amount",
        "coupon_code",
        "coupon_discount_percent",
        "coupon_discount_amount",
        "last_reminder_date",
        "created_at",
        "updated_at",
    )
    payload = {key: row[key] for key in keys if key in row.keys() and row[key] not in (None, "")}
    for key in ("paid_at", "expire_at", "expired_notice_at"):
        if row[key]:
            payload[key] = normalize_datetime(row[key])
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sqlite_path")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-pending", action="store_true")
    parser.add_argument("--english-user", action="append", default=[])
    args = parser.parse_args()

    connection = sqlite3.connect(args.sqlite_path)
    connection.row_factory = sqlite3.Row
    statuses = ("PAID", "EXPIRED", "PENDING") if args.include_pending else ("PAID", "EXPIRED")
    placeholders = ",".join("?" for _ in statuses)
    source_orders = list(
        connection.execute(f"select * from orders where status in ({placeholders}) order by created_at", statuses)
    )
    connection.close()

    order_ids = [str(row["order_id"]) for row in source_orders]
    existing = request(
        "GET",
        "orders",
        params={"select": "order_id", "order_id": f"in.({','.join(order_ids)})"},
    )
    existing_ids = {str(row["order_id"]) for row in existing}
    new_orders = [order_payload(row) for row in source_orders if str(row["order_id"]) not in existing_ids]

    print(f"Source orders: {len(source_orders)}")
    print(f"Existing orders skipped: {len(existing_ids)}")
    print(f"New orders to import: {len(new_orders)}")
    for order in new_orders:
        print(f"  {order['order_id']} | {order['telegram_user_id']} | {order['status']} | {order['plan_name']}")
    print(f"Users to mark English: {', '.join(args.english_user) or 'none'}")

    if not args.apply:
        print("Dry run only. Add --apply to migrate.")
        return

    if new_orders:
        request(
            "POST",
            "orders",
            params={"on_conflict": "order_id"},
            payload=new_orders,
            prefer="resolution=ignore-duplicates,return=minimal",
        )
    if args.english_user:
        request(
            "POST",
            "user_preferences",
            params={"on_conflict": "telegram_user_id"},
            payload=[{"telegram_user_id": str(user_id), "language": "en"} for user_id in args.english_user],
            prefer="resolution=merge-duplicates,return=minimal",
        )
    print("Migration completed.")


if __name__ == "__main__":
    main()
