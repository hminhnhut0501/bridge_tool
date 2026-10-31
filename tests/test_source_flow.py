import unittest

import httpx

from scripts.audit_simulations import enqueue, login, sandbox
from telegram_vault.api import create_app


class SourceFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_start_and_configure_modes_and_global_gate(self):
        async with sandbox() as c:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=create_app(c.config, c.engine)),
                base_url=c.config.app_url,
            ) as client:
                h = await login(client)
                ref = str(c.provider.groups[1]["chat_id"])
                result = await client.post(
                    "/api/sources", headers=h, json={"reference": ref, "rights_confirmed": True}
                )
                sid = result.json()["id"]
                self.assertEqual(result.json()["paused"], 1)
                items = (await client.get("/api/sources")).json()["items"]
                self.assertEqual(next(s for s in items if s["id"] == sid)["flow"]["stage"], "ready")
                self.assertEqual(
                    (await client.post(f"/api/sources/{sid}/scan", headers=h)).status_code, 409
                )
                c.db.set_setting("scheduler_paused", True)
                r = await client.post(
                    "/api/sources",
                    headers=h,
                    json={"reference": ref, "rights_confirmed": True, "start": True},
                )
                self.assertEqual(r.status_code, 409)
                self.assertEqual(
                    c.db.one("SELECT paused FROM sources WHERE id=?", (sid,))["paused"], 1
                )
                c.db.set_setting("scheduler_paused", False)
                r = await client.post(
                    "/api/sources",
                    headers=h,
                    json={"reference": ref, "rights_confirmed": True, "start": True},
                )
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(r.json()["paused"], 0)
                self.assertEqual(r.json()["scan_requested"], 1)
                items = (await client.get("/api/sources")).json()["items"]
                self.assertEqual(
                    next(s for s in items if s["id"] == sid)["flow"]["stage"], "scan_queued"
                )

    async def test_scan_progress_active_files_and_empty_watch_state(self):
        async with sandbox() as c:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=create_app(c.config, c.engine)),
                base_url=c.config.app_url,
            ) as client:
                await login(client)
                c.db.execute(
                    "UPDATE sources SET scan_target=100,scan_cursor=45,scanned=17 WHERE id=?",
                    (c.sid,),
                )
                enqueue(c, 0)
                job = c.db.claim()
                c.engine.progress[job["id"]] = {"speed": 1234}
                row = (await client.get("/api/sources")).json()["items"][0]
                self.assertEqual(row["flow"]["stage"], "scanning")
                self.assertEqual(row["scan_cursor"], 45)
                self.assertEqual(row["flow"]["active"], 1)
                self.assertEqual(row["active_files"][0]["speed"], 1234)
                c.db.execute("DELETE FROM transfers")
                c.db.execute("DELETE FROM jobs")
                c.db.execute(
                    "UPDATE sources SET scan_target=NULL,scan_requested=0,last_scan=1 WHERE id=?",
                    (c.sid,),
                )
                row = (await client.get("/api/sources")).json()["items"][0]
                self.assertEqual(row["flow"]["stage"], "watching")
                self.assertIn("chưa có file phù hợp", row["flow"]["detail"])
