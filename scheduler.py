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
from hidden_group_utils import is_lifetime_order, resolve_plan_groups
from i18n import get_user_language
from renewal_utils import build_early_renew_block, build_early_renew_offer
from supabase_store import supabase_store
from support_utils import is_lifetime_plan, is_support_group, mute_member, record_support_event, support_group_enabled, support_group_grace_days, support_group_id, support_group_mute_enabled, unmute_member

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm để tránh 1 ngày Bot gửi 2 lần tin nhắc cho cùng 1 người
notified_users = set()
recent_kicks = {}
SCHEDULER_DEFAULT_INTERVAL_SECONDS = 1800
SCHEDULER_MIN_INTERVAL_SECONDS = 1800

def now_local():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime.now(timezone).replace(tzinfo=None)

def config_enabled(key, default="ON"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ", "BẬT", "BAT"}

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

def should_skip_reminder(row, today_str):
    last_reminder_date = row_value(row, 10)
    return last_reminder_date == today_str

def should_skip_expired_notice(row):
    return bool(row_value(row, 11))

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

def user_active_group_ids(user_id, current_order_id, users_data, now):
    active_groups = set()
    for row in users_data:
        if row_value(row, 0) == current_order_id:
            continue
        if row_value(row, 1) != str(user_id):
            continue
        if row_value(row, 5).upper() != "PAID":
            continue
        other_plan = row_value(row, 3)
        other_groups = set(plan_group_ids(other_plan))
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

def user_has_active_membership(user_id, current_order_id, users_data, now):
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

async def ensure_support_group_muted(user_id, order_id, plan_name, expire_str):
    gid = support_group_id()
    if not (support_group_enabled() and support_group_mute_enabled() and gid):
        return False
    if latest_support_event("member_muted", user_id, order_id, gid):
        return True
    if latest_support_event("member_kicked", user_id, order_id, gid):
        return True
    try:
        await mute_member(gid, user_id)
        record_support_event(
            "member_muted",
            user_id,
            chat_id=gid,
            order_id=order_id,
            plan_name=plan_name,
            raw_data={"reason": "support_grace_started", "expire_at": expire_str, "grace_days": support_group_grace_days()},
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
            plan_name=plan_name,
            raw_data={"reason": "active_membership"},
        )
        logging.info("🔊 User %s đang có gói active, đã mở mute trong group hỗ trợ %s.", user_id, gid)
    except Exception as exc:
        logging.warning("⚠️ Không thể mở mute User %s trong group hỗ trợ %s: %s", user_id, gid, exc)

async def member_is_present(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
        raw_status = getattr(member, "status", "")
        status = str(getattr(raw_status, "value", raw_status)).lower()
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

async def ensure_member_kicked(chat_id, user_id, order_id, plan_name, reason, raw_data=None):
    now = now_local()
    normalized_chat_id = normalize_chat_id(chat_id)
    kick_key = (normalized_chat_id, str(user_id))
    cooldown_minutes = config_int("KICK_RECHECK_COOLDOWN_MINUTES", 1440, minimum=1)
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
        if not await member_is_present(chat_id, user_id):
            return True

    try:
        await bot.ban_chat_member(chat_id=chat_id, user_id=int(user_id))
        await bot.unban_chat_member(chat_id=chat_id, user_id=int(user_id))
        recent_kicks[kick_key] = now
        payload = {"reason": reason}
        payload.update(raw_data or {})
        if existing_kick:
            payload["previous_kick_event_at"] = existing_kick.get("created_at")
            payload["source"] = "recheck_member_present"
        record_support_event("member_kicked", user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_name, raw_data=payload)
        logging.info("🚪 Đã kick User %s khỏi group %s vì %s.", user_id, chat_id, reason)
        return True
    except Exception as exc:
        logging.error("❌ Lỗi kick User %s khỏi group %s: %s", user_id, chat_id, exc)
        payload = {"reason": reason, "error": str(exc)}
        payload.update(raw_data or {})
        record_support_event("member_kick_failed", user_id, chat_id=chat_id, order_id=order_id, plan_name=plan_name, raw_data=payload)
        return False

async def process_vip_kicks_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now):
    current_group_ids = plan_group_ids(plan_name)
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

    active_group_ids = user_active_group_ids(user_id, order_id, users_data, now)
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
                record_support_event("member_unmuted", user_id, chat_id=gid, order_id=order_id, plan_name=plan_name, raw_data={"reason": "active_renewal"})
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
        )
        if not ok:
            kick_errors.append(gid)
    return expired_group_ids, kick_errors

async def process_support_grace_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now):
    if user_has_active_membership(user_id, order_id, users_data, now):
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
        )
    except Exception as exc:
        logging.error("❌ Lỗi kick User %s khỏi group hỗ trợ %s: %s", user_id, gid, exc)

