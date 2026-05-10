import time
import asyncio
import urllib.parse
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from payment import payos_manager
from processor import process_successful_payment, auto_check_loop, cancelled_orders
from bot_instance import bot, is_spamming, MAINTENANCE_MODE

router = Router()
ADMIN_ID = 887869657 

BANK_NAMES = {
    "970422": "MB Bank", "970415": "VietinBank", "970436": "Vietcombank",
    "970418": "BIDV", "970423": "TPBank", "970407": "Techcombank",
    "970432": "VPBank", "970416": "ACB", "970405": "Agribank"
}

user_welcome_msgs = {}

async def cleanup_welcome(user_id, chat_id):
    if user_id in user_welcome_msgs:
        try:
            await bot.delete_message(chat_id, user_welcome_msgs[user_id])
        except: pass
        del user_welcome_msgs[user_id]

async def check_protection(event):
    user_id = event.from_user.id
    maintenance_status = str(db.get_config("MAINTENANCE_MODE", "OFF")).strip().upper()
    
    if maintenance_status in ["ON", "TRUE", "CÓ", "YES"] and user_id != ADMIN_ID:
        msg = db.get_config("MSG_MAINTENANCE", "🛠 <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nAdmin đang nâng cấp hệ thống. Bạn vui lòng quay lại sau ít phút nhé!").replace("\\n", "\n")
        alert_main = db.get_config("ALERT_MAINTENANCE", "🛠 Bot đang bảo trì, vui lòng quay lại sau...")
        if isinstance(event, Message): 
            await event.answer(msg, parse_mode="HTML")
        else: 
            await event.answer(alert_main, show_alert=True)
        return False
        
    if is_spamming(user_id) and user_id != ADMIN_ID:
        alert_spam = db.get_config("ALERT_SPAM", "⚠️ Thao tác quá nhanh! Vui lòng chậm lại.")
        if isinstance(event, CallbackQuery): 
            await event.answer(alert_spam, show_alert=True)
        return False
        
    return True

def format_currency(amount):
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except:
        return f"{amount}Đ"

def get_main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    
    p_1m_raw = db.get_config('PRICE_1_MONTH', '999')
    p_life_raw = db.get_config('PRICE_LIFETIME', '999')
    p_1m_fmt = format_currency(p_1m_raw)
    p_life_fmt = format_currency(p_life_raw)
    
    btn_full_life = db.get_config("BTN_FULL_LIFE", "🔥 SVIP+ TRỌN ĐỜI (FULL NHÓM)")
    btn_full_1m = db.get_config("BTN_FULL_1M", "💎 SVIP+ 1 THÁNG (FULL NHÓM)")
    btn_me = db.get_config("BTN_ME", "👤 Tài Khoản")
    btn_policy = db.get_config("BTN_POLICY", "📜 Quy Định")
    btn_support = db.get_config("BTN_SUPPORT", "💬 Hỗ Trợ")
    
    kb.row(InlineKeyboardButton(text=f"{btn_full_life} • {p_life_fmt}", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text=f"{btn_full_1m} • {p_1m_fmt}", callback_data="view_full_1m"))
    
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G1', 'G1')}", callback_data="group_1"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G2', 'G2')}", callback_data="group_2"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G3', 'G3')}", callback_data="group_3"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G4', 'G4')}", callback_data="group_4"))
    
    kb.row(
        InlineKeyboardButton(text=btn_me, callback_data="my_info"),
        InlineKeyboardButton(text=btn_policy, callback_data="policy"),
        InlineKeyboardButton(text=btn_support, callback_data="support_info")
    )
    return kb.as_markup()

async def smart_display(event, text, reply_markup, img=None):
    msg_updating = db.get_config("MSG_UPDATING", "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>")
    final_text = str(text).strip() if text else msg_updating
    final_img = str(img).strip() if img else ""
    if not final_img or len(final_img) < 10:
        final_img = "AgACAgUAAxkBAAIBNmn-9LFS5hvH-CaHRDmbB4nkwwb3AAIbEGsbTyj4V8xDVvbbF-TTAQADAgADeQADOwQ"

    try:
        if isinstance(event, Message):
            await event.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            message = event.message
            if message.photo:
                await message.edit_media(media=InputMediaPhoto(media=final_img, caption=final_text, parse_mode="HTML"), reply_markup=reply_markup)
            else:
                await message.delete()
                await message.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" in str(e).lower() or "tag" in str(e).lower():
            msg_err = db.get_config("MSG_HTML_ERROR", "⚠️ Lỗi định dạng thẻ HTML trên Sheet (quên đóng thẻ <b> hoặc <i>).\n\nNội dung gốc:\n")
            fallback_text = f"{msg_err}{final_text}"
            if isinstance(event, Message):
                await event.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)
            else:
                await event.message.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)

