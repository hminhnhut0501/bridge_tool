import asyncio
import logging
from datetime import datetime
from database import db
from bot_instance import bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm để tránh 1 ngày Bot gửi 2 lần tin nhắc cho cùng 1 người
notified_users = set()

async def check_expirations_professional():
    try:
        logging.info("⏳ [SCHEDULER] Đang quét danh sách thành viên để kiểm tra hạn dùng...")
        users_data = db.users_sheet.get_all_values()
        
        # Lấy số ngày báo trước từ Sheet (Mặc định báo trước 3 ngày)
        days_notice = int(db.get_config("REMINDER_DAYS", "3"))
        
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        # Duyệt từ dòng số 2 (bỏ qua tiêu đề)
        for i, row in enumerate(users_data[1:], start=2):
            if len(row) < 8: continue
            
            user_id = str(row[1]).strip()
            plan_name = str(row[3]).strip()
            status = str(row[5]).strip()
            expire_str = str(row[7]).strip()

            if status != "PAID" or not expire_str: 
                continue
                
            # Khách VIP Trọn đời thì bỏ qua luôn, không bao giờ lo hết hạn
            if "TRỌN ĐỜI" in plan_name.upper() or "LIFE" in plan_name.upper():
                continue

            try:
                expire_date = datetime.strptime(expire_str, "%Y-%m-%d")
                days_remaining = (expire_date.date() - now.date()).days
            except:
                continue

            notif_key = f"{user_id}_{today_str}"

            # ==========================================
            # 1. HẾT HẠN -> KICK KHỎI NHÓM & CẬP NHẬT SHEET
            # ==========================================
            if days_remaining < 0:
                # Đổi trạng thái thành EXPIRED trên Sheet
                db.users_sheet.update_cell(i, 6, "EXPIRED")
                logging.info(f"🚫 User {user_id} đã hết hạn gói {plan_name}. Đã cập nhật EXPIRED.")
                
                # Gửi tin báo tử
                msg_expired = db.get_config("MSG_EXPIRED", "⚠️ Gói <b>{plan}</b> của bạn đã hết hạn và bạn đã bị mời ra khỏi nhóm.\n\n👇 Vui lòng gia hạn để tiếp tục truy cập!").replace("\\n", "\n").replace("{plan}", plan_name)
                kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=db.get_config("BTN_RENEW", "🔄 Gia hạn ngay"), callback_data="nav:main_menu"))
                
                try: await bot.send_message(chat_id=user_id, text=msg_expired, reply_markup=kb.as_markup(), parse_mode="HTML")
                except: pass
                
                # Xử lý Kick (Ban rồi Unban để đuổi ra mà không khóa vĩnh viễn)
                for g in range(1, 5):
                    btn_name = db.get_config(f"BTN_G{g}", f"Nhóm {g}")
                    if btn_name.upper() in plan_name.upper() or f"G{g}" in plan_name or "FULL" in plan_name.upper() or "SVIP" in plan_name.upper():
                        gid = db.get_config(f"ID_G{g}")
                        if gid:
                            try:
                                await bot.ban_chat_member(chat_id=gid, user_id=int(user_id))
                                await bot.unban_chat_member(chat_id=gid, user_id=int(user_id)) # Unban ngay để họ còn mua lại được
                            except: pass
                continue

            # ==========================================
            # 2. NHẮC NHỞ SẮP HẾT HẠN (GỬI 1 LẦN/NGÀY)
            # ==========================================
            if days_remaining == days_notice and notif_key not in notified_users:
                msg_reminder = db.get_config("MSG_REMINDER", "⏰ Gói <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa!\n\n👇 Nhấn nút bên dưới để gia hạn ngay nhé:").replace("\\n", "\n").replace("{plan}", plan_name).replace("{days}", str(days_remaining))
                
                # Trỏ thẳng về các trang UI mới để khách mua hàng
                kb = InlineKeyboardBuilder()
                if "FULL" in plan_name.upper() or "SVIP" in plan_name.upper():
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_FULL", "🌟 Gia hạn / Lên Trọn Đời"), callback_data="nav:svip_page"))
                else:
                    kb.row(InlineKeyboardButton(text=db.get_config("BTN_RENEW_GROUP", "🔄 Gia hạn / Mở rộng gói"), callback_data="nav:main_menu"))

                try:
                    await bot.send_message(chat_id=user_id, text=msg_reminder, reply_markup=kb.as_markup(), parse_mode="HTML")
                    notified_users.add(notif_key) # Lưu nháp để hôm nay không nhắc lại nữa
                    logging.info(f"📩 Đã nhắc gia hạn ({days_remaining} ngày) cho User {user_id}")
                except Exception as e:
                    logging.error(f"❌ Lỗi gửi tin nhắc cho {user_id}: {e}")

    except Exception as e:
        logging.error(f"❌ Lỗi hệ thống quét định kỳ: {e}")

# Worker chạy ngầm vĩnh viễn
async def main():
    print("🚀 [MODULE] Scheduler (Quản gia: Nhắc hạn/Kick) đã khởi động!")
    await asyncio.sleep(60) 
    
    while True:
        await check_expirations_professional()
        
        # Cuối ngày dọn dẹp RAM xóa các record của ngày hôm trước
        today_str = datetime.now().strftime("%Y-%m-%d")
        to_remove = [k for k in notified_users if not k.endswith(today_str)]
        for k in to_remove: notified_users.remove(k)
            
        # Bot ngủ 4 tiếng rồi mới quét Sheet lại 1 lần (Cho nhẹ máy chủ)
        logging.info("💤 Hoàn tất chu kỳ quét. Quản gia đi ngủ 4 tiếng...")
        await asyncio.sleep(14400)