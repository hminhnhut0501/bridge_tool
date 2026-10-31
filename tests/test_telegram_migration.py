import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from telethon import TelegramClient, errors, functions, types

from scripts.audit_simulations import sandbox
from telegram_vault.providers import TelethonProvider


class TelegramMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_retries_real_telethon_call_after_phone_migration(self):
        async with sandbox() as c:
            c.config.api_id, c.config.api_hash = 12345, "a" * 32
            provider = TelethonProvider(c.config, c.engine.rate)
            with patch.object(TelegramClient, "connect", new=AsyncMock()), patch.object(
                TelegramClient, "is_user_authorized", new=AsyncMock(return_value=False)
            ):
                await provider.connect(lambda *args: None)
            client = provider.client
            calls = []

            class Sender:
                def send(self, request, **kwargs):
                    calls.append(request)
                    future = asyncio.get_running_loop().create_future()
                    if len(calls) == 1:
                        future.set_exception(errors.PhoneMigrateError(request=request, capture=5))
                    else:
                        future.set_result(True)
                    return future

            request = functions.auth.SendCodeRequest(
                phone_number="+12025550123", api_id=12345,
                api_hash="a" * 32, settings=types.CodeSettings()
            )
            client._switch_dc = AsyncMock()
            client.is_user_authorized = AsyncMock(return_value=False)
            result = await client._call(Sender(), request)
            self.assertTrue(result)
            self.assertEqual(len(calls), 2)
            client._switch_dc.assert_awaited_once_with(5)
            # The retry budget must not hide or sleep through a FloodWait.
            class FloodSender:
                def send(self, request, **kwargs):
                    future = asyncio.get_running_loop().create_future()
                    future.set_exception(errors.FloodWaitError(request=request, capture=60))
                    return future
            with self.assertRaises(errors.FloodWaitError):
                await client._call(FloodSender(), request)
            await client.disconnect()
