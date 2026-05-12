import os
import time
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv()

bot = Bot(
    token=os.getenv("BOT_TOKEN"), 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

async def set_commands():
    commands = [
        BotCommand(command="start", description="Trang chủ / Mua gói"),
        BotCommand(command="me", description="Kiểm tra gói & Hạn dùng"),
        BotCommand(command="support", description="Liên hệ hỗ trợ Admin"),
        BotCommand(command="policy", description="Đọc quy định nhóm"), # Thêm dòng này!
    ]
    await bot.set_my_commands(commands)

# Lưu trữ lịch sử bấm nút của User {user_id: timestamp}
user_cooldowns = {}
# Trạng thái bảo trì (True/False)
MAINTENANCE_MODE = False 

def is_spamming(user_id):
    current_time = time.time()
    last_time = user_cooldowns.get(user_id, 0)
    
    # Giới hạn 2 giây mới được bấm 1 lần
    if current_time - last_time < 2:
        return True
    
    user_cooldowns[user_id] = current_time
    return False