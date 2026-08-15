import asyncio
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database import db
from bot_instance import bot
try:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
except Exception:
    class InlineKeyboardBuilder:  # pragma: no cover - test fallback
        def __init__(self, *args, **kwargs):
            self._buttons = []

        def button(self, *args, **kwargs):
            self._buttons.append((args, kwargs))
            return self

        def row(self, *args, **kwargs):
            if args:
                self._buttons.append(("row", args, kwargs))
            return self

        def adjust(self, *args, **kwargs):
            return self

        def as_markup(self, *args, **kwargs):
            return {"inline_keyboard": []}

    class InlineKeyboardButton:  # pragma: no cover - test fallback
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
from config_utils import config_int, group_numbers
try:
    from hidden_group_utils import display_plan_name, is_lifetime_order, resolve_plan_groups
except ImportError:  # pragma: no cover - fallback for lightweight test stubs
    from hidden_group_utils import is_lifetime_order, resolve_plan_groups

    def display_plan_name(plan_name, user_id=None, language=None):
        return plan_name
from i18n import get_user_language
from renewal_utils import build_early_renew_block, build_early_renew_offer
from order_expiry_service import (
    days_until_order_expire as service_days_until_order_expire,
    order_is_active as service_order_is_active,
    order_is_expired as service_order_is_expired,
    reconcile_expired_paid_orders as service_reconcile_expired_paid_orders,
)
from kick_state_service import (
    is_kick_finalized,
    renewal_kick_state_v2,
)
import scheduler_kick_workflow as kick_workflow
import scheduler_cleanup_workflow as cleanup_workflow
import scheduler_expiration_workflow as expiration_workflow
import scheduler_membership_utils as membership_utils
import scheduler_state_utils as state_utils
from supabase_store import supabase_store
from support_utils import is_lifetime_plan, is_support_group, mute_member, record_support_event, revoke_support_invite_link, support_group_enabled, support_group_grace_days, support_group_id, support_group_mute_enabled, unmute_member
from bot_links import is_legacy_bot
from license_utils import license_renewal_enabled, load_license_plan_mapping
from new_core.observability import structured_cycle_log

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm để tránh 1 ngày Bot gửi 2 lần tin nhắc cho cùng 1 người
notified_users = set()
recent_kicks = {}
# Quét hạn dùng theo nhịp thưa hơn để giảm tải.
# Vẫn có thể đẩy thủ công từ admin nếu cần xử lý ngay.
SCHEDULER_DEFAULT_INTERVAL_SECONDS = 8 * 60 * 60
SCHEDULER_MIN_INTERVAL_SECONDS = 60
RENEWAL_WORKER_DEFAULT_INTERVAL_SECONDS = 15 * 60
RENEWAL_WORKER_MIN_INTERVAL_SECONDS = 60
RENEWAL_WORKER_DEFAULT_WINDOWS = "00:00,06:00,12:00,18:00"
RENEWAL_WORKER_WINDOW_MINUTES = 15
KICK_CONFIRMATION_DELAY_SECONDS = 30
KICK_MAX_ATTEMPTS = 3
KICK_CONFIRM_MAX_ATTEMPTS = 3
RENEWAL_KICK_V2_LOCK_MINUTES = 5
RENEWAL_KICK_V2_STALE_QUEUE_MINUTES = 10
RENEWAL_KICK_V2_STALE_CONFIRM_MINUTES = 15
ORDER_EXPIRED_RECONCILE_INTERVAL_SECONDS = 30 * 60
ORDER_EXPIRED_RECONCILE_MIN_INTERVAL_SECONDS = 60

RENEWAL_KICK_TASK_STATES = {
    "queued",
    "running",
    "waiting_confirm",
    "retry_scheduled",
    "partial_done",
    "done",
    "blocked",
    "review_required",
    "failed_terminal",
    "migrated_legacy",
    "blocked_active_order",
    "retry_pending",
    "pending_confirm",
    "processing",
    "error_retryable",
}
RENEWAL_KICK_GROUP_STATES = {
    "pending",
    "selected",
    "processing",
    "waiting_confirm",
    "kicked",
    "retained",
    "blocked_active_order",
    "unmapped",
    "retry_scheduled",
    "review_required",
    "failed_terminal",
}
RENEWAL_KICK_ATTEMPT_STATES = {
    "planned",
    "claimed",
    "kick_sent",
    "confirm_passed",
    "confirm_failed",
    "retry_scheduled",
    "review_required",
    "aborted",
    "failed_exception",
}
RENEWAL_KICK_REASON_CODES = {
    "kick_sent",
    "kick_confirmed",
    "confirm_pending",
    "confirm_unknown",
    "confirm_timeout",
    "retry_limit_reached",
    "group_unmapped",
    "active_order_retained",
    "bot_api_error",
    "telegram_rate_limited",
    "telegram_forbidden",
    "user_not_found",
    "chat_not_found",
    "manual_kick_detected",
    "already_kicked",
    "already_review_required",
    "legacy_ambiguous_state",
}

