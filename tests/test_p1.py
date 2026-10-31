"""Regression coverage for the four reproduced P1 defects."""

import unittest

from scripts.audit_simulations import (
    corrupted_incomplete_retry,
    scan_selection_race,
    unbounded_login_parallelism,
    worker_database_error,
)


class P1RegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_topic_change_during_scan(self):
        evidence, passed = await scan_selection_race()
        self.assertTrue(passed, evidence)

    async def test_corrupt_temporary_object_recovers(self):
        evidence, passed = await corrupted_incomplete_retry()
        self.assertTrue(passed, evidence)

    async def test_worker_db_error_recovers_and_health_degrades(self):
        evidence, passed = await worker_database_error()
        self.assertTrue(passed, evidence)

    async def test_parallel_login_hash_budget(self):
        evidence, passed = await unbounded_login_parallelism()
        self.assertTrue(passed, evidence)

    async def test_cancelled_login_keeps_hash_slot_until_thread_finishes(self):
        import asyncio
        import threading
        from types import SimpleNamespace
        from unittest.mock import patch

        import httpx

        from scripts.audit_simulations import sandbox
        from telegram_vault.api import create_app

        async with sandbox() as c:
            entered = threading.Event()
            release = threading.Event()
            calls = 0

            def verify(*args):
                nonlocal calls
                calls += 1
                entered.set()
                release.wait(5)
                return False

            with patch(
                "telegram_vault.api.PasswordHasher", return_value=SimpleNamespace(verify=verify)
            ):
                app = create_app(c.config, c.engine)
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
                ) as client:
                    payload = {"username": "admin", "password": "incorrect"}
                    first = asyncio.create_task(client.post("/api/auth/login", json=payload))
                    while not entered.is_set():
                        await asyncio.sleep(0.01)
                    first.cancel()
                    await asyncio.gather(first, return_exceptions=True)
                    second = asyncio.create_task(client.post("/api/auth/login", json=payload))
                    while calls < 2:
                        await asyncio.sleep(0.01)
                    busy = await client.post("/api/auth/login", json=payload)
                    self.assertEqual(busy.status_code, 429)
                    self.assertEqual(calls, 2)
                    release.set()
                    self.assertEqual((await second).status_code, 401)
                    await asyncio.sleep(0.02)
                    self.assertEqual(
                        (await client.post("/api/auth/login", json=payload)).status_code, 401
                    )

    async def test_scan_reset_while_latest_id_is_pending(self):
        import asyncio

        from scripts.audit_simulations import sandbox, source

        async with sandbox() as c:
            entered, release = asyncio.Event(), asyncio.Event()
            original = c.provider.latest_id

            async def delayed(item):
                entered.set()
                await release.wait()
                return await original(item)

            c.provider.latest_id = delayed
            old = asyncio.create_task(c.engine.scan_batch(source(c)))
            await entered.wait()
            c.db.execute(
                "UPDATE sources SET scan_generation=scan_generation+1,scan_cursor=0,scan_target=NULL WHERE id=?",
                (c.sid,),
            )
            release.set()
            await old
            self.assertIsNone(source(c)["scan_target"])
            self.assertEqual(source(c)["scan_cursor"], 0)
            c.provider.latest_id = original
            while source(c)["scan_requested"]:
                await c.engine.scan_batch(source(c))
            self.assertEqual(c.db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 12)

    async def test_worker_recovers_job_after_unhandled_database_error(self):
        import asyncio
        import sqlite3
        import time

        from scripts.audit_simulations import enqueue, sandbox

        async with sandbox() as c:
            enqueue(c)
            c.db.execute(
                "UPDATE sources SET scan_requested=0,last_scan=?,last_reconcile=?",
                (time.time(), time.time()),
            )
            original = c.engine.run_job
            calls = 0

            async def fail_once(job):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise sqlite3.OperationalError("database is locked")
                await original(job)

            c.engine.run_job = fail_once
            await c.engine.start()
            deadline = time.monotonic() + 10
            while c.db.job(1)["status"] != "COMPLETED" and time.monotonic() < deadline:
                await asyncio.sleep(0.05)
            self.assertEqual(c.db.job(1)["status"], "COMPLETED")
            self.assertGreaterEqual(calls, 2)
            self.assertTrue(c.engine.ready())

    def test_schema_v1_migration_preserves_source_and_creates_backup(self):
        import sqlite3
        import tempfile
        from pathlib import Path

        from telegram_vault.database import SCHEMA, Database

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vault.sqlite3"
            with sqlite3.connect(path) as connection:
                connection.executescript(SCHEMA + "PRAGMA user_version=1;")
                connection.execute(
                    "INSERT INTO sources(chat_id,name,path_name,kind,created_at) VALUES(1,'test','test','channel',0)"
                )
            connection.close()
            db = Database(path)
            try:
                self.assertEqual(db.one("SELECT * FROM sources")["scan_generation"], 0)
                self.assertEqual(db.one("SELECT * FROM sources")["name"], "test")
                self.assertEqual(db.connection.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertTrue(path.with_suffix(".pre-v2.sqlite3").exists())
            finally:
                db.close()
