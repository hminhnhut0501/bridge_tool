import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db

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
        val = db.get_config(key, "???")
        # Nếu biến đó là Giá tiền (chứa chữ PRICE), tự động làm đẹp số
        if "PRICE" in key and val != "???":
            val = format_currency(val)
        text = text.replace(f"{{{key}}}", val)
    return text

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
            
            if action.startswith('url:'):
                row_btns.append(InlineKeyboardButton(text=final_text, url=action.replace('url:', '').strip()))
            else:
                row_btns.append(InlineKeyboardButton(text=final_text, callback_data=action))
                
        if row_btns:
            kb.row(*row_btns)
            
    return kb.as_markup()

async def render_page(target, page_id):
    """Hàm lấy dữ liệu từ RAM và xuất ra giao diện"""
    page = db.pages_cache.get(page_id)
    if not page:
        err = f"⚠️ LỖI: Không tìm thấy trang `{page_id}` trên tab MenuBuilder!"
        if isinstance(target, CallbackQuery):
            await target.message.answer(err)
            await target.answer()
        else:
            await target.answer(err)
        return

    # 🔥 Dịch các biến {PRICE...} trong Nội dung bài viết
    raw_text = page['text'].replace('\\n', '\n')
    text = process_dynamic_text(raw_text)
    
    kb_markup = build_dynamic_keyboard(page['layout'])
    img_url = page['img']

    if isinstance(target, CallbackQuery):
        try:
            await target.message.delete()
        except:
            pass 

        if img_url and len(str(img_url)) > 10:
            await target.message.answer_photo(photo=img_url, caption=text, reply_markup=kb_markup, parse_mode="HTML")
        else:
            await target.message.answer(text, reply_markup=kb_markup, parse_mode="HTML")
        await target.answer()
        
    else:
        if img_url and len(str(img_url)) > 10:
            await target.answer_photo(photo=img_url, caption=text, reply_markup=kb_markup, parse_mode="HTML")
        else:
            await target.answer(text, reply_markup=kb_markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("nav:"))
async def handle_navigation(callback: CallbackQuery):
    page_id = callback.data.split("nav:")[1].strip()
    await render_page(callback, page_id)