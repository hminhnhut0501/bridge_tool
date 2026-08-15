from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

from scripts.production_renewal_snapshot import read_all


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_order(row: dict, *, now: datetime) -> str:
    status = str(row.get("status") or "").strip().upper()
    expire_at = parse_datetime(row.get("expire_at"))
    plan_family = str(row.get("canonical_plan_family") or "").strip().upper()
    duration = str(row.get("canonical_duration") or "").strip().upper()
    if not status:
        return "MISSING_STATUS"
    if not expire_at and duration == "LIFETIME":
        return "LIFETIME_NO_EXPIRY"
    if not expire_at:
        return "MISSING_EXPIRE_AT"
    if status == "PAID" and expire_at <= now and duration != "LIFETIME":
        return "PAID_BUT_EXPIRED_BY_DATE"
    if status == "EXPIRED" and expire_at > now and duration != "LIFETIME":
        return "EXPIRED_BUT_FUTURE_DATE"
    if status not in {"PAID", "EXPIRED", "CANCELLED", "REFUNDED"}:
        return "UNKNOWN_STATUS"
    if duration == "LIFETIME" and status == "EXPIRED":
        return "LIFETIME_EXPIRED"
    if not plan_family:
        return "MISSING_PLAN_FAMILY"
    return "OK"


def build_report(rows: list[dict], *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    classified = []
    counts = Counter()
    for row in rows:
        category = classify_order(row, now=now)
        counts[category] += 1
        if category != "OK":
            classified.append({
                "order_id": row.get("order_id"),
                "telegram_user_id": row.get("telegram_user_id"),
                "plan_name": row.get("plan_name"),
                "status": row.get("status"),
                "expire_at": row.get("expire_at"),
                "canonical_plan_family": row.get("canonical_plan_family"),
                "canonical_duration": row.get("canonical_duration"),
                "category": category,
            })
    return {
        "contract": "order_lifecycle_audit_v1",
        "checked_at": now.isoformat(),
        "rows": len(rows),
        "counts": dict(counts),
        "issues": classified,
        "write_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only order lifecycle audit.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        rows = read_all(base_url, key, "orders", {"select": "order_id,telegram_user_id,plan_name,status,expire_at,canonical_plan_family,canonical_duration"})
        report = build_report(rows)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps({"rows": report["rows"], "counts": report["counts"], "write_count": 0}, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"order lifecycle audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
