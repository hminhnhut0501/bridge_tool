import asyncio
import logging
import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database import db
from bot_instance import bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from config_utils import config_int, group_numbers
from hidden_group_utils import display_plan_name, is_lifetime_order, resolve_plan_groups
from i18n import get_user_language
from renewal_utils import build_early_renew_block, build_early_renew_offer
from supabase_store import supabase_store
from support_utils import is_lifetime_plan, is_support_group, mute_member, record_support_event, revoke_support_invite_link, support_group_enabled, support_group_grace_days, support_group_id, support_group_mute_enabled, unmute_member
from bot_links import is_legacy_bot

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm để tránh 1 ngày Bot gửi 2 lần tin nhắc cho cùng 1 người
notified_users = set()
recent_kicks = {}
SCHEDULER_DEFAULT_INTERVAL_SECONDS = 10800
SCHEDULER_MIN_INTERVAL_SECONDS = 10800

def now_local():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime.now(timezone).replace(tzinfo=None)

def config_enabled(key, default="ON"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ", "BẬT", "BAT"}

def parse_int_config(key, default=0, minimum=0):
    try:
        return max(minimum, int(float(str(db.get_config(key, default) or default).strip())))
    except (TypeError, ValueError):
        return max(minimum, int(default))

def parse_expire_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
            try:
                timezone = ZoneInfo(timezone_name)
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None

def normalize_chat_id(value):
    raw = str(value or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw

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
            return None
        logging.warning("⚠️ Không kiểm tra được quyền user %s trong group %s: %s", user_id, chat_id, exc)
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
    return parse_expire_datetime((event or {}).get("created_at"))

def event_happened_after(candidate, reference):
    candidate_at = parse_event_datetime(candidate)
    reference_at = parse_event_datetime(reference)
    return bool(candidate_at and reference_at and candidate_at >= reference_at)

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
    active_groups = set()
    for row in users_data:
        if row_value(row, 0) == current_order_id:
            continue
        if row_value(row, 1) != str(user_id):
            continue
        if row_value(row, 5).upper() != "PAID":
            continue
        other_plan = row_value(row, 3)
        other_groups = set(cached_plan_group_ids(other_plan, plan_group_cache))
        if not other_groups:
            continue
        if is_lifetime_order(other_plan) or is_lifetime_plan(other_plan):
            active_groups.update(other_groups)
            continue
        expire_raw = row_value(row, 7)
        expire_date = parse_expire_datetime(expire_raw)
        if expire_date and expire_date > now:
            active_groups.update(other_groups)
        elif expire_raw and not expire_date:
            active_groups.update(other_groups)
            logging.warning(
                "⚠️ User %s có đơn PAID %s cùng group nhưng expire_at không đọc được ('%s'); giữ quyền để tránh kick nhầm.",
                user_id,
                row_value(row, 0),
                expire_raw,
            )
    return active_groups

def user_has_active_membership(user_id, current_order_id, users_data, now, plan_group_cache=None):
    for row in users_data:
        if row_value(row, 0) == current_order_id:
            continue
        if row_value(row, 1) != str(user_id):
            continue
        if row_value(row, 5).upper() != "PAID":
            continue
        other_plan = row_value(row, 3)
        if is_lifetime_order(other_plan) or is_lifetime_plan(other_plan):
            return True
        expire_raw = row_value(row, 7)
        expire_date = parse_expire_datetime(expire_raw)
        if expire_date and expire_date > now:
            return True
        if expire_raw and not expire_date:
            logging.warning(
                "⚠️ User %s có đơn PAID %s nhưng expire_at không đọc được ('%s'); xem như active để tránh xử lý nhầm support.",
                user_id,
                row_value(row, 0),
                expire_raw,
            )
            return True
    return False

def build_users_index(users_data):
    users_index = {}
    for row in users_data:
        user_id = row_value(row, 1)
        if not user_id:
            continue
        users_index.setdefault(user_id, []).append(row)
    return users_index

def build_user_membership_cache(users_index, now, user_ids=None, plan_group_cache=None):
    cache = {}
    target_user_ids = set(str(user_id) for user_id in user_ids) if user_ids is not None else None
    for user_id, rows in users_index.items():
        if target_user_ids is not None and user_id not in target_user_ids:
            continue
        active_orders = []
        active_group_ids = set()
        support_active = False
        for row in rows:
            order_id = row_value(row, 0)
            status = row_value(row, 5).upper()
            if status != "PAID":
                continue
            plan_name = row_value(row, 3)
            expire_raw = row_value(row, 7)
            expired = False
            if is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                expired = False
            else:
                expire_date = parse_expire_datetime(expire_raw)
                if expire_date and expire_date <= now:
                    expired = True
                elif expire_raw and not expire_date:
                    expired = False
                else:
                    expired = False
            if not expired:
                active_orders.append(order_id)
                if is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                    support_active = True
                else:
                    expire_date = parse_expire_datetime(expire_raw)
                    if expire_date and expire_date > now:
                        support_active = True
                active_group_ids.update(cached_plan_group_ids(plan_name, plan_group_cache))
        if not active_orders:
            support_active = False
        cache[user_id] = {
            "active_orders": set(active_orders),
            "active_group_ids": active_group_ids,
            "has_active_membership": bool(active_orders),
            "support_active": support_active,
        }
    return cache

def build_user_membership_cache_from_rows(rows_by_user, now, plan_group_cache=None):
    cache = {}
    for user_id, rows in rows_by_user.items():
        active_orders = []
        active_group_ids = set()
        support_active = False
        for row in rows:
            order_id = row_value(row, 0)
            status = row_value(row, 5).upper()
            if status != "PAID":
                continue
            plan_name = row_value(row, 3)
            expire_raw = row_value(row, 7)
            if is_lifetime_order(plan_name) or is_lifetime_plan(plan_name):
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(cached_plan_group_ids(plan_name, plan_group_cache))
                continue
            expire_date = parse_expire_datetime(expire_raw)
            if expire_date and expire_date > now:
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(cached_plan_group_ids(plan_name, plan_group_cache))
            elif expire_raw and not expire_date:
                active_orders.append(order_id)
                support_active = True
                active_group_ids.update(cached_plan_group_ids(plan_name, plan_group_cache))
                logging.warning(
                    "⚠️ User %s có đơn PAID %s cùng group nhưng expire_at không đọc được ('%s'); giữ quyền để tránh kick nhầm.",
                    user_id,
                    order_id,
                    expire_raw,
                )
        cache[user_id] = {
            "active_orders": set(active_orders),
            "active_group_ids": active_group_ids,
            "has_active_membership": bool(active_orders),
            "support_active": support_active,
        }
    return cache

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
        if 0 <= days_remaining <= days_notice:
            reminder_rows.append((offset, row))
            expiring_user_ids.add(user_id)
    return expired_rows, reminder_rows, expiring_user_ids

async def send_html_message(chat_id, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" not in str(e).lower() and "can't parse entities" not in str(e).lower():
            raise
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=None)

def latest_support_event(event_type, user_id, order_id, chat_id):
    if not supabase_store.enabled:
        return None
    try:
        return supabase_store.latest_support_event(event_type, telegram_user_id=user_id, order_id=order_id, chat_id=chat_id)
    except Exception as exc:
        logging.warning("⚠️ Không đọc được support event %s user=%s order=%s chat=%s: %s", event_type, user_id, order_id, chat_id, exc)
        return None

def is_kick_finalized(user_id, order_id, chat_id):
    return bool(latest_support_event("member_kick_closed", user_id, order_id, chat_id))

async def ensure_support_group_muted(user_id, order_id, plan_name, expire_str):
    gid = support_group_id()
    if not (support_group_enabled() and support_group_mute_enabled() and gid):
        return False
    plan_label = display_plan_name(plan_name, user_id)
    if latest_support_event("member_muted", user_id, order_id, gid):
        return True
    if latest_support_event("member_mute_skipped_admin", user_id, order_id, gid):
        return True
    if latest_support_event("member_kicked", user_id, order_id, gid):
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
        record_support_event(
            "member_muted",
            user_id,
            chat_id=gid,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={"reason": "support_grace_started", "expire_at": expire_str, "grace_days": support_group_grace_days(), "plan_name_raw": plan_name},
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
    muted_event = latest_support_event("member_muted", user_id, order_id, gid)
    if not muted_event:
        return
    unmuted_event = latest_support_event("member_unmuted", user_id, order_id, gid)
    if event_happened_after(unmuted_event, muted_event):
        return
    try:
        await unmute_member(gid, user_id)
        record_support_event(
            "member_unmuted",
            user_id,
            chat_id=gid,
            order_id=order_id,
            plan_name=plan_label,
            raw_data={"reason": "active_membership", "plan_name_raw": plan_name},
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
    if is_kick_finalized(user_id, order_id, normalized_chat_id):
        logging.info(
            "⏭ Bỏ qua kick User %s group %s đơn %s vì đã có member_kick_closed.",
            user_id,
            chat_id,
            order_id,
        )
        return True
    recent_at = recent_kicks.get(kick_key)
    if recent_at and now - recent_at < timedelta(minutes=cooldown_minutes):
        logging.info(
            "⏭ Bỏ qua kick trùng User %s group %s; lần kick gần nhất trong RAM lúc %s.",
            user_id,
            chat_id,
            recent_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return True

    recent_group_kick = latest_support_event("member_kicked", user_id, None, chat_id)
    if event_happened_within(recent_group_kick, now, cooldown_minutes):
        logging.info(
            "⏭ Bỏ qua kick trùng User %s group %s; đã có event member_kicked gần đây lúc %s.",
            user_id,
            chat_id,
            recent_group_kick.get("created_at"),
        )
        recent_kicks[kick_key] = parse_event_datetime(recent_group_kick) or now
        return True

    existing_kick = latest_support_event("member_kicked", user_id, order_id, chat_id)
    if existing_kick:
        if event_happened_within(existing_kick, now, cooldown_minutes):
            logging.info(
                "⏭ Bỏ qua kick trùng User %s group %s đơn %s; đã có event member_kicked lúc %s.",
                user_id,
                chat_id,
                order_id,
                existing_kick.get("created_at"),
            )
            recent_kicks[kick_key] = parse_event_datetime(existing_kick) or now
            return True

    if latest_support_event("member_kick_skipped_admin", user_id, None, chat_id):
        return True

    if run_presence_cache is not None and kick_key in run_presence_cache:
        member = run_presence_cache[kick_key]
    else:
        member = await get_chat_member_safe(chat_id, user_id)
        if run_presence_cache is not None:
            run_presence_cache[kick_key] = member
    if member is None:
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
        await bot.ban_chat_member(chat_id=chat_id, user_id=int(user_id))
        await bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
        recent_kicks[kick_key] = now
        if run_kick_cache is not None:
            run_kick_cache.add(run_kick_key)
        payload = {"reason": reason}
        payload.update(raw_data or {})
        if existing_kick:
            payload["previous_kick_event_at"] = existing_kick.get("created_at")
            payload["source"] = "recheck_member_present"
        plan_label = display_plan_name(plan_name, user_id)
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
                "plan_name_raw": plan_name,
                **(raw_data or {}),
            },
        )
        logging.info("🚪 Đã kick User %s khỏi group %s vì %s.", user_id, chat_id, reason)
        return True
    except Exception as exc:
        logging.error("❌ Lỗi kick User %s khỏi group %s: %s", user_id, chat_id, exc)
        payload = {"reason": reason, "error": str(exc)}
        payload.update(raw_data or {})
        plan_label = display_plan_name(plan_name, user_id)
        payload["plan_name_raw"] = plan_name
        record_support_event("member_kick_failed", user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_label, raw_data=payload)
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
            muted_event = latest_support_event("member_muted", user_id, order_id, gid)
            unmuted_event = latest_support_event("member_unmuted", user_id, order_id, gid)
            if not muted_event or event_happened_after(unmuted_event, muted_event):
                continue
            try:
                await unmute_member(gid, user_id)
                record_support_event("member_unmuted", user_id, chat_id=gid, order_id=order_id, plan_name=display_plan_name(plan_name, user_id), raw_data={"reason": "active_renewal", "plan_name_raw": plan_name})
                logging.info("🔊 User %s đã gia hạn, mở mute lại ở group %s.", user_id, gid)
            except Exception as exc:
                logging.error("❌ Lỗi mở mute User %s ở group %s: %s", user_id, gid, exc)

    kick_errors = []
    for gid in expired_group_ids:
        ok = await ensure_member_kicked(
            gid,
            user_id,
            order_id,
            plan_name,
            "vip_expired",
            raw_data={"expired_notice_at": now.strftime("%Y-%m-%d %H:%M:%S"), "expire_at": expire_str},
            run_kick_cache=run_kick_cache,
            run_presence_cache=run_presence_cache,
        )
        if not ok:
            kick_errors.append(gid)
    return expired_group_ids, kick_errors

async def process_support_grace_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now, run_kick_cache=None, run_presence_cache=None, user_cache=None, plan_group_cache=None):
    has_active_membership = user_cache[user_id]["has_active_membership"] if user_cache and user_id in user_cache else user_has_active_membership(user_id, order_id, users_data, now, plan_group_cache=plan_group_cache)
    if has_active_membership:
        await ensure_support_group_unmuted(user_id, order_id, plan_name)
        return
    gid = support_group_id()
    if not (support_group_enabled() and support_group_mute_enabled() and gid):
        return
    if latest_support_event("member_kicked", user_id, order_id, gid):
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

    muted_event = latest_support_event("member_muted", user_id, order_id, gid)
    if not muted_event:
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
        if is_legacy_bot():
            logging.info("⏭ Scheduler bỏ qua vì BOT_VERSION=legacy, bot cũ chỉ còn chuyển hướng.")
            return
        logging.info("⏳ [SCHEDULER] Đang kiểm tra hạn dùng tới hạn/quá hạn...")
        use_supabase = supabase_store.enabled
        if not use_supabase and not db.users_sheet:
            db.connect()

        days_notice = config_int("REMINDER_DAYS", 3, minimum=0)
        now = now_local()
        today_str = now.strftime("%Y-%m-%d")
        await cleanup_used_activation_links(now)

        if use_supabase:
            order_limit = config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100)
            due_before = now + timedelta(days=days_notice)
            try:
                due_orders = supabase_store.list_scheduler_due_rows(due_before, limit=order_limit)
            except Exception as exc:
                logging.warning("⚠️ Không dùng được query due_rows, fallback quét rộng: %s", exc)
                due_orders = supabase_store.list_scheduler_orders(limit=order_limit)
            users_data = [supabase_store.order_to_sheet_row(order) for order in due_orders]
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
        users_index = build_users_index(users_data)
        expired_rows, reminder_rows, expiring_user_ids = split_scheduler_rows(users_data, now, days_notice)
        user_membership_cache = {}
        if use_supabase and expiring_user_ids:
            user_rows_by_id = {}
            for user_id in expiring_user_ids:
                try:
                    user_rows = supabase_store.list_paid_orders_for_user(user_id, limit=order_limit)
                except Exception as exc:
                    logging.warning("⚠️ Không lấy được paid orders cho user %s để giữ quyền kick: %s", user_id, exc)
                    user_rows = []
                combined = list(users_index.get(user_id, []))
                seen_order_ids = {row_value(row, 0) for row in combined}
                for order in user_rows:
                    order_row = supabase_store.order_to_sheet_row(order)
                    if row_value(order_row, 0) not in seen_order_ids:
                        combined.append(order_row)
                user_rows_by_id[user_id] = combined
            user_membership_cache = build_user_membership_cache_from_rows(user_rows_by_id, now, plan_group_cache=plan_group_cache)
        elif users_index:
            user_membership_cache = build_user_membership_cache(users_index, now, user_ids=expiring_user_ids, plan_group_cache=plan_group_cache)

        # Pass 1: xử lý EXPIRED trước để kick/mute đúng ngay.
        for offset, row in expired_rows:
            row_number = offset + 2
            order_id = row_value(row, 0)
            offer_ref = order_id if use_supabase else row_number
            user_id = str(row[1]).strip()
            plan_name = str(row[3]).strip()
            expire_str = str(row[7]).strip()
            if not expire_str:
                continue
            if not is_lifetime_plan(plan_name) and not cached_plan_group_ids(plan_name, plan_group_cache):
                logging.error(
                    "⏭ Bỏ qua xử lý đơn EXPIRED %s vì plan_name='%s' không map được group VIP; không mute/kick support để tránh xử lý nhầm.",
                    offer_ref,
                    plan_name,
                )
                continue
            await process_vip_kicks_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now, run_kick_cache=run_kick_cache, run_presence_cache=run_presence_cache, user_cache=user_membership_cache, plan_group_cache=plan_group_cache)
            await process_support_grace_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now, run_kick_cache=run_kick_cache, run_presence_cache=run_presence_cache, user_cache=user_membership_cache, plan_group_cache=plan_group_cache)

            if should_send_expired_notice(row, today_str):
                expire_date = parse_expire_datetime(expire_str)
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
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Trọn Đời"), callback_data="nav:svip_page"))
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
                        supabase_store.mark_expired_notice(order_id, now.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        db.users_sheet.update_cell(row_number, 12, now.strftime("%Y-%m-%d %H:%M:%S"))
                    logging.info("📮 Đã gửi tin báo hết hạn cho User %s, đơn/dòng %s, plan=%s.", user_id, offer_ref, plan_label)
                except Exception as e:
                    logging.error(f"❌ Lỗi gửi tin báo hết hạn cho {user_id}: {e}")

        # Pass 2: xử lý PAID reminder.
        for offset, row in reminder_rows:
            row_number = offset + 2
            order_id = row_value(row, 0)
            offer_ref = order_id if use_supabase else row_number
            user_id = str(row[1]).strip()
            plan_name = str(row[3]).strip()
            expire_str = str(row[7]).strip()
            expire_date = parse_expire_datetime(expire_str)
            if not expire_date:
                summary["invalid"] += 1
                logging.warning(f"⚠️ Bỏ qua đơn/dòng {offer_ref}: không đọc được ngày hết hạn '{expire_str}' cho user {user_id}.")
                continue
            if is_lifetime_plan(plan_name):
                continue
            days_remaining = (expire_date.date() - now.date()).days
            notif_key = f"{user_id}_{offer_ref}_{today_str}"
            if config_enabled("REMINDER_ENABLED", "ON") and 0 <= days_remaining <= days_notice and notif_key not in notified_users and not should_skip_reminder(row, today_str):
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
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Trọn Đời"), callback_data="nav:svip_page"))
                else:
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_GROUP", "🔄 Gia hạn / Mở rộng gói"), callback_data="nav:main_menu"))
                try:
                    await send_html_message(user_id, msg_reminder, kb.as_markup())
                    record_support_event("renewal_reminder_sent", user_id, order_id=order_id, plan_name=display_plan_name(plan_name, user_id), raw_data={"days_remaining": days_remaining, "expire_at": expire_str, "plan_name_raw": plan_name})
                    notified_users.add(notif_key)
                    summary["reminded"] += 1
                    if use_supabase:
                        supabase_store.mark_reminder_sent(order_id, today_str)
                    else:
                        db.users_sheet.update_cell(row_number, 11, today_str)
                    logging.info(f"📩 Đã nhắc gia hạn ({days_remaining} ngày) cho User {user_id}, đơn/dòng {offer_ref}, plan={plan_label}.")
                except Exception as e:
                    logging.error(f"❌ Lỗi gửi tin nhắc cho {user_id}: {e}")
            else:
                summary["skipped_not_due"] += 1

        logging.info(
            "✅ Scheduler xong: hết hạn=%s, báo hết hạn=%s, nhắc gia hạn=%s, chưa tới hạn=%s, lỗi ngày=%s.",
            summary["expired"],
            summary["expired_notice"],
            summary["reminded"],
            summary["skipped_not_due"],
            summary["invalid"],
        )

    except Exception as e:
        logging.error(f"❌ Lỗi hệ thống quét định kỳ: {e}")


async def cleanup_used_activation_links(now=None):
    await cleanup_order_invite_links(now=now, only_used=True)


async def cleanup_order_invite_links(now=None, *, only_used=False, group_id=None, force=False):
    if not supabase_store.enabled:
        return {"total": 0, "success": 0, "failed": 0, "rows": []}
    now = now or now_local()
    cleanup_days = parse_int_config("ACTIVATION_LINK_CLEANUP_DAYS", 7, minimum=1)
    cutoff = now - timedelta(days=cleanup_days)
    target_group_id = normalize_chat_id(group_id) if group_id else ""
    try:
        rows = supabase_store.list_order_activation_codes(limit=config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100))
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
        used_at = parse_expire_datetime(row.get("used_at") or row.get("activated_at"))
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
            item_group_id = normalize_chat_id(item.get("group_id"))
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

        try:
            plan_label = display_plan_name(row.get("plan_name"), row.get("telegram_user_id"))
            record_support_event(
                "activation_link_cleanup_done" if row_success else "activation_link_cleanup_failed",
                row.get("telegram_user_id"),
                full_name=row.get("full_name"),
                order_id=row.get("order_id"),
                plan_name=plan_label,
                raw_data={
                    "activation_code": row.get("code"),
                    "used_at": row.get("used_at") or row.get("activated_at"),
                    "cleanup_days": cleanup_days,
                    "plan_name_raw": row.get("plan_name"),
                    "cleanup_results": cleanup_results,
                    "group_id": target_group_id or "",
                    "mode": "manual" if force else "scheduled",
                },
            )
        except Exception as exc:
            logging.warning("⚠️ Không ghi được cleanup event cho %s: %s", row.get("code"), exc)

        results.append({
            "code": row.get("code"),
            "order_id": row.get("order_id"),
            "telegram_user_id": row.get("telegram_user_id"),
            "group_id": target_group_id or "",
            "success": row_success,
            "cleanup_results": cleanup_results,
        })

    return {"total": len(results), "success": success_count, "failed": failed_count, "rows": results}

