"""Conservative periodic runner for the new entitlement kick worker."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from adapters.supabase_kick_jobs import SupabaseKickJobAdapter
from adapters.telegram_membership import TelegramMembershipGateway
from new_core.delayed_kick_worker import run_delayed_kick_worker
from scripts.production_renewal_snapshot import read_all


_run_lock = asyncio.Lock()
_halted = False


def enabled() -> bool:
    return os.getenv("RENEWAL_KICK_WORKER_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}


def _runtime_config(base, key):
    import requests
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    response = requests.get(f"{base.rstrip('/')}/rest/v1/renewal_worker_config", headers=headers, params={"select": "*", "worker_name": "eq.entitlement_kick", "limit": "1"}, timeout=15)
    response.raise_for_status()
    return response.json()[0] if response.json() else {}


def _record_run(base, key, summary):
    import requests
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=minimal"}
    requests.patch(f"{base.rstrip('/')}/rest/v1/renewal_worker_config", headers=headers, params={"worker_name": "eq.entitlement_kick"}, json={"last_run_at": datetime.now(timezone.utc).isoformat(), "last_batch": summary}, timeout=15).raise_for_status()


async def run_one_periodic_batch(bot) -> dict:
    global _halted
    if _halted:
        return {"status": "HALTED", "reason": "retry_or_review_detected"}
    if _run_lock.locked():
        return {"status": "SKIPPED", "reason": "already_running"}
    async with _run_lock:
        base = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        config = _runtime_config(base, key)
        if not config.get("enabled") or config.get("halted"):
            return {"status": "DISABLED", "reason": config.get("halt_reason") or "admin_disabled"}
        limit = max(1, min(int(config.get("batch_limit") or 5), 5))
        entitlements = read_all(base, key, "customer_entitlements_v2", {"select": "*", "limit": "5000"})
        result = await run_delayed_kick_worker(
            SupabaseKickJobAdapter(base, key),
            TelegramMembershipGateway(bot),
            entitlements,
            now=datetime.now(timezone.utc),
            limit=limit,
        )
        summary = {"status": "EXECUTED", "scanned": result.scanned, "kicked": result.kicked, "already_absent": result.already_absent, "retained": result.retained, "retry": result.retry, "review": result.review}
        if result.retry or result.review:
            _halted = True
            summary["status"] = "HALTED"
            summary["reason"] = "retry_or_review_detected"
        _record_run(base, key, summary)
        return summary


async def renewal_kick_worker(bot):
    global _halted
    interval = 300
    print("⏱ Renewal kick worker enabled by admin config: interval>=300s batch<=5")
    while enabled() and not _halted:
        try:
            result = await run_one_periodic_batch(bot)
            print(f"🧹 Renewal kick batch: {result}")
            config = _runtime_config(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
            interval = max(300, int(config.get("interval_seconds") or 300))
        except Exception as exc:
            _halted = True
            print(f"🛑 Renewal kick worker halted: {type(exc).__name__}: {exc}")
        if not _halted:
            await asyncio.sleep(interval)
