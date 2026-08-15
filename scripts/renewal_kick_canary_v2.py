from __future__ import annotations

import argparse
import asyncio
import json
import os

from new_core.kick_canary import run_read_only_canary
from scripts.production_renewal_snapshot import read_all
from scripts.stale_task_membership_audit import telegram_get_member


class TelegramReadOnly:
    def __init__(self, token: str, *, timeout: float, retries: int):
        self.token = token
        self.timeout = timeout
        self.retries = retries

    async def is_present(self, group_id: str, user_id: str):
        outcome, _reason = telegram_get_member(
            self.token, group_id, user_id, timeout=self.timeout, retries=self.retries
        )
        return {"present": True, "absent": False, "unknown": None}[outcome]


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only renewal kick canary.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    token = os.getenv("BOT_TOKEN")
    if not base_url or not key or not token:
        raise SystemExit("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and BOT_TOKEN are required")
    jobs = read_all(base_url, key, "entitlement_kick_jobs", {"select": "*", "order": "run_at.asc"})
    entitlements = read_all(base_url, key, "customer_entitlements_v2", {"select": "*"})
    report = asyncio.run(run_read_only_canary(
        jobs, entitlements, TelegramReadOnly(token, timeout=args.timeout, retries=args.retries), limit=args.limit
    ))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ("scanned", "action_counts", "supabase_write_count", "telegram_mutation_count")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
