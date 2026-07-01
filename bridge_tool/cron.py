import asyncio
import logging
import os

from dotenv import load_dotenv

from bridge_tool.app import run_reminders_once
from supabase_store import supabase_store

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def main():
    if not os.getenv("BOT_TOKEN"):
        raise RuntimeError("Missing BOT_TOKEN")
    if not supabase_store.enabled:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    await run_reminders_once()


if __name__ == "__main__":
    asyncio.run(main())

