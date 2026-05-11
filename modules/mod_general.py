import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from bot_instance import bot
from helpers import ADMIN_ID, check_protection, cleanup_welcome, get_main_menu_keyboard, smart_display, user_welcome_msgs

router = Router()

async def send_welcome_messages(event):
    db.reload_config(force=True)
    user_id = event.from_user.id
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id

    await cleanup_welcome(user_id, chat_id)
    welcome_text = db.get_config("MSG_START", "👑 CHÀO MỪNG BẠN!").replace("\\n", "\n")
    img_start = db.get_config("IMG_START", "AgACAgUAAxkBAAMNaf3xkPP5Pr9JZtCsKMI4b1G0fC0AAmwRaxsHpelX2z3c8IQ6Xh8BAAMCAAN5AAM7BA")
    privilege_text = db.get_config("MSG_PRIVILEGE", "💎 Chọn gói dịch vụ:").replace("\\n", "\n")

    try:
        if img_start and len(str(img_start)) > 10: msg1 = await bot.send_photo(chat_id=chat_id, photo=img_start, caption=welcome_text, parse_mode="HTML")
        else: msg1 = await bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
        user_welcome_msgs[user_id] = msg1.message_id
        await asyncio.sleep(0.5)
        
        if isinstance(event, Message): await event.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
        else: await event.message.answer(text=privilege_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    except Exception as e:
        if "parse entities" in str(e).lower() or "tag" in str(e).lower():
            await bot.send_message(chat_id=chat_id, text="⚠️ Lỗi thẻ HTML trên Sheet MSG_START.", parse_mode="HTML")

@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if message.from_user.id == ADMIN_ID:
        db.reload_config(force=True)
        await message.reply(db.get_config("MSG_RELOAD_DONE", "🔄 Đã ép tải lại từ Sheet!"))

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
    
    support_text = db.get_config("MSG_SUPPORT", "👨‍💻 HỖ TRỢ").replace("\\n", "\n")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=db.get_config("BTN_CONTACT_ADMIN", "💬 Nhắn tin"), url=db.get_config("URL_ADMIN", "https://t.me/thamtucu")))
    kb.row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
    await smart_display(event, support_text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))

@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    all_data = db.users_sheet.get_all_values()
    my_plans = [row for row in all_data if row[1] == user_id and row[5] == "PAID"]
    
    text = db.get_config("MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    if not my_plans: text += db.get_config("MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        for p in my_plans: 
            text += db.get_config("MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", str(p[3])).replace("{date}", str(p[7]))
            
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME"))

@router.callback_query(F.data == "policy")
async def view_policy(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    text = db.get_config("MSG_POLICY", "Chính sách đang cập nhật...").replace("\\n", "\n")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
    await smart_display(callback, text, kb.as_markup(), img=db.get_config("IMG_POLICY"))

@router.message(F.photo)
async def get_file_id(message: Message):
    if message.from_user.id == ADMIN_ID: await message.reply(f"<code>{message.photo[-1].file_id}</code>")