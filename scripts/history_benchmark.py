"""Lazy 500k-message scanner benchmark, isolated SQLite only; no Telegram calls."""

import argparse
import asyncio
import json
import tempfile
import time
from pathlib import Path

import psutil

from telegram_vault.config import Config
from telegram_vault.database import Database
from telegram_vault.engine import Engine
from telegram_vault.models import Message
from telegram_vault.providers import MockTelegramProvider


async def run(count):
    with tempfile.TemporaryDirectory(prefix="vault-history-") as folder:
        config = Config(data_dir=Path(folder), telegram_mode="mock", scan_batch_size=1000)
        db = Database(config.database_path)
        provider = MockTelegramProvider()
        sid = db.add_source(provider.groups[1])

        class LazyHistory(MockTelegramProvider):
            async def latest_id(self, source):
                return count

            async def scan(self, source, cursor, target, limit, recent=False):
                for index in range(cursor + 1, min(target, cursor + limit) + 1):
                    yield Message(
                        source["chat_id"],
                        index,
                        1735689600,
                        file_id=f"doc-{index}" if index % 10 == 0 else "",
                        filename=f"video-{index}.mp4",
                        size=1048576 if index % 10 == 0 else 0,
                        mime_type="video/mp4",
                    )

        engine = Engine(config, db=db, provider=LazyHistory())
        process = psutil.Process()
        baseline, peak = process.memory_info().rss, 0
        start = time.monotonic()
        while True:
            source = db.one("SELECT * FROM sources WHERE id=?", (sid,))
            if not source["scan_requested"]:
                break
            await engine.scan_batch(source)
            peak = max(peak, process.memory_info().rss)
        report = dict(
            messages=count,
            jobs=db.one("SELECT COUNT(*) AS n FROM jobs")["n"],
            seconds=round(time.monotonic() - start, 2),
            baseline_rss_bytes=baseline,
            peak_rss_bytes=peak,
            ram_growth_bytes=peak - baseline,
            db_bytes=Path(config.database_path).stat().st_size,
            scope="Lazy mock metadata; persistent SQLite queue. No transfer, Telegram or Google traffic.",
        )
        destination = Path("data/reports/history.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--messages", type=int, default=500000)
    asyncio.run(run(parser.parse_args().messages))
