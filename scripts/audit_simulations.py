"""Isolated adversarial simulations. Records findings; never uses production storage."""

import asyncio
import configparser
import json
import secrets
import sqlite3
import subprocess
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from argon2 import PasswordHasher
from telethon.errors import FloodWaitError

from telegram_vault.api import create_app
from telegram_vault.config import Config
from telegram_vault.database import Database
from telegram_vault.engine import Engine
from telegram_vault.providers import AccountRateController, FloodPaused, MockTelegramProvider
from telegram_vault.storage import RcloneCryptStorage, StorageError

PASSWORD = "audit-only-password-123"
RESULTS = []


@asynccontextmanager
async def sandbox():
    with tempfile.TemporaryDirectory(prefix="vault-audit-") as directory:
        root = Path(directory)
        parser = configparser.ConfigParser(interpolation=None)

        def obscure():
            return (
                subprocess.check_output(
                    ["rclone", "obscure", "-"], input=secrets.token_hex(32).encode()
                )
                .decode()
                .strip()
            )

        parser["crypt"] = {
            "type": "crypt",
            "remote": str(root / "encrypted"),
            "filename_encryption": "standard",
            "directory_name_encryption": "true",
            "password": obscure(),
            "password2": obscure(),
        }
        config_path = root / "rclone.conf"
        with config_path.open("w") as file:
            parser.write(file)
        config_path.chmod(0o600)
        config = Config(
            data_dir=root,
            telegram_mode="mock",
            scan_batch_size=5,
            request_pace=0,
            download_bandwidth=0,
            file_pause_enabled=False,
            password_hash=PasswordHasher().hash(PASSWORD),
        )
        db = Database(config.database_path)
        provider = MockTelegramProvider(db)
        storage = RcloneCryptStorage(str(config_path))
        engine = Engine(config, db=db, provider=provider, storage=storage)
        sid = db.add_source(provider.groups[0])
        await engine.refresh_topics(sid)
        await provider.connect(engine.on_live)
        context = SimpleNamespace(
            config=config,
            db=db,
            provider=provider,
            storage=storage,
            engine=engine,
            sid=sid,
            root=root,
        )
        try:
            yield context
        finally:
            engine.stopping = True
            for task in engine.tasks:
                task.cancel()
            await asyncio.gather(*engine.tasks, return_exceptions=True)
            await provider.close()
            db.close()
            if engine.lock_file:
                engine.lock_file.close()


def source(c):
    return c.db.one("SELECT * FROM sources WHERE id=?", (c.sid,))


def enqueue(c, index=0):
    c.db.ingest(source(c), c.provider.messages[-1001001][index], "TelegramVault_TEST")
    return c.db.job(c.db.one("SELECT id FROM jobs ORDER BY id DESC LIMIT 1")["id"])


async def login(client):
    response = await client.post(
        "/api/auth/login", json={"username": "admin", "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf"]}


async def scan_selection_race():
    async with sandbox() as c:
        c.db.execute("UPDATE sources SET all_topics=0 WHERE id=?", (c.sid,))
        c.db.execute("UPDATE topics SET selected=0 WHERE source_id=? AND topic_id=1", (c.sid,))
        await c.engine.scan_batch(source(c))
        entered, release = asyncio.Event(), asyncio.Event()
        original = c.provider.scan

        async def delayed(*args, **kwargs):
            entered.set()
            await release.wait()
            async for message in original(*args, **kwargs):
                yield message

        c.provider.scan = delayed
        old_scan = asyncio.create_task(c.engine.scan_batch(source(c)))
        await entered.wait()
        app = create_app(c.config, c.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
        ) as client:
            headers = await login(client)
            response = await client.put(
                f"/api/sources/{c.sid}/topics",
                headers=headers,
                json={"all_topics": False, "selected": [1, 42]},
            )
            assert response.status_code == 200
        release.set()
        await old_scan
        c.provider.scan = original
        while source(c)["scan_requested"]:
            await c.engine.scan_batch(source(c))
        async for message in c.provider.scan(
            source(c), 0, 0, c.config.scan_batch_size, recent=True
        ):
            c.db.ingest(source(c), message, c.config.storage_root)
        present = {r["message_id"] for r in c.db.rows("SELECT message_id FROM media")}
        missing = sorted({m.message_id for m in c.provider.messages[-1001001]} - present)
        return {
            "checkpoint": source(c)["scan_cursor"],
            "expected_jobs": 12,
            "actual_jobs": len(present),
            "missing_message_ids": missing,
            "rescan_requested_afterwards": bool(source(c)["scan_requested"]),
        }, not missing


