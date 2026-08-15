from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone

from scripts.production_renewal_snapshot import read_all


def build_report(rows: list[dict]) -> dict:
    counts = Counter(str(row.get("state") or "UNKNOWN") for row in rows)
    reasons = Counter(str(row.get("state_reason") or "unknown") for row in rows)
    candidates = []
    for row in rows:
        state = str(row.get("state") or "UNKNOWN")
        if state in {"REVIEW", "EXPIRED"}:
            candidates.append({
                "source_order_id": row.get("source_order_id"),
                "telegram_user_id": row.get("telegram_user_id"),
                "plan_family": row.get("plan_family"),
                "group_code": row.get("group_code"),
                "expires_at": row.get("expires_at"),
                "state": state,
                "state_reason": row.get("state_reason"),
                "source_quality": row.get("source_quality"),
                "automatic_kick_eligible": state == "EXPIRED"
                and row.get("group_code") is not None
                and row.get("source_quality") == "VERIFIED",
            })
    return {
        "contract": "customer_entitlements_audit_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only",
        "rows": len(rows),
        "state_counts": dict(counts),
        "reason_counts": dict(reasons),
        "candidates": candidates,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the read-only entitlement projection.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    rows = read_all(base_url, key, "customer_entitlements_v1", {"select": "*"})
    report = build_report(rows)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ("rows", "state_counts", "reason_counts", "supabase_write_count", "telegram_mutation_count")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
