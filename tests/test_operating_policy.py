import time
import unittest

import httpx
from telethon.errors import FloodWaitError

from scripts.audit_simulations import login, sandbox
from telegram_vault.api import create_app
from telegram_vault.providers import AccountRateController, FloodPaused


class OperatingPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def test_source_requires_rights_ack_and_starts_paused(self):
        async with sandbox() as c:
            app = create_app(c.config, c.engine)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
            ) as client:
                headers = await login(client)
                chat = c.provider.groups[1]["chat_id"]
                response = await client.post(
                    "/api/sources", json={"chat_id": chat}, headers=headers
                )
                self.assertEqual(response.status_code, 422)
                self.assertIsNone(c.db.one("SELECT id FROM sources WHERE chat_id=?", (chat,)))
                response = await client.post(
                    "/api/sources",
                    json={"chat_id": chat, "rights_confirmed": True},
                    headers=headers,
                )
                self.assertEqual(response.status_code, 200)
                source = response.json()
                self.assertEqual(source["paused"], 1)
                self.assertGreater(c.db.setting(f"source_rights_confirmed:{source['id']}"), 0)
                c.db.ingest(source, c.provider.messages[chat][0], c.config.storage_root)
                self.assertIsNone(c.db.claim())
                response = await client.post(f"/api/sources/{source['id']}/resume", headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertIsNotNone(c.db.claim())

    async def test_three_floodwaits_trigger_persisted_one_hour_cooldown(self):
        async with sandbox() as c:

            async def limited():
                raise FloodWaitError(request=None, capture=10)

            for index in range(3):
                # Accelerate the earlier waits in this isolated DB; history remains.
                c.db.set_setting("telegram_pause_until", 0)
                rate = AccountRateController(c.db, 0)
                with self.assertRaises(FloodPaused) as caught:
                    await rate.call(limited)
                self.assertGreaterEqual(caught.exception.seconds, 3600 if index == 2 else 11)
            restarted = AccountRateController(c.db, 0)
            calls = 0

            async def operation():
                nonlocal calls
                calls += 1

            with self.assertRaises(FloodPaused):
                await restarted.call(operation)
            self.assertEqual(calls, 0)
            self.assertGreater(c.db.setting("telegram_pause_until") - time.time(), 3590)
            self.assertEqual(len(c.db.setting("telegram_flood_history")), 3)
