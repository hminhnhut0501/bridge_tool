import asyncio
from bot_instance import bot, dp, set_commands
from bot_handlers import router
from database import db

async def main():
    db.connect()
    dp.include_router(router)
    await set_commands() # Thêm dòng này
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())