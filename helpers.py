from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from bot_instance import bot, is_spamming

ADMIN_ID = 887869657
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
        msg = db.get_config("MSG_MAINTENANCE", "🛠 <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\\n\\nAdmin đang nâng cấp hệ thống. Bạn vui lòng quay lại sau ít phút nhé!").replace("\\n", "\n")
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
    try: return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except: return f"{amount}Đ"

def get_main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    p_1m_fmt = format_currency(db.get_config('PRICE_1_MONTH', '999'))
    p_life_fmt = format_currency(db.get_config('PRICE_LIFETIME', '999'))
    
    btn_full_life = db.get_config("BTN_FULL_LIFE", "🔥 SVIP+ TRỌN ĐỜI (FULL NHÓM)")
    btn_full_1m = db.get_config("BTN_FULL_1M", "💎 SVIP+ 1 THÁNG (FULL NHÓM)")
    
    kb.row(InlineKeyboardButton(text=f"{btn_full_life} • {p_life_fmt}", callback_data="view_full_life"))
    kb.row(InlineKeyboardButton(text=f"{btn_full_1m} • {p_1m_fmt}", callback_data="view_full_1m"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G1', 'G1')}", callback_data="group_1"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G2', 'G2')}", callback_data="group_2"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G3', 'G3')}", callback_data="group_3"))
    kb.row(InlineKeyboardButton(text=f"📂 {db.get_config('BTN_G4', 'G4')}", callback_data="group_4"))
    kb.row(
        InlineKeyboardButton(text=db.get_config("BTN_ME", "👤 Tài Khoản"), callback_data="my_info"),
        InlineKeyboardButton(text=db.get_config("BTN_POLICY", "📜 Quy Định"), callback_data="policy"),
        InlineKeyboardButton(text=db.get_config("BTN_SUPPORT", "💬 Hỗ Trợ"), callback_data="support_info")
    )
    return kb.as_markup()

async def smart_display(event, text, reply_markup, img=None):
    msg_updating = db.get_config("MSG_UPDATING", "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>")
    final_text = str(text).strip() if text else msg_updating
    final_img = str(img).strip() if img else "AgACAgUAAxkBAAIBNmn-9LFS5hvH-CaHRDmbB4nkwwb3AAIbEGsbTyj4V8xDVvbbF-TTAQADAgADeQADOwQ"

    try:
        if isinstance(event, Message):
            await event.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            if event.message.photo:
                await event.message.edit_media(media=InputMediaPhoto(media=final_img, caption=final_text, parse_mode="HTML"), reply_markup=reply_markup)
            else:
                await event.message.delete()
                await event.message.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        if "parse entities" in str(e).lower() or "tag" in str(e).lower():
            fallback_text = f"⚠️ Lỗi thẻ HTML trên Sheet.\\n\\nNội dung gốc:\\n{final_text}"
            if isinstance(event, Message): await event.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)
            else: await event.message.answer_photo(photo=final_img, caption=fallback_text, reply_markup=reply_markup, parse_mode=None)