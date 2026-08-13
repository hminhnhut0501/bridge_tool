#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from typing import Any

from scheduler import normalize_chat_id, normalize_renewal_kick_reason, normalize_renewal_kick_state, parse_expire_datetime
from supabase_store import supabase_store


TASK_STATE_MAP = {
    "queued": "queued",
    "pending": "queued",
    "processing": "processing",
    "pending_confirm": "waiting_confirm",
    "retry_pending": "retry_scheduled",
    "error_retryable": "retry_scheduled",
    "done": "done",
    "blocked_active_order": "blocked_active_order",
    "blocked": "blocked",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
    "migrated_legacy": "migrated_legacy",
}

GROUP_STATE_MAP = {
    "queued": "pending",
    "pending": "pending",
    "processing": "processing",
    "pending_confirm": "waiting_confirm",
    "retry_pending": "retry_scheduled",
    "error_retryable": "retry_scheduled",
    "done": "kicked",
    "blocked_active_order": "blocked_active_order",
    "blocked": "blocked_active_order",
    "review_required": "review_required",
    "failed_terminal": "failed_terminal",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _pick_reason(row: dict[str, Any]) -> str:
    candidates = [
        row.get("last_error"),
        row.get("last_error_code"),
        row.get("last_reason"),
        row.get("review_reason"),
        row.get("terminal_reason"),
        (row.get("metadata") or {}).get("reason"),
        (row.get("metadata") or {}).get("last_error"),
    ]
    for value in candidates:
        text = _text(value)
        if text:
            return text
    return ""


def _migrate_group_state(row: dict[str, Any]) -> str:
    state = normalize_renewal_kick_state(row.get("state") or row.get("group_state") or "")
    return GROUP_STATE_MAP.get(state, "pending")


def _migrate_task_state(rows: list[dict[str, Any]]) -> str:
    normalized_states = [normalize_renewal_kick_state(row.get("state") or row.get("group_state") or "") for row in rows]
    if any(state in {"review_required", "failed_terminal"} for state in normalized_states):
        return "review_required"
    if any(state in {"blocked", "blocked_active_order"} for state in normalized_states):
        return "blocked"
    if any(state in {"processing", "pending_confirm"} for state in normalized_states):
        return "processing"
    if any(state in {"retry_pending", "error_retryable"} for state in normalized_states):
        return "retry_scheduled"
    if all(state in {"done"} for state in normalized_states if state):
        return "done"
    if rows:
        return "queued"
    return "migrated_legacy"


def migrate_legacy_renewal_kick_tasks(limit: int, dry_run: bool = False) -> dict[str, int]:
    legacy_rows = supabase_store.list_renewal_kick_tasks(limit=limit)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in legacy_rows:
        order_id = _text(row.get("order_id"))
        telegram_user_id = _text(row.get("telegram_user_id"))
        if not order_id or not telegram_user_id:
            continue
        grouped[(order_id, telegram_user_id)].append(row)

    summary = {"legacy_rows": len(legacy_rows), "tasks": 0, "group_tasks": 0, "maps": 0, "skipped": 0}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for (order_id, telegram_user_id), rows in grouped.items():
        rows = sorted(rows, key=lambda row: _text(row.get("updated_at") or row.get("created_at")))
        latest = rows[-1]
        plan_name = _text(latest.get("plan_name") or rows[0].get("plan_name"))
        due_at = latest.get("due_at") or latest.get("requested_at") or latest.get("created_at") or now
        parent_payload = {
            "order_id": order_id,
            "telegram_user_id": telegram_user_id,
            "plan_name": plan_name,
            "task_state": TASK_STATE_MAP.get(normalize_renewal_kick_state(latest.get("state") or latest.get("task_state") or ""), _migrate_task_state(rows)),
            "priority": int(latest.get("priority") or 0),
            "due_at": due_at,
            "locked_at": latest.get("locked_at"),
            "locked_by": latest.get("locked_by"),
            "last_transition_at": latest.get("updated_at") or latest.get("last_transition_at") or now,
            "total_groups": len(rows),
            "kicked_groups": sum(1 for row in rows if _migrate_group_state(row) == "kicked"),
            "retained_groups": sum(1 for row in rows if _migrate_group_state(row) == "retained"),
            "pending_groups": sum(1 for row in rows if _migrate_group_state(row) in {"pending", "selected", "processing", "waiting_confirm", "retry_scheduled"}),
            "error_groups": sum(1 for row in rows if _migrate_group_state(row) in {"review_required", "failed_terminal"}),
            "review_groups": sum(1 for row in rows if _migrate_group_state(row) == "review_required"),
            "attempt_count": sum(int(row.get("attempt_count") or 0) for row in rows),
            "confirm_count": sum(int(row.get("confirm_count") or 0) for row in rows),
            "retry_count": sum(int(row.get("retry_count") or 0) for row in rows),
            "last_error": _pick_reason(latest) or "",
            "last_reason": _pick_reason(latest) or "",
            "review_reason": _pick_reason(latest) if _migrate_task_state(rows) == "review_required" else "",
            "terminal_reason": _pick_reason(latest) if _migrate_task_state(rows) == "done" else "",
            "metadata": {
                "migrated_from": "renewal_kick_tasks",
                "migrated_at": now,
                "legacy_rows": [row.get("id") for row in rows if row.get("id")],
            },
            "completed_at": latest.get("completed_at"),
            "resolved_at": latest.get("resolved_at"),
        }

        if not dry_run:
            parent_rows = supabase_store.upsert_renewal_kick_task_v2(parent_payload) or []
            parent_task_id = parent_rows[0]["id"] if parent_rows else None
        else:
            parent_task_id = f"dry-run:{order_id}:{telegram_user_id}"
        summary["tasks"] += 1

        for row in rows:
            group_id = _text(row.get("group_id"))
            if not group_id:
                summary["skipped"] += 1
                continue
            group_payload = {
                "task_id": parent_task_id,
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "group_id": group_id,
                "group_name": _text(row.get("group_name") or group_id),
                "group_no": _text(row.get("group_no") or row.get("group_id") or ""),
                "plan_name": plan_name,
                "group_state": _migrate_group_state(row),
                "attempt_count": int(row.get("attempt_count") or 0),
                "confirm_count": int(row.get("confirm_count") or 0),
                "locked_at": row.get("locked_at"),
                "locked_by": row.get("locked_by"),
                "first_due_at": row.get("due_at") or row.get("requested_at") or row.get("created_at") or due_at,
                "next_retry_at": row.get("next_retry_at"),
                "last_transition_at": row.get("updated_at") or row.get("last_transition_at") or now,
                "last_error": _pick_reason(row),
                "last_reason": _pick_reason(row),
                "review_reason": _pick_reason(row) if _migrate_group_state(row) == "review_required" else "",
                "terminal_reason": _pick_reason(row) if _migrate_group_state(row) == "kicked" else "",
                "metadata": {
                    "migrated_from": "renewal_kick_tasks",
                    "legacy_row_id": row.get("id"),
                    "legacy_state": row.get("state"),
                    "legacy_reason": row.get("last_error") or row.get("last_reason") or row.get("review_reason") or "",
                },
                "completed_at": row.get("completed_at"),
                "resolved_at": row.get("resolved_at"),
            }
            if not dry_run:
                group_rows = supabase_store.upsert_renewal_kick_group_task_v2(group_payload) or []
                group_task_id = group_rows[0]["id"] if group_rows else None
                if group_task_id:
                    supabase_store.upsert_renewal_kick_legacy_map_v2({
                        "legacy_key": f"renewal_kick_tasks:{row.get('id') or order_id}:{group_id}",
                        "task_id": parent_task_id,
                        "group_task_id": group_task_id,
                        "legacy_source": "old_task",
                        "legacy_ref": str(row.get("id") or ""),
                        "metadata": {
                            "order_id": order_id,
                            "telegram_user_id": telegram_user_id,
                            "group_id": group_id,
                            "legacy_state": row.get("state"),
                        },
                    })
                    summary["maps"] += 1
            summary["group_tasks"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill legacy renewal kick rows into v2 tables.")
    parser.add_argument("--limit", type=int, default=5000, help="Max legacy rows to scan.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only, do not write rows.")
    args = parser.parse_args()

    summary = migrate_legacy_renewal_kick_tasks(limit=max(1, args.limit), dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "MIGRATED"
    print(f"[{mode}] {summary}")


if __name__ == "__main__":
    main()
