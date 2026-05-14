import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from bot_instance import bot
from helpers import ADMIN_ID, check_protection, cleanup_welcome, smart_display
from modules.mod_engine import build_dynamic_keyboard, page_exists, render_page, send_with_html_fallback 
from sale_utils import build_sale_announcement
from scheduler import check_expirations_professional

router = Router()

# [1] HÀM CŨ DỰ PHÒNG CHỐNG LỖI IMPORT
async def send_welcome_messages(event):
    await cmd_start(event)

# [2] LỆNH RELOAD
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if message.from_user.id == ADMIN_ID: 
        db.reload_config(force=True)
        await message.reply(db.get_config("MSG_RELOAD_DONE", "🔄 Đã nạp lại toàn bộ dữ liệu & Giao diện từ Sheet!"))
    else:
        await message.reply("⚠️ Lệnh này chỉ dành cho Admin.")

@router.message(Command("check_expiry"))
async def cmd_check_expiry(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⚠️ Lệnh này chỉ dành cho Admin.")
        return

    await message.reply("⏳ Đang quét hạn dùng ngay bây giờ...")
    await check_expirations_professional()
    await message.reply("✅ Đã chạy xong một vòng quét hạn dùng. Xem log server để biết dòng nào đã gửi/kick hoặc bị bỏ qua.")

async def send_sale_announcement(message: Message):
    enabled = str(db.get_config("SALE_ANNOUNCE_ENABLED", "ON")).strip().upper()
    if enabled in ["OFF", "FALSE", "NO", "0", "TẮT", "TAT"]:
        return

    text = build_sale_announcement()
    if not text:
        return

    img = str(db.get_config("IMG_SALE_BANNER", "")).strip()
    layout = db.get_config("SALE_ANNOUNCE_BUTTONS", "").replace("\\n", "\n")
    reply_markup = build_dynamic_keyboard(layout) if layout.strip() else None

    try:
        if img and len(img) > 10:
            await send_with_html_fallback(message, photo=img, text=text, reply_markup=reply_markup)
        else:
            await send_with_html_fallback(message, text=text, reply_markup=reply_markup)
    except Exception as e:
        print(f"❌ Lỗi gửi thông báo sale: {e}")

# [3] LỆNH START & QUAY LẠI MENU CHÍNH
@router.message(CommandStart())
async def cmd_start(message: Message):
    if not await check_protection(message): return
    db.reload_config(force=True)
    await cleanup_welcome(message.from_user.id, message.chat.id)
    await send_sale_announcement(message)
    await render_page(message, "main_menu")

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not await check_protection(callback): return
    await render_page(callback, "main_menu")

# [4] TRANG QUY ĐỊNH (PHỤC HỒI CODE CŨ + BỔ SUNG LỆNH)
@router.message(Command("policy"))
@router.callback_query(F.data == "policy")
@router.callback_query(F.data == "policy_page")
@router.callback_query(F.data == "nav:policy_page")
async def view_policy(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    # Ưu tiên gọi giao diện mới từ Sheet. Nếu Sheet chưa tạo, lùi về dùng code cũ của bạn
    try:
        if not page_exists("policy_page"):
            db.reload_config(force=True)
        if page_exists("policy_page"):
            rendered = await render_page(event, "policy_page")
            if rendered:
                return
    except Exception as e:
        print(f"❌ Lỗi render policy_page: {e}")

    try:
        text = db.get_config("MSG_POLICY", "Chính sách đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_POLICY"))
    except Exception as e:
        print(f"❌ Lỗi fallback /policy: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer("Không thể mở trang quy định lúc này.", show_alert=True)

# [5] TRANG HỖ TRỢ (PHỤC HỒI CODE CŨ + BỔ SUNG LỆNH)
@router.message(Command("support"))
@router.callback_query(F.data == "support_info")
@router.callback_query(F.data == "nav:support_page")
async def view_support(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    # Ưu tiên gọi giao diện mới từ Sheet. Nếu Sheet chưa tạo, lùi về dùng code cũ của bạn
    try:
        if not page_exists("support_page"):
            db.reload_config(force=True)
        if page_exists("support_page"):
            rendered = await render_page(event, "support_page")
            if rendered:
                return
    except Exception as e:
        print(f"❌ Lỗi render support_page: {e}")

    try:
        text = db.get_config("MSG_SUPPORT", "Hỗ trợ đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))
    except Exception as e:
        print(f"❌ Lỗi fallback /support: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer("Không thể mở trang hỗ trợ lúc này.", show_alert=True)

# [6] TRANG THÔNG TIN TÀI KHOẢN (/ME)
@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    db.connect()
    all_data = db.users_sheet.get_all_values()
    
    my_plans = [row for row in all_data if len(row) > 7 and str(row[1]) == user_id and row[5] == "PAID"]
    
    text = db.get_config("MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    if not my_plans: 
        text += db.get_config("MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        for p in my_plans: 
            text += db.get_config("MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", str(p[3])).replace("{date}", str(p[7]))
            
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME", ""))

# [7] CÔNG CỤ ADMIN: LẤY FILE_ID CỦA ẢNH
@router.message(F.photo)
async def get_file_id(message: Message):
    if message.from_user.id == ADMIN_ID: 
        await message.reply(f"<code>{message.photo[-1].file_id}</code>")
