import time
import asyncio
import urllib.parse
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from payment import payos_manager
from processor import expire_pending_payment, parse_int_config, process_successful_payment, auto_check_loop, cancelled_orders
from bot_instance import bot
from supabase_store import supabase_store

from helpers import check_protection, format_currency, smart_display, cleanup_welcome, safe_delete_private_message
from i18n import get_user_language, t
from modules.mod_engine import render_page
from sale_utils import format_price_label, get_price, sale_banner
from renewal_utils import build_early_renew_offer, is_early_renew_enabled

router = Router()

BANK_NAMES = {
    "970422": "MB Bank", "970415": "VietinBank", "970436": "Vietcombank",
    "970418": "BIDV", "970423": "TPBank", "970407": "Techcombank",
    "970432": "VPBank", "970416": "ACB", "970405": "Agribank"
}

# 🛡 BIẾN LƯU TRỮ CHỐNG SPAM
user_cooldowns = {}

def safe_int(value_str):
    """Hàm thông minh: Tự động loại bỏ dấu chấm, dấu phẩy, chữ Đ để chống crash ValueError"""
    try:
        clean_str = str(value_str).replace('Đ', '').replace('đ', '').strip()
        if clean_str.endswith(".0") or clean_str.endswith(",0"):
            return int(float(clean_str.replace(",", ".")))
        if "." in clean_str and "," not in clean_str and len(clean_str.rsplit(".", 1)[-1]) == 3:
            clean_str = clean_str.replace(".", "")
        elif "," in clean_str and "." not in clean_str and len(clean_str.rsplit(",", 1)[-1]) == 3:
            clean_str = clean_str.replace(",", "")
        else:
            clean_str = clean_str.replace(",", ".")
        return int(float(clean_str))
    except Exception:
        return 999  # Trả về giá mặc định nếu lỗi

def sale_text_for_price(price_key, default=0):
    banner = sale_banner(price_key, default)
    return f"\n\n{banner}" if banner else ""

def create_pending_order(
    order_id,
    user_id,
    full_name,
    plan_name,
    amount,
    sale_id="",
    original_amount=None,
    coupon_code="",
    coupon_discount_percent=0,
    coupon_discount_amount=0,
):
    if supabase_store.enabled:
        return supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=user_id,
            full_name=full_name,
            plan_name=plan_name,
            amount=amount,
            sale_id=sale_id,
            original_amount=original_amount or amount,
            coupon_code=coupon_code,
            coupon_discount_percent=coupon_discount_percent,
            coupon_discount_amount=coupon_discount_amount,
        )

    db.users_sheet.append_row([
        order_id,
        str(user_id),
        full_name,
        plan_name,
        amount,
        "PENDING",
        "",
        "",
        sale_id,
        original_amount or amount,
    ])


def buy_data_from_plan_key(plan_key):
    key = str(plan_key or "").strip().upper()
    if key == "FULL_1M":
        return "buy_full_1m"
    if key == "FULL_LIFE":
        return "buy_full_life"
    if key.startswith("G") and key.endswith("_1M"):
        return f"buy_{key[:-3]}_1m"
    if key.startswith("G") and key.endswith("_LIFE"):
        return f"buy_{key[:-5]}_life"
    return ""


def config_text(user_id, key, default=""):
    return t(user_id, key, default) if user_id else db.get_config(key, default)


