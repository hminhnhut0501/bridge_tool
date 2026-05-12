import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from bot_instance import bot
from helpers import ADMIN_ID, check_protection, cleanup_welcome, smart_display
from modules.mod_engine import render_page 

router = Router()

@router.message(Command("reload"))
async def cmd_reload(message: Message):
    # Tạm thời bỏ comment dòng if bên dưới để test xem Bot có nhận lệnh không
    # if message.from_user.id == ADMIN_ID: 
    db.reload_config(force=True)
    await message.reply("🔄 Đã nạp lại dữ liệu từ Sheet!")

@router.message(CommandStart())
async def cmd_start(message: Message):
    if not await check_protection(message): return
    db.reload_config(force=True)
    await cleanup_welcome(message.from_user.id, message.chat.id)
    await render_page(message, "main_menu")

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not await check_protection(callback): return
    await render_page(callback, "main_menu")

# ==========================================
# TRANG DUY NHẤT CẦN CODE: THÔNG TIN TÀI KHOẢN (/ME)
# ==========================================
@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    all_data = db.users_sheet.get_all_values()
    my_plans = [row for row in all_data if len(row) > 7 and row[1] == user_id and row[5] == "PAID"]
    
    text = db.get_config("MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    if not my_plans: 
        text += db.get_config("MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        for p in my_plans: 
            text += db.get_config("MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", str(p[3])).replace("{date}", str(p[7]))
            
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME", ""))

# Lấy ID của Ảnh gửi cho Admin
@router.message(F.photo)
async def get_file_id(message: Message):
    if message.from_user.id == ADMIN_ID: 
        await message.reply(f"<code>{message.photo[-1].file_id}</code>")

# ==========================================
# CÁC LỆNH MENU ĐIỀU HƯỚNG BỔ SUNG
# ==========================================
@router.message(Command("support"))
async def cmd_support_telegram(message: Message):
    """Bắt lệnh /support từ Menu xanh của Telegram và xuất trang từ Sheet"""
    if not await check_protection(message): return
    await render_page(message, "support_page")

@router.message(Command("policy"))
async def cmd_policy_telegram(message: Message):
    """Bổ sung thêm lệnh /policy nếu khách gõ tay"""
    if not await check_protection(message): return
    await render_page(message, "policy_page")