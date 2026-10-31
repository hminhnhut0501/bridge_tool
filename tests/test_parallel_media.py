import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from scripts.audit_simulations import sandbox
from telegram_vault.providers import TelethonProvider


class ParallelMediaTests(unittest.IsolatedAsyncioTestCase):
    async def test_parallel_chunks_order_tail_and_cleanup(self):
        async with sandbox() as c:
            provider = TelethonProvider(c.config, c.engine.rate)
            provider.status = "connected"
            payload = bytes(range(256)) * 40000 + b"tail"
            active = peak = 0
            closed = []

            class Iterator:
                def __init__(self, offset, stride, limit, **kwargs):
                    self.offset, self.stride, self.limit = offset, stride, limit

                async def __anext__(self):
                    nonlocal active, peak
                    if not self.limit:
                        raise StopAsyncIteration
                    active += 1
                    peak = max(peak, active)
                    try:
                        await asyncio.sleep(0.001)
                        chunk = payload[self.offset : self.offset + 524288]
                        self.offset += self.stride
                        self.limit -= 1
                        return chunk
                    finally:
                        active -= 1

                async def close(self):
                    closed.append(self)

            provider.client = SimpleNamespace(
                get_input_entity=AsyncMock(return_value="peer"),
                get_messages=AsyncMock(
                    return_value=SimpleNamespace(document=SimpleNamespace(id=123), media="media")
                ),
                iter_download=lambda media, **kwargs: Iterator(**kwargs),
            )
            job = dict(chat_id=1, message_id=1, telegram_file_id="123", size=len(payload))
            output = b"".join([chunk async for chunk in provider.open_media_stream(job)])
            self.assertEqual(output, payload)
            self.assertEqual(peak, 8)
            self.assertEqual(len(closed), 8)

    async def test_cancel_stream_closes_all_lanes(self):
        async with sandbox() as c:
            provider = TelethonProvider(c.config, c.engine.rate)
            provider.status = "connected"
            closed = []

            class Iterator:
                async def __anext__(self):
                    return b"x" * 524288

                async def close(self):
                    closed.append(self)

            provider.client = SimpleNamespace(
                get_input_entity=AsyncMock(return_value="peer"),
                get_messages=AsyncMock(
                    return_value=SimpleNamespace(document=SimpleNamespace(id=123), media="media")
                ),
                iter_download=lambda *args, **kwargs: Iterator(),
            )
            stream = provider.open_media_stream(
                dict(chat_id=1, message_id=1, telegram_file_id="123", size=524288 * 16)
            )
            await anext(stream)
            await stream.aclose()
            self.assertEqual(len(closed), 8)
