"""Run one small production renewal kick batch through the new core."""

from __future__ import annotations

import asyncio
import os
import sys

from aiogram import Bot

from adapters.supabase_kick_jobs import SupabaseKickJobAdapter
from adapters.telegram_membership import TelegramMembershipGateway
from new_core.delayed_kick_worker import run_delayed_kick_worker
from scripts.production_renewal_snapshot import read_all


async def main() -> int:
    base = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    token = os.environ["BOT_TOKEN"]
    limit = max(1, min(int(os.getenv("KICK_WORKER_BATCH_LIMIT", "1")), 5))
    jobs = SupabaseKickJobAdapter(base, key)
    entitlements = read_all(base, key, "customer_entitlements_v2", {"select": "*", "limit": "5000"})
    bot = Bot(token=token)
    try:
        result = await run_delayed_kick_worker(
            jobs,
            TelegramMembershipGateway(bot),
            entitlements,
            limit=limit,
        )
        print({"scanned": result.scanned, "kicked": result.kicked, "already_absent": result.already_absent, "retained": result.retained, "review": result.review, "retry": result.retry})
    finally:
        await bot.session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
