from __future__ import annotations

import logging
import re
from datetime import timedelta

from supabase_store import supabase_store
from support_utils import is_lifetime_plan, is_support_group


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def parse_admin_ids():
    scheduler = _scheduler()
    raw = str(scheduler.db.get_config("ADMIN_IDS", "") or "").strip()
    if not raw:
        return set()
    ids = set()
    for item in re.split(r"[\n,;| ]+", raw):
        token = scheduler.normalize_chat_id(item)
        if token.isdigit():
            ids.add(token)
    return ids


def join_guard_active_orders(orders, now, plan_group_cache=None):
    scheduler = _scheduler()
    active_orders = []
    active_group_ids = set()
    for order in orders or []:
        plan_name = str(order.get("plan_name") or "").strip()
        if not plan_name:
            continue
        if str(order.get("status") or "").upper() != "PAID":
            continue
        if scheduler.is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
            active_orders.append(order)
            active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
            continue
        expire_raw = str(order.get("expire_at") or "").strip()
        expire_date = scheduler.parse_expire_datetime(expire_raw)
        if expire_date and expire_date > now:
            active_orders.append(order)
            active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
        elif expire_raw and not expire_date:
            active_orders.append(order)
            active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
            logging.warning(
                "⚠️ User %s có đơn PAID %s nhưng expire_at không đọc được ('%s'); giữ quyền để tránh kick nhầm.",
                order.get("telegram_user_id") or "",
                order.get("order_id") or "",
                expire_raw,
            )
    return active_orders, active_group_ids


async def evaluate_group_join_access(chat_id, user_id, *, chat_title="", chat_member=None, user_orders=None, now=None, plan_group_cache=None):
    scheduler = _scheduler()
    normalized_chat_id = scheduler.normalize_chat_id(chat_id)
    normalized_user_id = str(user_id or "").strip()
    if not normalized_chat_id or not normalized_user_id:
        return {"action": "review", "allowed": False, "reason": "missing_chat_or_user", "details": {}}

    admin_ids = parse_admin_ids()
    if normalized_user_id in admin_ids:
        return {"action": "allow", "allowed": True, "reason": "admin_allowlist", "details": {}}

    if chat_member is not None and scheduler.member_is_admin_or_owner(chat_member):
        return {"action": "allow", "allowed": True, "reason": "group_admin_or_owner", "details": {}}

    now_value = now or scheduler.now_local()
    if user_orders is None:
        try:
            user_orders = supabase_store.list_paid_orders_for_user(normalized_user_id, limit=200)
        except Exception as exc:
            return {"action": "review", "allowed": False, "reason": "orders_lookup_failed", "details": {"error": str(exc)}}

    active_orders, active_group_ids = join_guard_active_orders(user_orders, now_value, plan_group_cache=plan_group_cache)
    support_gid = scheduler.support_group_id()
    is_support_chat = scheduler.support_group_enabled() and support_gid and normalized_chat_id == support_gid

    if is_support_chat:
        if active_orders:
            return {
                "action": "allow",
                "allowed": True,
                "reason": "active_membership_support",
                "details": {
                    "active_order_ids": [str(order.get("order_id") or "") for order in active_orders],
                    "active_group_ids": sorted(active_group_ids),
                },
            }
        return {"action": "kick", "allowed": False, "reason": "no_active_membership_support", "details": {"active_order_ids": [], "active_group_ids": sorted(active_group_ids)}}

    if normalized_chat_id in active_group_ids:
        return {"action": "allow", "allowed": True, "reason": "active_membership_group", "details": {"active_order_ids": [str(order.get("order_id") or "") for order in active_orders], "active_group_ids": sorted(active_group_ids)}}

    if not active_orders:
        return {"action": "kick", "allowed": False, "reason": "no_active_membership", "details": {"active_order_ids": [], "active_group_ids": sorted(active_group_ids)}}

    return {"action": "kick", "allowed": False, "reason": "group_not_in_active_membership", "details": {"active_order_ids": [str(order.get("order_id") or "") for order in active_orders], "active_group_ids": sorted(active_group_ids)}}


