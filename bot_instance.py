import os
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from aiogram import Bot, Dispatcher
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    _AIOGRAM_AVAILABLE = True
except Exception:
    BotCommand = BotCommandScopeAllGroupChats = BotCommandScopeAllPrivateChats = None
    _AIOGRAM_AVAILABLE = False

    class _FallbackBot:
        async def set_my_commands(self, *args, **kwargs):
            return None

    class _FallbackDispatcher:
        def include_router(self, *args, **kwargs):
            return None

    bot = _FallbackBot()
    dp = _FallbackDispatcher()

async def set_commands():
    if not _AIOGRAM_AVAILABLE:
        return
    try:
        from database import db

        def command_desc(key, fallback):
            return db.get_config(key, fallback)
    except Exception:
        def command_desc(key, fallback):
            return fallback

    def enabled(key, default="ON"):
        return str(db.get_config(key, default) or default).strip().upper() in {"ON", "TRUE", "YES", "1", "CÓ"}

    private_commands = []
    group_commands = []

    def add_if(target, flag_key, command, desc_key, fallback):
        if enabled(flag_key, "ON"):
            target.append(BotCommand(command=command, description=command_desc(desc_key, fallback)))

    add_if(private_commands, "BOT_MENU_PRIVATE_START_ENABLED", "start", "BOT_COMMAND_DESC_START", "Trang chủ / Mua gói")
    add_if(private_commands, "BOT_MENU_PRIVATE_LANG_ENABLED", "lang", "BOT_COMMAND_DESC_LANG", "Đổi ngôn ngữ")
    add_if(private_commands, "BOT_MENU_PRIVATE_ME_ENABLED", "me", "BOT_COMMAND_DESC_ME", "Kiểm tra gói & Hạn dùng")
    add_if(private_commands, "BOT_MENU_PRIVATE_SUPPORT_ENABLED", "support", "BOT_COMMAND_DESC_SUPPORT", "Liên hệ hỗ trợ Admin")
    add_if(private_commands, "BOT_MENU_PRIVATE_POLICY_ENABLED", "policy", "BOT_COMMAND_DESC_POLICY", "Đọc quy định nhóm")

    add_if(group_commands, "BOT_MENU_GROUP_START_ENABLED", "start", "BOT_COMMAND_DESC_START", "Trang chủ / Mua gói")
    add_if(group_commands, "BOT_MENU_GROUP_LANG_ENABLED", "lang", "BOT_COMMAND_DESC_LANG", "Đổi ngôn ngữ")
    add_if(group_commands, "BOT_MENU_GROUP_ME_ENABLED", "me", "BOT_COMMAND_DESC_ME", "Kiểm tra gói & Hạn dùng")
    add_if(group_commands, "BOT_MENU_GROUP_SUPPORT_ENABLED", "support", "BOT_COMMAND_DESC_SUPPORT", "Liên hệ hỗ trợ Admin")
    add_if(group_commands, "BOT_MENU_GROUP_POLICY_ENABLED", "policy", "BOT_COMMAND_DESC_POLICY", "Đọc quy định nhóm")

    if enabled("BOT_MENU_PRIVATE_COUPON_ENABLED", "ON"):
        private_commands.insert(
            2,
            BotCommand(
                command="code",
                description=command_desc(
                    "BOT_COMMAND_DESC_CODE",
                    "Nhập mã / code / hidden code",
                ),
            ),
        )

    await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())

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
