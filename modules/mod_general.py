import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from bot_instance import bot
from hidden_group_utils import display_plan_name
from supabase_store import supabase_store
from helpers import check_protection, cleanup_welcome, is_admin_user, smart_display
from i18n import get_user_language, set_user_language, t
from modules.mod_engine import build_dynamic_keyboard, page_exists, render_page, send_with_html_fallback 
from sale_utils import build_sale_announcement
from scheduler import check_expirations_professional
from renewal_utils import is_early_renew_enabled

router = Router()


def language_switch_keyboard(current_language):
    kb = InlineKeyboardBuilder()
    if current_language == "en":
        kb.row(InlineKeyboardButton(text="🇻🇳 Tiếng Việt", callback_data="set_lang:vi"))
    else:
        kb.row(InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"))
    kb.row(InlineKeyboardButton(text="🏠 Main menu", callback_data="back_main"))
    return kb.as_markup()

def format_membership_expire(value, user_id=None):
    raw = str(value or "").strip()
    if not raw:
        return "-"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
            try:
                timezone = ZoneInfo(timezone_name)
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                parsed = None
        if not parsed:
            return raw.replace("T", " ").replace("+00:00", "")

    return parsed.strftime("%d/%m/%Y %H:%M")

def order_to_me_item(order):
    return [
        order.get("order_id", ""),
        order.get("telegram_user_id", ""),
        order.get("full_name", ""),
        order.get("plan_name", ""),
        order.get("amount", ""),
        order.get("status", ""),
        order.get("paid_at", ""),
        order.get("expire_at", ""),
    ]

# [1] HÀM CŨ DỰ PHÒNG CHỐNG LỖI IMPORT
async def send_welcome_messages(event):
    await cmd_start(event)

# [2] LỆNH RELOAD
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if is_admin_user(message.from_user.id):
        db.reload_config(force=True)
        await message.reply(db.get_config("MSG_RELOAD_DONE", "🔄 Đã nạp lại toàn bộ dữ liệu & Giao diện từ Sheet!"))
    else:
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))

@router.message(Command("check_expiry"))
async def cmd_check_expiry(message: Message):
    if not is_admin_user(message.from_user.id):
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))
        return

    await message.reply(db.get_config("MSG_CHECK_EXPIRY_STARTED", "⏳ Đang quét hạn dùng ngay bây giờ..."))
    await check_expirations_professional()
    await message.reply(db.get_config("MSG_CHECK_EXPIRY_DONE", "✅ Đã chạy xong một vòng quét hạn dùng. Xem log server để biết dòng nào đã gửi/kick hoặc bị bỏ qua."))

@router.message(Command("early_renew"))
async def cmd_early_renew(message: Message):
    if not is_admin_user(message.from_user.id):
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        status = "ON" if is_early_renew_enabled() else "OFF"
        await message.reply(
            db.get_config("MSG_EARLY_RENEW_STATUS", "EARLY_RENEW hiện đang: <b>{status}</b>\\nDùng: /early_renew on hoặc /early_renew off").replace("\\n", "\n").replace("{status}", status),
            parse_mode="HTML",
        )
        return

    action = parts[1].strip().lower()
    if action in {"on", "1", "true", "yes", "bat", "bật"}:
        db.set_config("EARLY_RENEW_ENABLED", "ON")
        await message.reply(db.get_config("MSG_EARLY_RENEW_ON", "✅ Đã bật EARLY_RENEW. Tin nhắc gia hạn sẽ kèm ưu đãi nếu đủ điều kiện."))
    elif action in {"off", "0", "false", "no", "tat", "tắt"}:
        db.set_config("EARLY_RENEW_ENABLED", "OFF")
        await message.reply(db.get_config("MSG_EARLY_RENEW_OFF", "✅ Đã tắt EARLY_RENEW. Tin nhắc gia hạn sẽ dùng nội dung và nút gia hạn thường."))
    else:
        await message.reply(db.get_config("MSG_EARLY_RENEW_USAGE", "Cú pháp: /early_renew on hoặc /early_renew off"))