async def send_welcome_messages(event):
    db.reload_config(force=True)
    user_id = event.from_user.id
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

    await cleanup_welcome(user_id, chat_id)

    welcome_text = db.get_config("MSG_START", "👑 CHÀO MỪNG BẠN ĐẾN VỚI PRIVE+ VIP!").replace("\\n", "\n")
    img_start = db.get_config("IMG_START", "AgACAgUAAxkBAAMNaf3xkPP5Pr9JZtCsKMI4b1G0fC0AAmwRaxsHpelX2z3c8IQ6Xh8BAAMCAAN5AAM7BA")
    privilege_text = db.get_config("MSG_PRIVILEGE", "💎 <b>ĐẶC QUYỀN HỘI VIÊN VIP:</b>\n👇 <b>Chọn gói dịch vụ của bạn ở menu bên dưới:</b>").replace("\\n", "\n")

    try:
        if img_start and len(str(img_start)) > 10:
            msg1 = await bot.send_photo(chat_id=chat_id, photo=img_start, caption=welcome_text, parse_mode="HTML")
        else:
            msg1 = await bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
        
        user_welcome_msgs[user_id] = msg1.message_id
        await asyncio.sleep(0.5)
        
        if isinstance(event, Message):
            await event.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
        else:
            await event.message.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
            
    except Exception as e:
        if "parse entities" in str(e).lower() or "tag" in str(e).lower():
            warning = db.get_config("MSG_ADMIN_HTML_ERR", "⚠️ <b>HỆ THỐNG PHÁT HIỆN LỖI ĐÁNH MÁY:</b>\nLỗi thẻ HTML trên Sheet MSG_START hoặc MSG_PRIVILEGE.").replace("\\n", "\n")
            await bot.send_message(chat_id=chat_id, text=warning, parse_mode="HTML")
            
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if message.from_user.id == ADMIN_ID:
        db.reload_config(force=True)
        msg = db.get_config("MSG_RELOAD_DONE", "🔄 Đã ép tải lại toàn bộ nội dung mới nhất từ Google Sheets!")
        await message.reply(msg)

@router.message(CommandStart())
async def cmd_start(message: Message):
    if not await check_protection(message): return
    await send_welcome_messages(message)

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not await check_protection(callback): return
    try: await callback.message.delete()
    except: pass
    await send_welcome_messages(callback)

@router.message(Command("support"))
@router.callback_query(F.data == "support_info")
async def cmd_support(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    support_text = db.get_config("MSG_SUPPORT", "👨‍💻 <b>HỖ TRỢ</b>\n────────────────────\nNếu bạn gặp vấn đề, vui lòng liên hệ Admin.").replace("\\n", "\n")
    btn_contact = db.get_config("BTN_CONTACT_ADMIN", "💬 Nhắn tin cho Admin")
    btn_back = db.get_config("BTN_BACK", "🔙 Quay lại")
    admin_url = db.get_config("URL_ADMIN", "https://t.me/thamtucu")
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=btn_contact, url=admin_url))
    kb.row(InlineKeyboardButton(text=btn_back, callback_data="back_main"))
    
    await smart_display(event, support_text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))