async def corrupted_incomplete_retry():
    async with sandbox() as c:
        enqueue(c)
        original = c.storage.put_stream
        corrupted = False

        async def corrupt_once(path, chunks, size, progress=None):
            nonlocal corrupted
            digest = await original(path, chunks, size, progress)
            if not corrupted:
                corrupted = True

                async def wrong_bytes():
                    for offset in range(0, size, 524288):
                        yield b"z" * min(524288, size - offset)

                await original(path, wrong_bytes(), size)
            return digest

        c.storage.put_stream = corrupt_once
        job = c.db.claim()
        await c.engine.run_job(job)
        statuses = [c.db.job(job["id"])["status"]]
        c.storage.put_stream = original
        for _ in range(2):
            if c.db.job(job["id"])["status"] == "COMPLETED":
                break
            c.engine.control_job(job["id"], "retry")
            await c.engine.run_job(c.db.claim())
            statuses.append(c.db.job(job["id"])["status"])
        return {
            "statuses_after_failure_and_two_manual_retries": statuses,
            "final_exists": bool(await c.storage.exists(job["remote_path"])),
        }, statuses[-1] == "COMPLETED"


async def worker_database_error():
    async with sandbox() as c:
        enqueue(c)
        original = c.db.claim
        calls = 0

        def busy_once():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise sqlite3.OperationalError("database is locked")
            return original()

        c.db.claim = busy_once
        # Start the real supervised lifecycle, not an unregistered task.
        await c.engine.start()
        app = create_app(c.config, c.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
        ) as client:
            await asyncio.sleep(0.05)
            during = await client.get("/api/health")
            deadline = time.monotonic() + 15
            while c.db.job(1)["status"] != "COMPLETED" and time.monotonic() < deadline:
                await asyncio.sleep(0.05)
            after = await client.get("/api/health")
        stopped = any(task.done() for task in c.engine.tasks)
        status = c.db.job(1)["status"]
        return (
            {
                "worker_stopped": stopped,
                "claim_calls": calls,
                "remaining_job_status": status,
                "health_during_recovery_http": during.status_code,
                "health_after_recovery_http": after.status_code,
            },
            not stopped
            and status == "COMPLETED"
            and during.status_code == 503
            and after.status_code == 200,
        )


async def password_reset_race():
    async with sandbox() as c:
        c.config.password_hash = ""
        c.db.set_setting("admin_password_hash", PasswordHasher().hash(PASSWORD))
        entered, release = asyncio.Event(), asyncio.Event()

        async def delayed_hash(function, *args):
            entered.set()
            await release.wait()
            return function(*args)

        app = create_app(c.config, c.engine)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
        ) as client:
            with patch("telegram_vault.api.asyncio.to_thread", side_effect=delayed_hash):
                task = asyncio.create_task(
                    client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
                )
                await entered.wait()
                # Same operations as init-admin: replace hash and revoke sessions.
                c.db.set_setting(
                    "admin_password_hash", PasswordHasher().hash("replacement-password-456")
                )
                c.db.execute("DELETE FROM auth_sessions")
                release.set()
                response = await task
                me = await client.get("/api/auth/me")
        return {
            "old_password_login_after_reset_http": response.status_code,
            "session_authorized_after_reset_http": me.status_code,
            "sessions_created_after_reset": c.db.one("SELECT COUNT(*) AS n FROM auth_sessions")[
                "n"
            ],
        }, response.status_code != 200


