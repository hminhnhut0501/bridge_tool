from __future__ import annotations

import json
import os
import sys
import urllib.parse
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from scripts.production_renewal_snapshot import read_all
from scripts.readonly_http import get_json


def telegram_get_member(token: str, group_id: str, user_id: str, timeout: float = 8.0, retries: int = 1):
    query = urllib.parse.urlencode({"chat_id": group_id, "user_id": user_id})
    url = f"https://api.telegram.org/bot{token}/getChatMember?{query}"
    try:
        payload = get_json(url, timeout=timeout, retries=retries)
    except Exception as exc:
        return "unknown", type(exc).__name__
    if not payload.get("ok"):
        description = str(payload.get("description") or "telegram_error").lower()
        if any(token in description for token in ("user not found", "participant_id_invalid", "member not found")):
            return "absent", description
        return "unknown", description
    status = str((payload.get("result") or {}).get("status") or "").lower()
    if status in {"left", "kicked", "banned"}:
        return "absent", status
    if status in {"member", "administrator", "creator", "restricted"}:
        return "present", status
    return "unknown", status or "missing_status"


def audit_rows(rows, token: str, max_workers: int = 16, timeout: float = 8.0, retries: int = 1):
    counts = Counter()
    reasons = Counter()
    audited_rows = []
    def check(row):
        return telegram_get_member(
            token,
            str(row.get("group_id") or ""),
            str(row.get("telegram_user_id") or ""),
            timeout=timeout,
            retries=retries,
        )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(check, rows)
    for index, (row, result) in enumerate(zip(rows, results), start=1):
        outcome, reason = result
        counts[outcome] += 1
        reasons[f"{outcome}:{reason}"] += 1
        audited_rows.append({
            "task_id": row.get("id"),
            "order_id": row.get("order_id"),
            "group_id": row.get("group_id"),
            "telegram_user_id": row.get("telegram_user_id"),
            "group_state": row.get("group_state"),
            "locked_at": row.get("locked_at"),
            "last_transition_at": row.get("last_transition_at"),
            "outcome": outcome,
            "reason": reason,
        })
        if index == len(rows) or index % 25 == 0:
            print(f"audit progress: {index}/{len(rows)}", file=sys.stderr, flush=True)
    return {
        "mode": "read_only",
        "scanned": len(rows),
        "outcomes": dict(counts),
        "reasons": dict(reasons),
        "rows": audited_rows,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only Telegram membership audit for stale renewal tasks.")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args()
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    token = os.getenv("BOT_TOKEN")
    if not base_url or not key or not token:
        print("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and BOT_TOKEN are required", file=sys.stderr)
        return 2
    try:
        rows = read_all(
            base_url,
            key,
            "renewal_kick_group_tasks_v2",
            {"select": "id,order_id,group_id,telegram_user_id,group_state,last_transition_at,locked_at", "group_state": "eq.processing"},
        )
        print(json.dumps(
            audit_rows(
                rows,
                token,
                max_workers=max(1, args.workers),
                timeout=max(0.5, args.timeout),
                retries=max(0, args.retries),
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ))
    except Exception as exc:
        print(f"stale membership audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
