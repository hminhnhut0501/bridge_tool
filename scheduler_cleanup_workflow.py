from __future__ import annotations

import logging
from datetime import timedelta

from supabase_store import supabase_store
from support_utils import revoke_support_invite_link


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


async def cleanup_order_invite_links(now=None, *, only_used=False, group_id=None, force=False):
    scheduler = _scheduler()
    if not supabase_store.enabled:
        return {"total": 0, "success": 0, "failed": 0, "rows": []}
    now = now or scheduler.now_local()
    cleanup_days = scheduler.parse_int_config("ACTIVATION_LINK_CLEANUP_DAYS", 7, minimum=1)
    cutoff = now - timedelta(days=cleanup_days)
    target_group_id = scheduler.normalize_chat_id(group_id) if group_id else ""
    try:
        rows = supabase_store.list_order_activation_codes(limit=scheduler.config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100))
    except Exception as exc:
        logging.warning("⚠️ Không đọc được order_activation_codes để dọn link: %s", exc)
        return {"total": 0, "success": 0, "failed": 0, "rows": [], "error": str(exc)}

    results = []
    success_count = 0
    failed_count = 0
    for row in rows:
        status = str(row.get("activation_status") or "").strip().upper()
        if only_used and status != "USED":
            continue
        used_at = scheduler.parse_expire_datetime(row.get("used_at") or row.get("activated_at"))
        if only_used and not force and (not used_at or used_at > cutoff):
            continue
        raw_data = row.get("raw_data") or {}
        if not isinstance(raw_data, dict):
            continue
        if not force and raw_data.get("invite_cleanup_done_at"):
            continue
        invite_results = raw_data.get("invite_results") or []
        cleanup_results = []
        row_success = False
        for item in invite_results:
            if not isinstance(item, dict):
                continue
            if not item.get("ok") or not item.get("invite_link") or not item.get("group_id"):
                continue
            item_group_id = scheduler.normalize_chat_id(item.get("group_id"))
            if target_group_id and item_group_id != target_group_id:
                continue
            ok, error = await revoke_support_invite_link(item.get("group_id"), item.get("invite_link"))
            cleanup_results.append({
                "group_id": str(item.get("group_id") or ""),
                "group_name": str(item.get("group_name") or ""),
                "ok": ok,
                "error": error,
            })
            row_success = row_success or ok
            success_count += int(ok)
            failed_count += int(not ok)
        if not cleanup_results:
            continue
        updated_raw = dict(raw_data)
        updated_raw["invite_cleanup_done_at"] = now.isoformat(timespec="seconds")
        updated_raw["invite_cleanup_results"] = cleanup_results
        try:
            supabase_store.update_order_activation_code(row.get("code"), {"raw_data": updated_raw})
        except Exception as exc:
            logging.warning("⚠️ Không update raw_data cleanup cho %s: %s", row.get("code"), exc)
            continue
        results.append({
            "code": row.get("code"),
            "order_id": row.get("order_id"),
            "telegram_user_id": row.get("telegram_user_id"),
            "group_id": target_group_id or "",
            "success": row_success,
            "cleanup_results": cleanup_results,
        })
    return {"total": len(results), "success": success_count, "failed": failed_count, "rows": results}


async def cleanup_used_activation_links(now=None):
    return await cleanup_order_invite_links(now=now, only_used=True)