def resolve_purchase_offer(data, user_id=None):
    sale_info = None
    original_amount = None
    price_key = ""
    data = data.replace("confirm_", "buy_")

    if "upsell_full" in data:
        plan_name = config_text(user_id, "PLAN_UPSELL_FULL", "SVIP+ Lifetime (Upgrade)" if get_user_language(user_id) == "en" else "SVIP+ Trọn Đời (Nâng cấp)")
        price_life, sale_life = get_price("PRICE_SVIP_LIFE", "999")
        price_1m, sale_1m = get_price("PRICE_SVIP_30D", "999")
        amount = max(0, price_life - price_1m)
        sale_info = sale_life or sale_1m
        original_amount = max(0, safe_int(db.get_config("PRICE_SVIP_LIFE", "999")) - safe_int(db.get_config("PRICE_SVIP_30D", "999")))
    elif "upsell_G" in data:
        num = data.split("_")[1][1:]
        plan_name = f"{config_text(user_id, 'PLAN_UPSELL_G', 'VIP Lifetime (Upgrade)' if get_user_language(user_id) == 'en' else 'VIP Trọn Đời (Nâng cấp)')} - {config_text(user_id, f'BTN_G{num}', f'Group {num}' if get_user_language(user_id) == 'en' else f'Nhóm {num}')}"
        price_life, sale_life = get_price(f"PRICE_G{num}_LIFE", "149000")
        price_1m, sale_1m = get_price(f"PRICE_G{num}_1M", "50000")
        amount = max(0, price_life - price_1m)
        sale_info = sale_life or sale_1m
        original_amount = max(0, safe_int(db.get_config(f"PRICE_G{num}_LIFE", "149000")) - safe_int(db.get_config(f"PRICE_G{num}_1M", "50000")))
    elif "full" in data:
        is_1m = "1m" in data
        plan_name = config_text(user_id, "PLAN_FULL_1M" if is_1m else "PLAN_FULL_LIFE", "SVIP+ All Groups")
        price_key = "PRICE_SVIP_30D" if is_1m else "PRICE_SVIP_LIFE"
        amount, sale_info = get_price(price_key, "999")
        original_amount = safe_int(db.get_config(price_key, "999"))
    else:
        parts = data.split("_")
        num, type_p = parts[1][1:], parts[2].upper()
        plan_name = f"{config_text(user_id, 'PLAN_G_1M' if type_p == '1M' else 'PLAN_G_LIFE', 'VIP')} - {config_text(user_id, f'BTN_G{num}', f'Group {num}' if get_user_language(user_id) == 'en' else f'Nhóm {num}')}"
        price_key = f"PRICE_G{num}_{type_p}"
        amount, sale_info = get_price(price_key, "50000")
        original_amount = safe_int(db.get_config(price_key, "50000"))

    return {
        "plan_name": plan_name,
        "price_key": price_key,
        "amount": amount,
        "sale_info": sale_info,
        "original_amount": original_amount or amount,
    }


def sale_caption(sale_info, original_amount, amount):
    if not sale_info:
        return ""
    text = f"\n🔥 <b>SALE:</b> <s>{format_currency(original_amount)}</s> → <b>{format_currency(amount)}</b> (-{sale_info['discount_percent']}%)"
    if sale_info["remaining_slots"] is not None:
        remaining_after_order = max(0, sale_info["remaining_slots"] - 1)
        text += f"\n🎟 Slot sale còn lại sau đơn này: {remaining_after_order}/{sale_info['slot_limit']}"
    if sale_info["countdown"]:
        text += f"\n⏳ Sale còn: {sale_info['countdown']}"
    return text


def english_vietqr_payment_enabled():
    return str(db.get_config("EN_VIETQR_PAYMENT_ENABLED", "OFF")).strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


async def block_english_vietqr_if_needed(callback):
    if get_user_language(callback.from_user.id) != "en" or english_vietqr_payment_enabled():
        return False

    text = t(
        callback.from_user.id,
        "MSG_EN_VIETQR_UNAVAILABLE",
        "<b>VietQR payment is currently supported only for Vietnam bank transfers.</b>\\n\\n"
        "Please switch to Vietnamese to pay by VietQR, or contact admin to pay by PayPal or crypto.",
    ).replace("\\n", "\n")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text=t(callback.from_user.id, "BTN_SWITCH_TO_VIETNAMESE", "🇻🇳 Switch to Vietnamese"),
        callback_data="set_lang|vi",
    ))
    kb.row(InlineKeyboardButton(
        text=t(callback.from_user.id, "BTN_CONTACT_ADMIN_PAYMENT", "Contact admin"),
        callback_data="nav:support_page",
    ))
    await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()
    return True

