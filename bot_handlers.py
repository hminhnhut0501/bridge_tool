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

# BỘ NHỚ LƯU TRỮ ID TIN NHẮN SỐ 1 ĐỂ DỌN DẸP
user_welcome_msgs = {}

async def cleanup_welcome(user_id, chat_id):
    """Hàm dọn dẹp tin nhắn MSG_START mồ côi"""
    if user_id in user_welcome_msgs:
        try:
            await bot.delete_message(chat_id, user_welcome_msgs[user_id])
        except: pass
        del user_welcome_msgs[user_id]

async def check_protection(event):
    user_id = event.from_user.id
    if MAINTENANCE_MODE and user_id != ADMIN_ID:
        msg = "🛠 <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nVui lòng quay lại sau ít phút!"
        if isinstance(event, Message): await event.answer(msg)
        else: await event.answer("Bot đang bảo trì...", show_alert=True)
        return False
    if is_spamming(user_id) and user_id != ADMIN_ID:
        if isinstance(event, CallbackQuery): await event.answer("⚠️ Thao tác quá nhanh!", show_alert=True)
        return False
    return True

# --- HÀM PHỤ TRỢ ĐỊNH DẠNG TIỀN TỀ ---
def format_currency(amount):
    """Biến 30000 thành 30.000Đ"""
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except:
        return f"{amount}Đ"

def get_main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    
    # Lấy giá trị thô từ Sheets
    p_1m_raw = db.get_config('PRICE_1_MONTH', '999')
    p_life_raw = db.get_config('PRICE_LIFETIME', '999')
    
    # Định dạng hiển thị đẹp
    p_1m_fmt = format_currency(p_1m_raw)
    p_life_fmt = format_currency(p_life_raw)
    
    kb.row(InlineKeyboardButton(text=f"🔥 ALL ACCESS VIP TRỌN ĐỜI • {p_life_fmt} 🔥", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text=f"💎 DÙNG THỬ VIP 1 THÁNG • {p_1m_fmt} 💎", callback_data="view_full_1m"))
    
    kb.row(
        InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G1', 'G1')}", callback_data="group_1")
    )
    kb.row(
        InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G2', 'G2')}", callback_data="group_2")
    )
    kb.row(
        InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G3', 'G3')}", callback_data="group_3")
    )
    kb.row(
        InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G4', 'G4')}", callback_data="group_4")
    )
    kb.row(
        InlineKeyboardButton(text="👤 Tài Khoản", callback_data="my_info"),
        InlineKeyboardButton(text="📜 Quy Định", callback_data="policy"),
        InlineKeyboardButton(text="💬 Hỗ Trợ", callback_data="support_info")
    )
    return kb.as_markup()

# --- HÀM HIỂN THỊ SMART (CÓ CƠ CHẾ CỨU HỘ HTML) ---
async def smart_display(event, text, reply_markup, img=None):
    final_text = str(text).strip() if text else ""
    if not final_text:
        final_text = "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>"
    
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
        error_msg = str(e)
        print(f"❌ Error Display: {error_msg}")
        if "parse entities" in error_msg.lower() or "tag" in error_msg.lower():
            # CỨU HỘ: Gửi chữ thô (bỏ HTML) và cảnh báo
            fallback_text = f"⚠️ Lỗi định dạng thẻ HTML trên Sheet (quên đóng thẻ <b> hoặc <i>).\n\nNội dung gốc:\n{final_text}"
            if isinstance(event, Message):
                await event.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)
            else:
                await event.message.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)

