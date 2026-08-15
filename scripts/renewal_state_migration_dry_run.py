from __future__ import annotations

import json
import os
import sys
from collections import Counter

from scripts.production_renewal_snapshot import read_all


TASK_MAP = {
    "running": "processing",
    "retry_pending": "processing",
    "pending_confirm": "processing",
    "queued": "queued",
    "processing": "processing",
    "done": "done",
    "partial_done": "partial_done",
    "blocked": "blocked",
    "blocked_active_order": "blocked_active_order",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
}

GROUP_MAP = {
    "pending": "pending",
    "selected": "processing",
    "running": "processing",
    "processing": "processing",
    "waiting_confirm": "waiting_confirm",
    "retry_scheduled": "retry_scheduled",
    "kicked": "kicked",
    "retained": "retained",
    "blocked_active_order": "blocked_active_order",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
    "unmapped": "review_required",
}

MANUAL_REVIEW = {"error", "unknown", "stale_processing", "stale_waiting_confirm"}


def build_migration_plan(tasks, groups):
    task_counts = Counter()
    group_counts = Counter()
    manual_review = Counter()
    task_change_count = 0
    group_change_count = 0

    for row in tasks:
        raw = str(row.get("task_state") or "unknown").strip().lower()
        target = TASK_MAP.get(raw)
        if target is None:
            manual_review[f"task:{raw}"] += 1
            continue
        task_counts[f"{raw}->{target}"] += 1
        if raw != target:
            task_change_count += 1

    for row in groups:
        raw = str(row.get("group_state") or "unknown").strip().lower()
        target = GROUP_MAP.get(raw)
        if target is None:
            manual_review[f"group:{raw}"] += 1
            continue
        group_counts[f"{raw}->{target}"] += 1
        if raw != target:
            group_change_count += 1

    return {
        "mode": "dry_run",
        "task_mapping": dict(task_counts),
        "group_mapping": dict(group_counts),
        "manual_review": dict(manual_review),
        "task_change_count": task_change_count,
        "group_change_count": group_change_count,
        "write_count": 0,
        "telegram_mutation_count": 0,
    }


def main():
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "id,task_state"})
        groups = read_all(base_url, key, "renewal_kick_group_tasks_v2", {"select": "id,group_state"})
        print(json.dumps(build_migration_plan(tasks, groups), ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"migration dry-run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
