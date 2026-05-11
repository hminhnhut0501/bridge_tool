import asyncio
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from database import db

router = Router()

# Bộ nhớ đệm để gom các ảnh trong cùng 1 Album (Tránh vỡ Group Media)
media_buffer = {}
active_flush_tasks = set()

# Cache cấu hình Nguồn để Bot không phải gọi Google Sheets mỗi giây
cached_sources = []
last_cache_time = 0

def get_valid_sources():
    """Đọc Tab AutoConfig để biết Bot cần 'đứng canh' ở những Group nào"""
    global cached_sources, last_cache_time
    now = datetime.now().timestamp()
    
    # Cập nhật cache mỗi 60 giây
    if now - last_cache_time > 60:
        try:
            sh = db.client.open_by_key(db.sh.id)
            sheet = sh.worksheet("AutoConfig")
            records = sheet.get_all_values()
            
            sources = []
            for row in records[1:]:
                if len(row) >= 2 and str(row[1]).strip():
                    group_id = str(row[1]).strip()
                    topic_id = str(row[2]).strip() if len(row) > 2 else ""
                    sources.append({"group_id": group_id, "topic_id": topic_id})
            
            cached_sources = sources
            last_cache_time = now
        except Exception as e:
            logging.error(f"❌ Lỗi đọc AutoConfig: {e}")
            
    return cached_sources

async def flush_to_sheet(group_id, topic_id, message_ids_list):
    """Ghi cụm ID đã gom được lên Tab AutoQueue"""
    try:
        sh = db.client.open_by_key(db.sh.id)
        queue_sheet = sh.worksheet("AutoQueue")
        
        # Nối các ID bằng dấu phẩy (VD: "101,102,103")
        ids_str = ",".join(map(str, message_ids_list))
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ghi 1 dòng mới tinh vào Hàng Đợi
        queue_sheet.append_row([group_id, topic_id, ids_str, time_str, "Pending"])
        logging.info(f"📥 Đã thu thập và lưu Hàng đợi: Nhóm {group_id} - ID [{ids_str}]")
    except Exception as e:
        logging.error(f"❌ Lỗi ghi AutoQueue: {e}")

async def wait_and_flush_media(media_group_id, group_id, topic_id):
    """Nín thở chờ 3 giây để gom đủ các ảnh trong Album rồi mới đem cất"""
    await asyncio.sleep(3) 
    
    if media_group_id in media_buffer:
        msg_ids = media_buffer.pop(media_group_id) # Lấy ra và xóa khỏi Buffer
        await flush_to_sheet(group_id, topic_id, msg_ids)
        
    active_flush_tasks.discard(media_group_id)

@router.message()
async def auto_collect_handler(message: Message):
    """Bắt mọi tin nhắn bay qua Bot và kiểm duyệt xem có phải Kênh Nguồn không"""
    chat_id_str = str(message.chat.id)
    thread_id_str = str(message.message_thread_id) if message.message_thread_id else ""
    
    valid_sources = get_valid_sources()
    
    # Kiểm tra xem tin nhắn này có thuộc về Group/Topic Nguồn mà sếp cài đặt không
    is_valid = False
    for src in valid_sources:
        if src["group_id"] == chat_id_str:
            # Nếu sếp cấu hình Topic thì phải trùng Topic, nếu không cấu hình thì bắt tất
            if not src["topic_id"] or src["topic_id"] == thread_id_str:
                is_valid = True
                break

    if not is_valid:
        return # Nếu là tin nhắn ở Group khác thì lướt qua luôn
        
    msg_id = message.message_id
    
    # XỬ LÝ ALBUM (GROUP MEDIA)
    if message.media_group_id:
        m_id = message.media_group_id
        if m_id not in media_buffer:
            media_buffer[m_id] = []
            
        media_buffer[m_id].append(msg_id)
        
        # Mở luồng đếm ngược 3 giây cho Album này
        if m_id not in active_flush_tasks:
            active_flush_tasks.add(m_id)
            asyncio.create_task(wait_and_flush_media(m_id, chat_id_str, thread_id_str))
            
    # XỬ LÝ TIN NHẮN/VIDEO LẺ (Ghi luôn không cần chờ)
    else:
        await flush_to_sheet(chat_id_str, thread_id_str, [msg_id])