# --- HÀM GỬI 2 TIN NHẮN TÁCH BIỆT (CÓ CỨU HỘ HTML) ---
async def send_welcome_messages(event):
    db.reload_config(force=True)
    user_id = event.from_user.id
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

    await cleanup_welcome(user_id, chat_id)

    welcome_text = db.get_config("MSG_START", "👑 CHÀO MỪNG BẠN ĐẾN VỚI PRIVE+ VIP!")
    img_start = db.get_config("IMG_START", "AgACAgUAAxkBAAMNaf3xkPP5Pr9JZtCsKMI4b1G0fC0AAmwRaxsHpelX2z3c8IQ6Xh8BAAMCAAN5AAM7BA")
    privilege_text = db.get_config(
        "MSG_PRIVILEGE", 
        "💎 <b>ĐẶC QUYỀN HỘI VIÊN VIP:</b>\n"
        "• Update nội dung siêu tốc mỗi ngày.\n"
        "• Tự động duyệt vào nhóm sau 5 giây.\n"
        "• Bảo mật, ẩn danh tuyệt đối.\n\n"
        "👇 <b>Chọn gói dịch vụ của bạn ở menu bên dưới:</b>"
    )

    try:
        # Gửi tin 1
        if img_start and len(str(img_start)) > 10:
            msg1 = await bot.send_photo(chat_id=chat_id, photo=img_start, caption=welcome_text, parse_mode="HTML")
        else:
            msg1 = await bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
        
        user_welcome_msgs[user_id] = msg1.message_id
        await asyncio.sleep(0.5)
        
        # Gửi tin 2
        if isinstance(event, Message):
            await event.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
        else:
            await event.message.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Lỗi gửi tin nhắn chào mừng: {error_msg}")
        if "parse entities" in error_msg.lower() or "tag" in error_msg.lower():
            # CỨU HỘ: Báo lỗi trực tiếp cho Admin dễ sửa
            warning = (
                "⚠️ <b>HỆ THỐNG PHÁT HIỆN LỖI ĐÁNH MÁY:</b>\n"
                "Bạn đang mở một thẻ HTML (như <code>&lt;b&gt;</code>) trên Google Sheets nhưng quên viết thẻ đóng <code>&lt;/b&gt;</code>.\n\n"
                "<i>Vui lòng lên Google Sheets kiểm tra lại các cột MSG_START và MSG_PRIVILEGE nhé!</i>"
            )
            await bot.send_message(chat_id=chat_id, text=warning, parse_mode="HTML")
            
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if message.from_user.id == ADMIN_ID:
        db.reload_config(force=True)
        await message.reply("🔄 Đã ép tải lại toàn bộ nội dung mới nhất từ Google Sheets!")

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
    
    # --- SỬA DÒNG NÀY ĐỂ LẤY TỪ SHEET ---
    support_text = db.get_config("MSG_SUPPORT", "👨‍💻 <b>HỖ TRỢ</b>\n\nNội dung hỗ trợ chưa được cấu hình trên Sheet.")
    
    kb = InlineKeyboardBuilder()
    # Bạn cũng có thể lấy link Telegram Admin từ Sheet nếu muốn
    admin_url = db.get_config("URL_ADMIN", "https://t.me/thamtucu")
    
    kb.row(InlineKeyboardButton(text="💬 Nhắn tin cho Admin", url=admin_url))
    kb.row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main"))
    
    await smart_display(event, support_text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))

