"""Benchmark actual engine + crypt with one/two mock streaming workers."""

import argparse
import asyncio
import configparser
import json
import os
import tempfile
import time
from pathlib import Path

import psutil

from telegram_vault.config import Config
from telegram_vault.database import Database
from telegram_vault.engine import Engine
from telegram_vault.providers import MockTelegramProvider
from telegram_vault.storage import RcloneCryptStorage


async def run(size):
    results = []
    for concurrency in (1, 2):
        with tempfile.TemporaryDirectory(prefix="vault-workers-") as directory:
            root = Path(directory)
            config = Config(
                data_dir=root, telegram_mode="mock", concurrency=concurrency, download_bandwidth=0
            )
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(os.environ["RCLONE_CONFIG"])
            parser["crypt"]["remote"] = str(root / "encrypted")
            path = root / "crypt.conf"
            with path.open("w") as file:
                parser.write(file)
            path.chmod(0o600)
            provider = MockTelegramProvider()

            async def generated(job):
                chunk = bytes(range(256)) * 2048
                for offset in range(0, job["size"], len(chunk)):
                    yield chunk[: min(len(chunk), job["size"] - offset)]

            provider.open_media_stream = generated
            db = Database(config.database_path)
            engine = Engine(config, db=db, provider=provider, storage=RcloneCryptStorage(str(path)))
            sid = db.add_source(provider.groups[0])
            for index in range(concurrency):
                message = provider.messages[-1001001][index]
                message.size = size
                db.ingest(
                    db.one("SELECT * FROM sources WHERE id=?", (sid,)), message, config.storage_root
                )
            jobs = [db.claim() for _ in range(concurrency)]
            stop = asyncio.Event()
            peak = peak_disk = 0
            process = psutil.Process()

            async def monitor():
                nonlocal peak, peak_disk
                while not stop.is_set():
                    rss = process.memory_info().rss
                    for child in process.children(recursive=True):
                        try:
                            rss += child.memory_info().rss
                        except psutil.NoSuchProcess:
                            pass
                    peak = max(peak, rss)
                    # Operational disk excludes the encrypted backend (cloud stand-in).
                    occupied = 0
                    for p in root.rglob("*"):
                        try:
                            if p.is_file() and root / "encrypted" not in p.parents:
                                occupied += p.stat().st_size
                        except FileNotFoundError:
                            pass
                    peak_disk = max(peak_disk, occupied)
                    await asyncio.sleep(0.05)

            task = asyncio.create_task(monitor())
            started = time.monotonic()
            await asyncio.gather(*(engine.run_job(job) for job in jobs))
            seconds = time.monotonic() - started
            stop.set()
            await task
            statuses = db.rows("SELECT status FROM jobs")
            if any(row["status"] != "COMPLETED" for row in statuses):
                raise RuntimeError("Engine benchmark job did not complete")
            results.append(
                dict(
                    workers=concurrency,
                    payload_bytes_per_worker=size,
                    seconds=round(seconds, 3),
                    aggregate_payload_bytes_per_second=int(size * concurrency / seconds),
                    peak_process_tree_rss_bytes=peak,
                    peak_operational_disk_bytes=peak_disk,
                    scope="Actual engine + local crypt; includes two decrypted hash passes. Synthetic Telegram; no Google traffic.",
                )
            )
            db.close()
    destination = Path("data/reports/workers.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bytes", type=int, default=256 * 1048576)
    asyncio.run(run(parser.parse_args().bytes))
