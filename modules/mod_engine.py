from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db

router = Router()

def build_dynamic_keyboard(layout_str):
    """Trình dịch cú pháp: Nút bấm => hành_động"""
    kb = InlineKeyboardBuilder()
    lines = layout_str.strip().split('\n')
    
    for line in lines:
        if not line.strip(): continue
        
        # Cắt bằng dấu | để tạo các nút nằm chung 1 hàng ngang
        buttons = line.split('|')
        row_btns = []
        
        for btn in buttons:
            if '=>' not in btn: continue
            text, action = btn.split('=>', 1)
            text = text.strip()
            action = action.strip()
            
            # Nếu là link Web
            if action.startswith('url:'):
                row_btns.append(InlineKeyboardButton(text=text, url=action.replace('url:', '').strip()))
            else:
                # Nếu là lệnh nav: hoặc buy: thì gán vào callback_data
                row_btns.append(InlineKeyboardButton(text=text, callback_data=action))
                
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

    # Lấy dữ liệu và dịch
    kb_markup = build_dynamic_keyboard(page['layout'])
    text = page['text'].replace('\\n', '\n')
    img_url = page['img']

    # Nếu người dùng click nút (Callback)
    if isinstance(target, CallbackQuery):
        await target.message.delete()
        if img_url:
            await target.message.answer_photo(photo=img_url, caption=text, reply_markup=kb_markup, parse_mode="HTML")
        else:
            await target.message.answer(text, reply_markup=kb_markup, parse_mode="HTML")
        await target.answer()
        
    # Nếu người dùng gõ lệnh /start (Message)
    else:
        if img_url:
            await target.answer_photo(photo=img_url, caption=text, reply_markup=kb_markup, parse_mode="HTML")
        else:
            await target.answer(text, reply_markup=kb_markup, parse_mode="HTML")

# Bắt tín hiệu chuyển trang (Khi khách bấm nút có chứa nav:)
@router.callback_query(F.data.startswith("nav:"))
async def handle_navigation(callback: CallbackQuery):
    page_id = callback.data.split("nav:")[1].strip()
    await render_page(callback, page_id)