@router.callback_query(F.data.startswith("group_"))
async def view_group_detail(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    num = callback.data.split("_")[1]
    name = db.get_config(f"BTN_G{num}", f"Nhóm {num}")
    desc = db.get_config(f"DESC_G{num}", "Đang cập nhật...")
    img = db.get_config(f"IMG_G{num}")
    
    p_1m_raw = db.get_config(f"PRICE_G{num}_1M", "50000")
    p_life_raw = db.get_config(f"PRICE_G{num}_LIFE", "149000")
    p_full_life_raw = db.get_config("PRICE_LIFETIME", "999")
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"💎 DÙNG THỬ 1 THÁNG • {format_currency(p_1m_raw)} 💎", callback_data=f"buy_G{num}_1m"))
    kb.row(InlineKeyboardButton(text=f"👑 VIP TRỌN ĐỜI • {format_currency(p_life_raw)} 👑", callback_data=f"buy_G{num}_life"))
    kb.row(InlineKeyboardButton(text=f"🔥 ALL ACCESS VIP TRỌN ĐỜI • {format_currency(p_full_life_raw)} 🔥", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main"))
    await smart_display(callback, desc, kb.as_markup(), img)

@router.callback_query(F.data.startswith("buy_") | F.data.startswith("view_full_"))
async def process_buy_request(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    if "full" in callback.data:
        plan_name = "Trọn bộ 4 Nhóm (1 Tháng)" if "1m" in callback.data else "Trọn bộ 4 Nhóm (Vĩnh viễn)"
        amount = int(db.get_config("PRICE_1_MONTH" if "1m" in callback.data else "PRICE_LIFETIME"))
    else:
        parts = callback.data.split("_")
        num, type_p = parts[1][1:], parts[2].upper()
        plan_name = f"Lẻ {db.get_config(f'BTN_G{num}')} ({'1 Tháng' if '1m' in callback.data else 'Vĩnh viễn'})"
        amount = int(db.get_config(f'PRICE_G{num}_{type_p}', 50000 if type_p == "1M" else 149000))

    msg_wait = await callback.message.answer("⏳ Đang tạo mã QR...")
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    
    pay_data = payos_manager.create_payment_link(order_id, amount, description)
    
    if pay_data:
        db.users_sheet.append_row([order_id, str(callback.from_user.id), callback.from_user.full_name, plan_name, amount, "PENDING"])
        
        raw_bin = str(pay_data.get('bin', ''))
        bank_display = BANK_NAMES.get(raw_bin, f"Bank ({raw_bin})")
        actual_stk = pay_data.get('accountNumber', 'N/A')
        
        qr_url = f"https://img.vietqr.io/image/{raw_bin}-{actual_stk}-print.png?amount={amount}&addInfo={description}&accountName={urllib.parse.quote(pay_data['accountName'])}"
        
        # --- TẠO BIẾN AMOUNT_FMT Ở ĐÂY ĐỂ TRÁNH LỖI NAMEERROR ---
        amount_fmt = format_currency(amount)
        
        # Khử ký tự đặc biệt trong tên tài khoản để chống lỗi HTML
        safe_account_name = str(pay_data['accountName']).replace('&', 'và').replace('<', '').replace('>', '')
        
        caption = (
            f"🏦 <b>XÁC NHẬN THANH TOÁN (DUYỆT TỰ ĐỘNG)</b>\n"
            f"────────────────────\n"
            f"📦 Đặc quyền: <b>{plan_name}</b>\n"
            f"💰 Số tiền: <b>{amount_fmt}</b>\n\n"
            f"🏛 Ngân hàng: <b>{bank_display}</b>\n"
            f"👤 Chủ TK: <b>{safe_account_name}</b>\n"
            f"💳 Số TK: <code>{actual_stk}</code>\n"
            f"📝 Nội dung: <code>{description}</code>\n"
            f"────────────────────\n"
            f"⚡️ <i>Hệ thống tự động phát link mời sau khi nhận được tiền.</i>\n"
            f"👉 Nhấp vào <b>Số TK</b> và <b>Nội dung</b> để Copy!"
        )
        
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🔄 Tôi đã chuyển khoản", callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text="❌ Hủy đơn này", callback_data=f"cancel_order_{order_id}"))
        
        # VÒNG AN TOÀN TRÁNH TREO BOT KHI QR LỖI
        try:
            # Thử gửi bằng ảnh QR
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=qr_url, 
                caption=caption, 
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Lỗi tải ảnh QR từ VietQR: {e} -> Chuyển sang gửi dạng Text")
            # Nếu Telegram từ chối tải ảnh, thêm nút "Xem mã QR" và gửi bằng Text
            kb.row(InlineKeyboardButton(text="🖼 Bấm vào đây để xem mã QR", url=qr_url))
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=caption,
                reply_markup=kb.as_markup(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
        # Dọn dẹp tin nhắn chờ
        try: await msg_wait.delete()
        except: pass
        try: await callback.message.delete()
        except: pass
            
        asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))
    else:
        await msg_wait.edit_text("❌ Lỗi cổng thanh toán. Vui lòng thử lại sau!")

@router.callback_query(F.data.startswith("check_"))
async def manual_check_payment(callback: CallbackQuery):
    if not await check_protection(callback): return
    
    order_id = callback.data.split("_")[1]
    
    status = payos_manager.get_payment_status(order_id)
    
    if status == "PAID":
        await callback.answer("✅ Giao dịch thành công! Đang lấy link nhóm cho bạn...", show_alert=True)
        await process_successful_payment(order_id)
        try: await callback.message.delete()
        except: pass
    else:
        alert_msg = "⏳ Hệ thống chưa nhận được tiền.\n\nNếu bạn vừa chuyển khoản thành công, xin vui lòng đợi thêm 1-2 phút để ngân hàng xử lý nhé!"
        await callback.answer(alert_msg, show_alert=True)

@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = callback.data.split("_")[-1]
    cancelled_orders.add(str(order_id)) 
    await callback.message.delete()
    await callback.answer("🚫 Đã hủy đơn.", show_alert=True)
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
    text = "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n"
    if not my_plans: text += "❌ Bạn chưa có gói VIP nào."
    else:
        for p in my_plans: text += f"🎁 Gói: <b>{p[3]}</b>\n📅 Hạn: <code>{p[7]}</code>\n────────────────────\n"
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main")).as_markup()
    await smart_display(event, text, kb, img=db.get_config("IMG_ME"))

@router.callback_query(F.data == "policy")
async def view_policy(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    text = db.get_config("MSG_POLICY", "Chính sách đang cập nhật...")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main")).as_markup()
    await smart_display(callback, text, kb, img=db.get_config("IMG_POLICY"))

@router.message(F.photo)
async def get_file_id(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply(f"<code>{message.photo[-1].file_id}</code>")