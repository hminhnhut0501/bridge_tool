from __future__ import annotations

from new_core.state import normalize_kick_state, normalize_order_state


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def _supabase_store():
    return _scheduler().supabase_store


async def build_kick_audit_rows(live=False, order_id_filter="", user_id_filter="", chat_id_filter="", updated_after: str | None = None):
    scheduler = _scheduler()
    from scheduler import parse_expire_datetime, plan_group_ids, user_active_group_ids

    db = scheduler.db
    now_local_naive = scheduler.now_local_naive
    normalize_chat_id = scheduler.normalize_chat_id
    member_live_state = scheduler.member_live_state
    warn_missing_table_once = scheduler.warn_missing_table_once
    is_missing_supabase_table_error = scheduler.is_missing_supabase_table_error

    db.reload_config(force=False)
    now = now_local_naive()
    store = _supabase_store()
    try:
        orders = store.list_scheduler_orders(limit=5000, updated_after=updated_after)
    except TypeError:
        orders = store.list_scheduler_orders(limit=5000)
    users_data = [store.order_to_sheet_row(order) for order in orders]
    try:
        renewal_kick_tasks_v2_fn = getattr(store, "list_renewal_kick_tasks_v2", None)
        renewal_kick_tasks_v2 = renewal_kick_tasks_v2_fn(limit=5000) if callable(renewal_kick_tasks_v2_fn) else []
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_tasks_v2"):
            warn_missing_table_once("renewal_kick_tasks_v2", exc)
            renewal_kick_tasks_v2 = []
        else:
            raise
    try:
        renewal_kick_group_tasks_v2 = store._request(
            "GET",
            "renewal_kick_group_tasks_v2",
            params={"select": "*", "order": "updated_at.desc", "limit": "5000"},
        )
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_group_tasks_v2"):
            warn_missing_table_once("renewal_kick_group_tasks_v2", exc)
            renewal_kick_group_tasks_v2 = []
        else:
            raise
    renewal_kick_v2_by_order = {str(task.get("order_id") or ""): task for task in renewal_kick_tasks_v2 if str(task.get("order_id") or "")}
    renewal_kick_v2_groups_by_order = {}
    for group_task in renewal_kick_group_tasks_v2:
        order_key = str(group_task.get("order_id") or "")
        if order_key:
            renewal_kick_v2_groups_by_order.setdefault(order_key, []).append(group_task)

    rows = []
    for order in orders:
        order_id = str(order.get("order_id") or "")
        user_id = str(order.get("telegram_user_id") or "")
        if order_id_filter and order_id != str(order_id_filter):
            continue
        if user_id_filter and user_id != str(user_id_filter):
            continue

        plan_name = str(order.get("plan_name") or "")
        display_name = str(order.get("full_name") or "").strip() or user_id or order_id or "-"
        raw_expire_at = order.get("expire_at")
        expire_at = parse_expire_datetime(raw_expire_at)
        normalized_order = normalize_order_state(order, now, parser=parse_expire_datetime)
        if raw_expire_at and not expire_at:
            rows.append({
                "audit_id": f"{order_id}:INVALID_EXPIRE_AT",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": raw_expire_at,
                "group_id": "",
                "group_name": "Chưa kiểm tra được",
                "status": "INVALID_EXPIRE_AT",
                "status_label": "Lỗi ngày hết hạn",
                "needs_action": True,
                "latest_kick_at": "",
                "latest_error": f"Không đọc được expire_at: {raw_expire_at}",
                "live_checked": False,
                "live_status": "",
                "live_present": None,
            })
            continue
        if normalized_order.state != "expired":
            continue

        current_group_ids = [normalize_chat_id(item) for item in plan_group_ids(plan_name)]
        active_group_ids = {normalize_chat_id(item) for item in user_active_group_ids(user_id, order_id, users_data, now)}
        if not current_group_ids:
            rows.append({
                "audit_id": f"{order_id}:NO_GROUP",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": order.get("expire_at"),
                "group_id": "",
                "group_name": "Không map được group",
                "status": "NO_GROUP",
                "status_label": "Không map được group",
                "needs_action": True,
                "latest_kick_at": "",
                "latest_error": "Tên gói không khớp BTN_G/ID_G.",
                "live_checked": False,
                "live_status": "",
                "live_present": None,
            })
            continue

        for gid in current_group_ids:
            if chat_id_filter and normalize_chat_id(chat_id_filter) != gid:
                continue
            retained = gid in active_group_ids
            v2_task = renewal_kick_v2_by_order.get(order_id)
            v2_group = next((item for item in renewal_kick_v2_groups_by_order.get(order_id, []) if str(item.get("group_id") or "") == gid), None)
            v2_task_state = str((v2_task or {}).get("task_state") or "").strip().lower()
            v2_group_state = str((v2_group or {}).get("group_state") or "").strip().lower()
            latest_kick = bool(v2_task_state in {"done", "partial_done"} or v2_group_state in {"kicked", "retained"})
            latest_kick_state = normalize_kick_state(
                renewal_task=v2_task,
                group_task=v2_group,
                support_event_state="done" if latest_kick else "none",
            )
            live_state = {"checked": False, "present": None, "status": "", "error": ""}
            should_live_check = live and latest_kick_state not in {"done", "kicked"} and (retained or not latest_kick or latest_kick_state in {"processing", "pending_confirm", "retry_pending", "waiting_confirm", "retry_scheduled"})
            if should_live_check:
                live_state = await member_live_state(gid, user_id)
            status = (
                "ACTIVE_RETAINED"
                if retained
                else "DONE"
                if latest_kick_state == "done"
                else "ERROR"
                if latest_kick_state == "failed_terminal"
                else "PROCESSING"
                if latest_kick_state == "processing"
                else "PENDING_CONFIRM"
                if latest_kick_state == "waiting_confirm"
                else "BLOCKED"
                if latest_kick_state == "blocked"
                else "REVIEW_REQUIRED"
                if latest_kick_state == "review_required"
                else "UNKNOWN"
            )
            status_label = (
                "Còn quyền active"
                if retained
                else "Đã kick xong"
                if latest_kick_state == "done"
                else "Lỗi kick"
                if latest_kick_state == "failed_terminal"
                else "Đang kick"
                if latest_kick_state == "processing"
                else "Đang chờ Telegram xác nhận"
                if latest_kick_state == "waiting_confirm"
                else "Bị giữ bởi đơn active khác"
                if latest_kick_state == "blocked"
                else "Cần review"
                if latest_kick_state == "review_required"
                else "Chưa rõ"
            )
            needs_action = not retained and latest_kick_state not in {"done", "failed_terminal"} and not latest_kick
            if latest_kick_state in {"processing", "waiting_confirm", "blocked", "review_required"}:
                needs_action = True
            if latest_kick_state == "done":
                needs_action = False
            if live_state["checked"]:
                if live_state["error"]:
                    status = "CHECK_ERROR"
                    status_label = "Lỗi kiểm tra live"
                    needs_action = True
                elif not retained and latest_kick and live_state["present"]:
                    status = "REJOINED"
                    status_label = "Đã join lại / cần kick lại"
                    needs_action = True
                elif not retained and not latest_kick and live_state["present"] is False:
                    status = "NEED_KICK"
                    status_label = "Cần kick"
                    needs_action = True
            rows.append({
                "audit_id": f"{order_id}:{gid}",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": order.get("expire_at"),
                "group_id": gid,
                "group_name": gid,
                "status": status,
                "status_label": status_label,
                "needs_action": needs_action,
                "latest_kick_at": str((v2_task or {}).get("updated_at") or (v2_task or {}).get("last_transition_at") or ""),
                "latest_error": str((v2_task or {}).get("last_error") or (v2_task or {}).get("review_reason") or ""),
                "live_checked": live_state["checked"],
                "live_status": live_state["status"] or "",
                "live_present": live_state["present"],
            })
    rows.sort(key=lambda row: (not row["needs_action"], row["status"], row["customer_name"], row["telegram_user_id"]))
    return {"summary": {"total": len(rows), "needs_action": sum(1 for row in rows if row["needs_action"])}, "rows": rows}
