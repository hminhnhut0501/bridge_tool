import re
from html import unescape
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db, normalize_key
from helpers import safe_delete_private_message
from i18n import get_user_language, language_switch_target, language_switch_text, localize_page_id, t_for_lang
from sale_utils import format_price_label, sale_banner, sale_placeholder

router = Router()

def format_currency(amount):
    """Định dạng tiền tệ VNĐ (VD: 3000 -> 3.000Đ)"""
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except:
        return f"{amount}Đ"

def process_dynamic_text(text):
    """Hàm quét và thay thế biến {KEY} thành giá trị thật từ tab Config"""
    # Tìm tất cả các chữ nằm trong ngoặc nhọn, VD: {PRICE_SVIP_LIFE}
    matches = re.findall(r'\{([A-Z0-9_]+)\}', text)
    for key in matches:
        if key.startswith("PRICE_"):
            val = format_price_label(key, 0)
        elif key.startswith("SALE_BANNER_"):
            price_key = key.replace("SALE_BANNER_", "", 1)
            val = sale_banner(price_key, 0)
        elif key.startswith("SALE_"):
            val = process_sale_placeholder(key)
        else:
            val = db.get_config(key, "???")
            # Nếu biến đó là Giá tiền (chứa chữ PRICE), tự động làm đẹp số
            if "PRICE" in key and val != "???":
                val = format_currency(val)
        text = text.replace(f"{{{key}}}", val)
    return text

def process_sale_placeholder(key):
    fields = [
        "SALE_OLD_PRICE_",
        "SALE_ORIGINAL_PRICE_",
        "SALE_SALE_PRICE_",
        "SALE_PRICE_",
        "SALE_PERCENT_",
        "SALE_DISCOUNT_",
        "SALE_COUNTDOWN_",
        "SALE_SLOTS_LEFT_",
        "SALE_SLOT_LIMIT_",
        "SALE_SLOTS_",
        "SALE_TEXT_",
        "SALE_LABEL_",
        "SALE_ID_",
    ]
    for prefix in fields:
        if key.startswith(prefix):
            field = prefix.replace("SALE_", "").strip("_")
            price_key = key.replace(prefix, "", 1)
            return sale_placeholder(price_key, field, 0)
    return ""

def page_exists(page_id):
    return db.get_page(page_id) is not None

def strip_html_tags(text):
    return unescape(re.sub(r"<[^>]*>", "", str(text or "")))

def config_enabled(key, default="OFF"):
    return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ"}

def language_switch_enabled():
    return config_enabled("BOT_LANGUAGE_SWITCH_ENABLED", "ON")

def menu_action_enabled(action):
    coupon_actions = {"coupon_enter", "coupon_code", "redeem_code"}
    if action in coupon_actions and not config_enabled("COUPON_MENU_ENABLED", "OFF"):
        return False
    return True

def append_language_switch(kb_markup, language):
    if not language_switch_enabled():
        return kb_markup
    kb_markup.inline_keyboard.append([
        InlineKeyboardButton(
            text=language_switch_text(language),
            callback_data=f"set_lang|{language_switch_target(language)}",
        )
    ])
    return kb_markup

def build_dynamic_keyboard(layout_str):
    """Trình dịch cú pháp: Nút bấm => hành_động"""
    kb = InlineKeyboardBuilder()
    lines = layout_str.strip().split('\n')
    
    for line in lines:
        if not line.strip(): continue
        
        buttons = line.split('|')
        row_btns = []
        
        for btn in buttons:
            if '=>' not in btn: continue
            raw_text, action = btn.split('=>', 1)
            
            # 🔥 Dịch các biến {PRICE...} trong Tên Nút
            final_text = process_dynamic_text(raw_text.strip())
            action = action.strip()
            if not menu_action_enabled(action):
                continue
            
            if action.startswith('url:'):
                row_btns.append(InlineKeyboardButton(text=final_text, url=action.replace('url:', '').strip()))
            else:
                row_btns.append(InlineKeyboardButton(text=final_text, callback_data=action))
                
        if row_btns:
            kb.row(*row_btns)
            
    return kb.as_markup()