def normalize_renewal_kick_state(value):
    return state_utils.normalize_renewal_kick_state(value)

def normalize_renewal_kick_reason(value):
    return state_utils.normalize_renewal_kick_reason(value)

def now_local():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime.now(timezone).replace(tzinfo=None)

def config_enabled(key, default="ON"):
    # Deployment flags must be controllable without a database write. Keep
    # normal bot configuration database-backed, but let renewal cutover flags
    # be overridden by the process environment for safe canary rollout.
    env_value = os.getenv(key) if key.startswith("RENEWAL_NEW_CORE_") else None
    value = env_value if env_value not in (None, "") else db.get_config(key, default)
    return str(value or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ", "BẬT", "BAT"}

def parse_int_config(key, default=0, minimum=0):
    try:
        return max(minimum, int(float(str(db.get_config(key, default) or default).strip())))
    except (TypeError, ValueError):
        return max(minimum, int(default))

def parse_time_list_config(raw):
    values = []
    for item in re.split(r"[\n,;| ]+", str(raw or "").strip()):
        token = item.strip()
        if not token:
            continue
        try:
            values.append(datetime.strptime(token, "%H:%M").time())
        except ValueError:
            continue
    return values

def renewal_worker_allowed_now(now=None):
    local_now = now or now_local()
    scheduled_times = parse_time_list_config(
        db.get_config("RENEWAL_WORKER_ACTIVE_TIMES", RENEWAL_WORKER_DEFAULT_WINDOWS) or RENEWAL_WORKER_DEFAULT_WINDOWS
    )
    if not scheduled_times:
        scheduled_times = parse_time_list_config(RENEWAL_WORKER_DEFAULT_WINDOWS)
    window_minutes = parse_int_config("RENEWAL_WORKER_WINDOW_MINUTES", RENEWAL_WORKER_WINDOW_MINUTES, minimum=1)
    current_time = local_now.time().replace(second=0, microsecond=0)
    for scheduled_time in scheduled_times:
        start_dt = datetime.combine(local_now.date(), scheduled_time)
        end_dt = start_dt + timedelta(minutes=window_minutes)
        if start_dt <= local_now < end_dt:
            return True
    return False


def license_plan_config(plan_code):
    mapping = load_license_plan_mapping(db)
    return mapping.get(str(plan_code or "").strip().upper())

def parse_expire_datetime(value):
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    return state_utils.parse_expire_datetime(value, timezone_name=timezone_name)

def normalize_chat_id(value):
    raw = str(value or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def parse_license_expire_datetime(value):
    return parse_expire_datetime(value)

def parse_admin_ids():
    raw = str(db.get_config("ADMIN_IDS", "") or "").strip()
    if not raw:
        return set()
    ids = set()
    for item in re.split(r"[\n,;| ]+", raw):
        token = normalize_chat_id(item)
        if token.isdigit():
            ids.add(token)
    return ids

def join_guard_active_orders(orders, now, plan_group_cache=None):
    return membership_utils.join_guard_active_orders(orders, now, plan_group_cache=plan_group_cache)

async def evaluate_group_join_access(chat_id, user_id, *, chat_title="", chat_member=None, user_orders=None, now=None, plan_group_cache=None):
    return await membership_utils.evaluate_group_join_access(chat_id, user_id, chat_title=chat_title, chat_member=chat_member, user_orders=user_orders, now=now, plan_group_cache=plan_group_cache)

def row_value(row, index, default=""):
    if len(row) <= index or row[index] is None:
        return default
    return str(row[index]).strip()

def member_status_value(member):
    raw_status = getattr(member, "status", "")
    return str(getattr(raw_status, "value", raw_status)).lower()

async def get_chat_member_safe(chat_id, user_id):
    try:
        return await bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
    except Exception as exc:
        text = str(exc).lower()
        if "user not found" in text or "participant_id_invalid" in text or "chat not found" in text:
            logging.info(
                "ℹ️ Telegram không tra được member user %s trong group %s: %s",
                user_id,
                chat_id,
                exc,
            )
            return None
        logging.warning(
            "⚠️ Telegram lỗi khi kiểm tra member user %s trong group %s; trả unknown để scheduler retry: %s",
            user_id,
            chat_id,
            exc,
        )
        return "unknown"

def member_is_admin_or_owner(member):
    if member in (None, "unknown"):
        return False
    status = member_status_value(member)
    return status in {"creator", "administrator", "owner"}

def record_admin_action_skipped(event_type, user_id, chat_id, order_id, plan_name, reason, raw_data=None):
    payload = {"reason": reason, "protected_status": "admin_or_owner"}
    payload.update(raw_data or {})
    record_support_event(event_type, user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_name, raw_data=payload)

def should_skip_reminder(row, today_str):
    last_reminder_date = row_value(row, 10)
    return last_reminder_date == today_str

def should_skip_expired_notice(row):
    return bool(row_value(row, 11))


def should_send_expired_notice(row, today_str):
    if not config_enabled("EXPIRED_NOTICE_ENABLED", "ON"):
        return False
    if should_skip_expired_notice(row):
        return False
    expire_str = row_value(row, 7)
    expire_date = parse_expire_datetime(expire_str)
    if not expire_date:
        return False
    return expire_date.date() < datetime.strptime(today_str, "%Y-%m-%d").date()

def parse_event_datetime(event):
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    return state_utils.parse_event_datetime(event, timezone_name=timezone_name)

def event_happened_after(candidate, reference):
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    return state_utils.event_happened_after(candidate, reference, timezone_name=timezone_name)

def event_happened_within(event, now, minutes):
    event_at = parse_event_datetime(event)
    return bool(event_at and now - event_at < timedelta(minutes=minutes))

def normalize_match_text(value):
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()

def significant_group_tokens(value):
    ignored = {
        "vip", "svip", "full", "goi", "nhom", "group", "ngay", "thang",
        "tron", "doi", "prive", "plus", "premium", "signature",
    }
    return [token for token in normalize_match_text(value).split() if token and token not in ignored and not token.isdigit()]

def group_alias_tokens(group_no):
    raw = str(db.get_config(f"BTN_G{group_no}_ALIASES", "") or "")
    return [normalize_match_text(item) for item in re.split(r"[\n,;|]+", raw) if normalize_match_text(item)]

def group_matches_plan(group_no, plan_name):
    btn_name = db.get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")
    plan_upper = str(plan_name or "").upper()
    if "FULL" in plan_upper or "SVIP" in plan_upper:
        return True
    if f"G{group_no}" in plan_upper:
        return True

    plan_text = normalize_match_text(plan_name)
    btn_text = normalize_match_text(btn_name)
    if btn_text and (btn_text in plan_text or plan_text in btn_text):
        return True
    alias_tokens = group_alias_tokens(group_no)
    if any(alias and (alias in plan_text or plan_text in alias) for alias in alias_tokens):
        return True

    plan_tokens = set(significant_group_tokens(plan_name))
    btn_tokens = set(significant_group_tokens(btn_name))
    return bool(btn_tokens and btn_tokens.issubset(plan_tokens)) or bool(plan_tokens and plan_tokens.issubset(btn_tokens))

def plan_group_ids(plan_name):
    groups = []
    for gid, _group_name in resolve_plan_groups(plan_name):
        normalized = normalize_chat_id(gid)
        if normalized and not is_support_group(normalized):
            groups.append(normalized)
    return groups

def cached_plan_group_ids(plan_name, plan_group_cache=None):
    key = str(plan_name or "").strip()
    if plan_group_cache is None:
        return plan_group_ids(plan_name)
    if key not in plan_group_cache:
        plan_group_cache[key] = tuple(plan_group_ids(plan_name))
    return plan_group_cache[key]

def user_active_group_ids(user_id, current_order_id, users_data, now, plan_group_cache=None):
    return membership_utils.user_active_group_ids(user_id, current_order_id, users_data, now, plan_group_cache=plan_group_cache)

def user_has_active_membership(user_id, current_order_id, users_data, now, plan_group_cache=None):
    return membership_utils.user_has_active_membership(user_id, current_order_id, users_data, now, plan_group_cache=plan_group_cache)

def build_users_index(users_data):
    return membership_utils.build_users_index(users_data)

def build_user_membership_cache(users_index, now, user_ids=None, plan_group_cache=None):
    return membership_utils.build_user_membership_cache(users_index, now, user_ids=user_ids, plan_group_cache=plan_group_cache)

def build_user_membership_cache_from_rows(rows_by_user, now, plan_group_cache=None):
    return membership_utils.build_user_membership_cache_from_rows(rows_by_user, now, plan_group_cache=plan_group_cache)

def split_scheduler_rows(rows, now, days_notice):
    expired_rows = []
    reminder_rows = []
    expiring_user_ids = set()
    for offset, row in enumerate(rows, start=0):
        if len(row) < 8:
            continue
        status = str(row[5]).strip().upper()
        if status not in {"EXPIRED", "PAID"}:
            continue
        user_id = str(row[1]).strip()
        expire_str = str(row[7]).strip()
        if not user_id or not expire_str:
            continue
        if status == "EXPIRED":
            expired_rows.append((offset, row))
            expiring_user_ids.add(user_id)
            continue
        plan_name = str(row[3]).strip()
        if is_lifetime_plan(plan_name):
            continue
        expire_date = parse_expire_datetime(expire_str)
        if not expire_date:
            continue
        days_remaining = (expire_date.date() - now.date()).days
        if days_remaining < 0:
            expired_rows.append((offset, row))
            expiring_user_ids.add(user_id)
            continue
        if 0 <= days_remaining <= days_notice:
            reminder_rows.append((offset, row))
            expiring_user_ids.add(user_id)
    return expired_rows, reminder_rows, expiring_user_ids

def reconcile_expired_paid_orders(rows, now, *, limit=5000):
    return service_reconcile_expired_paid_orders(
        rows,
        now,
        parser=parse_expire_datetime,
        mark_expired=supabase_store.mark_order_expired,
        limit=limit,
    )

def task_state_value(task):
    return state_utils.task_state_value(task)

def group_task_state_value(task):
    return state_utils.group_task_state_value(task)

def attempt_state_value(task):
    state = (task or {}).get("attempt_state")
    return normalize_renewal_kick_state(state)

def renewal_kick_group_key(order_id, user_id, group_id):
    return state_utils.renewal_kick_group_key(order_id, user_id, group_id)

def renewal_kick_state_reason(task):
    raw = (task or {}).get("metadata") or {}
    reason = raw.get("reason") or (task or {}).get("last_reason") or (task or {}).get("last_error") or ""
    return normalize_renewal_kick_reason(reason)

def renewal_kick_v2_lock_expired(task, now, *, lock_minutes=RENEWAL_KICK_V2_LOCK_MINUTES):
    return state_utils.renewal_kick_v2_lock_expired(task, now, lock_minutes=lock_minutes)

def renewal_kick_v2_task_age_minutes(task, now):
    return state_utils.renewal_kick_v2_task_age_minutes(task, now)

def summarize_renewal_kick_groups_v2(group_tasks):
    done = [item for item in group_tasks if group_task_state_value(item) == "done"]
    retained = [item for item in group_tasks if group_task_state_value(item) == "retained"]
    blocked = [item for item in group_tasks if group_task_state_value(item) == "blocked"]
    review = [item for item in group_tasks if group_task_state_value(item) == "review_required"]
    pending = [item for item in group_tasks if group_task_state_value(item) in {"pending", "selected", "processing", "waiting_confirm", "retry_scheduled"}]
    failed = [item for item in group_tasks if group_task_state_value(item) == "failed_terminal"]
    return {
        "total": len(group_tasks),
        "done": len(done),
        "kicked": len(done),
        "retained": len(retained),
        "blocked": len(blocked),
        "review": len(review),
        "pending": len(pending),
        "failed": len(failed),
    }

def finalize_renewal_kick_task_v2_from_groups(task, group_tasks, now):
    summary = summarize_renewal_kick_groups_v2(group_tasks)
    active = summary["pending"]
    if summary["review"] > 0:
        next_state = "review_required"
        terminal_reason = "group_review_required"
    elif summary["failed"] > 0 and summary["done"] == 0 and active == 0:
        next_state = "failed_terminal"
        terminal_reason = "group_failed_terminal"
    elif summary["blocked"] > 0 and summary["done"] == 0 and active == 0:
        next_state = "blocked"
        terminal_reason = "blocked_active_order"
    elif active > 0:
        next_state = "partial_done" if summary["done"] > 0 else "running"
        terminal_reason = ""
    elif summary["done"] > 0 and summary["pending"] == 0:
        if summary["retained"] > 0 or summary["blocked"] > 0:
            next_state = "partial_done"
            terminal_reason = "partial_completion"
        else:
            next_state = "done"
            terminal_reason = "all_groups_kicked"
    elif summary["retained"] > 0 and summary["done"] == 0 and summary["blocked"] == 0:
        next_state = "done"
        terminal_reason = "retained_only"
    else:
        next_state = "review_required"
        terminal_reason = "ambiguous_terminal_state"
    payload = {
        "task_state": next_state,
        "total_groups": summary["total"],
        "kicked_groups": summary["kicked"],
        "retained_groups": summary["retained"],
        "pending_groups": summary["pending"],
        "error_groups": summary["failed"] + summary["blocked"],
        "review_groups": summary["review"],
        "last_transition_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": now.strftime("%Y-%m-%d %H:%M:%S") if next_state in {"done", "blocked", "review_required", "failed_terminal"} else None,
        "completed_at": now.strftime("%Y-%m-%d %H:%M:%S") if next_state == "done" else None,
        "last_reason": terminal_reason,
        "terminal_reason": terminal_reason,
        "review_reason": terminal_reason if next_state == "review_required" else "",
        "metadata": {
            **(task.get("metadata") or {}),
            "reconciled_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "reconciled_source": "finalizer_v2",
        },
    }
    return next_state, payload

async def send_html_message(chat_id, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" not in str(e).lower() and "can't parse entities" not in str(e).lower():
            raise
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=None)

async def ensure_support_group_muted(user_id, order_id, plan_name, expire_str):
    gid = support_group_id()
    if not (support_group_enabled() and support_group_mute_enabled() and gid):
        return False
    plan_label = display_plan_name(plan_name, user_id)
    mute_state, mute_event = renewal_kick_state_v2(user_id, order_id, gid)
    if mute_state in {"done", "processing", "review_required", "blocked"}:
        return True
    kick_state, kick_event = renewal_kick_state_v2(user_id, order_id, gid)
    if kick_state in {"done", "processing", "review_required", "blocked"}:
        return True
    member = await get_chat_member_safe(gid, user_id)
    if member_is_admin_or_owner(member):
        record_admin_action_skipped(
            "member_mute_skipped_admin",
            user_id,
            gid,
            order_id,
            plan_label,
            "support_admin_protected",
            raw_data={"expire_at": expire_str, "grace_days": support_group_grace_days(), "plan_name_raw": plan_name},
        )
        logging.info("🛡 Bỏ qua mute User %s trong group hỗ trợ %s vì là admin/owner.", user_id, gid)
        return True
    try:
        await mute_member(gid, user_id)
        payload = {
            "reason": "support_grace_started",
            "expire_at": expire_str,
            "grace_days": support_group_grace_days(),
            "plan_name_raw": plan_name,
            "mute_state": "done",
        }
        record_support_event(
            "member_muted",
            user_id,
            chat_id=gid,
            order_id=order_id,
            plan_name=plan_label,
            raw_data=payload,
        )
        logging.info("🔇 Đã mute User %s trong group hỗ trợ %s sau khi hết hạn.", user_id, gid)
        return True
    except Exception as exc:
        logging.error("❌ Lỗi mute User %s trong group hỗ trợ %s: %s", user_id, gid, exc)
        return False

async def ensure_support_group_unmuted(user_id, order_id, plan_name):
    gid = support_group_id()
    if not (support_group_enabled() and gid):
        return
    plan_label = display_plan_name(plan_name, user_id)
    mute_state, muted_event = renewal_kick_state_v2(user_id, order_id, gid)
    if mute_state == "none" and not muted_event:
        return
    try:
        await unmute_member(gid, user_id)
        record_support_event(
            "member_unmuted",
            user_id,
            chat_id=gid,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={"reason": "active_membership", "plan_name_raw": plan_name, "mute_state": "done"},
        )
        logging.info("🔊 User %s đang có gói active, đã mở mute trong group hỗ trợ %s.", user_id, gid)
    except Exception as exc:
        logging.warning("⚠️ Không thể mở mute User %s trong group hỗ trợ %s: %s", user_id, gid, exc)

async def member_is_present(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
        status = member_status_value(member)
        if status in {"left", "kicked", "banned"}:
            return False
        if hasattr(member, "is_member") and member.is_member is False:
            return False
        return True
    except Exception as exc:
        text = str(exc).lower()
        if "user not found" in text or "participant_id_invalid" in text or "chat not found" in text:
            return False
        logging.warning("⚠️ Không kiểm tra được trạng thái user %s trong group %s: %s", user_id, chat_id, exc)
        return True

async def ensure_member_kicked(
    chat_id,
    user_id,
    order_id,
    plan_name,
    reason,
    raw_data=None,
    run_kick_cache=None,
    run_presence_cache=None,
):
    now = now_local()
    normalized_chat_id = normalize_chat_id(chat_id)
    kick_key = (normalized_chat_id, str(user_id))
    run_kick_key = (normalized_chat_id, str(user_id))
    cooldown_minutes = config_int("KICK_RECHECK_COOLDOWN_MINUTES", 1440, minimum=1)
    if run_kick_cache is not None and run_kick_key in run_kick_cache:
        logging.info(
            "⏭ Bỏ qua kick trùng trong cùng vòng chạy User %s group %s.",
            user_id,
            chat_id,
        )
        return True
    kick_state, kick_event = renewal_kick_state_v2(user_id, order_id, normalized_chat_id)
    if kick_state == "done":
        logging.info(
            "⏭ Bỏ qua kick User %s group %s đơn %s vì đã có trạng thái done.",
            user_id,
            chat_id,
            order_id,
        )
        return True
    if kick_state == "error":
        logging.info(
            "⏭ Bỏ qua kick User %s group %s đơn %s vì đã có trạng thái error.",
            user_id,
            chat_id,
            order_id,
        )
        return False
    recent_at = recent_kicks.get(kick_key)
    if recent_at and now - recent_at < timedelta(minutes=cooldown_minutes):
        logging.info(
            "⏭ Bỏ qua kick trùng User %s group %s; lần kick gần nhất trong RAM lúc %s.",
            user_id,
            chat_id,
            recent_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return True

    queue_state, queue_event = renewal_kick_state_v2(user_id, order_id, normalized_chat_id)
    if queue_state == "done":
        logging.info(
            "⏭ Bỏ qua kick User %s group %s đơn %s vì task đã done.",
            user_id,
            chat_id,
            order_id,
        )
        return True
    if queue_state in {"processing", "review_required", "blocked"}:
        logging.info(
            "⏭ Bỏ qua kick User %s group %s đơn %s vì task đang processing từ %s.",
            user_id,
            chat_id,
            order_id,
            (queue_event or {}).get("created_at") or "",
        )
        return True

    if run_presence_cache is not None and kick_key in run_presence_cache:
        member = run_presence_cache[kick_key]
    else:
        member = await get_chat_member_safe(chat_id, user_id)
        if run_presence_cache is not None:
            run_presence_cache[kick_key] = member
    if member is None:
        logging.info(
            "ℹ️ Không tra được member user %s trong group %s, tạm coi như không còn trong group để tránh kick mù.",
            user_id,
            chat_id,
        )
        if run_presence_cache is not None:
            run_presence_cache[kick_key] = False
        return True
    if member_is_admin_or_owner(member):
        recent_kicks[kick_key] = now
        record_admin_action_skipped(
            "member_kick_skipped_admin",
            user_id,
            chat_id,
            order_id,
            plan_name,
            reason,
            raw_data=raw_data,
        )
        logging.info("🛡 Bỏ qua kick User %s khỏi group %s vì là admin/owner.", user_id, chat_id)
        return True

    try:
        plan_label = display_plan_name(plan_name, user_id)
        queue_raw = {
            "reason": reason,
            "phase": "kick_queue",
            "expire_at": raw_data.get("expire_at") if isinstance(raw_data, dict) else None,
            "plan_name_raw": plan_name,
        }
        record_support_event(
            "renewal_kick_processing",
            user_id,
            chat_id=chat_id,
            order_id=order_id,
            plan_name=plan_label,
            raw_data=queue_raw,
        )
        await bot.ban_chat_member(chat_id=chat_id, user_id=int(user_id))
        await bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
        logging.info(
            "✅ Đã gửi lệnh kick user %s khỏi group %s cho đơn %s (%s).",
            user_id,
            chat_id,
            order_id,
            plan_label,
        )
        recent_kicks[kick_key] = now
        if run_kick_cache is not None:
            run_kick_cache.add(run_kick_key)
        payload = {"reason": reason}
        payload.update(raw_data or {})
        payload["kick_state"] = "pending"
        payload["plan_name_raw"] = plan_name
        record_support_event("member_kicked", user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_label, raw_data=payload)
        record_support_event(
            "member_kick_closed",
            user_id,
            chat_id=chat_id,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={
                "reason": reason,
                "source": "kick_finalized",
                "closed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "kick_state": "done",
                "plan_name_raw": plan_name,
                **(raw_data or {}),
            },
        )
        record_support_event(
            "renewal_kick_confirmed",
            user_id,
            chat_id=chat_id,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={
                "reason": reason,
                "phase": "kick_confirmed",
                "plan_name_raw": plan_name,
                "confirmed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        logging.info("🚪 Đã kick User %s khỏi group %s vì %s.", user_id, chat_id, reason)
        return True
    except Exception as exc:
        logging.exception(
            "❌ Kick user %s khỏi group %s thất bại cho đơn %s (%s), reason=%s, raw=%s: %s",
            user_id,
            chat_id,
            order_id,
            display_plan_name(plan_name, user_id),
            reason,
            raw_data or {},
            exc,
        )
        payload = {"reason": reason, "error": str(exc)}
        payload.update(raw_data or {})
        plan_label = display_plan_name(plan_name, user_id)
        payload["plan_name_raw"] = plan_name
        record_support_event("member_kick_failed", user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_label, raw_data={**payload, "kick_state": "error"})
        record_support_event(
            "renewal_kick_failed",
            user_id,
            chat_id=chat_id,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={
                "reason": reason,
                "phase": "kick_failed",
                "error": str(exc),
                "plan_name_raw": plan_name,
            },
        )
        if run_kick_cache is not None:
            run_kick_cache.add(run_kick_key)
        return False

async def process_vip_kicks_for_expired_order(
    user_id,
    order_id,
    plan_name,
    expire_str,
    users_data,
    now,
    run_kick_cache=None,
    run_presence_cache=None,
    user_cache=None,
    plan_group_cache=None,
):
    current_group_ids = cached_plan_group_ids(plan_name, plan_group_cache)
    if not current_group_ids:
        logging.warning(
            "⚠️ Đơn %s user %s đã hết hạn (%s) nhưng không map được group VIP từ plan_name='%s'. "
            "Kiểm tra BTN_G/ID_G hoặc tên gói coupon; scheduler sẽ retry ở vòng sau.",
            order_id,
            user_id,
            expire_str,
            plan_name,
        )
        return [], []

    if user_cache and user_id in user_cache:
        active_group_ids = set(user_cache[user_id].get("active_group_ids") or set()) & set(current_group_ids)
    else:
        active_group_ids = user_active_group_ids(user_id, order_id, users_data, now, plan_group_cache=plan_group_cache)
    retained_group_ids = [gid for gid in current_group_ids if gid in active_group_ids]
    expired_group_ids = [gid for gid in current_group_ids if gid not in active_group_ids]

    if retained_group_ids:
        logging.info(
            "✅ User %s vẫn còn quyền ở %s group từ đơn khác, không xử lý kick/mute các group đó.",
            user_id,
            len(retained_group_ids),
        )
        for gid in retained_group_ids:
            try:
                await unmute_member(gid, user_id)
                record_support_event("member_unmuted", user_id, chat_id=gid, order_id=order_id, plan_name=display_plan_name(plan_name, user_id), raw_data={"reason": "active_renewal", "plan_name_raw": plan_name})
                logging.info("🔊 User %s đã gia hạn, mở mute lại ở group %s.", user_id, gid)
            except Exception as exc:
                logging.error("❌ Lỗi mở mute User %s ở group %s: %s", user_id, gid, exc)
    await kick_workflow.enqueue_expired_renewal_kick_tasks_v2(
        user_id,
        order_id,
        plan_name,
        expire_str,
        now,
        plan_group_cache=plan_group_cache,
    )
    return expired_group_ids, []

async def process_support_grace_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now, run_kick_cache=None, run_presence_cache=None, user_cache=None, plan_group_cache=None):
    has_active_membership = user_cache[user_id]["has_active_membership"] if user_cache and user_id in user_cache else user_has_active_membership(user_id, order_id, users_data, now, plan_group_cache=plan_group_cache)
    if has_active_membership:
        await ensure_support_group_unmuted(user_id, order_id, plan_name)
        return
    gid = support_group_id()
    if not (support_group_enabled() and support_group_mute_enabled() and gid):
        return
    kick_state, _ = renewal_kick_state_v2(user_id, order_id, gid)
    if kick_state in {"done", "processing", "review_required", "blocked"}:
        if not await member_is_present(gid, user_id):
            return
        await ensure_member_kicked(
            gid,
            user_id,
            order_id,
            plan_name,
            "support_rejoined_after_kick",
            raw_data={"expire_at": expire_str},
            run_kick_cache=run_kick_cache,
            run_presence_cache=run_presence_cache,
        )
        return

    mute_state, muted_event = renewal_kick_state_v2(user_id, order_id, gid)
    if mute_state == "none" and not muted_event:
        await ensure_support_group_muted(user_id, order_id, plan_name, expire_str)
        return

    muted_at = parse_event_datetime(muted_event)
    if not muted_at:
        return
    grace_days = support_group_grace_days()
    if now < muted_at + timedelta(days=grace_days):
        return

    try:
        await ensure_member_kicked(
            gid,
            user_id,
            order_id,
            plan_name,
            "support_grace_expired",
            raw_data={"muted_at": muted_event.get("created_at"), "grace_days": grace_days},
            run_kick_cache=run_kick_cache,
            run_presence_cache=run_presence_cache,
        )
    except Exception as exc:
        logging.error("❌ Lỗi kick User %s khỏi group hỗ trợ %s: %s", user_id, gid, exc)

async def check_expirations_professional():
    try:
        from scheduler_new_core_runtime import full_cutover_gate
        cutover_config = {
            key: str(db.get_config(key, "") or "")
            for key in (
                "RENEWAL_NEW_CORE_FULL_CUTOVER",
                "RENEWAL_NEW_CORE_DRY_RUN",
                "RENEWAL_NEW_CORE_LIMITED_MUTATION",
                "RENEWAL_NEW_CORE_CUTOVER_ACK",
            )
        }
        full_cutover, gate_reason = full_cutover_gate(cutover_config)
        if str(cutover_config.get("RENEWAL_NEW_CORE_FULL_CUTOVER") or "").strip().upper() in {"ON", "TRUE", "1", "YES"} and not full_cutover:
            logging.error("⛔ Full worker cutover bị chặn: %s", gate_reason)
            return None
        if full_cutover:
            result = await run_new_core_cycle()
            logging.info("✅ Full new-core worker cycle: %s", result)
            return result
        if config_enabled("RENEWAL_NEW_CORE_CANARY", "OFF"):
            result = await run_new_core_cycle()
            logging.info(
                "renewal_cycle_completed %s",
                structured_cycle_log(result, correlation_id=str(uuid.uuid4()), occurred_at=now_local()),
            )
            return result
        await expiration_workflow.run_expiration_cycle()
    except Exception as e:
        logging.error(f"❌ Lỗi hệ thống quét định kỳ: {e}")


async def run_new_core_cycle():
    """Canary entrypoint; disabled by default until group planning is wired."""
    from scheduler_new_core_runtime import CallableClock, run_cycle, run_limited_mutation_cycle, run_read_only_cycle

    cohort_user_ids = {item.strip() for item in str(db.get_config("RENEWAL_NEW_CORE_COHORT_USER_IDS", "") or "").split(",") if item.strip()}
    cohort_order_ids = {item.strip() for item in str(db.get_config("RENEWAL_NEW_CORE_COHORT_ORDER_IDS", "") or "").split(",") if item.strip()}
    if config_enabled("RENEWAL_NEW_CORE_LIMITED_MUTATION", "OFF"):
        return await run_limited_mutation_cycle(
            store=supabase_store,
            bot=bot,
            clock=CallableClock(now_local),
            active_order_check=lambda user_id, order_id, group_id: group_id in user_active_group_ids(user_id, order_id, [], now_local()),
            cohort_user_ids=cohort_user_ids,
            cohort_order_ids=cohort_order_ids,
        )

    if config_enabled("RENEWAL_NEW_CORE_DRY_RUN", "ON"):
        return await run_read_only_cycle(
            store=supabase_store,
            bot=bot,
            clock=CallableClock(now_local),
            active_order_check=lambda user_id, order_id, group_id: group_id in user_active_group_ids(user_id, order_id, [], now_local()),
            plan_group_resolver=lambda plan_name: list(cached_plan_group_ids(plan_name)),
        )

    return await run_cycle(
        store=supabase_store,
        bot=bot,
        clock=CallableClock(now_local),
        parse_datetime=parse_expire_datetime,
        active_order_check=lambda user_id, order_id, group_id: group_id in user_active_group_ids(user_id, order_id, [], now_local()),
        plan_group_resolver=lambda plan_name: list(cached_plan_group_ids(plan_name)),
    )


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
            reconciled_orders = reconcile_expired_paid_orders(candidates, now, limit=reconcile_limit)
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


async def cleanup_used_activation_links(now=None):
    await cleanup_workflow.cleanup_used_activation_links(now=now)


async def cleanup_order_invite_links(now=None, *, only_used=False, group_id=None, force=False):
    return await cleanup_workflow.cleanup_order_invite_links(now=now, only_used=only_used, group_id=group_id, force=force)

# Worker chạy ngầm vĩnh viễn
async def main():
    print("🚀 [MODULE] Scheduler (Quản gia: Nhắc hạn/Kick) đã khởi động!")
    if not supabase_store.enabled and not db.users_sheet:
        db.connect()
    await asyncio.sleep(config_int("SCHEDULER_INITIAL_DELAY_SECONDS", 10, minimum=0))
    
    while True:
        if renewal_worker_allowed_now():
            await check_expirations_professional()
        else:
            logging.info("⏭ Bỏ qua vòng quét gia hạn ngoài khung giờ cho phép (00:00, 06:00, 12:00, 18:00).")
        
        # Cuối ngày dọn dẹp RAM xóa các record của ngày hôm trước
        today_str = now_local().strftime("%Y-%m-%d")
        to_remove = [k for k in notified_users if not k.endswith(today_str)]
        for k in to_remove: notified_users.remove(k)
        kick_cutoff = now_local() - timedelta(minutes=config_int("KICK_RECHECK_COOLDOWN_MINUTES", 1440, minimum=1))
        for key, kicked_at in list(recent_kicks.items()):
            if kicked_at < kick_cutoff:
                recent_kicks.pop(key, None)
            
        # Worker gia hạn chỉ nên thức trong 4 khung giờ/ngày; ngoài khung giờ thì ngủ dài hơn để tiết kiệm tài nguyên.
        if renewal_worker_allowed_now():
            interval_seconds = config_int(
                "RENEWAL_WORKER_INTERVAL_SECONDS",
                RENEWAL_WORKER_MIN_INTERVAL_SECONDS,
                minimum=RENEWAL_WORKER_MIN_INTERVAL_SECONDS,
            )
        else:
            interval_seconds = config_int(
                "RENEWAL_WORKER_SLEEP_SECONDS",
                RENEWAL_WORKER_DEFAULT_INTERVAL_SECONDS,
                minimum=RENEWAL_WORKER_MIN_INTERVAL_SECONDS,
            )
        logging.info("💤 Hoàn tất chu kỳ quét. Scheduler nghỉ %s giây trước vòng tiếp theo.", interval_seconds)
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(main())