def user_active_group_ids(user_id, current_order_id, users_data, now, plan_group_cache=None):
    scheduler = _scheduler()
    active_groups = set()
    for row in users_data:
        if scheduler.row_value(row, 0) == current_order_id:
            continue
        if scheduler.row_value(row, 1) != str(user_id):
            continue
        if scheduler.row_value(row, 5).upper() != "PAID":
            continue
        other_plan = scheduler.row_value(row, 3)
        other_groups = set(scheduler.cached_plan_group_ids(other_plan, plan_group_cache))
        if not other_groups:
            continue
        if scheduler.is_lifetime_order(other_plan) or is_lifetime_plan(other_plan):
            active_groups.update(other_groups)
            continue
        expire_raw = scheduler.row_value(row, 7)
        expire_date = scheduler.parse_expire_datetime(expire_raw)
        if expire_date and expire_date > now:
            active_groups.update(other_groups)
        elif expire_raw and not expire_date:
            active_groups.update(other_groups)
            logging.warning("⚠️ User %s có đơn PAID %s cùng group nhưng expire_at không đọc được ('%s'); giữ quyền để tránh kick nhầm.", user_id, scheduler.row_value(row, 0), expire_raw)
    return active_groups


def user_has_active_membership(user_id, current_order_id, users_data, now, plan_group_cache=None):
    scheduler = _scheduler()
    for row in users_data:
        if scheduler.row_value(row, 0) == current_order_id:
            continue
        if scheduler.row_value(row, 1) != str(user_id):
            continue
        if scheduler.row_value(row, 5).upper() != "PAID":
            continue
        other_plan = scheduler.row_value(row, 3)
        if scheduler.is_lifetime_order(other_plan) or is_lifetime_plan(other_plan):
            return True
        expire_raw = scheduler.row_value(row, 7)
        expire_date = scheduler.parse_expire_datetime(expire_raw)
        if expire_date and expire_date > now:
            return True
        if expire_raw and not expire_date:
            logging.warning("⚠️ User %s có đơn PAID %s nhưng expire_at không đọc được ('%s'); xem như active để tránh xử lý nhầm support.", user_id, scheduler.row_value(row, 0), expire_raw)
            return True
    return False


def build_users_index(users_data):
    scheduler = _scheduler()
    users_index = {}
    for row in users_data:
        user_id = scheduler.row_value(row, 1)
        if not user_id:
            continue
        users_index.setdefault(user_id, []).append(row)
    return users_index


def build_user_membership_cache(users_index, now, user_ids=None, plan_group_cache=None):
    scheduler = _scheduler()
    cache = {}
    target_user_ids = set(str(user_id) for user_id in user_ids) if user_ids is not None else None
    for user_id, rows in users_index.items():
        if target_user_ids is not None and user_id not in target_user_ids:
            continue
        active_orders = []
        active_group_ids = set()
        support_active = False
        for row in rows:
            order_id = scheduler.row_value(row, 0)
            status = scheduler.row_value(row, 5).upper()
            if status != "PAID":
                continue
            plan_name = scheduler.row_value(row, 3)
            expire_raw = scheduler.row_value(row, 7)
            expired = False
            if scheduler.is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                expired = False
            else:
                expire_date = scheduler.parse_expire_datetime(expire_raw)
                if expire_date and expire_date <= now:
                    expired = True
                elif expire_raw and not expire_date:
                    expired = False
                else:
                    expired = False
            if not expired:
                active_orders.append(order_id)
                if scheduler.is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                    support_active = True
                else:
                    expire_date = scheduler.parse_expire_datetime(expire_raw)
                    if expire_date and expire_date > now:
                        support_active = True
                active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
        if not active_orders:
            support_active = False
        cache[user_id] = {"active_orders": set(active_orders), "active_group_ids": active_group_ids, "has_active_membership": bool(active_orders), "support_active": support_active}
    return cache


def build_user_membership_cache_from_rows(rows_by_user, now, plan_group_cache=None):
    scheduler = _scheduler()
    cache = {}
    for user_id, rows in rows_by_user.items():
        active_orders = []
        active_group_ids = set()
        support_active = False
        for row in rows:
            order_id = scheduler.row_value(row, 0)
            status = scheduler.row_value(row, 5).upper()
            if status != "PAID":
                continue
            plan_name = scheduler.row_value(row, 3)
            expire_raw = scheduler.row_value(row, 7)
            if scheduler.is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
                continue
            expire_date = scheduler.parse_expire_datetime(expire_raw)
            if expire_date and expire_date > now:
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
            elif expire_raw and not expire_date:
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(scheduler.cached_plan_group_ids(plan_name, plan_group_cache))
                logging.warning("⚠️ User %s có đơn PAID %s cùng group nhưng expire_at không đọc được ('%s'); giữ quyền để tránh kick nhầm.", user_id, order_id, expire_raw)
        cache[user_id] = {"active_orders": set(active_orders), "active_group_ids": active_group_ids, "has_active_membership": bool(active_orders), "support_active": support_active}
    return cache

