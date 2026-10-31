import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from argon2 import PasswordHasher
from telethon import errors

from telegram_vault.api import create_app
from telegram_vault.config import Config
from telegram_vault.engine import Engine


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.authorized = False
        self.user_id = 123
        self.sent = 0
        self.need_password = False
        self.flood = False

    def add_event_handler(self, *args):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def is_user_authorized(self):
        return self.authorized

    async def send_code_request(self, phone):
        self.sent += 1
        if self.flood:
            raise errors.FloodWaitError(request=None, capture=60)
        return SimpleNamespace(phone_code_hash="private-code-hash")

    async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
        if code == "00000":
            raise errors.PhoneCodeInvalidError(request=None)
        if code == "11111":
            raise errors.PhoneCodeExpiredError(request=None)
        if code and self.need_password:
            raise errors.SessionPasswordNeededError(request=None)
        if password == "wrong-password":
            raise errors.PasswordHashInvalidError(request=None)
        self.authorized = True

    async def get_me(self):
        return SimpleNamespace(id=self.user_id)

    async def log_out(self):
        self.authorized = False
        return True


class TelegramWebTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Config(
            data_dir=Path(self.temp.name),
            telegram_mode="real",
            request_pace=0,
            password_hash=PasswordHasher().hash("web-test-password-123"),
        )
        self.engine = Engine(self.config)
        self.fake = FakeClient()
        self.patcher = patch("telegram_vault.providers.TelegramClient", return_value=self.fake)
        self.patcher.start()
        self.app = create_app(self.config, self.engine)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url=self.config.app_url
        )
        r = await self.client.post(
            "/api/auth/login", json={"username": "admin", "password": "web-test-password-123"}
        )
        self.headers = {"X-CSRF-Token": r.json()["csrf"]}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.provider.close()
        self.engine.db.close()
        self.patcher.stop()
        self.temp.cleanup()

    async def post(self, path, body=None):
        return await self.client.post("/api/telegram/" + path, json=body, headers=self.headers)

    async def configure(self):
        r = await self.post("credentials", {"api_id": 12345, "api_hash": "a" * 32})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["step"], "phone")

    async def send(self):
        r = await self.post("send-code", {"phone": "+84901234567"})
        self.assertEqual(r.status_code, 200, r.text)
        return r

    async def test_credentials_otp_connected_and_private_persistence(self):
        await self.configure()
        path = self.config.data_dir / "telegram-api.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with patch.dict(
            os.environ,
            {
                "DATA_DIR": str(self.config.data_dir),
                "TELEGRAM_MODE": "real",
                "TELEGRAM_API_ID": "999",
                "TELEGRAM_API_HASH": "old",
            },
            clear=True,
        ):
            restored = Config.from_env()
        self.assertEqual(restored.api_id, 12345)
        self.assertEqual(restored.api_hash, "a" * 32)
        r = await self.send()
        self.assertNotIn("+84901234567", r.text)
        self.assertNotIn("private-code-hash", r.text)
        bad = await self.post("verify-code", {"code": "00000"})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual((await self.client.get("/api/auth/me")).status_code, 200)
        ok = await self.post("verify-code", {"code": "12345"})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["step"], "connected")
        events = json.dumps(self.engine.db.rows("SELECT * FROM events"))
        self.assertNotIn("a" * 32, events)
        self.assertNotIn("private-code-hash", events)
        self.assertNotIn("+84901234567", events)

    async def test_two_factor_and_logout(self):
        await self.configure()
        self.fake.need_password = True
        await self.send()
        r = await self.post("verify-code", {"code": "12345"})
        self.assertEqual(r.json()["step"], "password")
        r = await self.post("verify-password", {"password": "wrong-password"})
        self.assertEqual(r.status_code, 422)
        r = await self.post("verify-password", {"password": "correct-secret-2fa"})
        self.assertEqual(r.json()["state"], "connected")
        self.assertNotIn(
            "correct-secret-2fa", json.dumps(self.engine.db.rows("SELECT * FROM settings"))
        )
        r = await self.post("logout")
        self.assertEqual(r.json()["step"], "phone")
        self.assertFalse(self.fake.authorized)

    async def test_expired_otp_and_send_throttle(self):
        await self.configure()
        await self.send()
        self.assertEqual((await self.send_without_assert()).status_code, 429)
        self.assertEqual(self.fake.sent, 1)
        r = await self.post("verify-code", {"code": "11111"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual((await self.client.get("/api/telegram/auth")).json()["step"], "phone")
        self.assertEqual(self.fake.sent, 1)

    async def send_without_assert(self):
        return await self.post("send-code", {"phone": "+84901234567"})

    async def test_auth_csrf_and_validation_do_not_echo_secrets(self):
        anonymous = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url=self.config.app_url
        )
        try:
            self.assertEqual((await anonymous.get("/api/telegram/auth")).status_code, 401)
        finally:
            await anonymous.aclose()
        self.assertEqual(
            (
                await self.client.post(
                    "/api/telegram/credentials", json={"api_id": 1, "api_hash": "a" * 32}
                )
            ).status_code,
            403,
        )
        r = await self.post("credentials", {"api_id": 1, "api_hash": "sensitive-invalid-value"})
        self.assertEqual(r.status_code, 422)
        self.assertNotIn("sensitive-invalid-value", r.text)
        self.assertFalse((self.config.data_dir / "telegram-api.json").exists())

    async def test_another_admin_session_cannot_take_over_challenge(self):
        await self.configure()
        await self.send()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url=self.config.app_url
        ) as other:
            r = await other.post(
                "/api/auth/login", json={"username": "admin", "password": "web-test-password-123"}
            )
            status = (await other.get("/api/telegram/auth")).json()
            self.assertFalse(status["can_control"])
            self.assertIsNone(status["phone"])
            r = await other.post("/api/telegram/cancel", headers={"X-CSRF-Token": r.json()["csrf"]})
            self.assertEqual(r.status_code, 409)

    async def test_floodwait_and_verification_attempt_limit(self):
        await self.configure()
        self.fake.flood = True
        self.assertEqual((await self.send_without_assert()).status_code, 429)
        self.assertGreater(self.engine.db.setting("telegram_pause_until"), time.time())
        self.engine.db.set_setting("telegram_pause_until", 0)
        self.engine.db.set_setting("telegram_auth_send_after", 0)
        self.fake.flood = False
        await self.send()
        for _ in range(5):
            self.assertEqual((await self.post("verify-code", {"code": "00000"})).status_code, 422)
        self.assertEqual((await self.post("verify-code", {"code": "00000"})).status_code, 429)

    async def test_new_process_requires_new_code_and_rejects_cross_account(self):
        await self.configure()
        await self.send()
        restarted = create_app(self.config, self.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=restarted),
            base_url=self.config.app_url,
            cookies=self.client.cookies,
        ) as other:
            self.assertEqual((await other.get("/api/telegram/auth")).json()["step"], "phone")
            r = await other.post(
                "/api/telegram/verify-code", json={"code": "12345"}, headers=self.headers
            )
            self.assertEqual(r.status_code, 409)
        self.engine.db.set_setting("telegram_account_id", 987)
        self.engine.db.add_source({"chat_id": 1, "name": "old", "kind": "channel", "forum": False})
        r = await self.post("verify-code", {"code": "12345"})
        self.assertEqual(r.status_code, 409)
        self.assertFalse(self.fake.authorized)

    async def test_cannot_logout_while_source_is_active(self):
        await self.configure()
        await self.send()
        await self.post("verify-code", {"code": "12345"})
        sid = self.engine.db.add_source(
            {"chat_id": 1, "name": "old", "kind": "channel", "forum": False}
        )
        self.assertEqual((await self.post("logout")).status_code, 409)
        self.assertTrue(self.fake.authorized)
        self.engine.db.execute("UPDATE sources SET paused=1 WHERE id=?", (sid,))
        self.assertEqual((await self.post("logout")).status_code, 200)

    async def test_restored_session_with_another_account_never_activates_engine(self):
        await self.configure()
        self.engine.db.set_setting("telegram_account_id", 987)
        self.engine.db.add_source({"chat_id": 1, "name": "old", "kind": "channel", "forum": False})
        self.fake.authorized = True
        await self.engine.provider.connect(self.engine.on_live)
        self.assertEqual(self.engine.provider.status, "account_mismatch")
        self.assertEqual((await self.post("send-code", {"phone": "+84901234567"})).status_code, 409)
        self.assertEqual(self.fake.sent, 0)
