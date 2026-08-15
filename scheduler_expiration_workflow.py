from __future__ import annotations

import logging
from datetime import timedelta

from bot_instance import bot
from config_utils import config_int
from database import db
from hidden_group_utils import display_plan_name
from license_utils import license_renewal_enabled
from renewal_utils import build_early_renew_block, build_early_renew_offer
from support_utils import record_support_event, support_group_grace_days
from i18n import get_user_language
try:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
except Exception:
    class InlineKeyboardBuilder:  # pragma: no cover - fallback for tests without aiogram
        def __init__(self, *args, **kwargs):
            self._buttons = []

        def row(self, *args, **kwargs):
            return self

        def as_markup(self, *args, **kwargs):
            return {"inline_keyboard": []}

    class InlineKeyboardButton:  # pragma: no cover - fallback for tests without aiogram
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs


def _scheduler():
    import scheduler as _scheduler_module

    return _scheduler_module


def _supabase_store():
    return _scheduler().supabase_store


def config_enabled(key, default="ON"):
    scheduler = _scheduler()
    return scheduler.config_enabled(key, default)


def new_kick_worker_enabled() -> bool:
    """When the new worker owns kicks, the legacy expiration path must not duplicate them."""
    return str(__import__("os").getenv("RENEWAL_KICK_WORKER_ENABLED", "0")).strip().lower() in {"1", "true", "yes", "on"}


async def send_html_message(chat_id, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" not in str(e).lower() and "can't parse entities" not in str(e).lower():
            raise
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=None)