async def send_sale_announcement(message: Message):
    enabled = str(db.get_config("SALE_ANNOUNCE_ENABLED", "ON")).strip().upper()
    if enabled in ["OFF", "FALSE", "NO", "0", "TẮT", "TAT"]:
        return False

    text = build_sale_announcement()
    if not text:
        return False

    img = str(db.get_config("IMG_SALE_BANNER", "")).strip()
    layout = db.get_config(
        "SALE_ANNOUNCE_BUTTONS",
        "🔥 Mua SVIP Trọn Đời => buy_full_life\n💎 Mua SVIP 30 Ngày => buy_full_1m\n📋 Xem toàn bộ gói => nav:main_menu",
    ).replace("\\n", "\n")
    reply_markup = build_dynamic_keyboard(layout) if layout.strip() else None

    try:
        if img and len(img) > 10:
            await send_with_html_fallback(message, photo=img, text=text, reply_markup=reply_markup)
        else:
            await send_with_html_fallback(message, text=text, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi thông báo sale: {e}")
        return False

# [3] LỆNH START & QUAY LẠI MENU CHÍNH
@router.message(CommandStart())
async def cmd_start(message: Message):
    if not await check_protection(message): return
    db.reload_config(force=True)
    await cleanup_welcome(message.from_user.id, message.chat.id)
    if await send_sale_announcement(message):
        return
    await render_page(message, "main_menu")

@router.message(Command("menu"))
@router.message(Command("home"))
async def cmd_menu(message: Message):
    if not await check_protection(message): return
    db.reload_config(force=True)
    await cleanup_welcome(message.from_user.id, message.chat.id)
    await render_page(message, "main_menu")

@router.message(Command("lang"))
@router.message(Command("language"))
async def cmd_language(message: Message):
    if not await check_protection(message): return
    current_language = get_user_language(message.from_user.id)
    text = (
        "Choose your language and I’ll bring you back to the main menu."
        if current_language == "en"
        else "Chọn ngôn ngữ để quay lại menu chính."
    )
    await message.answer(text, reply_markup=language_switch_keyboard(current_language))

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not await check_protection(callback): return
    await render_page(callback, "main_menu")

@router.callback_query(F.data.startswith("set_lang:"))
async def change_language(callback: CallbackQuery):
    if not await check_protection(callback):
        return
    language = set_user_language(callback.from_user.id, callback.data.split(":", 1)[1])
    try:
        await callback.answer("Language updated." if language == "en" else "Đã đổi ngôn ngữ.")
    except Exception as exc:
        if "query is too old" not in str(exc).lower() and "query id is invalid" not in str(exc).lower():
            raise
    try:
        rendered = await render_page(callback, "main_menu")
        if rendered:
            return
    except Exception as exc:
        print(f"❌ Lỗi render menu sau khi đổi ngôn ngữ user {callback.from_user.id}: {exc}")

    fallback = "Language updated, but the menu could not be loaded. Please send /start." if language == "en" else "Đã đổi ngôn ngữ nhưng chưa tải được menu. Vui lòng gửi /start."
    await callback.message.answer(fallback)

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
        text = t(event.from_user.id, "MSG_POLICY", "Chính sách đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_POLICY"))
    except Exception as e:
        print(f"❌ Lỗi fallback /policy: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer(t(event.from_user.id, "ALERT_POLICY_UNAVAILABLE", "Không thể mở trang quy định lúc này."), show_alert=True)

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
        text = t(event.from_user.id, "MSG_SUPPORT", "Hỗ trợ đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))
    except Exception as e:
        print(f"❌ Lỗi fallback /support: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer(t(event.from_user.id, "ALERT_SUPPORT_UNAVAILABLE", "Không thể mở trang hỗ trợ lúc này."), show_alert=True)

# [6] TRANG THÔNG TIN TÀI KHOẢN (/ME)
@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    if supabase_store.enabled:
        my_plans = [
            order_to_me_item(order)
            for order in supabase_store.list_paid_orders_for_user(user_id, limit=100)
        ]
    else:
        db.connect()
        all_data = db.users_sheet.get_all_values()
        my_plans = [row for row in all_data if len(row) > 7 and str(row[1]) == user_id and row[5] == "PAID"]
    
    text = t(event.from_user.id, "MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    if not my_plans: 
        text += t(event.from_user.id, "MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        for p in my_plans: 
            expire_text = format_membership_expire(p[7], event.from_user.id)
            text += t(event.from_user.id, "MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", display_plan_name(str(p[3]))).replace("{date}", expire_text)
            
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME", ""))

# [7] CÔNG CỤ ADMIN: LẤY FILE_ID CỦA ẢNH
@router.message(F.photo)
async def get_file_id(message: Message):
    if message.chat.type != "private":
        return
    if is_admin_user(message.from_user.id):
        await message.reply(f"<code>{message.photo[-1].file_id}</code>", parse_mode="HTML")
