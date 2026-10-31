import time
import unittest
from unittest.mock import patch

import httpx

from scripts.audit_simulations import enqueue, login, sandbox
from telegram_vault.api import create_app
from telegram_vault.database import Database


class FilePauseTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_file_blocks_next_claim_and_survives_reopen(self):
        async with sandbox() as c:
            c.config.file_pause_enabled = True
            c.config.file_pause_min_seconds = 5
            c.config.file_pause_max_seconds = 60
            enqueue(c, 0)
            enqueue(c, 1)
            job = c.db.claim()
            with patch("telegram_vault.engine.random.uniform", return_value=17) as random_delay:
                await c.engine.run_job(job)
            self.assertEqual(c.db.job(job["id"])["status"], "COMPLETED")
            random_delay.assert_called_once_with(5, 60)
            deadline = c.db.setting("transfer_pause_until")
            self.assertGreater(deadline - time.time(), 15)
            self.assertIsNone(c.db.claim())
            reopened = Database(c.config.database_path)
            try:
                self.assertEqual(reopened.setting("transfer_pause_until"), deadline)
                self.assertIsNone(reopened.claim())
                with patch("telegram_vault.database.time.time", return_value=deadline + 1):
                    self.assertIsNotNone(reopened.claim())
            finally:
                reopened.close()

    async def test_failure_has_no_success_pause(self):
        async with sandbox() as c:
            c.config.file_pause_enabled = True
            enqueue(c)

            async def disconnected(job):
                yield b"x" * 524288
                raise ConnectionResetError()

            c.provider.open_media_stream = disconnected
            await c.engine.run_job(c.db.claim())
            self.assertEqual(c.db.job(1)["status"], "RETRY_WAIT")
            self.assertEqual(c.db.setting("transfer_pause_until", 0), 0)

    async def test_settings_validate_persist_preserve_and_disable_current_rest(self):
        async with sandbox() as c:
            app = create_app(c.config, c.engine)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
            ) as client:
                headers = await login(client)
                form = (await client.get("/api/settings")).json()
                base = {
                    key: form[key]
                    for key in [
                        "download_bandwidth",
                        "upload_bandwidth",
                        "reconciliation_interval",
                        "max_retries",
                        "verify_hash",
                    ]
                }
                good = {
                    **base,
                    "file_pause_enabled": True,
                    "file_pause_min_seconds": 7,
                    "file_pause_max_seconds": 23,
                }
                r = await client.patch("/api/settings", json=good, headers=headers)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(c.db.setting("runtime_settings")["file_pause_max_seconds"], 23)
                bad = await client.patch(
                    "/api/settings", json={**good, "file_pause_min_seconds": 50}, headers=headers
                )
                self.assertEqual(bad.status_code, 422)
                self.assertEqual(c.config.file_pause_min_seconds, 7)
                self.assertEqual(c.db.setting("runtime_settings")["file_pause_min_seconds"], 7)
                # Existing clients that omit new fields must retain the saved range.
                r = await client.patch("/api/settings", json=base, headers=headers)
                self.assertEqual(r.json()["file_pause_max_seconds"], 23)
                c.db.set_setting("transfer_pause_until", time.time() + 60)
                r = await client.patch(
                    "/api/settings", json={**base, "file_pause_enabled": False}, headers=headers
                )
                self.assertEqual(r.status_code, 200)
                self.assertEqual(c.db.setting("transfer_pause_until"), 0)
                self.assertFalse(c.db.setting("runtime_settings")["file_pause_enabled"])

    async def test_auxiliary_tasks_and_rest_do_not_make_health_unready(self):
        import asyncio

        async with sandbox() as c:
            await c.engine.start()
            c.db.set_setting("transfer_pause_until", time.time() + 30)
            auxiliary = asyncio.create_task(asyncio.sleep(30))
            c.engine.tasks.append(auxiliary)
            self.assertTrue(c.engine.ready())
            app = create_app(c.config, c.engine)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
            ) as client:
                self.assertEqual((await client.get("/api/health")).status_code, 200)
