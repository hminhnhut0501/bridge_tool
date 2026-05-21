import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database import db
from bot_instance import bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from config_utils import config_int, group_numbers
from renewal_utils import build_early_renew_block, build_early_renew_offer
from supabase_store import supabase_store
from support_utils import is_lifetime_plan, is_support_group, mute_member, record_support_event, support_group_grace_days, support_group_mute_enabled, unmute_member

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm để tránh 1 ngày Bot gửi 2 lần tin nhắc cho cùng 1 người
notified_users = set()

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

def group_matches_plan(group_no, plan_name):
    btn_name = db.get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")
    return btn_name.upper() in plan_name.upper() or f"G{group_no}" in plan_name or "FULL" in plan_name.upper() or "SVIP" in plan_name.upper()

def plan_group_ids(plan_name):
    groups = []
    for group_no in group_numbers():
        if not group_matches_plan(group_no, plan_name):
            continue
        gid = normalize_chat_id(db.get_config(f"ID_G{group_no}"))
        if gid and not is_support_group(gid):
            groups.append(gid)
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
        if is_lifetime_plan(other_plan):
            active_groups.update(other_groups)
            continue
        expire_date = parse_expire_datetime(row_value(row, 7))
        if expire_date and expire_date > now:
            active_groups.update(other_groups)
    return active_groups

async def send_html_message(chat_id, text, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" not in str(e).lower() and "can't parse entities" not in str(e).lower():
            raise
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=None)