async def send_payment_bill(callback, order_id, plan_name, amount, description, pay_data, extra_caption=""):
    raw_bin = str(pay_data.get('bin', ''))
    bank_display = BANK_NAMES.get(raw_bin, f"Bank ({raw_bin})")
    actual_stk = pay_data.get('accountNumber', 'N/A')
    qr_url = f"https://img.vietqr.io/image/{raw_bin}-{actual_stk}-print.png?amount={amount}&addInfo={description}&accountName={urllib.parse.quote(pay_data['accountName'])}"
    safe_name = str(pay_data['accountName']).replace('&', 'và').replace('<', '').replace('>', '')
    
    caption = t(callback.from_user.id, "MSG_BILL_TEMPLATE", "Mã Đơn: {desc}\nSố tiền: {amount}").replace("\\n", "\n")
    caption = caption.replace("{plan}", str(plan_name)).replace("{amount}", format_currency(amount)).replace("{bank}", bank_display).replace("{name}", safe_name).replace("{stk}", actual_stk).replace("{desc}", description)
    caption += extra_caption
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CHECK_PAYMENT", "🔄 Đã chuyển khoản"), callback_data=f"check_{order_id}"))
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CANCEL_ORDER", "❌ Hủy"), callback_data=f"cancel_order_{order_id}"))
    
    try:
        sent = await bot.send_photo(chat_id=callback.message.chat.id, photo=qr_url, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
    except:
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_VIEW_QR", "🖼 Xem QR"), url=qr_url))
        sent = await bot.send_message(chat_id=callback.message.chat.id, text=caption, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
    if supabase_store.enabled and sent:
        try:
            supabase_store.set_payment_message(order_id, sent.chat.id, sent.message_id)
        except Exception as e:
            print(f"⚠️ Không lưu được payment message cho đơn {order_id}: {e}")
    return sent

@router.callback_query(F.data.startswith("renew_"))
async def process_early_renew(callback: CallbackQuery):
    if not await check_protection(callback): return
    if await block_english_vietqr_if_needed(callback): return

    if not is_early_renew_enabled():
        await callback.answer(t(callback.from_user.id, "ALERT_EARLY_RENEW_OFF", "Ưu đãi gia hạn sớm đang tắt. Vui lòng gia hạn theo giá thường."), show_alert=True)
        await render_page(callback, "main_menu")
        return

    row_index = None
    row = None
    if callback.data.startswith("renew_order_"):
        source_order_id = callback.data.replace("renew_order_", "", 1).strip()
        if supabase_store.enabled:
            order = supabase_store.get_order(source_order_id)
            row = supabase_store.order_to_sheet_row(order)
            row_index = source_order_id
    else:
        try:
            row_index = int(callback.data.split("_", 1)[1])
        except Exception:
            await callback.answer(t(callback.from_user.id, "ALERT_RENEW_CODE_INVALID", "Mã gia hạn không hợp lệ."), show_alert=True)
            return

        users_data = db.users_sheet.get_all_values()
        if row_index < 2 or row_index > len(users_data):
            await callback.answer(t(callback.from_user.id, "ALERT_RENEW_OFFER_INVALID", "Ưu đãi gia hạn không còn hợp lệ."), show_alert=True)
            return
        row = users_data[row_index - 1]

    if not row:
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_OFFER_INVALID", "Ưu đãi gia hạn không còn hợp lệ."), show_alert=True)
        return

    if len(row) < 8 or str(row[1]).strip() != str(callback.from_user.id):
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_NOT_OWNER", "Ưu đãi này không thuộc tài khoản của bạn."), show_alert=True)
        return

    offer = build_early_renew_offer(row, row_index)
    if not offer:
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_EXPIRED", "Ưu đãi gia hạn sớm đã hết hạn hoặc không còn hợp lệ."), show_alert=True)
        return

    user_id = callback.from_user.id
    current_time = time.time()
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 15:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Thao tác quá nhanh! Vui lòng chờ 15s."), show_alert=True)
        return
    user_cooldowns[user_id] = current_time

    msg_wait = await callback.message.answer(t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR..."))
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    amount = offer["renew_price"]

    pay_data = payos_manager.create_payment_link(order_id, amount, description)
    if not pay_data:
        await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
        return

    create_pending_order(
        order_id=order_id,
        user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        plan_name=offer["plan_name"],
        amount=amount,
        sale_id=offer["offer_id"],
        original_amount=offer["original_price"],
    )

    extra_caption = (
        f"\n🔥 <b>ƯU ĐÃI GIA HẠN SỚM:</b> <s>{format_currency(offer['original_price'])}</s> → "
        f"<b>{format_currency(amount)}</b> (-{offer['discount_percent']}%)"
        f"\n⏳ Ưu đãi hết khi VIP hết hạn: <code>{offer['expire_at'].strftime('%d/%m/%Y %H:%M:%S')}</code>"
    )
    await send_payment_bill(callback, order_id, offer["plan_name"], amount, description, pay_data, extra_caption)
    await safe_delete_private_message(msg_wait)
    await safe_delete_private_message(callback.message)
    asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))

@router.callback_query(F.data.startswith("group_"))
async def view_group_detail(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    num = callback.data.split("_")[1]
    desc = t(callback.from_user.id, f"DESC_G{num}", "Updating..." if get_user_language(callback.from_user.id) == "en" else "Đang cập nhật...").replace("\\n", "\n")
    desc += sale_text_for_price(f"PRICE_G{num}_1M", "50000")
    desc += sale_text_for_price(f"PRICE_G{num}_LIFE", "149000")
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{t(callback.from_user.id, 'BTN_BUY_1M', '💎 VIP 30 NGÀY')} • {format_price_label(f'PRICE_G{num}_1M', '50000')}", callback_data=f"buy_G{num}_1m"))
    kb.row(InlineKeyboardButton(text=f"{t(callback.from_user.id, 'BTN_BUY_LIFE', '👑 VIP TRỌN ĐỜI')} • {format_price_label(f'PRICE_G{num}_LIFE', '149000')}", callback_data=f"buy_G{num}_life"))
    # Nút dẫn sang trang SVIP Page
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_VIEW_SVIP_PAGE", "🌟 XEM GÓI SVIP+"), callback_data="view_svip_page"))
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
    
    await smart_display(callback, desc, kb.as_markup(), img=db.get_config(f"IMG_G{num}"))

# ==========================================
# 🌟 TRANG CHI TIẾT GÓI SVIP (GIỮ NGUYÊN CODE CỦA BẠN - ĐÃ FIX LỖI VÒNG LẶP)
# ==========================================
# 🛠 FIX 1: Loại bỏ "buy_full_life" và "buy_full_1m" khỏi F.data.in_ để không tranh sóng với hàm tạo QR
@router.callback_query(F.data.in_(["view_svip_page", "view_full_life", "view_full_1m"]))
async def show_svip_page(callback: CallbackQuery):
    """Hiển thị trang giới thiệu SVIP với ảnh cover và mô tả"""
    if callback.data.startswith("confirm_"):
        return

    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    img_url = db.get_config("IMG_SVIP_PAGE", "https://via.placeholder.com/800x450.png?text=SVIP+PRO")
    description = t(callback.from_user.id, "TXT_SVIP_DESCRIPTION", "🔥 <b>ALL-IN SVIP+ ACCESS</b> 🔥\n\n✅ Access all private groups.\n✅ New content updated daily.\n✅ Priority support.\n\n👇 <i>Choose a plan below:</i>" if get_user_language(callback.from_user.id) == "en" else "🔥 <b>ĐẶC QUYỀN SVIP+ TRỌN BỘ</b> 🔥\n\n✅ Truy cập toàn bộ 4 Group kín vĩnh viễn.\n✅ Cập nhật nội dung mới mỗi ngày.\n✅ Hỗ trợ ưu tiên 24/7.\n\n👇 <i>Chọn gói đăng ký bên dưới:</i>").replace("\\n", "\n")
    description += sale_text_for_price("PRICE_SVIP_LIFE", "3000")
    description += sale_text_for_price("PRICE_SVIP_30D", "2000")
    
    btn_life_text = t(callback.from_user.id, "BTN_BUY_SVIP_LIFE", "🔥 MUA TRỌN ĐỜI")
    btn_30d_text = t(callback.from_user.id, "BTN_BUY_SVIP_30D", "💎 MUA 30 NGÀY")
    
    btn_back_text = t(callback.from_user.id, "BTN_BACK", "🔙 Quay lại")

    kb = InlineKeyboardBuilder()
    # TRUYỀN TÍN HIỆU BUY ĐỂ GỌI HÀM TẠO MÃ QR BÊN DƯỚI
    kb.row(InlineKeyboardButton(text=f"{btn_life_text} • {format_price_label('PRICE_SVIP_LIFE', '3000')}", callback_data="buy_full_life"))
    kb.row(InlineKeyboardButton(text=f"{btn_30d_text} • {format_price_label('PRICE_SVIP_30D', '2000')}", callback_data="buy_full_1m"))
    kb.row(InlineKeyboardButton(text=btn_back_text, callback_data="back_main"))

    await smart_display(callback, description, kb.as_markup(), img=img_url)

# ==========================================
# 💳 XỬ LÝ THANH TOÁN & CHỐNG SPAM
# ==========================================
@router.callback_query(F.data.startswith("confirm_") | F.data.startswith("buy_") | F.data.startswith("upsell_"))
async def process_buy_request(callback: CallbackQuery):
    if not await check_protection(callback): return
    if await block_english_vietqr_if_needed(callback): return
    
    # 🛡 LOGIC CHỐNG SPAM (15 GIÂY)
    user_id = callback.from_user.id
    current_time = time.time()
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 15:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Thao tác quá nhanh! Vui lòng chờ 15s."), show_alert=True)
        return
    user_cooldowns[user_id] = current_time

    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    offer = resolve_purchase_offer(callback.data, callback.from_user.id)
    plan_name = offer["plan_name"]
    amount = offer["amount"]
    sale_info = offer["sale_info"]
    original_amount = offer["original_amount"]

    msg_wait = await callback.message.answer(t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR..."))
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    
    pay_data = payos_manager.create_payment_link(order_id, amount, description)
    
    if pay_data:
        sale_id = sale_info["sale_id"] if sale_info else ""
        create_pending_order(
            order_id=order_id,
            user_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            plan_name=plan_name,
            amount=amount,
            sale_id=sale_id,
            original_amount=original_amount or amount,
        )
        extra_caption = sale_caption(sale_info, original_amount, amount)

        await send_payment_bill(callback, order_id, plan_name, amount, description, pay_data, extra_caption)
            
        await safe_delete_private_message(msg_wait)
        await safe_delete_private_message(callback.message)
            
        asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))
    else: await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))


