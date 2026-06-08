import asyncio
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_utils import group_numbers
from database import db
from bot_instance import bot 
from hidden_group_utils import display_plan_name, is_lifetime_order, resolve_plan_groups
from payment import payment_manager
from supabase_store import supabase_store
from support_utils import add_support_join_button, is_lifetime_plan, is_support_group, record_support_event, unmute_member
from i18n import t

# Tập hợp chứa các ID đơn hàng bị khách bấm Hủy
cancelled_orders = set()
processing_orders = set()


def bot_timezone():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def now_local():
    return datetime.now(bot_timezone()).replace(tzinfo=None)

# Hàm lọc ký tự đặc biệt chống sập định dạng HTML
def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def parse_expire_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            parsed = parsed.astimezone(bot_timezone()).replace(tzinfo=None)
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

def parse_int_config(key, default):
    try:
        return int(float(str(db.get_config(key, default)).strip()))
    except (TypeError, ValueError):
        return default

def find_current_expire(users_data, user_id, plan_name):
    now = now_local()
    best_expire = None
    target_plan = plan_name.upper()
    for row in users_data[1:]:
        if len(row) < 8:
            continue
        if str(row[1]).strip() != str(user_id):
            continue
        if str(row[5]).strip().upper() != "PAID":
            continue
        if str(row[3]).strip().upper() != target_plan:
            continue

        expire = parse_expire_datetime(row[7])
        if expire and expire > now and (best_expire is None or expire > best_expire):
            best_expire = expire
    return best_expire

def find_current_expire_from_orders(orders, user_id, plan_name):
    now = now_local()
    best_expire = None
    target_plan = plan_name.upper()
    for order in orders:
        if str(order.get("telegram_user_id", "")).strip() != str(user_id):
            continue
        if str(order.get("status", "")).strip().upper() != "PAID":
            continue
        if str(order.get("plan_name", "")).strip().upper() != target_plan:
            continue

        expire = parse_expire_datetime(order.get("expire_at"))
        if expire and expire > now and (best_expire is None or expire > best_expire):
            best_expire = expire
    return best_expire

async def delete_payment_message(order):
    if not order:
        return
    chat_id = order.get("payment_message_chat_id")
    message_id = order.get("payment_message_id")
    if not chat_id or not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=int(message_id))
    except Exception as e:
        print(f"⚠️ Không thể xoá tin QR đơn {order.get('order_id')}: {e}")

