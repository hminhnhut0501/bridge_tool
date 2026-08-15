from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def build_plan(audit: dict, snapshot: dict | None = None) -> dict:
    rows = [row for row in audit.get("rows", []) if row.get("outcome") == "absent"]
    return {
        "mode": "read_only_repair_plan",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "stale_task_membership_audit",
        "candidate_count": len(rows),
        "unknown_excluded": sum(1 for row in audit.get("rows", []) if row.get("outcome") == "unknown"),
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
        "candidates": rows,
        "snapshot_integrity": (snapshot or {}).get("integrity", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only stale task repair plan.")
    parser.add_argument("audit_file")
    parser.add_argument("--snapshot-file")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.audit_file, encoding="utf-8") as handle:
        audit = json.load(handle)
    snapshot = None
    if args.snapshot_file:
        with open(args.snapshot_file, encoding="utf-8") as handle:
            snapshot = json.load(handle)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(build_plan(audit, snapshot), handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
