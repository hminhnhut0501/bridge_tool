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
    try:
        from database import db

        coupon_enabled = str(db.get_config("COUPON_COMMAND_ENABLED", "OFF") or "OFF").strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ"}
        def command_desc(key, fallback):
            return db.get_config(key, fallback)
    except Exception:
        coupon_enabled = False
        def command_desc(key, fallback):
            return fallback

    commands = [
        BotCommand(command="start", description=command_desc("BOT_COMMAND_DESC_START", "Trang chủ / Mua gói")),
        BotCommand(command="me", description=command_desc("BOT_COMMAND_DESC_ME", "Kiểm tra gói & Hạn dùng")),
        BotCommand(command="support", description=command_desc("BOT_COMMAND_DESC_SUPPORT", "Liên hệ hỗ trợ Admin")),
        BotCommand(command="policy", description=command_desc("BOT_COMMAND_DESC_POLICY", "Đọc quy định nhóm")),
    ]
    if coupon_enabled:
        commands.insert(2, BotCommand(command="coupon", description=command_desc("BOT_COMMAND_DESC_COUPON", "Nhập mã giảm giá / mã kích hoạt")))
    await bot.set_my_commands(commands)

# Lưu trữ lịch sử bấm nút của User {user_id: timestamp}
user_cooldowns = {}
def is_spamming(user_id):
    current_time = time.time()
    last_time = user_cooldowns.get(user_id, 0)
    
    # Giới hạn 2 giây mới được bấm 1 lần
    if current_time - last_time < 2:
        return True
    
    user_cooldowns[user_id] = current_time
    return False