async def check_expirations_professional():
    try:
        logging.info("⏳ [SCHEDULER] Đang quét danh sách thành viên để kiểm tra hạn dùng...")
        use_supabase = supabase_store.enabled
        if not use_supabase and not db.users_sheet:
            db.connect()

        if use_supabase:
            order_limit = config_int("SCHEDULER_ORDER_LIMIT", 5000, minimum=100)
            users_data = [supabase_store.order_to_sheet_row(order) for order in supabase_store.list_paid_orders(limit=order_limit)]
        else:
            users_data = db.users_sheet.get_all_values()[1:]
        
        # Lấy số ngày báo trước từ Sheet (Mặc định báo trước 3 ngày)
        days_notice = config_int("REMINDER_DAYS", 3, minimum=0)
        
        now = now_local()
        today_str = now.strftime("%Y-%m-%d")
        logging.info(f"⏰ Scheduler dùng timezone Asia/Ho_Chi_Minh, hiện tại: {now:%Y-%m-%d %H:%M:%S}, nhắc trước {days_notice} ngày.")
        
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

            if status != "PAID" or not expire_str: 
                continue
                
            # Khách VIP Trọn đời thì bỏ qua luôn, không bao giờ lo hết hạn hoặc bị xử lý support.
            if is_lifetime_plan(plan_name):
                continue

            expire_date = parse_expire_datetime(expire_str)
            if not expire_date:
                logging.warning(f"⚠️ Bỏ qua đơn/dòng {offer_ref}: không đọc được ngày hết hạn '{expire_str}' cho user {user_id}.")
                continue

            days_remaining = (expire_date.date() - now.date()).days
            notif_key = f"{user_id}_{offer_ref}_{today_str}"

            # ==========================================
            # 1. HẾT HẠN -> MUTE, SAU GRACE DAYS MỚI KICK
            # ==========================================
            if expire_date <= now:
                logging.info(f"🚫 User {user_id} đã hết hạn gói {plan_name} từ {expire_date:%Y-%m-%d %H:%M:%S}.")
                current_group_ids = plan_group_ids(plan_name)
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
                        try:
                            await unmute_member(gid, user_id)
                            record_support_event("member_unmuted", user_id, chat_id=gid, order_id=order_id, plan_name=plan_name, raw_data={"reason": "active_renewal"})
                            logging.info(f"🔊 User {user_id} đã gia hạn, mở mute lại ở group {gid}.")
                        except Exception as e:
                            logging.error(f"❌ Lỗi mở mute User {user_id} ở group {gid}: {e}")

                if not expired_group_ids:
                    try:
                        if use_supabase:
                            supabase_store.mark_order_expired(order_id, expired_notice_at=row_value(row, 11) or now.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            db.users_sheet.update(f"F{row_number}:L{row_number}", [["EXPIRED", row_value(row, 6), row_value(row, 7), row_value(row, 8), row_value(row, 9), row_value(row, 10), row_value(row, 11) or now.strftime("%Y-%m-%d %H:%M:%S")]])
                    except Exception as e:
                        logging.error(f"❌ Lỗi đóng đơn cũ đã được gia hạn {offer_ref}: {e}")
                    continue

                if config_enabled("EXPIRED_NOTICE_ENABLED", "ON") and not should_skip_expired_notice(row):
                    # Gửi tin báo hết hạn và mute
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
                        logging.info(f"📩 Đã gửi thông báo hết hạn cho User {user_id}")
                    except Exception as e:
                        logging.error(f"❌ Lỗi gửi thông báo hết hạn cho {user_id}: {e}")
                    for gid in expired_group_ids:
                        if not support_group_mute_enabled():
                            logging.info(f"⏭ Bỏ qua mute User {user_id} ở group {gid}: SUPPORT_GROUP_MUTE_ENABLED=OFF")
                            continue
                        try:
                            await mute_member(gid, user_id)
                            record_support_event("member_muted", user_id, chat_id=gid, order_id=order_id, plan_name=plan_name, raw_data={"expire_at": expire_str})
                            logging.info(f"🔇 Đã mute User {user_id} trong group {gid}")
                        except Exception as e:
                            logging.error(f"❌ Lỗi mute User {user_id} trong group {gid}: {e}")

                    if use_supabase:
                        supabase_store.mark_expired_notice(order_id, expired_notice_at=now.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        db.users_sheet.update_cell(row_number, 12, now.strftime("%Y-%m-%d %H:%M:%S"))
                    logging.info(f"✅ Đã cập nhật mốc mute/hết hạn tại đơn/dòng {offer_ref}.")

                expired_notice_at = parse_expire_datetime(row_value(row, 11)) or now
                kick_at = expire_date + timedelta(days=support_group_grace_days())
                if now >= kick_at:
                    for gid in expired_group_ids:
                        try:
                            await bot.ban_chat_member(chat_id=gid, user_id=int(user_id))
                            await bot.unban_chat_member(chat_id=gid, user_id=int(user_id))
                            record_support_event("member_kicked", user_id, chat_id=gid, order_id=order_id, plan_name=plan_name, raw_data={"expired_notice_at": expired_notice_at.strftime("%Y-%m-%d %H:%M:%S")})
                            logging.info(f"🚪 Đã kick User {user_id} khỏi group {gid} sau grace period.")
                        except Exception as e:
                            logging.error(f"❌ Lỗi kick User {user_id} khỏi group {gid}: {e}")

                    try:
                        if use_supabase:
                            supabase_store.mark_order_expired(order_id, expired_notice_at=expired_notice_at.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            db.users_sheet.update(f"F{row_number}:L{row_number}", [["EXPIRED", row_value(row, 6), row_value(row, 7), row_value(row, 8), row_value(row, 9), row_value(row, 10), expired_notice_at.strftime("%Y-%m-%d %H:%M:%S")]])
                        logging.info(f"✅ Đã cập nhật EXPIRED tại đơn/dòng {offer_ref}.")
                    except Exception as e:
                        logging.error(f"❌ Lỗi cập nhật EXPIRED đơn/dòng {offer_ref}: {e}")
                else:
                    logging.info(
                        "⏳ User %s đã được báo hết hạn nhưng chưa tới ngày kick. Hết hạn: %s, grace_days=%s, kick_at=%s.",
                        user_id,
                        expire_date.strftime("%Y-%m-%d %H:%M:%S"),
                        support_group_grace_days(),
                        kick_at.strftime("%Y-%m-%d %H:%M:%S"),
                    )
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
                early_renew_offer = build_early_renew_offer(row, offer_ref, now)
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
                    if use_supabase:
                        supabase_store.mark_reminder_sent(order_id, today_str)
                    else:
                        db.users_sheet.update_cell(row_number, 11, today_str)
                    logging.info(f"📩 Đã nhắc gia hạn ({days_remaining} ngày) cho User {user_id}, đơn/dòng {offer_ref}.")
                except Exception as e:
                    logging.error(f"❌ Lỗi gửi tin nhắc cho {user_id}: {e}")
            else:
                logging.info(f"⏭ Đơn/dòng {offer_ref}: User {user_id} còn {days_remaining} ngày, chưa tới điều kiện nhắc.")

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
            
        # Bot ngủ 4 tiếng rồi mới quét Sheet lại 1 lần (Cho nhẹ máy chủ)
        logging.info("💤 Hoàn tất chu kỳ quét. Quản gia đi ngủ 4 tiếng...")
        await asyncio.sleep(config_int("SCHEDULER_INTERVAL_SECONDS", 14400, minimum=60))

if __name__ == "__main__":
    asyncio.run(main())
