import asyncio
import os
import tempfile
import time
import unittest
from pathlib import Path

from telethon.errors import FloodWaitError

from telegram_vault.cli import synthetic
from telegram_vault.rate import TelegramRateController
from telegram_vault.storage import RcloneCryptStorage


class RateTests(unittest.IsolatedAsyncioTestCase):
    async def test_flood_wait_blocks_shared_gate(self):
        rate = TelegramRateController(pace=0)
        calls = []

        async def operation():
            calls.append(time.monotonic())
            if len(calls) <= 2:
                raise FloodWaitError(request=None, capture=1)
            return "ok"

        self.assertEqual(await rate.call(operation), "ok")
        self.assertGreaterEqual(calls[1] - calls[0], 1)
        self.assertGreaterEqual(calls[2] - calls[1], 1)


class StorageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = Path(self.directory.name) / "rclone.conf"
        original = Path(os.environ["RCLONE_CONFIG"]).read_text()
        # Test config shares only local test keys; isolated destination.
        import configparser

        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(original)
        parser["crypt"]["remote"] = str(Path(self.directory.name) / "encrypted")
        with self.config.open("w") as file:
            parser.write(file)
        self.config.chmod(0o600)
        self.storage = RcloneCryptStorage(str(self.config))

    def tearDown(self):
        self.directory.cleanup()

    def test_reject_traversal_and_plain_remote(self):
        for path in (
            "/etc/passwd",
            "TelegramVault_TEST/../bad",
            "Other/file",
            "TelegramVault_TEST/\\bad",
        ):
            with self.assertRaises(ValueError):
                self.storage.target(path)
        with self.assertRaises(ValueError):
            RcloneCryptStorage(str(self.config), "plain:")

    async def test_real_crypt_roundtrip_and_encrypted_names(self):
        path = "TelegramVault_TEST/.incomplete/video.mp4"
        digest = await self.storage.put_stream(path, synthetic(2 * 1024 * 1024), 2 * 1024 * 1024)
        self.assertEqual(digest, await self.storage.hash_stream(path))
        names = [p.name for p in Path(self.directory.name).rglob("*")]
        self.assertNotIn("video.mp4", names)
        self.assertNotIn("TelegramVault_TEST", names)
        encrypted = next(
            p for p in (Path(self.directory.name) / "encrypted").rglob("*") if p.is_file()
        )
        with encrypted.open("rb") as file:
            self.assertEqual(file.read(8), b"RCLONE\x00\x00")

    async def test_truncated_input_never_verified(self):
        with self.assertRaises(ValueError):
            await self.storage.put_stream(
                "TelegramVault_TEST/.incomplete/truncated", synthetic(1), 100
            )

    async def test_cancel_reaps_rclone_and_closes_generator(self):
        entered, closed = asyncio.Event(), asyncio.Event()

        async def stalled():
            try:
                yield b"x"
                entered.set()
                await asyncio.Event().wait()
            finally:
                closed.set()

        task = asyncio.create_task(
            self.storage.put_stream("TelegramVault_TEST/.incomplete/cancel", stalled(), 100)
        )
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(closed.is_set())


if __name__ == "__main__":
    unittest.main()