@router.callback_query(F.data.startswith("group_"))
async def view_group_detail(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    num = callback.data.split("_")[1]
    desc = db.get_config(f"DESC_G{num}", "Đang cập nhật...").replace("\\n", "\n")
    img = db.get_config(f"IMG_G{num}")
    
    p_1m_raw = db.get_config(f"PRICE_G{num}_1M", "50000")
    p_life_raw = db.get_config(f"PRICE_G{num}_LIFE", "149000")
    p_full_life_raw = db.get_config("PRICE_LIFETIME", "999")
    
    btn_buy_1m = db.get_config("BTN_BUY_1M", "💎 VIP 1 THÁNG")
    btn_buy_life = db.get_config("BTN_BUY_LIFE", "👑 VIP TRỌN ĐỜI")
    btn_full_life = db.get_config("BTN_FULL_LIFE", "🔥 SVIP+ TRỌN ĐỜI (FULL NHÓM)")
    btn_back = db.get_config("BTN_BACK", "🔙 Quay lại")
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{btn_buy_1m} • {format_currency(p_1m_raw)}", callback_data=f"buy_G{num}_1m"))
    kb.row(InlineKeyboardButton(text=f"{btn_buy_life} • {format_currency(p_life_raw)}", callback_data=f"buy_G{num}_life"))
    kb.row(InlineKeyboardButton(text=f"{btn_full_life} • {format_currency(p_full_life_raw)}", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text=btn_back, callback_data="back_main"))
    await smart_display(callback, desc, kb.as_markup(), img)

# ĐÃ MỞ RỘNG ĐỂ BẮT SỰ KIỆN UP-SALE TỪ SCHEDULER
@router.callback_query(F.data.startswith("buy_") | F.data.startswith("view_full_") | F.data.startswith("upsell_"))
async def process_buy_request(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    # --- PHÂN LOẠI CÁC LOẠI ĐƠN HÀNG (BAO GỒM UP-SALE GIẢM GIÁ) ---
    if "upsell_full" in callback.data:
        plan_name = db.get_config("PLAN_UPSELL_FULL", "SVIP+ Trọn Đời (Nâng cấp từ 1 Tháng)")
        p_life = int(db.get_config("PRICE_LIFETIME", "999"))
        p_1m = int(db.get_config("PRICE_1_MONTH", "999"))
        amount = max(0, p_life - p_1m)
        
    elif "upsell_G" in callback.data:
        num = callback.data.split("_")[1][1:] # G1 -> 1
        group_name = db.get_config(f"BTN_G{num}", f"Nhóm {num}")
        prefix = db.get_config("PLAN_UPSELL_G", "VIP Trọn Đời (Nâng cấp)")
        plan_name = f"{prefix} - {group_name}"
        p_life = int(db.get_config(f"PRICE_G{num}_LIFE", "149000"))
        p_1m = int(db.get_config(f"PRICE_G{num}_1M", "50000"))
        amount = max(0, p_life - p_1m)
        
    elif "full" in callback.data:
        if "1m" in callback.data:
            plan_name = db.get_config("PLAN_FULL_1M", "SVIP+ 1 Tháng (Full Nhóm)")
            amount = int(db.get_config("PRICE_1_MONTH", "999"))
        else:
            plan_name = db.get_config("PLAN_FULL_LIFE", "SVIP+ Trọn Đời (Full Nhóm)")
            amount = int(db.get_config("PRICE_LIFETIME", "999"))
            
    else:
        parts = callback.data.split("_")
        num, type_p = parts[1][1:], parts[2].upper()
        group_name = db.get_config(f"BTN_G{num}", f"Nhóm {num}")
        
        if type_p == "1M":
            prefix = db.get_config("PLAN_G_1M", "VIP 1 Tháng")
            amount = int(db.get_config(f'PRICE_G{num}_1M', "50000"))
        else:
            prefix = db.get_config("PLAN_G_LIFE", "VIP Trọn Đời")
            amount = int(db.get_config(f'PRICE_G{num}_LIFE', "149000"))
            
        plan_name = f"{prefix} - {group_name}"

    msg_wait_qr = db.get_config("MSG_WAIT_QR", "⏳ Đang tạo mã QR...")
    msg_wait = await callback.message.answer(msg_wait_qr)
    
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    
    pay_data = payos_manager.create_payment_link(order_id, amount, description)
    
    if pay_data:
        db.users_sheet.append_row([order_id, str(callback.from_user.id), callback.from_user.full_name, plan_name, amount, "PENDING"])
        
        raw_bin = str(pay_data.get('bin', ''))
        bank_display = BANK_NAMES.get(raw_bin, f"Bank ({raw_bin})")
        actual_stk = pay_data.get('accountNumber', 'N/A')
        
        qr_url = f"https://img.vietqr.io/image/{raw_bin}-{actual_stk}-print.png?amount={amount}&addInfo={description}&accountName={urllib.parse.quote(pay_data['accountName'])}"
        
        amount_fmt = format_currency(amount)
        safe_account_name = str(pay_data['accountName']).replace('&', 'và').replace('<', '').replace('>', '')
        
        # --- TEMPLATE BILL THANH TOÁN ---
        bill_template = db.get_config("MSG_BILL_TEMPLATE", (
            "🏦 <b>XÁC NHẬN THANH TOÁN (DUYỆT TỰ ĐỘNG)</b>\n"
            "────────────────────\n"
            "📦 Đặc quyền: <b>{plan}</b>\n"
            "💰 Số tiền: <b>{amount}</b>\n\n"
            "🏛 Ngân hàng: <b>{bank}</b>\n"
            "👤 Chủ TK: <b>{name}</b>\n"
            "💳 Số TK: <code>{stk}</code>\n"
            "📝 Nội dung: <code>{desc}</code>\n"
            "────────────────────\n"
            "⚡️ <i>Hệ thống tự động phát link mời sau khi nhận được tiền.</i>\n"
            "👉 Nhấp vào <b>Số TK</b> và <b>Nội dung</b> để Copy!"
        )).replace("\\n", "\n")
        
        caption = bill_template.replace("{plan}", str(plan_name))
        caption = caption.replace("{amount}", str(amount_fmt))
        caption = caption.replace("{bank}", str(bank_display))
        caption = caption.replace("{name}", str(safe_account_name))
        caption = caption.replace("{stk}", str(actual_stk))
        caption = caption.replace("{desc}", str(description))
        
        btn_check = db.get_config("BTN_CHECK_PAYMENT", "🔄 Tôi đã chuyển khoản")
        btn_cancel = db.get_config("BTN_CANCEL_ORDER", "❌ Hủy đơn này")
        btn_view_qr = db.get_config("BTN_VIEW_QR", "🖼 Bấm vào đây để xem mã QR")
        
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=btn_check, callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text=btn_cancel, callback_data=f"cancel_order_{order_id}"))
        
        try:
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=qr_url, 
                caption=caption, 
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Lỗi tải ảnh QR: {e} -> Text mode")
            kb.row(InlineKeyboardButton(text=btn_view_qr, url=qr_url))
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=caption,
                reply_markup=kb.as_markup(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
        try: await msg_wait.delete()
        except: pass
        try: await callback.message.delete()
        except: pass
            
        asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))
    else:
        msg_err = db.get_config("MSG_QR_ERROR", "❌ Lỗi cổng thanh toán. Vui lòng thử lại sau!")
        await msg_wait.edit_text(msg_err)