async def expire_pending_payment(order_code, user_id):
    order = supabase_store.get_order(order_code) if supabase_store.enabled else None
    if order and str(order.get("status", "")).upper() != "PENDING":
        return

    if supabase_store.enabled:
        supabase_store.expire_pending_order(order_code)
        await delete_payment_message(order)

    msg_timeout = t(
        user_id,
        "MSG_TIMEOUT_QR",
        "⏳ Mã QR đã hết hạn sau {minutes} phút. Vui lòng tạo đơn mới để thanh toán.",
    ).replace("\\n", "\n")
    qr_ttl_seconds = parse_int_config("QR_TTL_SECONDS", 300)
    msg_timeout = msg_timeout.replace("{minutes}", str(max(1, qr_ttl_seconds // 60)))
    kb_timeout = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    try:
        await bot.send_message(chat_id=user_id, text=msg_timeout, reply_markup=kb_timeout.as_markup(), parse_mode="HTML")
    except Exception:
        pass

# ======================================================
# 1. HÀM XỬ LÝ GIAO HÀNG (TỐI ƯU CỰC SẠCH)
# ======================================================
async def process_successful_payment(order_code: str):
    target_code = str(order_code).strip()
    if target_code in processing_orders:
        print(f"⏭ Đơn {target_code} đang được xử lý giao hàng ở luồng khác.")
        return
    processing_orders.add(target_code)
    try:
        print(f"🔄 Đang bắt đầu xử lý giao hàng cho đơn: {target_code}")

        row_index = -1
        user_id = None
        plan_name = None 
        users_data = []
        paid_orders = []

        if supabase_store.enabled:
            order = supabase_store.get_order(target_code)
            if not order:
                print(f"❌ Không tìm thấy đơn {target_code} trên Supabase để giao hàng.")
                return
            if str(order.get("status", "")).strip().upper() == "PAID":
                print(f"⚠️ Đơn {target_code} đã được xử lý trước đó.")
                return
            user_id = str(order.get("telegram_user_id", "")).strip()
            plan_name = str(order.get("plan_name", "")).strip()
            paid_orders = supabase_store.list_paid_orders_for_user(user_id, limit=200)
        else:
            db.connect() # Làm mới dữ liệu
            users_data = db.users_sheet.get_all_values()
        
            # Duyệt ngược từ dưới lên lấy đơn hàng (Siêu tốc độ)
            for i in range(len(users_data) - 1, 0, -1):
                row = users_data[i]
                if str(row[0]).strip() == target_code:
                    if len(row) > 5 and row[5].strip() == "PAID":
                        print(f"⚠️ Đơn {target_code} đã được xử lý trước đó.")
                        return
                    row_index = i + 1
                    user_id = str(row[1]).strip()
                    plan_name = str(row[3]).strip()
                    break
                
        if not user_id:
            print(f"❌ Không tìm thấy đơn {target_code} để giao hàng.")
            return

        # Tính toán hạn dùng. Nếu gia hạn sớm cùng gói, cộng tiếp từ hạn cũ.
        plan_token = str((order or {}).get("plan_token", "")).strip() if supabase_store.enabled else ""
        is_lifetime = is_lifetime_order(plan_name, plan_token) or is_lifetime_plan(plan_name)
        days_to_add = 3650 if is_lifetime else 30
        if supabase_store.enabled:
            base_date = find_current_expire_from_orders(paid_orders, user_id, plan_name) or now_local()
        else:
            base_date = find_current_expire(users_data, user_id, plan_name) or now_local()
        expire_date = (base_date + timedelta(days=days_to_add)).strftime("%Y-%m-%d %H:%M:%S")

        # Xác định ID nhóm từ Sheet (Hỗ trợ cấu hình động)
        groups_to_invite = [(normalize_chat_id(gid), gname) for gid, gname in resolve_plan_groups(plan_name, plan_token) if normalize_chat_id(gid)]

        # Tạo link mời (Giới hạn 1 người vào)
        links_msg = ""
        delivered_groups = []
        failed_groups = []
        if not groups_to_invite:
            failed_groups.append("UNMAPPED_PLAN")
            links_msg = (
                "⚠️ <i>Hệ thống chưa map được gói này với group nhận link. "
                "Admin đã được ghi nhận để kiểm tra cấu hình.</i>\n"
            )
        for gid, gname in groups_to_invite:
            try:
                # 🛡 Cố gắng Unban (Ngoại trừ Admin) để tránh lỗi Crash
                try:
                    await bot.unban_chat_member(chat_id=gid, user_id=int(user_id), only_if_banned=True)
                except Exception as unban_err:
                    if "administrator" not in str(unban_err).lower():
                        print(f"⚠️ Không thể unban user {user_id}: {unban_err}")

                invite = await bot.create_chat_invite_link(
                    chat_id=gid,
                    member_limit=1,
                    creates_join_request=False
                )
                delivered_groups.append(gname)
                links_msg += f"👉 <b>{escape_html(gname)}</b>:\n{invite.invite_link}\n\n"
                try:
                    if not is_support_group(gid):
                        await unmute_member(gid, user_id)
                except Exception as unmute_err:
                    print(f"⚠️ Không thể mở mute user {user_id} ở group {gid}: {unmute_err}")
            except Exception as e:
                failed_groups.append(gname)
                links_msg += f"👉 <b>{escape_html(gname)}</b>: <i>❌ Lỗi tạo link ({e})</i>\n\n"

        # Cập nhật trạng thái đơn
        paid_at = now_local().strftime("%Y-%m-%d %H:%M:%S")
        if supabase_store.enabled:
            supabase_store.mark_order_paid(target_code, paid_at=paid_at, expire_at=expire_date)
            if order.get("coupon_code"):
                try:
                    supabase_store.consume_coupon_for_order(order)
                except Exception as coupon_err:
                    print(f"⚠️ Không thể ghi nhận coupon cho đơn {target_code}: {coupon_err}")
            await delete_payment_message(order)
        else:
            db.users_sheet.update(f"F{row_index}:H{row_index}", [["PAID", paid_at, expire_date]])

        event_type = "delivery_failed" if failed_groups else "delivery_success"
        record_support_event(
            event_type,
            user_id,
            order_id=target_code,
            plan_name=plan_name,
            raw_data={
                "delivered_groups": delivered_groups,
                "failed_groups": failed_groups,
                "expected_group_count": len(groups_to_invite),
            },
        )

        # Gửi tin nhắn thành công
        msg_template = t(user_id, "MSG_DELIVERY", "✅ <b>THANH TOÁN THÀNH CÔNG!</b>\n\nGói: {plan}\nHạn dùng: {date}\n\nLink tham gia của bạn:\n{links}").replace("\\n", "\n")
        final_msg = msg_template.replace("{plan}", escape_html(display_plan_name(plan_name))).replace("{date}", expire_date).replace("{links}", links_msg)
        
        # Tạo nút điều hướng về UI chính bằng cơ chế mới
        kb = InlineKeyboardBuilder()
        support_error = await add_support_join_button(kb, user_id)
        if support_error:
            final_msg += support_error
        kb.row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))

        try:
            await bot.send_message(chat_id=user_id, text=final_msg, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
        except Exception as html_err:
            print(f"⚠️ LỖI HTML TỪ SHEET: {html_err}")
            await bot.send_message(chat_id=user_id, text=final_msg, reply_markup=kb.as_markup(), parse_mode=None, disable_web_page_preview=True)

    except Exception as e:
        print(f"❌ Lỗi giao hàng tổng quát: {e}")
    finally:
        processing_orders.discard(target_code)

# =====================================================
# 2. HÀM TỰ ĐỘNG CHECK TRẠNG THÁI (AUTO LOOP TỐI ƯU HÓA)
# =====================================================
async def auto_check_loop(order_code, user_id):
    str_code = str(order_code).strip()
    order = supabase_store.get_order(str_code) if supabase_store.enabled else None
    provider = str((order or {}).get("payment_provider") or "PAYOS").upper()
    ttl_key = "TRON_USDT_TTL_SECONDS" if provider == "TRON_USDT" else "NOWPAYMENTS_TTL_SECONDS" if provider == "NOWPAYMENTS" else "QR_TTL_SECONDS"
    ttl_default = 7200 if provider == "TRON_USDT" else 3600 if provider == "NOWPAYMENTS" else 300
    qr_ttl_seconds = max(60, parse_int_config(ttl_key, ttl_default))
    check_interval_seconds = max(5, parse_int_config("PAYMENT_CHECK_INTERVAL_SECONDS", 10))
    max_checks = max(1, math.ceil(qr_ttl_seconds / check_interval_seconds))
    print(f"🕵️ Bắt đầu Auto-check đơn {str_code}: tối đa {qr_ttl_seconds}s, mỗi {check_interval_seconds}s.")

    for _ in range(max_checks):
        if str_code in cancelled_orders:
            try: cancelled_orders.remove(str_code)
            except: pass
            return

        await asyncio.sleep(check_interval_seconds)

        if supabase_store.enabled:
            order = supabase_store.get_order(str_code)
            if order and str(order.get("status", "")).upper() != "PENDING":
                print(f"ℹ️ Dừng auto-check đơn {str_code} vì trạng thái hiện tại là {order.get('status')}.")
                return
        
        # Đẩy việc kiểm tra cổng thanh toán sang một luồng riêng để không kẹt Bot
        try:
            status = await asyncio.to_thread(payment_manager.get_payment_status, str_code)
        except Exception as api_err:
            print(f"⚠️ Lỗi check thanh toán: {api_err}")
            continue
        
        if status == "PAID":
            print(f"💰 Đơn {str_code} đã thanh toán! Đang giao hàng...")
            await process_successful_payment(str_code)
            return

    print(f"⌛ Đơn {str_code} hết hạn QR sau {qr_ttl_seconds}s.")
    await expire_pending_payment(str_code, user_id)


async def binance_pay_polling_worker():
    interval_seconds = max(30, parse_int_config("BINANCE_PAY_POLL_INTERVAL_SECONDS", 120))
    batch_limit = max(1, parse_int_config("BINANCE_PAY_POLL_BATCH_LIMIT", 200))
    print(f"🚀 Binance Pay polling worker khởi động: interval={interval_seconds}s batch={batch_limit}.")
    while True:
        try:
            matched_orders = await asyncio.to_thread(payment_manager.scan_pending_orders, "BINANCE_PAY")
            if matched_orders:
                print(f"💰 Binance Pay quét thấy {len(matched_orders)} đơn PAID chờ giao hàng: {', '.join(matched_orders[:10])}")
            for order_id in matched_orders[:batch_limit]:
                if cancelled_orders.__contains__(order_id):
                    continue
                await process_successful_payment(order_id)
        except Exception as exc:
            print(f"⚠️ Binance Pay polling lỗi: {exc}")
        await asyncio.sleep(interval_seconds)
