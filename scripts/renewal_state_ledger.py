from __future__ import annotations

import json
import os
import sys

from new_core.state_ledger import build_state_ledger
from scripts.production_renewal_snapshot import read_all


def main() -> int:
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        orders = read_all(base_url, key, "orders", {"select": "order_id,status,expire_at,telegram_user_id,plan_name", "status": "in.(PAID,EXPIRED)"})
        tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "id,order_id,telegram_user_id,task_state,updated_at,locked_at,resolved_at"})
        groups = read_all(base_url, key, "renewal_kick_group_tasks_v2", {"select": "id,task_id,order_id,telegram_user_id,group_id,group_state,updated_at,locked_at,resolved_at"})
        attempts = read_all(base_url, key, "renewal_kick_attempts_v2", {"select": "id,task_id,group_task_id,order_id,attempt_state,started_at"})
        print(json.dumps(build_state_ledger(orders=orders, tasks=tasks, groups=groups, attempts=attempts), ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"state ledger failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