@router.callback_query(F.data.startswith("check_"))
async def manual_check_payment(callback: CallbackQuery):
    if not await check_protection(callback): return
    
    order_id = callback.data.split("_")[1]
    status = payos_manager.get_payment_status(order_id)
    
    if status == "PAID":
        alert_paid = db.get_config("ALERT_PAID_SUCCESS", "✅ Giao dịch thành công! Đang lấy link nhóm cho bạn...")
        await callback.answer(alert_paid, show_alert=True)
        await process_successful_payment(order_id)
        try: await callback.message.delete()
        except: pass
    else:
        alert_not_paid = db.get_config("ALERT_NOT_PAID", "⏳ Hệ thống chưa nhận được tiền.\n\nNếu bạn vừa chuyển khoản thành công, xin vui lòng đợi thêm 1-2 phút nhé!").replace("\\n", "\n")
        await callback.answer(alert_not_paid, show_alert=True)

@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = callback.data.split("_")[-1]
    cancelled_orders.add(str(order_id)) 
    await callback.message.delete()
    
    alert_cancel = db.get_config("ALERT_CANCELLED", "🚫 Đã hủy đơn.")
    await callback.answer(alert_cancel, show_alert=True)
    await send_welcome_messages(callback)

@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    all_data = db.users_sheet.get_all_values()
    my_plans = [row for row in all_data if row[1] == user_id and row[5] == "PAID"]
    
    msg_me_title = db.get_config("MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    msg_me_empty = db.get_config("MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    msg_me_item = db.get_config("MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n────────────────────\n").replace("\\n", "\n")
    
    text = msg_me_title
    if not my_plans: 
        text += msg_me_empty
    else:
        for p in my_plans: 
            item = msg_me_item.replace("{plan}", str(p[3])).replace("{date}", str(p[7]))
            text += item
        
    btn_back = db.get_config("BTN_BACK", "🔙 Quay lại")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=btn_back, callback_data="back_main")).as_markup()
    await smart_display(event, text, kb, img=db.get_config("IMG_ME"))

@router.callback_query(F.data == "policy")
async def view_policy(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    text = db.get_config("MSG_POLICY", "Chính sách đang cập nhật...").replace("\\n", "\n")
    btn_back = db.get_config("BTN_BACK", "🔙 Quay lại")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=btn_back, callback_data="back_main")).as_markup()
    await smart_display(callback, text, kb, img=db.get_config("IMG_POLICY"))

@router.message(F.photo)
async def get_file_id(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply(f"<code>{message.photo[-1].file_id}</code>")