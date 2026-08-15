from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def build_candidates(ledger: dict, membership_audit: dict | None = None) -> dict:
    audit_rows = (membership_audit or {}).get("rows", [])
    absent = [row for row in audit_rows if row.get("outcome") == "absent"]
    unknown = [row for row in audit_rows if row.get("outcome") == "unknown"]
    integrity = ledger.get("integrity", {})
    return {
        "contract": "renewal_historical_repair_candidates_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only",
        "source_contract": ledger.get("contract", "unknown"),
        "support_events_used": False,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
        "candidates": {
            "membership_absent": absent,
            "membership_unknown": unknown,
            "orders_without_task": integrity.get("orders_without_task", []),
            "tasks_without_order": integrity.get("tasks_without_order", []),
            "groups_without_parent": integrity.get("groups_without_parent", []),
            "stale_locked_tasks": integrity.get("stale_locked_tasks", []),
            "duplicate_task_keys": integrity.get("duplicate_task_keys", []),
            "duplicate_group_keys": integrity.get("duplicate_group_keys", []),
        },
        "policy": {
            "repairable_now": "membership_absent only",
            "manual_review_required": [
                "membership_unknown",
                "orders_without_task",
                "tasks_without_order",
                "groups_without_parent",
                "stale_locked_tasks",
                "duplicate_task_keys",
                "duplicate_group_keys",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build read-only historical renewal repair candidates.")
    parser.add_argument("ledger_file")
    parser.add_argument("--membership-audit")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.ledger_file, encoding="utf-8") as handle:
        ledger = json.load(handle)
    membership = None
    if args.membership_audit:
        with open(args.membership_audit, encoding="utf-8") as handle:
            membership = json.load(handle)
    report = build_candidates(ledger, membership)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
