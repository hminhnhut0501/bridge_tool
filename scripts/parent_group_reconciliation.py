from __future__ import annotations

import argparse
import json
import os
import sys

from new_core.reconciliation import build_parent_group_reconciliation
from scripts.production_renewal_snapshot import read_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only renewal parent/group reconciliation.")
    parser.add_argument("--output")
    args = parser.parse_args()
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        orders = read_all(base_url, key, "orders", {"select": "order_id,status,expire_at,telegram_user_id,plan_name", "status": "in.(PAID,EXPIRED)"})
        tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "id,order_id,telegram_user_id,task_state,updated_at,locked_at,resolved_at"})
        groups = read_all(base_url, key, "renewal_kick_group_tasks_v2", {"select": "id,task_id,order_id,telegram_user_id,group_id,group_state,updated_at,locked_at,resolved_at"})
        report = build_parent_group_reconciliation(orders=orders, tasks=tasks, groups=groups)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(rendered + "\n")
        else:
            print(rendered)
    except Exception as exc:
        print(f"reconciliation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