# Worker chạy ngầm vĩnh viễn
async def main():
    print("🚀 [MODULE] Scheduler (Quản gia: Nhắc hạn/Kick) đã khởi động!")
    if not supabase_store.enabled and not db.users_sheet:
        db.connect()
    await asyncio.sleep(config_int("SCHEDULER_INITIAL_DELAY_SECONDS", 10, minimum=0))
    
    while True:
        await check_expirations_professional()
        
        # Cuối ngày dọn dẹp RAM xóa các record của ngày hôm trước
        today_str = now_local().strftime("%Y-%m-%d")
        to_remove = [k for k in notified_users if not k.endswith(today_str)]
        for k in to_remove: notified_users.remove(k)
        kick_cutoff = now_local() - timedelta(minutes=config_int("KICK_RECHECK_COOLDOWN_MINUTES", 1440, minimum=1))
        for key, kicked_at in list(recent_kicks.items()):
            if kicked_at < kick_cutoff:
                recent_kicks.pop(key, None)
            
        # 3 tiếng/vòng để giảm request Supabase/Telegram; cần chạy ngay có thể dùng lệnh admin quét hạn.
        interval_seconds = config_int(
            "SCHEDULER_INTERVAL_SECONDS",
            SCHEDULER_DEFAULT_INTERVAL_SECONDS,
            minimum=SCHEDULER_MIN_INTERVAL_SECONDS,
        )
        logging.info("💤 Hoàn tất chu kỳ quét. Scheduler nghỉ %s giây trước vòng tiếp theo.", interval_seconds)
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(main())
