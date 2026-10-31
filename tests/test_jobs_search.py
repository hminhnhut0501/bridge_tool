import unittest

import httpx

from scripts.audit_simulations import enqueue, login, sandbox
from telegram_vault.api import create_app


class JobsSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_precedes_pagination_and_combines_scope_and_status(self):
        async with sandbox() as c:
            enqueue(c, 0)
            enqueue(c, 1)
            first, second = c.db.rows("SELECT id,media_id FROM jobs ORDER BY id")
            c.db.execute(
                "UPDATE media SET original_filename='target %_ file.mp4' WHERE id=?",
                (first["media_id"],),
            )
            c.db.execute(
                "UPDATE media SET original_filename='Other.mp4',remote_path='Root/unique-destination.mp4' WHERE id=?",
                (second["media_id"],),
            )
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=create_app(c.config, c.engine)),
                base_url=c.config.app_url,
            ) as client:
                await login(client)
                rows = (await client.get("/api/jobs", params={"q": "%_", "limit": 1})).json()
                self.assertEqual([r["id"] for r in rows["items"]], [first["id"]])
                self.assertIsNone(rows["next_cursor"])
                rows = (
                    await client.get(
                        "/api/jobs",
                        params={"q": "UNIQUE-destination", "source_id": c.sid, "status": "QUEUED"},
                    )
                ).json()
                self.assertEqual([r["id"] for r in rows["items"]], [second["id"]])
                rows = (
                    await client.get("/api/jobs", params={"q": "Other", "status": "COMPLETED"})
                ).json()
                self.assertEqual(rows["items"], [])
                rows = (
                    await client.get("/api/jobs", params={"q": "Other", "source_id": 999})
                ).json()
                self.assertEqual(rows["items"], [])
                self.assertEqual((await client.get("/api/transfers")).status_code, 200)
