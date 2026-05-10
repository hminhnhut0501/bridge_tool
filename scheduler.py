import asyncio
import logging
from datetime import datetime, timedelta
from database import db
from bot_instance import bot

# Cấu hình logging để theo dõi lịch sử vận hành
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Bộ nhớ tạm để đảm bảo mỗi User chỉ nhận 1 tin nhắn nhắc nhở/ngày
notified_users = set()

async def check_expirations_professional():
    """
    Hệ thống kiểm tra hạn dùng chuyên nghiệp:
    - Nhắc nhở tinh tế trước 24h.
    - Xử lý mời rời nhóm khi hết hạn.
    - Tối ưu hóa hiệu suất hệ thống.
    """
    try:
        logging.info("⏳ Hệ thống đang quét danh sách thành viên...")
        
        # Làm mới kết nối để đảm bảo dữ liệu luôn mới nhất
        db.connect()
        users_data = db.users_sheet.get_all_values()
        
        for i, row in enumerate(users_data[1:], start=2):
            if len(row) < 8: continue
            
            user_id = row[1].strip()
            plan_name = row[3]
            status = row[5].strip()
            expire_str = row[7].strip()

            # Chỉ xử lý các gói đã thanh toán và có thời hạn
            if status != "PAID" or expire_str == "Vĩnh viễn" or not expire_str:
                continue

            # --- BỘ LỌC ĐỊNH DẠNG NGÀY THÁNG ĐA NĂNG ---
            expire_dt = None
            for fmt in ["%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
                try:
                    expire_dt = datetime.strptime(expire_str, fmt)
                    break 
                except ValueError:
                    continue

            if not expire_dt:
                logging.warning(f"⚠️ Dòng {i}: Định dạng ngày '{expire_str}' không hợp lệ.")
                continue

            now = datetime.now()
            time_left = expire_dt - now

            # --- 1. NHẮC NHỞ TINH TẾ TRƯỚC 1 NGÀY (Khoảng 23-24 tiếng) ---
            if timedelta(hours=23) < time_left <= timedelta(hours=24):
                if user_id not in notified_users:
                    # Lấy mẫu tin nhắn nhắc nhở từ Google Sheets
                    msg_template = db.get_config("MSG_REMINDER", (
                        "⏰ <b>TÀI KHOẢN CỦA BẠN SẮP HẾT HẠN!</b> ⏰\n"
                        "────────────────────\n"
                        "Prive+ VIP báo nhỏ nè, gói <b>{plan}</b> của bạn sẽ kết thúc vào lúc:\n"
                        "⏳ <code>{date}</code> (Chỉ còn chưa đầy 24h nữa).\n\n"
                        "🔥 Rất nhiều siêu phẩm mới vừa được update lên nhóm hôm nay. Để không bị gián đoạn trải nghiệm VIP và bỏ lỡ nội dung hot, hãy gia hạn ngay nhé!\n\n"
                        "👉 Gõ /start để nhận mã QR gia hạn tự động (Mất đúng 5 giây)."
                    )).replace("\\n", "\n")
                    
                    # Lắp ráp dữ liệu thực tế vào form
                    msg = msg_template.replace("{plan}", str(plan_name)).replace("{date}", str(expire_str))
                    
                    try:
                        await bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")
                        notified_users.add(user_id)
                        logging.info(f"📩 Đã gửi nhắc nhở tinh tế cho User {user_id}")
                    except Exception as e:
                        logging.error(f"❌ Không gửi được tin nhắc cho {user_id}: {e}")

            # --- 2. XỬ LÝ KICK KHI CHÍNH THỨC HẾT HẠN ---
            elif now >= expire_dt:
                logging.info(f"🚫 User {user_id} đã hết hạn. Đang tiến hành mời rời nhóm...")
                
                # Cập nhật trạng thái trên Google Sheets trước
                db.users_sheet.update(f"F{i}", [["EXPIRED"]])
                
                # Lấy mẫu tin nhắn hết hạn từ Google Sheets
                farewell_template = db.get_config("MSG_EXPIRED", (
                    "✨ <b>THÔNG BÁO HẾT HẠN GÓI VIP</b> ✨\n"
                    "────────────────────\n"
                    "Gói dịch vụ <b>{plan}</b> của bạn đã chính thức khép lại.\n\n"
                    "🙏 <b>Prive+</b> xin gửi lời cảm ơn chân thành vì bạn đã đồng hành cùng chúng mình thời gian qua. "
                    "Hệ thống đã tạm thời mời bạn rời khỏi nhóm VIP.\n\n"
                    "🔥 Rất hy vọng được sớm gặp lại bạn trong tương lai gần! Chúc bạn một ngày tốt lành! ❤️"
                )).replace("\\n", "\n")
                
                # Lắp ráp dữ liệu thực tế vào form
                farewell_msg = farewell_template.replace("{plan}", str(plan_name))
                
                try:
                    await bot.send_message(chat_id=user_id, text=farewell_msg, parse_mode="HTML")
                except: pass

                # Thực hiện Kick khỏi tất cả các nhóm cấu hình
                for j in range(1, 5):
                    group_id = db.get_config(f"GROUP_{j}_ID")
                    if group_id:
                        try:
                            # Kick và Unban ngay để User có thể quay lại sau khi gia hạn
                            await bot.ban_chat_member(chat_id=int(group_id), user_id=int(user_id))
                            await bot.unban_chat_member(chat_id=int(group_id), user_id=int(user_id))
                            logging.info(f"✅ Đã mời User {user_id} rời khỏi nhóm {j}")
                        except Exception as e:
                            logging.error(f"⚠️ Lỗi xử lý tại nhóm {j}: {e}")
                
                # Dọn dẹp bộ nhớ tạm
                if user_id in notified_users:
                    notified_users.remove(user_id)

    except Exception as e:
        logging.error(f"❌ Lỗi hệ thống quét định kỳ: {e}")

async def main():
    print("🚀 [PRIVE+] Hệ thống Scheduler vận hành chính thức đã khởi động!")
    
    # Bắt Scheduler đợi 10 giây để nhường đường cho Bot chính chạy trước
    logging.info("⏳ Đang nhường ưu tiên cho Bot chính khởi động. Sẽ bắt đầu quét sau 10 giây...")
    await asyncio.sleep(10) 
    
    while True:
        await check_expirations_professional()
        
        # Dọn dẹp bộ nhớ tạm mỗi ngày một lần để tránh đầy RAM
        if datetime.now().hour == 0:
            notified_users.clear()
            
        # Nghỉ đúng 1 tiếng (3600 giây) để tối ưu tài nguyên
        logging.info("💤 Hoàn tất chu kỳ quét. Sẽ quay lại sau 60 phút...")
        await asyncio.sleep(3600) 

if __name__ == "__main__":
    asyncio.run(main())