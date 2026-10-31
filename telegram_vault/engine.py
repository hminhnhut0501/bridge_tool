import asyncio
import fcntl
import logging
import random
import re
import time
import uuid
from pathlib import PurePosixPath
from collections import deque

from .database import Database
from .models import Message
from .providers import (
    AccountRateController,
    FloodPaused,
    MediaDeferred,
    MediaUnavailable,
    MockTelegramProvider,
    TelethonProvider,
)
from .storage import RcloneCryptStorage, StorageError


def retry_delay(attempt):
    return min(900, 5 * 3 ** min(attempt - 1, 5)) * random.uniform(1, 1.2)


class TransferSlots:
    """Resizable capacity: lowering the limit lets existing holders finish."""
    def __init__(self, limit):
        self.limit, self.used = limit, 0
        self.changed = asyncio.Event()

    async def acquire(self):
        while self.used >= self.limit:
            self.changed.clear()
            await self.changed.wait()
        self.used += 1

    def release(self):
        self.used -= 1
        self.changed.set()

    def resize(self, limit):
        self.limit = limit
        self.changed.set()


class Engine:
    def __init__(self, config, db=None, provider=None, storage=None):
        self.config = config
        self.db = db or Database(config.database_path)
        self.rate = AccountRateController(self.db, config.request_pace)
        self.provider = provider or (
            MockTelegramProvider(self.db)
            if config.telegram_mode == "mock"
            else TelethonProvider(config, self.rate)
        )
        self.storage = storage
        self.storage_error = "not_configured"
        if storage is None and config.rclone_config:
            try:
                self.storage = RcloneCryptStorage(
                    config.rclone_config,
                    config.remote,
                    config.rclone_binary,
                    root=config.storage_root,
                    upload_bandwidth=max(1, config.upload_bandwidth // config.concurrency)
                    if config.upload_bandwidth
                    else 0,
                )
                self.storage_error = None
            except (ValueError, OSError):
                self.storage_error = "invalid_crypt_config"
        elif storage:
            self.storage_error = None
        self.started = time.time()
        self.stopping = False
        self.tasks = []
        self.active = {}
        self.progress = {}
        self.lock_file = None
        self.storage_health = {"state": "unchecked", "checked_at": None}
        self.last_discovery = []
        self.discovery_time = 0
        self.operation_lock = asyncio.Lock()
        self.bandwidth_lock = asyncio.Lock()
        self.next_download = 0.0
        self.running = False
        self.task_failures = set()
        self.interrupted_jobs = set()
        self.transfer_slots = TransferSlots(config.concurrency)
        self.verification_slots = asyncio.Semaphore(1)
        self.job_slots = {}
        self.worker_count = config.concurrency

    def ready(self):
        expected = {"scanner", "maintenance"} | {
            f"worker-{i}" for i in range(self.worker_count)
        }
        critical = [task for task in self.tasks if task.get_name() in expected]
        return (
            self.running
            and not self.stopping
            and not self.task_failures
            and len(critical) == len(expected)
            and all(not task.done() for task in critical)
        )

    async def supervise(self, factory, name):
        while not self.stopping:
            try:
                if name.startswith("worker"):
                    for job_id in tuple(self.interrupted_jobs):
                        job = self.db.job(job_id)
                        if job and job["status"] in ("TRANSFERRING", "VERIFYING"):
                            self.db.transition(
                                job_id,
                                job["cancel_requested"] or "RETRY_WAIT",
                                next_attempt=time.time(),
                                last_error="worker_interrupted",
                                cancel_requested=None,
                            )
                        self.interrupted_jobs.discard(job_id)
                    self.task_failures.discard("job-dispatch")
                self.task_failures.discard(name)
                await factory()
                if not self.stopping:
                    raise RuntimeError("Background task returned unexpectedly")
            except asyncio.CancelledError:
                raise
            except Exception as error:
                self.task_failures.add(name)
                # Logging must survive a failed SQLite event write.
                logging.getLogger("telegram_vault").error(
                    "background_task_failed task=%s error=%s", name, type(error).__name__
                )
                await asyncio.sleep(1)

    def set_concurrency(self, limit):
        self.transfer_slots.resize(limit)
        if self.running:
            while self.worker_count < limit:
                index = self.worker_count
                self.worker_count += 1
                self.tasks.append(asyncio.create_task(self.worker_loop(), name=f"worker-{index}"))

    async def start(self):
        self.worker_count = self.config.concurrency
        # Runtime settings are applied by API lifespan after Engine construction.
        self.transfer_slots = TransferSlots(self.config.concurrency)
        self.verification_slots = asyncio.Semaphore(1)
        self.lock_file = open(self.config.database_path + ".lock", "a")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock_file.close()
            raise RuntimeError("Another Telegram Vault process owns this database") from None
        # Never resume an interrupted operation as completed without reconciliation.
        self.db.execute(
            "UPDATE transfers SET status='RETRY_WAIT',finished_at=? WHERE finished_at IS NULL",
            (time.time(),),
        )
        for job in self.db.rows(
            "SELECT id,cancel_requested FROM jobs WHERE status IN ('TRANSFERRING','VERIFYING')"
        ):
            status = job["cancel_requested"] or "RETRY_WAIT"
            self.db.transition(
                job["id"],
                status,
                next_attempt=time.time(),
                last_error="service_interrupted",
                cancel_requested=None,
            )
        self.db.event("service_started", f"Telegram adapter: {self.provider.mode}")
        self.db.set_setting("reconcile_running", False)
        if not self.config.file_pause_enabled:
            self.db.set_setting("transfer_pause_until", 0)
        try:
            await self.provider.connect(self.on_live)
        except Exception:
            self.provider.status = "disconnected"
            self.db.event("telegram_connection_failed")
        self.tasks = [
            asyncio.create_task(self.supervise(self.scanner_loop, "scanner"), name="scanner"),
            asyncio.create_task(
                self.supervise(self.maintenance_loop, "maintenance"), name="maintenance"
            ),
        ]
        self.running = True
        self.tasks += [
            asyncio.create_task(self.worker_loop(), name=f"worker-{i}")
            for i in range(self.worker_count)
        ]

    async def stop(self):
        self.stopping = True
        for task in [*self.tasks, *self.active.values()]:
            task.cancel()
        await asyncio.gather(*self.tasks, *self.active.values(), return_exceptions=True)
        await self.provider.close()
        self.db.event("service_stopped")
        self.db.close()
        if self.lock_file:
            self.lock_file.close()

    async def discover(self, force=False):
        if force or not self.last_discovery or time.time() - self.discovery_time > 60:
            async with self.operation_lock:
                self.last_discovery = await self.provider.list_sources()
                self.discovery_time = time.time()
        return self.last_discovery

    async def add_source(self, chat_id):
        async with self.operation_lock:
            source = await self.provider.resolve_source(chat_id)
        source_id = self.db.add_source(source, paused=True)
        if source["forum"]:
            await self.refresh_topics(source_id)
        self.db.event("source_added", source_id=source_id)
        return source_id

    async def refresh_topics(self, source_id):
        source = self.db.one("SELECT * FROM sources WHERE id=?", (source_id,))
        if source["forum"]:
            for topic in await self.provider.list_topics(source["chat_id"]):
                self.db.upsert_topic(source_id, topic["topic_id"], topic["name"])

    async def on_live(self, chat_id, message):
        source = self.db.one(
            "SELECT * FROM sources WHERE chat_id=? AND enabled=1 AND paused=0 AND deleted=0",
            (chat_id,),
        )
        if source and not self.db.setting("scheduler_paused", False):
            metadata = (
                message
                if isinstance(message, Message)
                else await self.provider.named_metadata(message, chat_id, source["forum"])
            )
            # Resume scanning catches events received while this scope was paused.
            self.db.ingest(source, metadata, self.config.storage_root, priority=100)

    async def scan_batch(self, source):
        generation = source["scan_generation"]
        if source["scan_target"] is None:
            target = await self.provider.latest_id(source)
            updated = self.db.execute(
                "UPDATE sources SET scan_target=? WHERE id=? AND scan_generation=? AND scan_requested=1",
                (target, source["id"], generation),
            )
            if not updated.rowcount:
                return
            source["scan_target"] = target
            self.db.event("scan_started", source_id=source["id"])
        count = 0
        async for message in self.provider.scan(
            source, source["scan_cursor"], source["scan_target"], self.config.scan_batch_size
        ):
            current = self.db.one("SELECT * FROM sources WHERE id=?", (source["id"],))
            if (
                self.db.setting("scheduler_paused", False)
                or current["scan_generation"] != generation
                or current["paused"]
                or not current["enabled"]
                or current["deleted"]
            ):
                return
            if not self.db.ingest(
                current,
                message,
                self.config.storage_root,
                checkpoint=True,
                scan_generation=generation,
            ):
                return
            count += 1
        if count < self.config.scan_batch_size:
            self.db.execute(
                "UPDATE sources SET scan_cursor=MAX(scan_cursor,?),scan_target=NULL,scan_requested=0,last_scan=?,scan_error=NULL WHERE id=? AND scan_target=? AND scan_generation=?",
                (
                    source["scan_target"],
                    time.time(),
                    source["id"],
                    source["scan_target"],
                    generation,
                ),
            )
            self.db.event("scan_completed", source_id=source["id"])

    async def scanner_loop(self):
        while True:
            try:
                if self.provider.status == "connected" and not self.db.setting(
                    "scheduler_paused", False
                ):
                    for source in self.db.rows(
                        "SELECT * FROM sources WHERE enabled=1 AND paused=0 AND deleted=0 ORDER BY id"
                    ):
                        try:
                            if source["scan_requested"]:
                                await self.scan_batch(source)
                            elif (
                                not source["last_scan"]
                                or time.time() - source["last_scan"]
                                > self.config.reconciliation_interval
                            ):
                                # First catch every missed message after checkpoint; then a bounded recent pass for edits.
                                self.db.execute(
                                    "UPDATE sources SET scan_requested=1,scan_target=NULL WHERE id=?",
                                    (source["id"],),
                                )
                            if (
                                not source["last_reconcile"]
                                or time.time() - source["last_reconcile"]
                                > self.config.reconciliation_interval
                            ):
                                async for message in self.provider.scan(
                                    source, 0, 0, self.config.scan_batch_size, recent=True
                                ):
                                    self.db.ingest(source, message, self.config.storage_root)
                                self.db.execute(
                                    "UPDATE sources SET last_reconcile=? WHERE id=?",
                                    (time.time(), source["id"]),
                                )
                        except FloodPaused:
                            break
                        except asyncio.CancelledError:
                            raise
                        except Exception as error:
                            self.db.execute(
                                "UPDATE sources SET scan_error=? WHERE id=?",
                                (type(error).__name__, source["id"]),
                            )
                            self.db.event(
                                "scan_failed", type(error).__name__, source_id=source["id"]
                            )
                            await asyncio.sleep(5)
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise

    async def worker_loop(self):
        await self.supervise(self._worker_loop, asyncio.current_task().get_name())

    async def _worker_loop(self):
        while True:
            if self.interrupted_jobs:
                raise RuntimeError("Job requires supervised recovery")
            await self.transfer_slots.acquire()
            job = None
            try:
                if (
                    self.storage and self.provider.status == "connected"
                    and self.db.setting("telegram_pause_until", 0) <= time.time()
                    and self.db.setting("storage_pause_until", 0) <= time.time()
                ):
                    job = self.db.claim()
                if job:
                    lease = {"phase": "transfer", "released": asyncio.Event()}
                    self.job_slots[job["id"]] = lease
                    task = asyncio.create_task(self.scheduled_job(job), name=f"job-{job['id']}")
                    self.active[job["id"]] = task
                    task.add_done_callback(lambda done, jid=job["id"]: self.cleanup_scheduled_job(jid, done))
            except BaseException:
                self.transfer_slots.release()
                raise
            if not job:
                self.transfer_slots.release()
                await asyncio.sleep(0.5)
                continue
            # A verification handoff frees this worker to dispatch another file.
            await lease["released"].wait()

    async def job_phase(self, job_id, phase):
        lease = self.job_slots.get(job_id)
        if not lease or lease["phase"] == phase:
            return
        if phase == "verification":
            await self.verification_slots.acquire()
            self.transfer_slots.release()
            lease["phase"] = phase
            lease["released"].set()
        else:
            # Release verification before waiting for download capacity: avoids
            # a cycle with uploads waiting to hand off to verification.
            self.verification_slots.release()
            lease["phase"] = None
            await self.transfer_slots.acquire()
            lease["phase"] = phase

    async def scheduled_job(self, job):
        lease = self.job_slots[job["id"]]
        try:
            await self.run_job(job)
        except asyncio.CancelledError:
            # Cancellation before run_job starts must still release its claim.
            current = self.db.job(job["id"])
            if current and current["status"] in ("TRANSFERRING", "VERIFYING"):
                self.db.transition(job["id"], current["cancel_requested"] or "RETRY_WAIT",
                                   next_attempt=time.time(), last_error="service_interrupted" if self.stopping else "cancelled_by_user",
                                   cancel_requested=None)
            raise
        except Exception as error:
            self.interrupted_jobs.add(job["id"])
            self.task_failures.add("job-dispatch")
            logging.getLogger("telegram_vault").error("job_task_failed job=%s error=%s", job["id"], type(error).__name__)
        finally:
            self.cleanup_scheduled_job(job["id"], asyncio.current_task())

    def cleanup_scheduled_job(self, job_id, task):
        lease = self.job_slots.pop(job_id, None)
        if not lease:
            return
        if lease["phase"] == "transfer":
            self.transfer_slots.release()
        elif lease["phase"] == "verification":
            self.verification_slots.release()
        lease["released"].set()
        self.active.pop(job_id, None)
        self.progress.pop(job_id, None)
        if task.cancelled():
            try:
                current = self.db.job(job_id)
                if current and current["status"] in ("TRANSFERRING", "VERIFYING"):
                    self.db.transition(job_id, current["cancel_requested"] or "RETRY_WAIT",
                                       next_attempt=time.time(), last_error="service_interrupted" if self.stopping else "cancelled_by_user",
                                       cancel_requested=None)
            except Exception:
                self.interrupted_jobs.add(job_id)

    async def verified(self, path, job, receipt=None):
        stat = await self.storage.exists(path)
        if not stat:
            return False
        if stat["Size"] != job["size"] or not job["plaintext_sha256"]:
            raise MediaUnavailable("remote_conflict_requires_review")
        if await self.storage.hash_stream(path) != job["plaintext_sha256"]:
            raise MediaUnavailable("remote_hash_conflict_requires_review")
        if receipt is not None:
            receipt.update(stat)
        return True

    def complete(self, job):
        with self.db.transaction():
            self.db.set_setting(
                "uploaded_total", self.db.setting("uploaded_total", 0) + job["size"]
            )
            self.db.transition(
                job["id"],
                "COMPLETED",
                completed_at=time.time(),
                downloaded=job["size"],
                uploaded=job["size"],
                last_error=None,
                cancel_requested=None,
            )
            self.db.execute(
                "UPDATE transfers SET downloaded=?,uploaded=? WHERE job_id=? AND finished_at=(SELECT MAX(finished_at) FROM transfers WHERE job_id=?)",
                (job["size"], job["size"], job["id"], job["id"]),
            )
            self.db.event("transfer_completed", job_id=job["id"])
            if self.config.file_pause_enabled:
                duration = random.uniform(
                    self.config.file_pause_min_seconds, self.config.file_pause_max_seconds
                )
                deadline = max(self.db.setting("transfer_pause_until", 0), time.time() + duration)
                self.db.set_setting("transfer_pause_until", deadline)
                self.db.event(
                    "transfer_rest_started", f"Rest {duration:.1f} seconds", job_id=job["id"]
                )

    async def run_job(self, job):
        self.db.event("transfer_started", job_id=job["id"])
        try:
            if (
                self.provider.mode == "real"
                and job["attempts"] == 1
                and not job["temp_path"]
                and not job["plaintext_sha256"]
                and re.match(r"^\d+_\d+_[a-f0-9]{10}_", PurePosixPath(job["remote_path"]).name)
            ):
                entity = await self.provider.entity(job["chat_id"])
                raw = await self.rate.call(
                    lambda: self.provider.client.get_messages(entity, ids=job["message_id"])
                )
                if not raw:
                    raise MediaUnavailable("media_deleted_or_replaced")
                source = self.db.one("SELECT * FROM sources WHERE id=?", (job["source_id"],))
                metadata = await self.provider.named_metadata(raw, job["chat_id"], source["forum"])
                if metadata.file_id != job["telegram_file_id"]:
                    raise MediaUnavailable("media_deleted_or_replaced")
                topic = self.db.one(
                    "SELECT * FROM topics WHERE source_id=? AND topic_id=?",
                    (job["source_id"], metadata.topic_id),
                )
                target = metadata.remote_path(self.config.storage_root, source, topic)
                if self.db.one(
                    "SELECT id FROM media WHERE remote_path=? AND id<>?", (target, job["media_id"])
                ):
                    raise MediaUnavailable("filename_conflict")
                self.db.execute(
                    "UPDATE media SET remote_path=? WHERE id=?", (target, job["media_id"])
                )
                job["remote_path"] = target
            # Recovery reads remote contents before any new Telegram transfer.
            if job["plaintext_sha256"]:
                await self.job_phase(job["id"], "verification")
                self.db.transition(job["id"], "VERIFYING")
            # Crash between remote promotion and DB commit: verify existing final with stored digest.
            if await self.verified(job["remote_path"], job):
                self.db.transition(job["id"], "VERIFYING")
                self.complete(job)
                return
            temp_valid = False
            verified_temp_stat = {}
            if job["temp_path"] and job["plaintext_sha256"]:
                try:
                    temp_valid = await self.verified(job["temp_path"], job, receipt=verified_temp_stat)
                except MediaUnavailable:
                    # Only abandon a corrupt temporary attempt. Final conflicts
                    # above remain permanent and are never overwritten.
                    self.db.event("incomplete_corrupt_restarting", job_id=job["id"])
            if temp_valid:
                self.db.transition(job["id"], "VERIFYING")
            else:
                await self.job_phase(job["id"], "transfer")
                self.db.transition(job["id"], "TRANSFERRING")
                temp = f"{self.config.storage_root}/.incomplete/{job['id']}/{uuid.uuid4().hex}"
                # Unique failed attempts never masquerade as the final file. Retained for manual cleanup.
                self.db.execute("UPDATE jobs SET temp_path=? WHERE id=?", (temp, job["id"]))
                job["temp_path"] = temp
                began = time.monotonic()
                last_record = 0
                recorded_bytes = 0
                speed_samples = deque([(time.monotonic(), 0)])

                async def bounded():
                    iterator = self.provider.open_media_stream(job)
                    try:
                        async for chunk in iterator:
                            if self.config.download_bandwidth:
                                async with self.bandwidth_lock:
                                    await asyncio.sleep(
                                        max(0, self.next_download - time.monotonic())
                                    )
                                    self.next_download = (
                                        time.monotonic()
                                        + len(chunk) / self.config.download_bandwidth
                                    )
                            sent_at = time.monotonic()
                            yield chunk
                            elapsed_write = time.monotonic() - sent_at
                            self.progress.setdefault(job["id"], {})["downstream_wait_seconds"] = elapsed_write
                            if elapsed_write > 0.5:
                                self.rate.backpressured_until = time.monotonic() + 45
                    finally:
                        await iterator.aclose()

                def progress(total):
                    nonlocal last_record, recorded_bytes
                    now = time.monotonic()
                    speed_samples.append((now, total))
                    while len(speed_samples) > 2 and speed_samples[1][0] < now - 20:
                        speed_samples.popleft()
                    start_sample, start_bytes = speed_samples[0]
                    self.progress[job["id"]] = {
                        "downstream_wait_seconds": self.progress.get(job["id"], {}).get("downstream_wait_seconds", 0),
                        "bytes": total,
                        "speed": (total - start_bytes) / max(now - start_sample, 0.01),
                    }
                    if now - last_record >= 0.5 or total == job["size"]:
                        self.db.execute(
                            "UPDATE jobs SET downloaded=? WHERE id=?", (total, job["id"])
                        )
                        self.db.execute(
                            "UPDATE transfers SET downloaded=? WHERE job_id=? AND finished_at IS NULL",
                            (total, job["id"]),
                        )
                        self.db.set_setting(
                            "downloaded_total",
                            self.db.setting("downloaded_total", 0) + total - recorded_bytes,
                        )
                        recorded_bytes = total
                        last_record = now

                digest = await self.storage.put_stream(temp, bounded(), job["size"], progress)
                self.db.execute(
                    "UPDATE media SET plaintext_sha256=? WHERE id=?", (digest, job["media_id"])
                )
                job["plaintext_sha256"] = digest
                await self.job_phase(job["id"], "verification")
                self.db.transition(job["id"], "VERIFYING", uploaded=job["size"])
                self.db.execute(
                    "UPDATE transfers SET uploaded=?,status='VERIFYING' WHERE job_id=? AND finished_at IS NULL",
                    (job["size"], job["id"]),
                )
                verified_temp_stat = getattr(digest, "verified_stat", None) or {}
                if verified_temp_stat:
                    current_temp = await self.storage.stat(job["temp_path"])
                    if any(current_temp.get(key) != verified_temp_stat.get(key) for key in ("ID", "Size", "ModTime")):
                        verified_temp_stat = {}
                if self.config.verify_hash and not verified_temp_stat:
                    await self.verified(job["temp_path"], job, receipt=verified_temp_stat)
            # Recheck final; never overwrite an uncertain existing object.
            final_verified = await self.verified(job["remote_path"], job)
            if not final_verified:
                await self.storage.move(job["temp_path"], job["remote_path"])
            stat = await self.storage.stat(job["remote_path"])
            if stat["Size"] != job["size"]:
                raise StorageError("final_size_mismatch")
            identity_preserved = (
                bool(verified_temp_stat.get("ID"))
                and verified_temp_stat.get("ID") == stat.get("ID")
                and verified_temp_stat.get("Size") == stat["Size"]
                and verified_temp_stat.get("ModTime") == stat.get("ModTime")
            )
            if self.config.verify_hash and identity_preserved and not final_verified:
                self.db.event("verification_checksum_identity", job_id=job["id"])
            if (
                self.config.verify_hash and not final_verified and not identity_preserved
                and await self.storage.hash_stream(job["remote_path"]) != job["plaintext_sha256"]
            ):
                raise MediaUnavailable("final_hash_conflict_requires_review")
            self.complete(job)
        except asyncio.CancelledError:
            current = self.db.job(job["id"])
            target = current["cancel_requested"] or "RETRY_WAIT"
            self.db.transition(
                job["id"],
                target,
                last_error="service_interrupted" if self.stopping else "cancelled_by_user",
                next_attempt=time.time() + 5,
                cancel_requested=None,
            )
            self.db.event("transfer_cancelled", job_id=job["id"])
            raise
        except Exception as error:
            network_failure = isinstance(error, (ConnectionError, asyncio.TimeoutError))
            if network_failure:
                delay, reason = 60, "telegram_connection_unavailable"
                self.provider.status = "disconnected"
                self.db.execute("UPDATE jobs SET attempts=MAX(0,attempts-1) WHERE id=?", (job["id"],))
                self.db.set_setting("telegram_pause_until", max(self.db.setting("telegram_pause_until", 0), time.time() + delay))
                self.db.event("telegram_connection_unavailable", job_id=job["id"])
            elif isinstance(error, FloodPaused):
                delay, reason = error.seconds, "telegram_media_no_progress" if isinstance(error, MediaDeferred) else "telegram_flood_wait"
                # FloodWait does not exhaust transient retry budget.
                self.db.execute(
                    "UPDATE jobs SET attempts=MAX(0,attempts-1) WHERE id=?", (job["id"],)
                )
            else:
                delay = retry_delay(job["attempts"])
                reason = (
                    str(error)
                    if isinstance(error, (StorageError, MediaUnavailable))
                    else type(error).__name__
                )
            if isinstance(error, StorageError):
                if error.category == "google_rate_limit":
                    # Drive may enforce a longer upload quota window. Avoid
                    # burning the entire retry budget with immediate retries.
                    delay = max(delay, min(3600, 900 * 2 ** min(job["attempts"] - 1, 2)))
                self.db.set_setting(
                    "storage_pause_until",
                    max(self.db.setting("storage_pause_until", 0), time.time() + delay),
                )
                self.db.event(error.category, job_id=job["id"])
            permanent = isinstance(error, MediaUnavailable)
            target = (
                "FAILED"
                if permanent
                or (
                    not isinstance(error, FloodPaused) and not network_failure
                    and job["attempts"] >= self.config.max_retries
                )
                else "RETRY_WAIT"
            )
            self.db.transition(
                job["id"], target, next_attempt=time.time() + delay, priority=0 if isinstance(error, MediaDeferred) else 50, last_error=reason
            )
            self.db.event("transfer_waiting_telegram" if isinstance(error, FloodPaused) else "transfer_failed", reason, job_id=job["id"])

    def control_job(self, job_id, action):
        job = self.db.job(job_id)
        if not job:
            raise ValueError("Unknown job")
        if action == "retry":
            if job["status"] not in ("FAILED", "RETRY_WAIT", "CANCELLED", "SKIPPED"):
                raise ValueError("Only stopped/failed jobs can be retried")
            self.db.set_setting(f"media_no_progress:{job_id}", 0)
            self.db.transition(
                job_id,
                "QUEUED",
                attempts=0,
                priority=50,
                next_attempt=0,
                last_error=None,
                cancel_requested=None,
            )
        else:
            target = "SKIPPED" if action == "skip" else "CANCELLED"
            if job["status"] == "COMPLETED":
                raise ValueError("Completed backups cannot be cancelled or skipped")
            task = self.active.get(job_id)
            if task:
                self.db.execute("UPDATE jobs SET cancel_requested=? WHERE id=?", (target, job_id))
                task.cancel()
            else:
                self.db.transition(job_id, target, cancel_requested=None)
        self.db.event("job_" + action, job_id=job_id)

    async def control_scope(self, operation, source_id=None, topic_id=None, job_id=None):
        if topic_id is not None and source_id is None:
            raise ValueError("Chọn group trước khi chọn topic.")
        if operation not in ("pause", "resume", "cancel", "delete"):
            raise ValueError("Thao tác không hợp lệ.")
        where, args = "1=1", []
        if source_id is not None:
            source = self.db.one("SELECT * FROM sources WHERE id=? AND deleted=0", (source_id,))
            if not source:
                raise ValueError("Group không tồn tại.")
            where += " AND m.source_id=?"
            args.append(source_id)
            if topic_id is not None:
                if not self.db.one(
                    "SELECT * FROM topics WHERE source_id=? AND topic_id=?", (source_id, topic_id)
                ):
                    raise ValueError("Topic không tồn tại.")
                where += " AND m.topic_id=?"
                args.append(topic_id)
        if job_id is not None:
            if operation != "delete":
                raise ValueError("Chỉ dùng phạm vi job cho thao tác xóa.")
            job = self.db.job(job_id)
            if not job or job["status"] == "COMPLETED":
                raise ValueError("Chỉ xóa job chưa hoàn thành; backup đã lưu được giữ lại.")
            where += " AND j.id=?"
            args.append(job_id)
        tasks = []
        with self.db.transaction():
            if job_id is None:
                stopped = operation != "resume"
                if source_id is None:
                    self.db.set_setting("scheduler_paused", stopped)
                    if not stopped:
                        self.db.execute("UPDATE sources SET scan_requested=1 WHERE deleted=0")
                elif topic_id is None:
                    self.db.execute(
                        "UPDATE sources SET paused=?,scan_generation=scan_generation+1 WHERE id=?",
                        (stopped, source_id),
                    )
                    if operation == "resume":
                        self.db.execute(
                            "UPDATE sources SET scan_requested=1 WHERE id=?", (source_id,)
                        )
                    if operation == "delete":
                        self.db.execute(
                            "UPDATE sources SET deleted=1,enabled=0 WHERE id=?", (source_id,)
                        )
                else:
                    if source["all_topics"]:
                        self.db.execute(
                            "UPDATE topics SET selected=1 WHERE source_id=?", (source_id,)
                        )
                    self.db.execute(
                        "UPDATE sources SET all_topics=0,scan_generation=scan_generation+1 WHERE id=?",
                        (source_id,),
                    )
                    self.db.execute(
                        "UPDATE topics SET selected=? WHERE source_id=? AND topic_id=?",
                        (not stopped, source_id, topic_id),
                    )
                    if operation == "resume":
                        self.db.execute(
                            "UPDATE sources SET scan_requested=1,scan_cursor=0,scan_target=NULL WHERE id=?",
                            (source_id,),
                        )
            rows = self.db.rows(
                "SELECT j.id,j.status FROM jobs j JOIN media m ON m.id=j.media_id WHERE "
                + where
                + " AND j.status<>'COMPLETED'",
                args,
            )
            if operation != "resume":
                for row in rows:
                    task = self.active.get(row["id"])
                    if operation == "pause" and task:
                        self.db.execute(
                            "UPDATE jobs SET cancel_requested='RETRY_WAIT' WHERE id=?", (row["id"],)
                        )
                        task.cancel()
                    elif operation in ("cancel", "delete"):
                        self.control_job(row["id"], "cancel")
                    if task:
                        tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        # Cancellation before run_job enters its try/finally still releases the claim.
        if operation != "resume":
            for row in rows:
                current = self.db.job(row["id"])
                if current and current["status"] in ("TRANSFERRING", "VERIFYING"):
                    target = "RETRY_WAIT" if operation == "pause" else "CANCELLED"
                    self.db.transition(row["id"], target, cancel_requested=None, next_attempt=0)
                    self.db.execute(
                        "UPDATE transfers SET status=?,finished_at=? WHERE job_id=? AND finished_at IS NULL",
                        (target, time.time(), row["id"]),
                    )
        removed = 0
        if operation == "delete":
            with self.db.transaction():
                for row in rows:
                    current = self.db.job(row["id"])
                    if current and current["status"] not in (
                        "COMPLETED",
                        "TRANSFERRING",
                        "VERIFYING",
                    ):
                        self.db.execute("DELETE FROM transfers WHERE job_id=?", (row["id"],))
                        self.db.execute("DELETE FROM jobs WHERE id=?", (row["id"],))
                        removed += 1
        self.db.event(
            "queue_" + operation,
            f"scope source={source_id} topic={topic_id}; matched={len(rows)} removed={removed}",
        )
        return {"ok": True, "matched": len(rows), "removed": removed, "backups_retained": True}

    async def probe_storage(self):
        if not self.storage:
            return {"state": self.storage_error or "not_configured", "checked_at": time.time()}
        try:
            await self.storage.command("lsd", self.storage.remote, timeout=30)
            self.storage_health = {"state": "connected", "checked_at": time.time()}
        except Exception:
            self.storage_health = {"state": "unavailable", "checked_at": time.time()}
        return self.storage_health

    async def reconcile(self):
        if not self.storage:
            raise ValueError("Storage not configured")
        missing = checked = unexpected = 0
        cursor = 0
        while True:
            rows = self.db.rows(
                "SELECT id FROM jobs WHERE status='COMPLETED' AND id>? ORDER BY id LIMIT 100",
                (cursor,),
            )
            if not rows:
                break
            for row in rows:
                job = self.db.job(row["id"])
                cursor = row["id"]
                checked += 1
                stat = await self.storage.exists(job["remote_path"])
                if not stat or stat["Size"] != job["size"]:
                    self.db.transition(
                        job["id"],
                        "FAILED",
                        last_error="remote_missing_or_size_mismatch",
                        completed_at=None,
                    )
                    missing += 1
        async for path in self.storage.list(self.config.storage_root):
            if not self.db.one(
                "SELECT id FROM media WHERE remote_path=?", (path,)
            ) and not self.db.one("SELECT id FROM jobs WHERE temp_path=?", (path,)):
                unexpected += 1
                # Count only; do not delete or expose remote names in logs.
        result = dict(checked=checked, missing=missing, unexpected=unexpected)
        self.db.event("reconciliation_completed", str(result))
        return result

    async def maintenance_loop(self):
        while True:
            try:
                if time.time() - self.db.setting("last_db_backup", 0) > 86400:
                    folder = self.config.data_dir / "db-backups"
                    self.db.backup(folder / f"vault-{int(time.time())}.sqlite3")
                    backups = sorted(folder.glob("vault-*.sqlite3"))
                    for path in backups[: -self.config.backup_retention]:
                        path.unlink()
                    self.db.set_setting("last_db_backup", time.time())
                self.db.execute(
                    "DELETE FROM events WHERE created_at<?",
                    (time.time() - self.config.event_retention_days * 86400,),
                )
                self.db.execute("DELETE FROM auth_sessions WHERE expires_at<?", (time.time(),))
                self.db.execute("DELETE FROM login_attempts WHERE reset_at<?", (time.time(),))
                self.db.execute("PRAGMA wal_checkpoint(PASSIVE)")
                if (
                    not self.storage_health["checked_at"]
                    or time.time() - self.storage_health["checked_at"] > 60
                ):
                    await self.probe_storage()
                if self.provider.status in ("disconnected", "login_required"):
                    try:
                        async with self.operation_lock:
                            await asyncio.wait_for(self.provider.connect(self.on_live), timeout=45)
                    except Exception:
                        self.provider.status = "disconnected"
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                self.db.event("maintenance_failed", type(error).__name__)
                await asyncio.sleep(30)
