import time
import asyncio
import urllib.parse
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from payment import payos_manager
from processor import process_successful_payment, auto_check_loop, cancelled_orders
from bot_instance import bot

from helpers import check_protection, format_currency, smart_display, cleanup_welcome
from modules.mod_general import send_welcome_messages

router = Router()

BANK_NAMES = {
    "970422": "MB Bank", "970415": "VietinBank", "970436": "Vietcombank",
    "970418": "BIDV", "970423": "TPBank", "970407": "Techcombank",
    "970432": "VPBank", "970416": "ACB", "970405": "Agribank"
}

@router.callback_query(F.data.startswith("group_"))
async def view_group_detail(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    num = callback.data.split("_")[1]
    desc = db.get_config(f"DESC_G{num}", "Đang cập nhật...").replace("\\n", "\n")
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{db.get_config('BTN_BUY_1M', '💎 VIP 1 THÁNG')} • {format_currency(db.get_config(f'PRICE_G{num}_1M', '50000'))}", callback_data=f"buy_G{num}_1m"))
    kb.row(InlineKeyboardButton(text=f"{db.get_config('BTN_BUY_LIFE', '👑 VIP TRỌN ĐỜI')} • {format_currency(db.get_config(f'PRICE_G{num}_LIFE', '149000'))}", callback_data=f"buy_G{num}_life"))
    kb.row(InlineKeyboardButton(text=f"{db.get_config('BTN_FULL_LIFE', '🔥 SVIP+ TRỌN ĐỜI')} • {format_currency(db.get_config('PRICE_LIFETIME', '999'))}", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
    await smart_display(callback, desc, kb.as_markup(), img=db.get_config(f"IMG_G{num}"))

@router.callback_query(F.data.startswith("buy_") | F.data.startswith("view_full_") | F.data.startswith("upsell_"))
async def process_buy_request(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    if "upsell_full" in callback.data:
        plan_name = db.get_config("PLAN_UPSELL_FULL", "SVIP+ Trọn Đời (Nâng cấp)")
        amount = max(0, int(db.get_config("PRICE_LIFETIME", "999")) - int(db.get_config("PRICE_1_MONTH", "999")))
    elif "upsell_G" in callback.data:
        num = callback.data.split("_")[1][1:]
        plan_name = f"{db.get_config('PLAN_UPSELL_G', 'VIP Trọn Đời (Nâng cấp)')} - {db.get_config(f'BTN_G{num}', f'Nhóm {num}')}"
        amount = max(0, int(db.get_config(f"PRICE_G{num}_LIFE", "149000")) - int(db.get_config(f"PRICE_G{num}_1M", "50000")))
    elif "full" in callback.data:
        plan_name = db.get_config("PLAN_FULL_1M" if "1m" in callback.data else "PLAN_FULL_LIFE", "SVIP+ Full Nhóm")
        amount = int(db.get_config("PRICE_1_MONTH" if "1m" in callback.data else "PRICE_LIFETIME", "999"))
    else:
        parts = callback.data.split("_")
        num, type_p = parts[1][1:], parts[2].upper()
        plan_name = f"{db.get_config('PLAN_G_1M' if type_p == '1M' else 'PLAN_G_LIFE', 'VIP')} - {db.get_config(f'BTN_G{num}')}"
        amount = int(db.get_config(f'PRICE_G{num}_{type_p}', "50000"))

    msg_wait = await callback.message.answer(db.get_config("MSG_WAIT_QR", "⏳ Đang tạo mã QR..."))
    order_id = int(time.time())
    description = f"PRIVE{order_id}"[-20:]
    
    pay_data = payos_manager.create_payment_link(order_id, amount, description)
    
    if pay_data:
        db.users_sheet.append_row([order_id, str(callback.from_user.id), callback.from_user.full_name, plan_name, amount, "PENDING"])
        
        raw_bin = str(pay_data.get('bin', ''))
        bank_display = BANK_NAMES.get(raw_bin, f"Bank ({raw_bin})")
        actual_stk = pay_data.get('accountNumber', 'N/A')
        qr_url = f"https://img.vietqr.io/image/{raw_bin}-{actual_stk}-print.png?amount={amount}&addInfo={description}&accountName={urllib.parse.quote(pay_data['accountName'])}"
        safe_name = str(pay_data['accountName']).replace('&', 'và').replace('<', '').replace('>', '')
        
        caption = db.get_config("MSG_BILL_TEMPLATE", "Mã Đơn: {desc}\nSố tiền: {amount}").replace("\\n", "\n")
        caption = caption.replace("{plan}", str(plan_name)).replace("{amount}", format_currency(amount)).replace("{bank}", bank_display).replace("{name}", safe_name).replace("{stk}", actual_stk).replace("{desc}", description)
        
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=db.get_config("BTN_CHECK_PAYMENT", "🔄 Đã chuyển khoản"), callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text=db.get_config("BTN_CANCEL_ORDER", "❌ Hủy"), callback_data=f"cancel_order_{order_id}"))
        
        try: await bot.send_photo(chat_id=callback.message.chat.id, photo=qr_url, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        except: 
            kb.row(InlineKeyboardButton(text=db.get_config("BTN_VIEW_QR", "🖼 Xem QR"), url=qr_url))
            await bot.send_message(chat_id=callback.message.chat.id, text=caption, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
            
        try: await msg_wait.delete()
        except: pass
        try: await callback.message.delete()
        except: pass
            
        asyncio.create_task(auto_check_loop(order_id, callback.from_user.id))
    else: await msg_wait.edit_text(db.get_config("MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))

@router.callback_query(F.data.startswith("check_"))
async def manual_check_payment(callback: CallbackQuery):
    if not await check_protection(callback): return
    order_id = callback.data.split("_")[1]
    
    if payos_manager.get_payment_status(order_id) == "PAID":
        await callback.answer(db.get_config("ALERT_PAID_SUCCESS", "✅ Giao dịch thành công!"), show_alert=True)
        await process_successful_payment(order_id)
        try: await callback.message.delete()
        except: pass
    else: await callback.answer(db.get_config("ALERT_NOT_PAID", "⏳ Hệ thống chưa nhận được tiền!").replace("\\n", "\n"), show_alert=True)

@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    cancelled_orders.add(str(callback.data.split("_")[-1])) 
    await callback.message.delete()
    await callback.answer(db.get_config("ALERT_CANCELLED", "🚫 Đã hủy đơn."), show_alert=True)
    await send_welcome_messages(callback)