@router.callback_query(F.data.startswith("couponbuy|"))
async def process_coupon_buy_request(callback: CallbackQuery):
    if not await check_protection(callback):
        return
    if await block_english_vietqr_if_needed(callback):
        return

    try:
        _, code, plan_key = callback.data.split("|", 2)
    except ValueError:
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_INVALID", "Mã giảm giá không hợp lệ."), show_alert=True)
        return

    from modules.mod_coupon import (
        coupon_discount_percent,
        coupon_matches_plan,
        coupon_type,
        find_coupon,
        normalize_code,
        validate_coupon_base,
    )

    code = normalize_code(code)
    _, _, _, coupon = find_coupon(code)
    valid, reason = validate_coupon_base(coupon, callback.from_user.id)
    if not valid:
        await callback.answer(reason, show_alert=True)
        return
    if coupon_type(coupon) != "DISCOUNT" or not coupon_matches_plan(coupon, plan_key):
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_NOT_APPLICABLE", "Mã này không áp dụng cho gói đã chọn."), show_alert=True)
        return

    user_id = callback.from_user.id
    current_time = time.time()
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 15:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Thao tác quá nhanh! Vui lòng chờ 15s."), show_alert=True)
        return
    user_cooldowns[user_id] = current_time

    buy_data = buy_data_from_plan_key(plan_key)
    if not buy_data:
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_PLAN_INVALID", "Gói áp dụng không hợp lệ."), show_alert=True)
        return

    offer = resolve_purchase_offer(buy_data, callback.from_user.id)
    percent = coupon_discount_percent(coupon)
    before_coupon = offer["amount"]
    discount_amount = int(round(before_coupon * percent / 100))
    amount = max(0, before_coupon - discount_amount)
    if amount <= 0:
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_ZERO_AMOUNT", "Mã giảm giá làm đơn về 0đ. Hãy dùng coupon kích hoạt thay vì coupon giảm giá."), show_alert=True)
        return

    msg_wait = await callback.message.answer(t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR..."))
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    pay_data = payos_manager.create_payment_link(order_id, amount, description)

    if not pay_data:
        await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
        return

    sale_info = offer["sale_info"]
    sale_id = sale_info["sale_id"] if sale_info else ""
    create_pending_order(
        order_id=order_id,
        user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        plan_name=offer["plan_name"],
        amount=amount,
        sale_id=sale_id,
        original_amount=offer["original_amount"],
        coupon_code=code,
        coupon_discount_percent=percent,
        coupon_discount_amount=discount_amount,
    )
    extra_caption = sale_caption(sale_info, offer["original_amount"], before_coupon)
    extra_caption += f"\n🎟 <b>COUPON {code}:</b> -{percent}% (-{format_currency(discount_amount)})"
    extra_caption += f"\n💳 <b>Cần thanh toán:</b> {format_currency(amount)}"

    await send_payment_bill(callback, order_id, offer["plan_name"], amount, description, pay_data, extra_caption)
    await safe_delete_private_message(msg_wait)
    await safe_delete_private_message(callback.message)
    asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))

