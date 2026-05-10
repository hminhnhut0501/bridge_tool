import asyncio
import logging
from datetime import datetime, timedelta
from database import db
from bot_instance import bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bộ nhớ tạm theo dõi việc gửi tin nhắn (Tránh 1 ngày gửi 2 lần)
notified_users = set()

def format_currency(amount):
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except:
        return f"{amount}Đ"

async def check_expirations_professional():
    try:
        logging.info("⏳ Hệ thống đang quét danh sách thành viên...")
        db.connect()
        users_data = db.users_sheet.get_all_values()
        
        # Lấy cấu hình thời gian báo trước từ Sheet
        days_notice = int(db.get_config("REMINDER_DAYS", "3"))
        reminder_hour = int(db.get_config("REMINDER_HOUR", "21"))
        
        now = datetime.now()
        today_str = str(now.date())
        
        for i, row in enumerate(users_data[1:], start=2):
            if len(row) < 8: continue
            
            user_id = row[1].strip()
            plan_name = row[3]
            status = row[5].strip()
            expire_str = row[7].strip()

            if status != "PAID" or expire_str == "Vĩnh viễn" or not expire_str:
                continue

            expire_dt = None
            for fmt in ["%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
                try:
                    expire_dt = datetime.strptime(expire_str, fmt)
                    break 
                except ValueError:
                    continue

            if not expire_dt:
                continue

            time_left = expire_dt - now

            # --- 1. XỬ LÝ KICK KHI ĐÃ HẾT HẠN ---
            if now >= expire_dt:
                logging.info(f"🚫 User {user_id} đã hết hạn. Đang tiến hành mời rời nhóm...")
                db.users_sheet.update(f"F{i}", [["EXPIRED"]])
                
                farewell_template = db.get_config("MSG_EXPIRED", (
                    "✨ <b>THÔNG BÁO HẾT HẠN GÓI VIP</b> ✨\n"
                    "────────────────────\n"
                    "Gói dịch vụ <b>{plan}</b> của bạn đã chính thức khép lại.\n\n"
                    "🙏 Cảm ơn bạn đã đồng hành cùng <b>Prive+</b>. Hệ thống đã tạm thời mời bạn rời khỏi nhóm VIP.\n\n"
                    "🔥 Rất hy vọng được sớm gặp lại bạn trong tương lai gần!"
                )).replace("\\n", "\n")
                
                try:
                    await bot.send_message(chat_id=user_id, text=farewell_template.replace("{plan}", str(plan_name)), parse_mode="HTML")
                except: pass

                for j in range(1, 5):
                    group_id = db.get_config(f"GROUP_{j}_ID")
                    if group_id:
                        try:
                            await bot.ban_chat_member(chat_id=int(group_id), user_id=int(user_id))
                            await bot.unban_chat_member(chat_id=int(group_id), user_id=int(user_id))
                        except Exception: pass
                continue

            # --- 2. NHẮC NHỞ & UP-SALE TRƯỚC X NGÀY VÀO LÚC Y GIỜ ---
            if 0 < time_left.total_seconds() <= days_notice * 24 * 3600:
                if now.hour == reminder_hour:
                    notif_key = f"{user_id}_{today_str}"
                    
                    if notif_key not in notified_users:
                        days_rounded = time_left.days + 1
                        
                        msg_template = db.get_config("MSG_REMINDER", (
                            "⏰ <b>TÀI KHOẢN CỦA BẠN SẮP HẾT HẠN!</b> ⏰\n"
                            "────────────────────\n"
                            "Gói <b>{plan}</b> của bạn sẽ kết thúc vào:\n"
                            "⏳ <code>{date}</code> (Chỉ còn {days} ngày nữa).\n\n"
                            "🔥 Đừng để gián đoạn trải nghiệm VIP. Hãy gia hạn ngay hôm nay, hoặc <b>NÂNG CẤP TRỌN ĐỜI</b> để được trừ lại tiền gói 1 tháng bạn đang dùng nhé!"
                        )).replace("\\n", "\n")
                        
                        msg = msg_template.replace("{plan}", str(plan_name)).replace("{date}", str(expire_str)).replace("{days}", str(days_rounded))
                        
                        # TẠO NÚT UP-SALE THÔNG MINH
                        kb = InlineKeyboardBuilder()
                        is_full = ("full" in plan_name.lower() or "svip" in plan_name.lower())
                        renew_cb = None; upsell_cb = None; p_1m = 0; p_life = 0
                        
                        if is_full:
                            renew_cb = "view_full_1m"
                            upsell_cb = "upsell_full"
                            p_1m = int(db.get_config("PRICE_1_MONTH", "999"))
                            p_life = int(db.get_config("PRICE_LIFETIME", "999"))
                        else:
                            for j in range(1, 5):
                                g_name = db.get_config(f"BTN_G{j}", f"Nhóm {j}").lower()
                                if g_name in plan_name.lower() or f"nhóm {j}" in plan_name.lower() or f"g{j}" in plan_name.lower():
                                    renew_cb = f"buy_G{j}_1m"
                                    upsell_cb = f"upsell_G{j}"
                                    p_1m = int(db.get_config(f"PRICE_G{j}_1M", "50000"))
                                    p_life = int(db.get_config(f"PRICE_G{j}_LIFE", "149000"))
                                    break
                        
                        if renew_cb and upsell_cb:
                            upsell_price = max(0, p_life - p_1m) # Giảm giá bằng đúng gói 1 tháng
                            
                            btn_renew_text = db.get_config("BTN_REM_RENEW", "♻️ Gia hạn 1 Tháng ({price})")
                            btn_upsell_text = db.get_config("BTN_REM_UPSELL", "🚀 Lên Trọn đời (Chỉ bù {upsell_price})")
                            
                            btn_renew_text = btn_renew_text.replace("{price}", format_currency(p_1m))
                            btn_upsell_text = btn_upsell_text.replace("{upsell_price}", format_currency(upsell_price))
                            
                            kb.row(InlineKeyboardButton(text=btn_renew_text, callback_data=renew_cb))
                            kb.row(InlineKeyboardButton(text=btn_upsell_text, callback_data=upsell_cb))
                        
                        try:
                            if len(kb.as_markup().inline_keyboard) > 0:
                                await bot.send_message(chat_id=user_id, text=msg, reply_markup=kb.as_markup(), parse_mode="HTML")
                            else:
                                await bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")
                                
                            notified_users.add(notif_key)
                            logging.info(f"📩 Đã nhắc gia hạn ({days_rounded} ngày) cho User {user_id}")
                        except Exception as e:
                            logging.error(f"❌ Lỗi gửi tin nhắc cho {user_id}: {e}")

    except Exception as e:
        logging.error(f"❌ Lỗi hệ thống quét định kỳ: {e}")

async def main():
    print("🚀 [PRIVE+] Hệ thống Scheduler vận hành chính thức đã khởi động!")
    await asyncio.sleep(10) 
    
    while True:
        await check_expirations_professional()
        
        # Dọn dẹp bộ nhớ RAM mỗi ngày (Chỉ giữ lại những user đã thông báo trong ngày hôm nay)
        today_str = str(datetime.now().date())
        to_remove = [k for k in notified_users if not k.endswith(today_str)]
        for k in to_remove: notified_users.remove(k)
            
        logging.info("💤 Hoàn tất chu kỳ quét. Sẽ quay lại sau 60 phút...")
        await asyncio.sleep(3600) 

if __name__ == "__main__":
    asyncio.run(main())