async def unbounded_login_parallelism():
    async with sandbox() as c:
        active = peak = 0
        mutex = threading.Lock()

        def slow_verify(*args):
            nonlocal active, peak
            with mutex:
                active += 1
                peak = max(peak, active)
            time.sleep(0.15)
            with mutex:
                active -= 1
            return False

        with patch(
            "telegram_vault.api.PasswordHasher", return_value=SimpleNamespace(verify=slow_verify)
        ):
            app = create_app(c.config, c.engine)

            async def request(index):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app, client=(f"198.51.100.{index}", 1)),
                    base_url=c.config.app_url,
                ) as client:
                    return (
                        await client.post(
                            "/api/auth/login", json={"username": "admin", "password": "incorrect"}
                        )
                    ).status_code

            codes = await asyncio.gather(*(request(index) for index in range(20)))
        memory = PasswordHasher().memory_cost * 1024
        return {
            "parallel_requests": len(codes),
            "peak_simultaneous_hash_tasks": peak,
            "estimated_argon2_memory_bytes": peak * memory,
            "memory_is_estimate_not_allocation": True,
            "busy_requests": codes.count(429),
            "all_requests_rejected": all(code in (401, 429) for code in codes),
        }, peak <= 2 and codes.count(429) >= 18


async def truncated_stream_recovery():
    async with sandbox() as c:
        enqueue(c)
        original = c.provider.open_media_stream

        async def disconnected(job):
            yield b"a" * 524288
            raise ConnectionResetError("simulated")

        c.provider.open_media_stream = disconnected
        job = c.db.claim()
        await c.engine.run_job(job)
        first = c.db.job(job["id"])["status"]
        c.provider.open_media_stream = original
        c.engine.control_job(job["id"], "retry")
        await c.engine.run_job(c.db.claim())
        final = c.db.job(job["id"])
        return {
            "after_disconnect": first,
            "after_retry": final["status"],
            "hash_matches": await c.storage.hash_stream(final["remote_path"])
            == final["plaintext_sha256"],
        }, first == "RETRY_WAIT" and final["status"] == "COMPLETED"


async def floodwait_shared_deadline():
    async with sandbox() as c:
        rate = AccountRateController(c.db, 0)
        calls = 0

        async def fail():
            nonlocal calls
            calls += 1
            raise FloodWaitError(request=None, capture=300)

        outcomes = await asyncio.gather(
            *(rate.call(fail) for _ in range(20)), return_exceptions=True
        )
        restarted = AccountRateController(c.db, 0)
        try:
            await restarted.call(fail)
        except FloodPaused:
            pass
        remaining = c.db.setting("telegram_pause_until") - time.time()
        return {
            "concurrent_operations": 20,
            "actual_api_calls": calls,
            "all_paused": all(isinstance(result, FloodPaused) for result in outcomes),
            "remaining_deadline_seconds": round(remaining, 2),
        }, calls == 1 and remaining >= 299


async def repeated_google429():
    async with sandbox() as c:
        enqueue(c)
        c.config.max_retries = 3

        async def unavailable(*args):
            raise StorageError("google_rate_limit")

        c.storage.exists = unavailable
        statuses, delays = [], []
        for _ in range(3):
            c.db.execute(
                "UPDATE jobs SET next_attempt=0 WHERE id=1"
            )  # Accelerate clock only in isolated test.
            await c.engine.run_job(c.db.claim())
            job = c.db.job(1)
            statuses.append(job["status"])
            delays.append(round(job["next_attempt"] - time.time(), 2))
        return {
            "statuses": statuses,
            "backoff_seconds": delays,
            "concurrency": c.config.concurrency,
        }, statuses == ["RETRY_WAIT", "RETRY_WAIT", "FAILED"] and delays[0] < delays[1] < delays[2]


async def same_size_corruption_reconcile():
    async with sandbox() as c:
        enqueue(c)
        job = c.db.claim()
        await c.engine.run_job(job)
        job = c.db.job(1)

        async def changed():
            for offset in range(0, job["size"], 524288):
                yield b"q" * min(524288, job["size"] - offset)

        await c.storage.put_stream(job["remote_path"], changed(), job["size"])
        matches = await c.storage.hash_stream(job["remote_path"]) == job["plaintext_sha256"]
        result = await c.engine.reconcile()
        status = c.db.job(1)["status"]
        return {
            "stored_digest_matches": matches,
            "reconcile_result": result,
            "job_status_after_reconcile": status,
        }, status != "COMPLETED"


