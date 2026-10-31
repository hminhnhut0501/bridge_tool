import asyncio
import unittest

import httpx

from scripts.audit_simulations import enqueue, login, sandbox
from telegram_vault.api import create_app


class QueueControlTests(unittest.IsolatedAsyncioTestCase):
    async def test_global_pause_resume_and_cancel_cover_all_jobs(self):
        async with sandbox() as c:
            enqueue(c, 0)
            enqueue(c, 1)
            await c.engine.control_scope("pause")
            self.assertIsNone(c.db.claim())
            await c.engine.control_scope("resume")
            self.assertIsNotNone(c.db.claim())
            # Simulate stopped claim without a worker task.
            c.db.execute("UPDATE jobs SET status='QUEUED'")
            await c.engine.control_scope("cancel")
            self.assertEqual(
                {r["status"] for r in c.db.rows("SELECT status FROM jobs")}, {"CANCELLED"}
            )
            self.assertTrue(c.db.setting("scheduler_paused"))

    async def test_delete_topic_preserves_other_topic_and_completed_backup(self):
        async with sandbox() as c:
            enqueue(c, 0)
            enqueue(c, 1)
            enqueue(c, 2)
            c.db.execute("UPDATE jobs SET status='COMPLETED' WHERE id=1")
            result = await c.engine.control_scope("delete", source_id=c.sid, topic_id=1)
            self.assertEqual(result["removed"], 1)
            self.assertIsNotNone(c.db.job(1))
            self.assertIsNotNone(c.db.job(2))
            self.assertIsNone(c.db.job(3))
            self.assertEqual(
                c.db.one("SELECT selected FROM topics WHERE source_id=? AND topic_id=1", (c.sid,))[
                    "selected"
                ],
                0,
            )
            self.assertEqual(
                c.db.one("SELECT selected FROM topics WHERE source_id=? AND topic_id=42", (c.sid,))[
                    "selected"
                ],
                1,
            )
            # A rescan of deleted media must not recreate its job.
            enqueue(c, 2)
            self.assertIsNone(c.db.job(3))

    async def test_pause_active_waits_cleanup_and_releases_retry_job(self):
        async with sandbox() as c:
            enqueue(c, 0)
            job = c.db.claim()
            started = asyncio.Event()

            async def blocked(job):
                started.set()
                await asyncio.sleep(60)
                yield b""

            c.provider.open_media_stream = blocked
            task = asyncio.create_task(c.engine.run_job(job))
            c.engine.active[job["id"]] = task
            await started.wait()
            await c.engine.control_scope("pause")
            self.assertTrue(task.done())
            self.assertEqual(c.db.job(job["id"])["status"], "RETRY_WAIT")
            self.assertIsNone(c.db.claim())
            await c.engine.control_scope("delete", job_id=job["id"])
            self.assertIsNone(c.db.job(job["id"]))

    async def test_api_requires_auth_and_keeps_completed_records(self):
        async with sandbox() as c:
            enqueue(c, 0)
            c.db.execute("UPDATE jobs SET status='COMPLETED'")
            app = create_app(c.config, c.engine)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
            ) as client:
                self.assertEqual(
                    (
                        await client.post("/api/queue/control", json={"operation": "delete"})
                    ).status_code,
                    401,
                )
                headers = await login(client)
                self.assertEqual(
                    (
                        await client.post(
                            "/api/queue/control",
                            headers=headers,
                            json={"operation": "delete", "job_id": 1},
                        )
                    ).status_code,
                    409,
                )
                result = await client.post(
                    "/api/queue/control",
                    headers=headers,
                    json={"operation": "delete", "source_id": c.sid},
                )
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(result.json()["removed"], 0)
                self.assertIsNotNone(c.db.job(1))
                self.assertEqual(
                    c.db.one("SELECT deleted FROM sources WHERE id=?", (c.sid,))["deleted"], 1
                )

    async def test_cancel_before_worker_starts_releases_claim(self):
        async with sandbox() as c:
            enqueue(c, 0)
            job = c.db.claim()
            task = asyncio.create_task(asyncio.sleep(60))
            c.engine.active[job["id"]] = task
            await c.engine.control_scope("pause")
            self.assertTrue(task.cancelled())
            self.assertEqual(c.db.job(job["id"])["status"], "RETRY_WAIT")
            self.assertEqual(
                c.db.one("SELECT status FROM transfers WHERE job_id=?", (job["id"],))["status"],
                "RETRY_WAIT",
            )