async def check_expirations_professional():
    try:
        logging.info("⏳ [SCHEDULER] Đang kiểm tra hạn dùng tới hạn/quá hạn...")
        use_supabase = supabase_store.enabled
        if not use_supabase and not db.users_sheet:
            db.connect()

        days_notice = config_int("REMINDER_DAYS", 3, minimum=0)
        now = now_local()
        today_str = now.strftime("%Y-%m-%d")

        if use_supabase:
            order_limit = config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100)
            due_before = now + timedelta(days=days_notice)
            try:
                scheduler_orders = supabase_store.list_scheduler_due_orders(due_before, limit=order_limit)
            except Exception as exc:
                logging.warning("⚠️ Không dùng được query tối ưu scheduler, fallback quét rộng: %s", exc)
                scheduler_orders = supabase_store.list_scheduler_orders(limit=order_limit)
            users_data = [supabase_store.order_to_sheet_row(order) for order in scheduler_orders]
        else:
            users_data = db.users_sheet.get_all_values()[1:]

        logging.info(
            "⏰ Scheduler timezone Asia/Ho_Chi_Minh: %s, nhắc trước %s ngày, xử lý %s đơn/dòng.",
            now.strftime("%Y-%m-%d %H:%M:%S"),
            days_notice,
            len(users_data),
        )
        summary = {"expired": 0, "expired_notice": 0, "reminded": 0, "skipped_not_due": 0, "invalid": 0}
        
        # Duyệt danh sách đơn PAID từ Supabase hoặc các dòng Users từ Sheet.
        for offset, row in enumerate(users_data, start=0):
            if len(row) < 8: continue

            row_number = offset + 2
            order_id = row_value(row, 0)
            offer_ref = order_id if use_supabase else row_number
            
            user_id = str(row[1]).strip()
            plan_name = str(row[3]).strip()
            status = str(row[5]).strip().upper()
            expire_str = str(row[7]).strip()

            if status == "EXPIRED" and expire_str:
                if not is_lifetime_plan(plan_name) and not plan_group_ids(plan_name):
                    logging.error(
                        "⏭ Bỏ qua xử lý đơn EXPIRED %s vì plan_name='%s' không map được group VIP; "
                        "không mute/kick support để tránh xử lý nhầm.",
                        offer_ref,
                        plan_name,
                    )
                    continue
                await process_vip_kicks_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now)
                await process_support_grace_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now)
                continue

            if status != "PAID" or not expire_str: 
                continue
                
            # Khách VIP Trọn đời thì bỏ qua luôn, không bao giờ lo hết hạn hoặc bị xử lý support.
            if is_lifetime_plan(plan_name):
                continue

            expire_date = parse_expire_datetime(expire_str)
            if not expire_date:
                summary["invalid"] += 1
                logging.warning(f"⚠️ Bỏ qua đơn/dòng {offer_ref}: không đọc được ngày hết hạn '{expire_str}' cho user {user_id}.")
                continue

            days_remaining = (expire_date.date() - now.date()).days
            notif_key = f"{user_id}_{offer_ref}_{today_str}"

            # ==========================================
            # 1. HẾT HẠN -> KICK NGAY KHỎI GROUP VIP CHÍNH
            # SUPPORT_GROUP_GRACE_DAYS chỉ áp dụng cho group hỗ trợ/bảo hành.
            # plan_group_ids() đã loại support group, nên các group ở đây là group VIP chính.
            # ==========================================
            if expire_date <= now:
                summary["expired"] += 1
                logging.info(f"🚫 User {user_id} đã hết hạn gói {plan_name} từ {expire_date:%Y-%m-%d %H:%M:%S}.")
                if not plan_group_ids(plan_name):
                    logging.error(
                        "⏭ Chưa đóng EXPIRED đơn/dòng %s vì plan_name='%s' không map được group VIP. "
                        "Cần sửa tên gói hoặc BTN_G/ID_G trước khi kick.",
                        offer_ref,
                        plan_name,
                    )
                    continue
                expired_group_ids, kick_errors = await process_vip_kicks_for_expired_order(user_id, order_id, plan_name, expire_str, users_data, now)

                if not expired_group_ids:
                    if not user_has_active_membership(user_id, order_id, users_data, now):
                        await ensure_support_group_muted(user_id, order_id, plan_name, expire_str)
                    try:
                        if use_supabase:
                            supabase_store.mark_order_expired(order_id, expired_notice_at=row_value(row, 11) or now.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            db.users_sheet.update(f"F{row_number}:L{row_number}", [["EXPIRED", row_value(row, 6), row_value(row, 7), row_value(row, 8), row_value(row, 9), row_value(row, 10), row_value(row, 11) or now.strftime("%Y-%m-%d %H:%M:%S")]])
                    except Exception as e:
                        logging.error(f"❌ Lỗi đóng đơn cũ đã được gia hạn {offer_ref}: {e}")
                    continue

                if kick_errors:
                    logging.error(f"⏭ Chưa đóng EXPIRED đơn/dòng {offer_ref} vì còn lỗi kick: {kick_errors}")
                    continue

                if not user_has_active_membership(user_id, order_id, users_data, now):
                    await ensure_support_group_muted(user_id, order_id, plan_name, expire_str)

                if config_enabled("EXPIRED_NOTICE_ENABLED", "ON") and not should_skip_expired_notice(row):
                    msg_expired = (
                        db.get_config("MSG_EXPIRED", "⚠️ Gói <b>{plan}</b> của bạn đã hết hạn. Bạn đã bị tắt quyền gửi tin trong nhóm.\n\nBạn có <b>{grace_days} ngày</b> để gia hạn. Nếu không gia hạn, hệ thống sẽ mời bạn ra khỏi nhóm.")
                        .replace("\\n", "\n")
                        .replace("{plan}", plan_name)
                        .replace("{date}", expire_date.strftime("%d/%m/%Y %H:%M:%S"))
                        .replace("{grace_days}", str(support_group_grace_days()))
                    )
                    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_RENEW", "🔄 Gia hạn ngay"), callback_data="nav:main_menu"))

                    try:
                        await send_html_message(user_id, msg_expired, kb.as_markup())
                        record_support_event("expired_notice_sent", user_id, order_id=order_id, plan_name=plan_name, raw_data={"expire_at": expire_str})
                        summary["expired_notice"] += 1
                        logging.info(f"📩 Đã gửi thông báo hết hạn cho User {user_id}")
                    except Exception as e:
                        logging.error(f"❌ Lỗi gửi thông báo hết hạn cho {user_id}: {e}")

                processed_at = now.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    if use_supabase:
                        supabase_store.mark_order_expired(order_id, expired_notice_at=processed_at)
                    else:
                        db.users_sheet.update(f"F{row_number}:L{row_number}", [["EXPIRED", row_value(row, 6), row_value(row, 7), row_value(row, 8), row_value(row, 9), row_value(row, 10), processed_at]])
                    logging.info(f"✅ Đã cập nhật EXPIRED tại đơn/dòng {offer_ref}.")
                except Exception as e:
                    logging.error(f"❌ Lỗi cập nhật EXPIRED đơn/dòng {offer_ref}: {e}")
                continue

            # ==========================================
            # 2. NHẮC NHỞ SẮP HẾT HẠN (GỬI 1 LẦN/NGÀY)
            # ==========================================
            if config_enabled("REMINDER_ENABLED", "ON") and 0 <= days_remaining <= days_notice and notif_key not in notified_users and not should_skip_reminder(row, today_str):
                msg_reminder = (
                    db.get_config("MSG_REMINDER", "⏰ Gói <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa!\n\n👇 Nhấn nút bên dưới để gia hạn ngay nhé:")
                    .replace("\\n", "\n")
                    .replace("{plan}", plan_name)
                    .replace("{days}", str(days_remaining))
                    .replace("{date}", expire_date.strftime("%d/%m/%Y %H:%M:%S"))
                )
                renew_currency = "USD" if get_user_language(user_id) == "en" else "VND"
                early_renew_offer = build_early_renew_offer(row, offer_ref, now, currency=renew_currency)
                msg_reminder += build_early_renew_block(early_renew_offer)
                
                # Trỏ thẳng về các trang UI mới để khách mua hàng
                kb = InlineKeyboardBuilder()
                if early_renew_offer:
                    callback_data = f"renew_order_{order_id}" if use_supabase else f"renew_{row_number}"
                    kb.row(InlineKeyboardButton(
                        text=db.get_config("BTN_EARLY_RENEW", f"🔥 Gia hạn sớm -{early_renew_offer['discount_percent']}%"),
                        callback_data=callback_data,
                    ))
                elif "FULL" in plan_name.upper() or "SVIP" in plan_name.upper():
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Trọn Đời"), callback_data="nav:svip_page"))
                else:
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_GROUP", "🔄 Gia hạn / Mở rộng gói"), callback_data="nav:main_menu"))

                try:
                    await send_html_message(user_id, msg_reminder, kb.as_markup())
                    record_support_event("renewal_reminder_sent", user_id, order_id=order_id, plan_name=plan_name, raw_data={"days_remaining": days_remaining, "expire_at": expire_str})
                    notified_users.add(notif_key) # Lưu nháp để hôm nay không nhắc lại nữa
                    summary["reminded"] += 1
                    if use_supabase:
                        supabase_store.mark_reminder_sent(order_id, today_str)
                    else:
                        db.users_sheet.update_cell(row_number, 11, today_str)
                    logging.info(f"📩 Đã nhắc gia hạn ({days_remaining} ngày) cho User {user_id}, đơn/dòng {offer_ref}.")
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
            
        # 30 phút/vòng là đủ kịp cho hạn VIP và nhẹ hơn cho Render free.
        interval_seconds = config_int(
            "SCHEDULER_INTERVAL_SECONDS",
            SCHEDULER_DEFAULT_INTERVAL_SECONDS,
            minimum=SCHEDULER_MIN_INTERVAL_SECONDS,
        )
        logging.info("💤 Hoàn tất chu kỳ quét. Scheduler nghỉ %s giây trước vòng tiếp theo.", interval_seconds)
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(main())
