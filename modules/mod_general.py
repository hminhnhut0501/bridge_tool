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

# ==========================================
# LỆNH RELOAD: CẬP NHẬT DỮ LIỆU TỪ SHEET
# ==========================================
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    # Bạn có thể mở khóa dòng if bên dưới nếu muốn bảo mật chỉ Admin được reload
    if message.from_user.id == ADMIN_ID: 
        db.reload_config(force=True)
        await message.reply(db.get_config("MSG_RELOAD_DONE", "🔄 Đã nạp lại toàn bộ dữ liệu & Giao diện từ Sheet!"))
    else:
        await message.reply("⚠️ Lệnh này chỉ dành cho Admin.")

# ==========================================
# LỆNH START & QUAY LẠI MENU CHÍNH
# ==========================================
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
# XỬ LÝ NÚT QUY ĐỊNH (POLICY)
# ==========================================
@router.message(Command("policy"))
@router.callback_query(F.data == "policy") # Giữ lại tín hiệu cũ để không lỗi nút cũ
async def cmd_policy_dynamic(event):
    if not await check_protection(event): return
    # Gọi trang policy_page từ tab MenuBuilder
    await render_page(event, "policy_page")

# ==========================================
# XỬ LÝ NÚT HỖ TRỢ (SUPPORT)
# ==========================================
@router.message(Command("support"))
@router.callback_query(F.data == "support_info") # Giữ lại tín hiệu cũ
async def cmd_support_dynamic(event):
    if not await check_protection(event): return
    # Gọi trang support_page từ tab MenuBuilder
    await render_page(event, "support_page")

# ==========================================
# TRANG THÔNG TIN TÀI KHOẢN (/ME)
# ==========================================
@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    db.connect() # Làm mới kết nối để lấy hạn dùng mới nhất
    all_data = db.users_sheet.get_all_values()
    
    # Lọc danh sách gói đã mua của user
    my_plans = [row for row in all_data if len(row) > 7 and str(row[1]) == user_id and row[5] == "PAID"]
    
    text = db.get_config("MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    if not my_plans: 
        text += db.get_config("MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        for p in my_plans: 
            text += db.get_config("MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", str(p[3])).replace("{date}", str(p[7]))
            
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    
    # Hiển thị thông minh kết hợp ảnh từ Config
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME", ""))

# ==========================================
# CÔNG CỤ ADMIN: LẤY FILE_ID CỦA ẢNH
# ==========================================
@router.message(F.photo)
async def get_file_id(message: Message):
    """Admin gửi ảnh vào Bot để lấy mã ID dán lên Sheet"""
    if message.from_user.id == ADMIN_ID: 
        await message.reply(f"Mã ảnh của bạn (Dán mã này vào cột B trên Sheet):\n\n<code>{message.photo[-1].file_id}</code>")

# ==========================================
# HÀM CŨ DỰ PHÒNG (KHÔNG XOÁ ĐỂ TRÁNH LỖI IMPORT)
# ==========================================
async def send_welcome_messages(event):
    """Hàm này hiện tại đã được cmd_start và render_page thay thế"""
    await cmd_start(event)