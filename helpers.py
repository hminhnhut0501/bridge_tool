from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
import re
from html import unescape
from database import db
from bot_instance import is_spamming

ADMIN_ID = 887869657  # Nhớ thay bằng ID Telegram của bạn nếu chưa đổi nhé
user_welcome_msgs = {}

def strip_html_tags(text):
    return unescape(re.sub(r"<[^>]*>", "", str(text or "")))

async def cleanup_welcome(user_id, chat_id):
    """Giữ tương thích code cũ, không xoá tin nhắn trong group."""
    user_welcome_msgs.pop(user_id, None)

async def safe_delete_private_message(message):
    """Chỉ xoá tin trong private chat, tuyệt đối không xoá message trong group."""
    if not message or getattr(message.chat, "type", None) != "private":
        return False

    try:
        await message.delete()
        return True
    except Exception:
        return False

async def check_protection(event):
    """Lớp khiên bảo vệ: Chống Spam click và Khóa Bot khi Bảo trì"""
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
        alert_spam = db.get_config("ALERT_SPAM", "⏳ Vui lòng thao tác chậm lại!")
        if isinstance(event, CallbackQuery):
            await event.answer(alert_spam, show_alert=False)
        return False
        
    return True

def format_currency(amount):
    """Định dạng tiền tệ VNĐ (VD: 3000 -> 3.000Đ)"""
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except:
        return f"{amount}Đ"

async def smart_display(event, text, reply_markup, img=None):
    """Hàm xuất giao diện thông minh (Giữ lại để phục vụ cho trang /me)"""
    msg_updating = db.get_config("MSG_UPDATING", "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>")
    final_text = str(text).strip() if text else msg_updating
    final_img = str(img).strip() if img else None

    try:
        if isinstance(event, Message):
            if final_img and len(final_img) > 10:
                await event.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await event.answer(text=final_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await safe_delete_private_message(event.message)
            
            if final_img and len(final_img) > 10:
                await event.message.answer_photo(photo=final_img, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await event.message.answer(text=final_text, reply_markup=reply_markup, parse_mode="HTML")
            await event.answer()
                
    except TelegramBadRequest as e:
        if "parse entities" in str(e).lower() or "can't parse entities" in str(e).lower() or "tag" in str(e).lower():
            fallback_text = strip_html_tags(final_text)
            if isinstance(event, Message):
                await event.answer(fallback_text, reply_markup=reply_markup, parse_mode=None)
            else:
                await event.message.answer(fallback_text, reply_markup=reply_markup, parse_mode=None)
                await event.answer()
        else:
            print(f"❌ Lỗi xuất giao diện: {e}")
    except Exception as e:
        print(f"❌ Lỗi xuất giao diện: {e}")
