import asyncio
import time


class TelegramRateController:
    """Single shared request gate; monotonic FloodWait deadline."""

    def __init__(self, pace=1.0):
        self.pace = pace
        self.deadline = 0.0
        self.lock = asyncio.Lock()

    async def call(self, operation):
        from telethon.errors import FloodWaitError

        async with self.lock:
            while True:
                await asyncio.sleep(max(0, self.deadline - time.monotonic()))
                try:
                    result = await operation()
                    self.deadline = time.monotonic() + self.pace
                    return result
                except FloodWaitError as error:
                    self.deadline = time.monotonic() + error.seconds