@router.callback_query(F.data.startswith("check_"))
async def manual_check_payment(callback: CallbackQuery):
    if not await check_protection(callback): return
    order_id = callback.data.split("_")[1]

    qr_ttl_seconds = max(60, parse_int_config("QR_TTL_SECONDS", 300))
    try:
        if int(time.time()) - int(order_id) > qr_ttl_seconds:
            await callback.answer(t(callback.from_user.id, "ALERT_QR_EXPIRED", "⏳ Mã QR đã hết hạn. Vui lòng tạo đơn mới."), show_alert=True)
            await expire_pending_payment(order_id, callback.from_user.id)
            await safe_delete_private_message(callback.message)
            return
    except ValueError:
        pass
    
    if payos_manager.get_payment_status(order_id) == "PAID":
        await callback.answer(t(callback.from_user.id, "ALERT_PAID_SUCCESS", "✅ Giao dịch thành công!"), show_alert=True)
        await process_successful_payment(order_id)
        await safe_delete_private_message(callback.message)
    else: await callback.answer(t(callback.from_user.id, "ALERT_NOT_PAID", "⏳ Hệ thống chưa nhận được tiền!").replace("\\n", "\n"), show_alert=True)

@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = str(callback.data.split("_")[-1])
    cancelled_orders.add(order_id)
    if supabase_store.enabled:
        try:
            supabase_store.update_order_status(order_id, "CANCELLED")
        except Exception as e:
            print(f"⚠️ Không thể cập nhật CANCELLED cho đơn {order_id}: {e}")
    await safe_delete_private_message(callback.message)
    await callback.answer(t(callback.from_user.id, "ALERT_CANCELLED", "🚫 Đã hủy đơn."), show_alert=True)
    await render_page(callback, "main_menu")