async def incomplete_growth():
    async with sandbox() as c:
        enqueue(c)
        original = c.provider.open_media_stream

        async def disconnect(job):
            yield b"z" * 524288
            yield b"z" * 524288
            raise ConnectionResetError()

        c.provider.open_media_stream = disconnect
        paths = []
        for attempt in range(3):
            if attempt:
                c.engine.control_job(1, "retry")
            await c.engine.run_job(c.db.claim())
            paths.append(c.db.job(1)["temp_path"])
        objects = [path async for path in c.storage.list("TelegramVault_TEST")]
        tracked = c.db.job(1)["temp_path"]
        c.provider.open_media_stream = original
        return {
            "attempts": 3,
            "unique_attempt_paths": len(set(paths)),
            "incomplete_objects_retained": len(objects),
            "objects_without_current_job_path": sum(path != tracked for path in objects),
        }, len(objects) <= 1


async def slow_sink_backpressure():
    async with sandbox() as c:
        # Actual rclone crypt with a 1 MiB/s cap, lazy 8 MiB input.
        c.storage.upload_bandwidth = 1048576
        generated = 0
        size = 8 * 1048576

        async def chunks():
            nonlocal generated
            for _ in range(size // 524288):
                generated += 524288
                yield b"x" * 524288

        began = time.monotonic()
        task = asyncio.create_task(
            c.storage.put_stream("TelegramVault_TEST/.incomplete/backpressure", chunks(), size)
        )
        await asyncio.sleep(0.2)
        ahead = generated
        digest = await task
        elapsed = time.monotonic() - began
        equal = await c.storage.hash_stream("TelegramVault_TEST/.incomplete/backpressure") == digest
        return {
            "payload_bytes": size,
            "source_bytes_generated_after_200ms": ahead,
            "duration_seconds": round(elapsed, 2),
            "hash_matches": equal,
        }, ahead < size and elapsed > 4 and equal


async def run():
    checks = [
        ("S01", "Network disconnect and manual recovery", "P0", truncated_stream_recovery),
        ("S02", "20 operations + persisted FloodWait 300", "P0", floodwait_shared_deadline),
        ("S03", "Repeated Google 429 + retry threshold", "P0", repeated_google429),
        ("S04", "Slow rclone sink backpressure", "P0", slow_sink_backpressure),
        ("F01", "Topic selection while history scan is in flight", "P1", scan_selection_race),
        ("F02", "Corrupt incomplete target followed by retries", "P1", corrupted_incomplete_retry),
        ("F03", "Transient DB error recovery and readiness", "P1", worker_database_error),
        ("F04", "Password reset during an in-flight login", "P2", password_reset_race),
        (
            "F05",
            "Concurrent logins from distinct simulated clients",
            "P1",
            unbounded_login_parallelism,
        ),
        (
            "F06",
            "Same-size changed content during maintenance reconciliation",
            "P2",
            same_size_corruption_reconcile,
        ),
        ("F07", "Repeated incomplete attempt storage growth", "P2", incomplete_growth),
    ]
    for identifier, name, severity, check in checks:
        began = time.monotonic()
        try:
            evidence, passed = await check()
            row = {
                "id": identifier,
                "scenario": name,
                "severity_if_failed": severity,
                "verdict": "PASS" if passed else "WEAKNESS_REPRODUCED",
                "evidence": evidence,
                "seconds": round(time.monotonic() - began, 3),
            }
        except Exception as error:
            row = {
                "id": identifier,
                "scenario": name,
                "verdict": "HARNESS_ERROR",
                "error_type": type(error).__name__,
            }
        RESULTS.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    output = Path("data/reports/adversarial-audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2))
    print(f"Evidence saved: {output}")


if __name__ == "__main__":
    asyncio.run(run())