async def process_due_expired_rows(
    users_data,
    expired_rows,
    now,
    today_str,
    *,
    use_supabase,
    run_kick_cache,
    run_presence_cache,
    user_membership_cache,
    plan_group_cache,
):
    scheduler = _scheduler()
    summary = {"expired_notice": 0}
    for offset, row in expired_rows:
        row_number = offset + 2
        order_id = scheduler.row_value(row, 0)
        offer_ref = order_id if use_supabase else row_number
        user_id = str(row[1]).strip()
        plan_name = str(row[3]).strip()
        expire_str = str(row[7]).strip()
        if not expire_str:
            continue
        if not scheduler.is_lifetime_plan(plan_name) and not scheduler.cached_plan_group_ids(plan_name, plan_group_cache):
            logging.error(
                "⏭ Bỏ qua xử lý đơn EXPIRED %s vì plan_name='%s' không map được group VIP; không mute/kick support để tránh xử lý nhầm.",
                offer_ref,
                plan_name,
            )
            continue
        if not new_kick_worker_enabled():
            await scheduler.process_vip_kicks_for_expired_order(
                user_id,
                order_id,
                plan_name,
                expire_str,
                users_data,
                now,
                run_kick_cache=run_kick_cache,
                run_presence_cache=run_presence_cache,
                user_cache=user_membership_cache,
                plan_group_cache=plan_group_cache,
            )
            await scheduler.process_support_grace_for_expired_order(
                user_id,
                order_id,
                plan_name,
                expire_str,
                users_data,
                now,
                run_kick_cache=run_kick_cache,
                run_presence_cache=run_presence_cache,
                user_cache=user_membership_cache,
                plan_group_cache=plan_group_cache,
            )
        else:
            logging.info("⏭ Bỏ qua legacy renewal kick cho order %s; new entitlement worker đang sở hữu luồng kick.", order_id)
        if not scheduler.should_send_expired_notice(row, today_str):
            continue
        expire_date = scheduler.parse_expire_datetime(expire_str)
        if not expire_date:
            continue
        days_grace = support_group_grace_days()
        plan_label = display_plan_name(plan_name, user_id)
        msg_expired = (
            db.get_config("MSG_EXPIRED", "⚠️ Gói <b>{plan}</b> của bạn đã hết hạn vào <b>{date}</b>.\n\nNếu muốn tiếp tục dùng bot, vui lòng gia hạn ngay nhé:")
            .replace("\\n", "\n")
            .replace("{plan}", plan_label)
            .replace("{date}", expire_date.strftime("%d/%m/%Y %H:%M:%S"))
            .replace("{grace_days}", str(days_grace))
        )
        kb = InlineKeyboardBuilder()
        if "FULL" in plan_name.upper() or "SVIP" in plan_name.upper():
            kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Combo"), callback_data="nav:svip_page"))
        else:
            kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_GROUP", "🔄 Gia hạn / Mở rộng gói"), callback_data="nav:main_menu"))
        try:
            await send_html_message(user_id, msg_expired, kb.as_markup())
            record_support_event(
                "expired_notice_sent",
                user_id,
                order_id=order_id,
                plan_name=plan_label,
                raw_data={"expire_at": expire_str, "grace_days": days_grace, "plan_name_raw": plan_name},
            )
            summary["expired_notice"] += 1
            if use_supabase:
                _supabase_store().mark_expired_notice(order_id, now.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                db.users_sheet.update_cell(row_number, 12, now.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as exc:
            logging.error("❌ Lỗi gửi tin báo hết hạn cho %s: %s", user_id, exc)
    return summary


async def process_due_reminder_rows(reminder_rows, now, today_str, *, use_supabase, days_notice, notified_users):
    scheduler = _scheduler()
    summary = {"reminded": 0, "skipped_not_due": 0, "invalid": 0}
    for offset, row in reminder_rows:
        row_number = offset + 2
        order_id = scheduler.row_value(row, 0)
        offer_ref = order_id if use_supabase else row_number
        user_id = str(row[1]).strip()
        plan_name = str(row[3]).strip()
        expire_str = str(row[7]).strip()
        expire_date = scheduler.parse_expire_datetime(expire_str)
        if not expire_date:
            summary["invalid"] += 1
            logging.warning("⚠️ Bỏ qua đơn/dòng %s: không đọc được ngày hết hạn '%s' cho user %s.", offer_ref, expire_str, user_id)
            continue
        if scheduler.is_lifetime_plan(plan_name):
            continue
        days_remaining = (expire_date.date() - now.date()).days
        notif_key = f"{user_id}_{offer_ref}_{today_str}"
        if config_enabled("REMINDER_ENABLED", "ON") and 0 <= days_remaining <= days_notice and notif_key not in notified_users and not scheduler.should_skip_reminder(row, today_str):
            plan_label = display_plan_name(plan_name, user_id)
            msg_reminder = (
                db.get_config("MSG_REMINDER", "⏰ Gói <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa!\n\n👇 Nhấn nút bên dưới để gia hạn ngay nhé:")
                .replace("\\n", "\n")
                .replace("{plan}", plan_label)
                .replace("{days}", str(days_remaining))
                .replace("{date}", expire_date.strftime("%d/%m/%Y %H:%M:%S"))
            )
            renew_currency = "USD" if get_user_language(user_id) == "en" else "VND"
            early_renew_offer = build_early_renew_offer(row, offer_ref, now, currency=renew_currency)
            msg_reminder += build_early_renew_block(early_renew_offer)
            kb = InlineKeyboardBuilder()
            if early_renew_offer:
                callback_data = f"renew_order_{order_id}" if use_supabase else f"renew_{row_number}"
                kb.row(InlineKeyboardButton(text=db.get_config("BTN_EARLY_RENEW", f"🔥 Gia hạn sớm -{early_renew_offer['discount_percent']}%"), callback_data=callback_data))
            elif "FULL" in plan_name.upper() or "SVIP" in plan_name.upper():
                kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Combo"), callback_data="nav:svip_page"))
            else:
                kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_GROUP", "🔄 Gia hạn / Mở rộng gói"), callback_data="nav:main_menu"))
            try:
                await send_html_message(user_id, msg_reminder, kb.as_markup())
                record_support_event("renewal_reminder_sent", user_id, order_id=order_id, plan_name=plan_label, raw_data={"days_remaining": days_remaining, "expire_at": expire_str, "plan_name_raw": plan_name})
                notified_users.add(notif_key)
                summary["reminded"] += 1
                if use_supabase:
                    _supabase_store().mark_reminder_sent(order_id, today_str)
                else:
                    db.users_sheet.update_cell(row_number, 11, today_str)
            except Exception as exc:
                logging.error("❌ Lỗi gửi tin nhắc cho %s: %s", user_id, exc)
        else:
            summary["skipped_not_due"] += 1
    return summary


async def run_expiration_cycle():
    scheduler = _scheduler()
    # Keep the boundary compatible with lightweight scheduler test doubles and
    # older deployments while the legacy scheduler is being sunset.
    if getattr(scheduler, "is_legacy_bot", lambda: False)():
        logging.info("⏭ Scheduler bỏ qua vì BOT_VERSION=legacy, bot cũ chỉ còn chuyển hướng.")
        return
    logging.info("⏳ [SCHEDULER] Đang kiểm tra hạn dùng tới hạn/quá hạn...")
    use_supabase = _supabase_store().enabled
    if not use_supabase and not db.users_sheet:
        db.connect()

    days_notice = config_int("REMINDER_DAYS", 3, minimum=0)
    now = scheduler.now_local()
    today_str = now.strftime("%Y-%m-%d")
    await scheduler.cleanup_used_activation_links(now)

    if use_supabase:
        order_limit = config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100)
        due_before = now + timedelta(days=days_notice)
        try:
            due_orders = _supabase_store().list_scheduler_due_rows(due_before, limit=order_limit)
        except Exception as exc:
            logging.warning("⚠️ Không dùng được query due_rows, fallback quét rộng: %s", exc)
            due_orders = _supabase_store().list_scheduler_orders(limit=order_limit)
        users_data = [_supabase_store().order_to_sheet_row(order) for order in due_orders]
    else:
        users_data = db.users_sheet.get_all_values()[1:]

    logging.info(
        "⏰ Scheduler timezone Asia/Ho_Chi_Minh: %s, nhắc trước %s ngày, xử lý %s đơn/dòng.",
        now.strftime("%Y-%m-%d %H:%M:%S"),
        days_notice,
        len(users_data),
    )
    summary = {"expired": 0, "expired_notice": 0, "reminded": 0, "skipped_not_due": 0, "invalid": 0}
    run_kick_cache = set()
    run_presence_cache = {}
    plan_group_cache = {}
    users_index = scheduler.build_users_index(users_data)
    expired_rows, reminder_rows, expiring_user_ids = scheduler.split_scheduler_rows(users_data, now, days_notice)
    user_membership_cache = {}
    if use_supabase and expiring_user_ids:
        user_rows_by_id = {}
        for user_id in expiring_user_ids:
            try:
                user_rows = _supabase_store().list_paid_orders_for_user(user_id, limit=order_limit)
            except Exception as exc:
                logging.warning("⚠️ Không lấy được paid orders cho user %s để giữ quyền kick: %s", user_id, exc)
                user_rows = []
            combined = list(users_index.get(user_id, []))
            seen_order_ids = {scheduler.row_value(row, 0) for row in combined}
            for order in user_rows:
                order_row = _supabase_store().order_to_sheet_row(order)
                if scheduler.row_value(order_row, 0) not in seen_order_ids:
                    combined.append(order_row)
            user_rows_by_id[user_id] = combined
        user_membership_cache = scheduler.build_user_membership_cache_from_rows(user_rows_by_id, now, plan_group_cache=plan_group_cache)
    elif users_index:
        user_membership_cache = scheduler.build_user_membership_cache(users_index, now, user_ids=expiring_user_ids, plan_group_cache=plan_group_cache)

    summary["expired_notice"] += (await process_due_expired_rows(
        users_data,
        expired_rows,
        now,
        today_str,
        use_supabase=use_supabase,
        run_kick_cache=run_kick_cache,
        run_presence_cache=run_presence_cache,
        user_membership_cache=user_membership_cache,
        plan_group_cache=plan_group_cache,
    ))["expired_notice"]

    kick_queue_v2_summary = await scheduler.kick_workflow.process_due_renewal_kick_group_tasks_v2(
        now,
        run_kick_cache=run_kick_cache,
        run_presence_cache=run_presence_cache,
        user_cache=user_membership_cache,
        plan_group_cache=plan_group_cache,
    )
    kick_finalizer_v2_summary = await scheduler.kick_workflow.process_due_renewal_kick_finalizer_v2(now)

    reminder_summary = await process_due_reminder_rows(reminder_rows, now, today_str, use_supabase=use_supabase, days_notice=days_notice, notified_users=scheduler.notified_users)
    summary.update(reminder_summary)

    if use_supabase and license_renewal_enabled():
        try:
            license_rows = _supabase_store().list_license_records(limit=config_int("SCHEDULER_LICENSE_LIMIT", 1000, minimum=100))
        except Exception as exc:
            logging.warning("⚠️ Không đọc được licenses để nhắc gia hạn: %s", exc)
            license_rows = []
        for row in license_rows:
            license_key = str(row.get("license_key") or "").strip().upper()
            telegram_user_id = str(row.get("telegram_user_id") or "").strip()
            plan_code = str(row.get("plan_code") or "").strip().upper()
            plan = scheduler.license_plan_config(plan_code)
            if not license_key or not telegram_user_id or not plan:
                continue
            if row.get("is_lifetime") or plan.duration_days is None or not plan.allow_renew:
                continue
            raw_data = row.get("raw_data") if isinstance(row.get("raw_data"), dict) else {}
            if str(row.get("status") or "").strip().lower() == "revoked":
                if raw_data.get("revoked_notice_sent_at"):
                    continue
                revoke_text = db.get_config("MSG_LICENSE_REVOKED", "⛔ License <b>{plan}</b> của bạn đã bị thu hồi. Vui lòng liên hệ hỗ trợ nếu cần kiểm tra lại.").replace("\\n", "\n").replace("{plan}", display_plan_name(plan_code, telegram_user_id))
                try:
                    await send_html_message(telegram_user_id, revoke_text)
                except Exception as exc:
                    logging.error("❌ Lỗi gửi revoke notice cho %s: %s", telegram_user_id, exc)
                continue
            expire_date = scheduler.parse_license_expire_datetime(row.get("expires_at"))
            if not expire_date:
                continue
            days_remaining = (expire_date.date() - now.date()).days
            notif_key = f"license_{license_key}_{today_str}"
            if not (0 <= days_remaining <= days_notice) or notif_key in scheduler.notified_users:
                continue
            message_text = db.get_config("MSG_LICENSE_REMINDER", "⏰ License <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa.\n\nVui lòng gia hạn để giữ quyền truy cập không gián đoạn.").replace("\\n", "\n").replace("{plan}", display_plan_name(plan_code, telegram_user_id)).replace("{days}", str(days_remaining)).replace("{date}", expire_date.strftime("%d/%m/%Y %H:%M:%S"))
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text=db.get_config("BTN_LICENSE_RENEW", "🔄 Gia hạn license"), callback_data=f"nav:license_renew:{license_key}"))
            try:
                await send_html_message(telegram_user_id, message_text, kb.as_markup())
                scheduler.notified_users.add(notif_key)
            except Exception as exc:
                logging.error("❌ Lỗi gửi nhắc license cho %s: %s", telegram_user_id, exc)

    logging.info(
        "✅ Scheduler xong: hết hạn=%s, báo hết hạn=%s, nhắc gia hạn=%s, chưa tới hạn=%s, lỗi ngày=%s, queue_v2=%s, finalizer_v2=%s.",
        0,
        summary["expired_notice"],
        summary["reminded"],
        summary["skipped_not_due"],
        summary["invalid"],
        kick_queue_v2_summary,
        kick_finalizer_v2_summary,
    )
