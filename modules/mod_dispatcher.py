import asyncio
import logging
from datetime import datetime
from aiogram import Router
from database import db
from bot_instance import bot

router = Router()

async def dispatcher_worker():
    """Kẻ canh gác thời gian và phân phát nội dung"""
    logging.info("🚀 [MODULE] Dispatcher (Người Phân Phát) đã sẵn sàng!")
    await asyncio.sleep(20) # Chờ 20s cho Bot chính ổn định

    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            sh = db.client.open_by_key(db.sh.id)
            try:
                config_sheet = sh.worksheet("AutoConfig")
                queue_sheet = sh.worksheet("AutoQueue")
            except Exception as e:
                logging.error(f"⚠️ Chưa tìm thấy Tab AutoConfig hoặc AutoQueue.")
                await asyncio.sleep(60)
                continue

            # 1. Đọc Bảng điều khiển
            configs = config_sheet.get_all_values()
            
            # Lặp qua các nhiệm vụ từ Bảng điều khiển (Lưu lại vị trí c_idx để cập nhật trạng thái)
            for c_idx, config_row in enumerate(configs[1:], start=2):
                if len(config_row) < 6: continue
                
                task_name = str(config_row[0]).strip()
                src_group = str(config_row[1]).strip()
                src_topic = str(config_row[2]).strip()
                dst_group = str(config_row[3]).strip()
                dst_topic = str(config_row[4]).strip()
                schedule_str = str(config_row[5]).strip()
                
                scheduled_times = [t.strip() for t in schedule_str.split(",") if t.strip()]
                
                # Nếu đến giờ hoàng đạo
                if current_time in scheduled_times:
                    logging.info(f"⏰ Tới giờ nhiệm vụ: {task_name}. Đang tìm bài trong kho...")
                    
                    # 2. Đọc Kho Hàng Đợi
                    queue_records = queue_sheet.get_all_values()
                    
                    row_to_process = None
                    row_index_to_delete = None
                    
                    # Quét từ trên xuống dưới để bốc bài cũ nhất
                    for q_idx, q_row in enumerate(queue_records[1:], start=2):
                        if len(q_row) >= 5:
                            q_src_group = str(q_row[0]).strip()
                            q_src_topic = str(q_row[1]).strip()
                            q_status = str(q_row[4]).strip()
                            
                            if q_src_group == src_group and q_src_topic == src_topic and q_status == "Pending":
                                row_to_process = q_row
                                row_index_to_delete = q_idx
                                break
                    
                    if not row_to_process:
                        logging.info(f"📭 Hàng đợi của '{task_name}' đang trống.")
                        # Báo cáo lên AutoConfig nếu kho trống
                        config_sheet.update(f"G{c_idx}", [[f"⚠️ Kho trống lúc {current_time}! Hãy nạp thêm bài."]])
                        continue
                        
                    # 3. Lấy dữ liệu bài và Bắt đầu COPY
                    raw_ids = str(row_to_process[2]).strip().split(",")
                    msg_ids_to_copy = [int(i.strip()) for i in raw_ids if i.strip().isdigit()]
                    dst_thread_id = int(dst_topic) if dst_topic.isdigit() else None
                    
                    try:
                        # Copy bài
                        if len(msg_ids_to_copy) == 1:
                            await bot.copy_message(chat_id=dst_group, from_chat_id=src_group, message_id=msg_ids_to_copy[0], message_thread_id=dst_thread_id)
                        else:
                            await bot.copy_messages(chat_id=dst_group, from_chat_id=src_group, message_ids=msg_ids_to_copy, message_thread_id=dst_thread_id)
                            
                        # 4. ĐĂNG XONG -> XÓA DÒNG Ở AUTOQUEUE + BÁO CÁO LÊN AUTOCONFIG
                        queue_sheet.delete_rows(row_index_to_delete)
                        
                        # Ghi báo cáo lên Cột G của tab AutoConfig
                        status_msg = f"✅ Đã phát cụm ID [{','.join(raw_ids)}] lúc {current_time}"
                        config_sheet.update(f"G{c_idx}", [[status_msg]])
                        
                        logging.info(f"{status_msg} cho nhiệm vụ '{task_name}'")
                        
                        await asyncio.sleep(3)
                        
                    except Exception as copy_err:
                        queue_sheet.delete_rows(row_index_to_delete)
                        err_msg = f"❌ Bỏ qua cụm ID [{','.join(raw_ids)}] bị lỗi lúc {current_time}"
                        config_sheet.update(f"G{c_idx}", [[err_msg]])
                        logging.error(f"❌ Lỗi Copy '{task_name}': {copy_err}")

        except Exception as e:
            logging.error(f"❌ Lỗi vòng lặp Dispatcher: {e}")

        await asyncio.sleep(60)

asyncio.create_task(dispatcher_worker())