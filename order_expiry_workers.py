from __future__ import annotations

import asyncio
import logging

from config_utils import config_int
from order_expiry_service import reconcile_expired_paid_orders
from scheduler import check_expirations_professional, now_local, parse_expire_datetime, parse_int_config
from supabase_store import supabase_store


ORDER_EXPIRED_RECONCILE_INTERVAL_SECONDS = 30 * 60
ORDER_EXPIRED_RECONCILE_MIN_INTERVAL_SECONDS = 60


async def expiration_scanner_worker():
    logging.info("⏳ Expiration scanner worker đã khởi động.")
    while True:
        try:
            await check_expirations_professional()
        except Exception as exc:
            logging.error("❌ Expiration scanner worker lỗi: %s", exc)

        interval_seconds = config_int(
            "SCHEDULER_INTERVAL_SECONDS",
            8 * 60 * 60,
            minimum=60,
        )
        await asyncio.sleep(interval_seconds)


async def order_expired_reconcile_worker():
    logging.info("♻️ Order expired reconcile worker đã khởi động.")
    if not supabase_store.enabled:
        logging.info("⏭ Bỏ qua reconcile worker vì Supabase chưa bật.")
        return

    await asyncio.sleep(config_int("ORDER_EXPIRED_RECONCILE_INITIAL_DELAY_SECONDS", 30, minimum=0))
    while True:
        try:
            now = now_local()
            reconcile_limit = config_int("ORDER_EXPIRED_RECONCILE_LIMIT", 5000, minimum=100)
            try:
                candidates = supabase_store.list_scheduler_due_rows(now, limit=reconcile_limit)
            except Exception as exc:
                logging.warning("⚠️ Không tải được danh sách đơn để reconcile: %s", exc)
                candidates = []
            reconciled_orders = reconcile_expired_paid_orders(
                candidates,
                now,
                parser=parse_expire_datetime,
                mark_expired=supabase_store.mark_order_expired,
                limit=reconcile_limit,
            )
            if reconciled_orders:
                logging.info("♻️ Reconcile worker đổi %s đơn sang EXPIRED.", len(reconciled_orders))
        except Exception as exc:
            logging.error("❌ Order expired reconcile worker lỗi: %s", exc)
        interval_seconds = config_int(
            "ORDER_EXPIRED_RECONCILE_INTERVAL_SECONDS",
            ORDER_EXPIRED_RECONCILE_INTERVAL_SECONDS,
            minimum=ORDER_EXPIRED_RECONCILE_MIN_INTERVAL_SECONDS,
        )
        await asyncio.sleep(interval_seconds)
