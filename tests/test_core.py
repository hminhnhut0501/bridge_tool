import asyncio
import configparser
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

import httpx
from argon2 import PasswordHasher

from telegram_vault.api import create_app
from telegram_vault.config import Config
from telegram_vault.database import Database
from telegram_vault.engine import Engine
from telegram_vault.models import sanitize
from telegram_vault.providers import (
    AccountRateController,
    FloodPaused,
    MockTelegramProvider,
    topic_id,
)
from telegram_vault.storage import RcloneCryptStorage, StorageError


class CoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config(
            data_dir=self.root,
            telegram_mode="mock",
            password_hash=PasswordHasher().hash("test-password-123"),
            download_bandwidth=0,
            file_pause_enabled=False,
            request_pace=0,
            scan_batch_size=5,
        )
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(os.environ["RCLONE_CONFIG"])
        parser["crypt"]["remote"] = str(self.root / "encrypted")
        config_path = self.root / "crypt.conf"
        with config_path.open("w") as file:
            parser.write(file)
        config_path.chmod(0o600)
        self.storage = RcloneCryptStorage(str(config_path))
        self.db = Database(self.config.database_path)
        self.provider = MockTelegramProvider()
        self.engine = Engine(self.config, db=self.db, provider=self.provider, storage=self.storage)
        self.sid = self.db.add_source(self.provider.groups[0])
        await self.engine.refresh_topics(self.sid)

    async def asyncTearDown(self):
        if self.engine.tasks:
            await self.engine.stop()
        else:
            self.db.close()
        self.temp.cleanup()

    def source(self):
        return self.db.one("SELECT * FROM sources WHERE id=?", (self.sid,))

    def enqueue(self, index=0, priority=10):
        self.db.ingest(
            self.source(), self.provider.messages[-1001001][index], "TelegramVault_TEST", priority
        )
        return self.db.one("SELECT id FROM jobs ORDER BY id DESC LIMIT 1")["id"]

    async def test_dedupe_revision_and_stable_paths(self):
        message = self.provider.messages[-1001001][0]
        self.enqueue()
        path = self.db.one("SELECT remote_path FROM media")["remote_path"]
        self.db.execute("UPDATE sources SET name='Renamed' WHERE id=?", (self.sid,))
        self.db.upsert_topic(self.sid, 1, "Renamed topic")
        self.enqueue()
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 1)
        self.assertEqual(self.db.one("SELECT remote_path FROM media")["remote_path"], path)
        message.file_id = "new-file-revision"
        self.enqueue()
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 2)

    async def test_queue_priority_fairness_pause_and_claim_transaction(self):
        sid2 = self.db.add_source(self.provider.groups[1])
        self.enqueue(0)
        self.enqueue(1)
        self.db.ingest(
            self.db.one("SELECT * FROM sources WHERE id=?", (sid2,)),
            self.provider.messages[-1001002][0],
            "TelegramVault_TEST",
            100,
        )
        first = self.db.claim()
        self.assertEqual(first["source_id"], sid2)
        second = self.db.claim()
        self.assertEqual(second["source_id"], self.sid)
        self.db.execute("UPDATE sources SET paused=1 WHERE id=?", (self.sid,))
        self.assertIsNone(self.db.claim())
        with self.assertRaises(ValueError):
            self.db.transition(second["id"], "COMPLETED")

    async def test_scanner_checkpoints_resume_and_filters(self):
        await self.engine.scan_batch(self.source())
        self.assertEqual(self.source()["scan_cursor"], 5)
        await self.engine.scan_batch(self.source())
        self.assertEqual(self.source()["scan_cursor"], 10)
        await self.engine.scan_batch(self.source())
        self.assertEqual(self.source()["scan_cursor"], 12)
        self.assertFalse(self.source()["scan_requested"])
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 12)
        self.db.execute(
            "UPDATE sources SET scan_cursor=0,scan_target=NULL,scan_requested=1 WHERE id=?",
            (self.sid,),
        )
        await self.engine.scan_batch(self.source())
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 12)

    async def test_real_worker_completion_and_crash_after_remote_promotion(self):
        jid = self.enqueue()
        job = self.db.claim()
        await self.engine.run_job(job)
        job = self.db.job(jid)
        self.assertEqual(job["status"], "COMPLETED")
        self.assertEqual(
            await self.storage.hash_stream(job["remote_path"]), job["plaintext_sha256"]
        )
        # Simulate crash window: final exists but DB was VERIFYING.
        self.db.execute("UPDATE jobs SET status='VERIFYING',completed_at=NULL WHERE id=?", (jid,))
        self.db.transition(jid, "RETRY_WAIT", next_attempt=0)
        recovered = self.db.claim()
        await self.engine.run_job(recovered)
        self.assertEqual(self.db.job(jid)["status"], "COMPLETED")
        paths = [p async for p in self.storage.list("TelegramVault_TEST")]
        self.assertEqual(len(paths), 1)

    async def test_truncation_retries_without_false_complete(self):
        jid = self.enqueue()
        job = self.db.claim()

        async def truncated(job):
            yield b"not a complete video"

        self.provider.open_media_stream = truncated
        await self.engine.run_job(job)
        current = self.db.job(jid)
        self.assertEqual(current["status"], "RETRY_WAIT")
        self.assertIsNone(current["completed_at"])
        self.assertIsNone(await self.storage.exists(current["remote_path"]))

    async def test_remote_conflict_never_overwritten(self):
        jid = self.enqueue()
        job = self.db.claim()

        async def payload():
            yield b"unexpected data"

        await self.storage.put_stream(job["remote_path"], payload(), 15)
        await self.engine.run_job(job)
        self.assertEqual(self.db.job(jid)["status"], "FAILED")
        self.assertEqual((await self.storage.stat(job["remote_path"]))["Size"], 15)

    async def test_startup_recovers_and_keeps_cancel_intent(self):
        jid = self.enqueue()
        self.db.claim()
        self.db.execute("UPDATE jobs SET cancel_requested='CANCELLED' WHERE id=?", (jid,))
        self.db.execute("UPDATE sources SET paused=1 WHERE id=?", (self.sid,))
        await self.engine.start()
        self.assertEqual(self.db.job(jid)["status"], "CANCELLED")

    async def test_persisted_account_floodwait(self):
        from telethon.errors import FloodWaitError

        rate = AccountRateController(self.db, 0)
        calls = 0

        async def request():
            nonlocal calls
            calls += 1
            raise FloodWaitError(request=None, capture=300)

        with self.assertRaises(FloodPaused):
            await rate.call(request)
        self.assertGreaterEqual(self.db.setting("telegram_pause_until"), time.time() + 299)
        rate2 = AccountRateController(self.db, 0)
        with self.assertRaises(FloodPaused):
            await rate2.call(request)
        self.assertEqual(calls, 1)

    async def test_api_auth_csrf_filters_pagination_and_removal(self):
        app = create_app(self.config, self.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=self.config.app_url
        ) as client:
            self.assertEqual((await client.get("/api/status")).status_code, 401)
            login = await client.post(
                "/api/auth/login", json={"username": "admin", "password": "test-password-123"}
            )
            self.assertEqual(login.status_code, 200)
            self.assertIn("HttpOnly", login.headers["set-cookie"])
            self.assertNotIn("test-password", login.text)
            token = login.json()["csrf"]
            self.assertEqual((await client.post(f"/api/sources/{self.sid}/pause")).status_code, 403)
            headers = {"X-CSRF-Token": token, "Origin": self.config.app_url}
            self.assertEqual(
                (
                    await client.post(
                        f"/api/sources/{self.sid}/pause",
                        headers={**headers, "Origin": "https://evil.invalid"},
                    )
                ).status_code,
                403,
            )
            self.assertEqual(
                (await client.post(f"/api/sources/{self.sid}/pause", headers=headers)).status_code,
                200,
            )
            self.assertEqual(
                (
                    await client.patch(
                        f"/api/sources/{self.sid}", headers=headers, json={"min_size": None}
                    )
                ).status_code,
                422,
            )
            for i in range(4):
                self.enqueue(i)
            first = (await client.get("/api/jobs?limit=2")).json()
            second = (await client.get(f"/api/jobs?limit=2&cursor={first['next_cursor']}")).json()
            self.assertFalse({r["id"] for r in first["items"]} & {r["id"] for r in second["items"]})
            self.assertEqual((await client.get("/api/jobs?limit=100000")).status_code, 422)
            self.assertEqual(
                (await client.delete(f"/api/sources/{self.sid}", headers=headers)).status_code, 200
            )
            self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 0)
            self.assertIsNone(self.db.claim())

    async def test_google_429_pauses_storage_and_retries(self):
        jid = self.enqueue()
        job = self.db.claim()
        original = self.storage.put_stream

        async def rate_limited(*args, **kwargs):
            raise StorageError("google_rate_limit")

        self.storage.put_stream = rate_limited
        await self.engine.run_job(job)
        self.storage.put_stream = original
        self.assertEqual(self.db.job(jid)["status"], "RETRY_WAIT")
        self.assertEqual(self.db.job(jid)["last_error"], "google_rate_limit")
        self.assertGreater(self.db.setting("storage_pause_until"), time.time())
        self.assertEqual(self.db.job(jid)["uploaded"], 0)

    async def test_worker_cancel_closes_stream_and_sets_cancelled(self):
        jid = self.enqueue()
        job = self.db.claim()
        entered, closed = asyncio.Event(), asyncio.Event()

        async def stalled(job):
            try:
                yield b"x" * 524288
                entered.set()
                await asyncio.Event().wait()
            finally:
                closed.set()

        self.provider.open_media_stream = stalled
        task = asyncio.create_task(self.engine.run_job(job))
        self.engine.active[jid] = task
        await entered.wait()
        self.engine.control_job(jid, "cancel")
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(closed.is_set())
        self.assertEqual(self.db.job(jid)["status"], "CANCELLED")
        self.assertIsNone(await self.storage.exists(job["remote_path"]))

    async def test_selected_topics_and_updated_filters_block_queued_jobs(self):
        self.enqueue(0)
        self.enqueue(1)
        self.db.execute("UPDATE sources SET all_topics=0 WHERE id=?", (self.sid,))
        self.db.execute(
            "UPDATE topics SET selected=0 WHERE source_id=? AND topic_id=1", (self.sid,)
        )
        job = self.db.claim()
        self.assertEqual(job["topic_id"], 42)
        self.assertIsNone(self.db.claim())
        self.db.transition(job["id"], "RETRY_WAIT", next_attempt=0)
        self.db.execute("UPDATE sources SET min_size=999999999 WHERE id=?", (self.sid,))
        self.assertIsNone(self.db.claim())

    async def test_snapshot_restores_queue_and_settings(self):
        self.enqueue()
        self.db.set_setting("runtime_settings", {"max_retries": 7})
        target = self.root / "snapshot.sqlite3"
        self.db.backup(target)
        restored = Database(target)
        self.assertEqual(restored.one("SELECT COUNT(*) AS n FROM jobs")["n"], 1)
        self.assertEqual(restored.setting("runtime_settings")["max_retries"], 7)
        restored.close()

    async def test_chunked_request_size_limit(self):
        app = create_app(self.config, self.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=self.config.app_url
        ) as client:

            async def huge():
                for _ in range(100):
                    yield b"x" * 1024

            response = await client.post(
                "/api/auth/login", content=huge(), headers={"Content-Type": "application/json"}
            )
            self.assertEqual(response.status_code, 413)

    async def test_login_rate_limiting(self):
        app = create_app(self.config, self.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=self.config.app_url
        ) as client:
            for _ in range(5):
                self.assertEqual(
                    (
                        await client.post(
                            "/api/auth/login", json={"username": "admin", "password": "wrong"}
                        )
                    ).status_code,
                    401,
                )
            self.assertEqual(
                (
                    await client.post(
                        "/api/auth/login",
                        json={"username": "admin", "password": "test-password-123"},
                    )
                ).status_code,
                429,
            )


class PathTests(unittest.TestCase):
    def test_unicode_sanitizer_and_topic_mapping(self):
        value = sanitize("../a\\b/\u202eTên Việt\x00" * 100)
        self.assertNotIn("/", value)
        self.assertNotIn("\\", value)
        self.assertNotIn("\u202e", value)
        self.assertLessEqual(len(value.encode()), 100)
        self.assertIn("Tên Việt", value)
        header = SimpleNamespace(forum_topic=True, reply_to_top_id=42, reply_to_msg_id=999)
        self.assertEqual(topic_id(SimpleNamespace(reply_to=header), True), 42)
        self.assertEqual(topic_id(SimpleNamespace(reply_to=None), True), 1)
        self.assertEqual(topic_id(SimpleNamespace(reply_to=header), False), 0)


if __name__ == "__main__":
    unittest.main()
