import asyncio
import logging
from datetime import datetime
from aiogram import Router
from database import db
from bot_instance import bot

router = Router()

def parse_telegram_link(link: str):
    """Hàm thông minh bóc tách Chat ID và Message ID từ link Telegram"""
    link = link.strip().rstrip('/')
    parts = link.split('/')
    try:
        msg_id = int(parts[-1])
        # Nếu là link private group/channel (có chữ /c/)
        if "c" in parts:
            idx = parts.index("c")
            chat_id = f"-100{parts[idx+1]}"
        # Nếu là link public (username)
        else:
            chat_id = f"@{parts[-2]}"
        return chat_id, msg_id
    except:
        return None, None

def build_next_link(original_link: str, increment: int):
    """Hàm tạo link mới cho ngày hôm sau"""
    link = original_link.strip().rstrip('/')
    parts = link.split('/')
    try:
        new_msg_id = int(parts[-1]) + increment
        parts[-1] = str(new_msg_id)
        return "/".join(parts)
    except:
        return original_link

async def auto_post_worker():
    """Trái tim của hệ thống: Vòng lặp kiểm tra và đăng bài tự động"""
    logging.info("🚀 [MODULE] Auto-Post (Đăng bài tự động) đã khởi chạy!")
    
    # Đợi 15 giây khi mới boot server để các module khác chạy ổn định
    await asyncio.sleep(15) 

    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            today_date = now.strftime("%Y-%m-%d")

            # Kết nối thẳng vào tab AutoPost (Độc lập với tab Config)
            sh = db.client.open_by_key(db.sh.id)
            try:
                sheet = sh.worksheet("AutoPost")
            except:
                logging.error("❌ Không tìm thấy Tab 'AutoPost' trên Google Sheets.")
                await asyncio.sleep(300)
                continue

            records = sheet.get_all_values()

            # Duyệt từ dòng số 2 (Bỏ qua header)
            for i, row in enumerate(records[1:], start=2):
                if len(row) < 6: continue # Bỏ qua dòng thiếu dữ liệu
                
                task_name = str(row[0]).strip()
                target_chat = str(row[1]).strip()
                topic_id = str(row[2]).strip()
                post_time = str(row[3]).strip()
                source_link = str(row[4]).strip()
                batch_size = str(row[5]).strip()
                last_posted = str(row[6]).strip() if len(row) > 6 else ""

                if not target_chat or not source_link or last_posted == today_date:
                    continue # Bỏ qua nếu thiếu data hoặc hôm nay đã đăng rồi

                # CHIẾN LƯỢC SMART TRIGGER: Nếu đã qua giờ đăng mà chưa đăng thì quất luôn
                if current_time >= post_time:
                    logging.info(f"⏳ Đang thực hiện nhiệm vụ: {task_name}")
                    
                    batch = int(batch_size) if batch_size.isdigit() else 1
                    source_chat, start_msg_id = parse_telegram_link(source_link)
                    
                    if not source_chat or not start_msg_id:
                        sheet.update(f"H{i}", [["❌ Lỗi: Link nguồn không hợp lệ"]])
                        continue

                    thread_id = int(topic_id) if topic_id.isdigit() else None
                    msg_ids_to_copy = [start_msg_id + j for j in range(batch)]
                    
                    try:
                        # Thực hiện COPY ẨN DANH (Hỗ trợ cả Album nếu batch > 1)
                        if batch == 1:
                            await bot.copy_message(chat_id=target_chat, message_thread_id=thread_id, from_chat_id=source_chat, message_id=msg_ids_to_copy[0])
                        else:
                            await bot.copy_messages(chat_id=target_chat, message_thread_id=thread_id, from_chat_id=source_chat, message_ids=msg_ids_to_copy)
                        
                        # Thành công -> Tính toán Link của ngày mai
                        next_link = build_next_link(source_link, batch)
                        success_msg = f"✅ Đã đăng {batch} tin ({start_msg_id} -> {msg_ids_to_copy[-1]}) lúc {current_time}"
                        
                        # Cập nhật: Link mới, Ngày đã đăng, Trạng thái
                        sheet.update(f"E{i}:H{i}", [[next_link, batch_size, today_date, success_msg]])
                        logging.info(f"✅ Auto-Post thành công: {task_name}")
                        
                        # Nghỉ 3 giây trước khi đăng Group tiếp theo để tránh bị Telegram đánh Spam
                        await asyncio.sleep(3)

                    except Exception as copy_err:
                        err_str = str(copy_err).lower()
                        if "message to copy not found" in err_str:
                            msg_err = f"⚠️ Lỗi lúc {current_time}: Tin nhắn gốc ID {start_msg_id} đã bị xóa hoặc Bot không có mặt trong Kênh Nguồn."
                            # Vẫn tự động tăng Link để ngày mai không bị kẹt ở cái link lỗi này
                            next_link = build_next_link(source_link, batch)
                            sheet.update(f"E{i}:H{i}", [[next_link, batch_size, today_date, msg_err]])
                        else:
                            sheet.update(f"H{i}", [[f"❌ Lỗi: {copy_err}"]])
                            logging.error(f"❌ Auto-post lỗi tại {task_name}: {copy_err}")

        except Exception as e:
            logging.error(f"❌ Lỗi vòng lặp Auto-Post: {e}")

        # Cho vòng lặp ngủ 60 giây (Tiết kiệm tài nguyên tuyệt đối)
        await asyncio.sleep(60)

# Kích hoạt module chạy ngầm
asyncio.create_task(auto_post_worker())