async def send_with_html_fallback(sender, *, text=None, photo=None, reply_markup=None):
    """Gửi HTML trước; nếu Sheet sai thẻ HTML thì gửi lại dạng text thường."""
    final_text = str(text or "")
    caption_limit = 1024

    try:
        if photo:
            if len(final_text) <= caption_limit:
                await sender.answer_photo(photo=photo, caption=final_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await sender.answer_photo(photo=photo, parse_mode=None)
                await sender.answer(final_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await sender.answer(final_text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "parse entities" not in err and "can't parse entities" not in err:
            raise

        print(f"❌ Lỗi định dạng HTML khi render MenuBuilder: {e}")
        safe_text = strip_html_tags(final_text)
        if photo:
            if len(safe_text) <= caption_limit:
                await sender.answer_photo(photo=photo, caption=safe_text, reply_markup=reply_markup, parse_mode=None)
            else:
                await sender.answer_photo(photo=photo, parse_mode=None)
                await sender.answer(safe_text, reply_markup=reply_markup, parse_mode=None)
        else:
            await sender.answer(safe_text, reply_markup=reply_markup, parse_mode=None)

async def render_page(target, page_id):
    """Hàm lấy dữ liệu từ RAM và xuất ra giao diện"""
    language = get_user_language(target.from_user.id)
    page_id = normalize_key(page_id)
    requested_page_id = page_id
    page_id = localize_page_id(page_id, language)
    page = db.get_page(page_id)
    if not page:
        err = t_for_lang(language, "MSG_MENU_PAGE_NOT_FOUND", "⚠️ LỖI: Không tìm thấy trang `{page_id}` trên tab MenuBuilder!").replace("{page_id}", requested_page_id)
        if isinstance(target, CallbackQuery):
            await target.message.answer(err)
            await target.answer()
        else:
            await target.answer(err)
        return False

    # 🔥 Dịch các biến {PRICE...} trong Nội dung bài viết
    raw_text = page['text'].replace('\\n', '\n')
    text = process_dynamic_text(raw_text)
    
    kb_markup = build_dynamic_keyboard(page['layout'])
    if requested_page_id == "main_menu":
        kb_markup = append_language_switch(kb_markup, language)
    img_url = page['img']

    if isinstance(target, CallbackQuery):
        await safe_delete_private_message(target.message)

        if img_url and len(str(img_url)) > 10:
            await send_with_html_fallback(target.message, photo=img_url, text=text, reply_markup=kb_markup)
        else:
            await send_with_html_fallback(target.message, text=text, reply_markup=kb_markup)
        await target.answer()
        
    else:
        if img_url and len(str(img_url)) > 10:
            await send_with_html_fallback(target, photo=img_url, text=text, reply_markup=kb_markup)
        else:
            await send_with_html_fallback(target, text=text, reply_markup=kb_markup)
    return True

async def render_static_fallback(callback: CallbackQuery, page_id):
    """Fallback cho các trang lõi khi MenuBuilder chưa có dữ liệu."""
    fallback_pages = {
        "policy_page": ("MSG_POLICY", "Chính sách đang cập nhật...", "IMG_POLICY"),
        "support_page": ("MSG_SUPPORT", "Hỗ trợ đang cập nhật...", "IMG_SUPPORT"),
    }
    fallback = fallback_pages.get(page_id)
    if not fallback:
        return False

    text_key, default_text, img_key = fallback
    text = db.get_config(text_key, default_text).replace("\\n", "\n")
    img_url = db.get_config(img_key, "")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))

    await safe_delete_private_message(callback.message)

    if img_url and len(str(img_url)) > 10:
        await send_with_html_fallback(callback.message, photo=img_url, text=text, reply_markup=kb.as_markup())
    else:
        await send_with_html_fallback(callback.message, text=text, reply_markup=kb.as_markup())
    await callback.answer()
    return True

@router.callback_query(F.data.startswith("nav:"))
async def handle_navigation(callback: CallbackQuery):
    page_id = normalize_key(callback.data.split("nav:", 1)[1])
    if not page_exists(page_id):
        db.reload_config(force=True)
    if not page_exists(page_id) and await render_static_fallback(callback, page_id):
        return
    await render_page(callback, page_id)
