import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from telethon.errors import FloodWaitError

from scripts.audit_simulations import sandbox
from telegram_vault.providers import AccountRateController, FloodPaused


class MediaRateTests(unittest.IsolatedAsyncioTestCase):
    async def test_chunks_do_not_wait_for_metadata_lock_or_pacing(self):
        async with sandbox() as c:
            rate = AccountRateController(c.db, 0.5)
            rate.next_request = float("inf")
            async with rate.lock:
                with patch("telegram_vault.providers.asyncio.sleep", new=AsyncMock()) as sleep:
                    self.assertEqual(
                        await asyncio.wait_for(
                            rate.call(AsyncMock(return_value=b"data"), media=True), 1
                        ),
                        b"data",
                    )
                    sleep.assert_not_awaited()
            self.assertEqual(rate.next_request, float("inf"))

    async def test_media_floodwait_blocks_metadata_and_following_chunks(self):
        async with sandbox() as c:
            rate = AccountRateController(c.db, 0.5)
            operation = AsyncMock(side_effect=FloodWaitError(request=None, capture=20))
            with self.assertRaises(FloodPaused):
                await rate.call(operation, media=True)
            for media in (False, True):
                next_call = AsyncMock()
                with self.assertRaises(FloodPaused):
                    await rate.call(next_call, media=media)
                next_call.assert_not_awaited()
