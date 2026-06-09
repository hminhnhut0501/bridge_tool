import asyncio
import logging

from aiogram import Router

from helpers import recompute_bot_runtime_state

router = Router()


async def bot_runtime_worker():
    logging.info("🧭 Bot runtime state worker đã khởi động.")
    await recompute_bot_runtime_state()
    while True:
        try:
            recompute_bot_runtime_state()
        except Exception as exc:
            logging.error("❌ Bot runtime state worker lỗi: %s", exc)
        await asyncio.sleep(15)
