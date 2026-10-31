import asyncio
import configparser
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from telegram_vault.config import Config
from telegram_vault.database import Database
from telegram_vault.providers import MockTelegramProvider
from telegram_vault.storage import RcloneCryptStorage

CHILD = """
import asyncio, os
from pathlib import Path
from telegram_vault.config import Config
from telegram_vault.engine import Engine
from telegram_vault.providers import MockTelegramProvider
async def main():
    config=Config(data_dir=Path(os.environ["CRASH_DATA"]), telegram_mode="mock", rclone_config=os.environ["CRASH_CRYPT"], download_bandwidth=0, upload_bandwidth=0)
    provider=MockTelegramProvider()
    provider.messages[-1001001][0].size=32*1048576
    engine=Engine(config,provider=provider)
    await engine.start()
    try:
        while engine.db.job(1)["status"] != "COMPLETED":
            if engine.db.job(1)["status"] == "FAILED":
                raise RuntimeError("job failed")
            await asyncio.sleep(.05)
    finally:
        await engine.stop()
os.umask(0o077)
asyncio.run(main())
"""


class HardCrashTests(unittest.TestCase):
    def test_sigkill_at_10_50_90_percent_restarts_without_duplicate_or_false_complete(self):
        for fraction in (0.1, 0.5, 0.9):
            with (
                self.subTest(fraction=fraction),
                tempfile.TemporaryDirectory(prefix="vault-crash-") as folder,
            ):
                root = Path(folder)
                config = Config(data_dir=root, telegram_mode="mock")
                parser = configparser.ConfigParser(interpolation=None)
                parser.read(os.environ["RCLONE_CONFIG"])
                parser["crypt"]["remote"] = str(root / "encrypted")
                rconfig = root / "crypt.conf"
                with rconfig.open("w") as file:
                    parser.write(file)
                rconfig.chmod(0o600)
                db = Database(config.database_path)
                sid = db.add_source(MockTelegramProvider().groups[0])
                db.execute(
                    "UPDATE sources SET scan_requested=0,last_scan=?,last_reconcile=? WHERE id=?",
                    (time.time(), time.time(), sid),
                )
                message = MockTelegramProvider().messages[-1001001][0]
                message.size = 32 * 1048576
                db.ingest(
                    db.one("SELECT * FROM sources WHERE id=?", (sid,)),
                    message,
                    "TelegramVault_TEST",
                )
                db.close()
                env = {**os.environ, "CRASH_DATA": str(root), "CRASH_CRYPT": str(rconfig)}

                def launch():
                    return subprocess.Popen(
                        [sys.executable, "-c", CHILD],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )

                process = launch()
                try:
                    with sqlite3.connect(config.database_path) as inspect:
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            row = inspect.execute(
                                "SELECT status,downloaded FROM jobs WHERE id=1"
                            ).fetchone()
                            if row[1] >= message.size * fraction:
                                break
                            self.assertIsNone(process.poll())
                            time.sleep(0.02)
                        else:
                            self.fail("Did not reach crash point")
                    os.killpg(
                        process.pid, signal.SIGKILL
                    )  # Isolated service + rclone process group.
                    process.wait(timeout=5)
                    with sqlite3.connect(config.database_path) as inspect:
                        self.assertNotEqual(
                            inspect.execute("SELECT status FROM jobs WHERE id=1").fetchone()[0],
                            "COMPLETED",
                        )
                        self.assertEqual(
                            inspect.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                        )
                    process = launch()
                    self.assertEqual(process.wait(timeout=25), 0)
                    db = Database(config.database_path)
                    job = db.job(1)
                    self.assertEqual(job["status"], "COMPLETED")
                    self.assertEqual(db.one("SELECT COUNT(*) AS n FROM jobs")["n"], 1)
                    storage = RcloneCryptStorage(str(rconfig))
                    self.assertEqual(
                        asyncio.run(storage.hash_stream(job["remote_path"])),
                        job["plaintext_sha256"],
                    )
                    db.close()
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
