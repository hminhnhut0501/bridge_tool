import asyncio
import json
import logging
import linecache
from collections import deque
import re
import time
from contextlib import nullcontext
from datetime import timezone
from pathlib import Path
from urllib.parse import urlsplit

from telethon import TelegramClient, errors, events, functions, types, utils
from telethon.errors import FloodWaitError

from .models import Message


class FloodPaused(Exception):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__("telegram_flood_wait")


class MediaDeferred(FloodPaused):
    """No-progress download yields its slot without consuming retry budget."""


class MediaUnavailable(Exception):
    pass


class AccountRateController:
    def __init__(self, db, pace):
        self.db, self.pace = db, pace
        self.lock = asyncio.Lock()
        self.next_request = 0.0
        self.media_lock = asyncio.Lock()
        self.transport_v3 = bool(db.setting("telegram_transport_v3", False))
        self.media_floor = 0.02 if self.transport_v3 else 0.25
        self.media_inflight = asyncio.Semaphore(2)
        self.backpressured_until = 0.0
        self.next_media = 0.0
        self.recent_requests = deque(maxlen=2000)
        self.last_relax = time.monotonic()
        self.success_bytes = 0
        self.metrics = {"pacing_seconds": 0.0, "telegram_seconds": 0.0, "media_bytes": 0}

    async def call(self, operation, *, media=False, operation_name=None, stage=None, job_id=None, source_id=None, context=None):
        # Bounded media lanes run concurrently with pipe backpressure. Metadata
        # remains serialized and paced; all lanes share FloodWait deadlines.
        async with (self.media_inflight if self.transport_v3 else nullcontext()) if media else self.lock:
            deadline = self.db.setting("telegram_pause_until", 0)
            if deadline > time.time():
                raise FloodPaused(deadline - time.time())
            if media:
                async with self.media_lock:
                    interval = max(self.media_floor, min(4.0, float(self.db.setting("telegram_media_interval", self.media_floor))))
                    wait_began = time.monotonic()
                    await asyncio.sleep(max(0, self.next_media - time.monotonic()))
                    self.metrics["pacing_seconds"] += time.monotonic() - wait_began
                    self.next_media = time.monotonic() + interval
            else:
                await asyncio.sleep(max(0, self.next_request - time.monotonic()))
            # Another media lane can enter cooldown while metadata is pacing.
            deadline = self.db.setting("telegram_pause_until", 0)
            if deadline > time.time():
                raise FloodPaused(deadline - time.time())
            label = operation_name or getattr(operation, "__name__", "unknown")
            label = "unlabelled" if label == "<lambda>" else label
            self.recent_requests.append((time.monotonic(), label, media))
            try:
                request_began = time.monotonic()
                try:
                    result = await operation()
                finally:
                    if media:
                        self.metrics["telegram_seconds"] += time.monotonic() - request_began
                if media and isinstance(result, (bytes, bytearray, memoryview)):
                    self.success_bytes += len(result)
                    self.metrics["media_bytes"] += len(result)
                    if time.monotonic() >= self.backpressured_until and time.monotonic() - self.last_relax >= 45 and self.success_bytes >= 4 * 1048576:
                        old = float(self.db.setting("telegram_media_interval", 0.25))
                        new = max(self.media_floor, old * 0.75)
                        self.db.set_setting("telegram_media_interval", new)
                        self.last_relax = time.monotonic()
                        self.success_bytes = 0
                        if new < old:
                            self.db.event("telegram_speed_recovery", f"chunk interval {old:.2f}s → {new:.2f}s after successful media")
                return result
            except (FloodWaitError, errors.FloodPremiumWaitError) as error:
                cached = False
                tb = error.__traceback__
                while tb:
                    cached |= "raise errors.FloodWaitError(request=r, capture=diff)" in linecache.getline(tb.tb_frame.f_code.co_filename, tb.tb_lineno)
                    tb = tb.tb_next
                now = time.time()
                recent = [
                    stamp
                    for stamp in self.db.setting("telegram_flood_history", [])
                    if stamp > now - 3600
                ]
                # Concurrent lanes report one incident; count a burst once.
                distinct = not cached and (not recent or now - recent[-1] >= 2)
                if distinct:
                    recent.append(now)
                    self.db.set_setting("telegram_flood_history", recent[-3:])
                    lanes = max(1, int(self.db.setting("telegram_media_lanes", 8)) // 2)
                    self.db.set_setting("telegram_media_lanes", lanes)
                    interval = min(4.0, max(0.1 if self.transport_v3 else 0.25, float(self.db.setting("telegram_media_interval", self.media_floor)) * 2))
                    self.db.set_setting("telegram_media_interval", interval)
                    self.db.set_setting("telegram_last_flood", now)
                    self.last_relax = time.monotonic()
                    self.success_bytes = 0
                delay = error.seconds + 1
                if len(recent) >= 3:
                    # Brief media throttles need graduated backoff (max 30s), not a rigid 120s or 1h freeze.
                    delay = max(delay, min(30, error.seconds + 5 * (len(recent) - 2)) if media else 3600)
                if distinct and len(recent) >= 3:
                    self.db.event("telegram_repeated_flood_cooldown")
                deadline = max(self.db.setting("telegram_pause_until", 0), now + delay)
                self.db.set_setting("telegram_pause_until", deadline)
                if distinct or cached:
                    request = getattr(error, "request", None)
                    rpc = type(request).__name__ if request is not None else None
                    window = [item for item in self.recent_requests if item[0] >= time.monotonic() - 60]
                    diagnostic = {"error_class": type(error).__name__, "origin": "telethon_cached_deadline" if cached else "rpc_error_path",
                                  "request_offset": getattr(request, "offset", None), "request_limit": getattr(request, "limit", None),
                                  **{k:v for k,v in (context or {}).items() if k in ("offset", "dc_id", "file_size", "lane")},
                                  "event": "telegram_flood_diagnostic", "rpc": rpc, "operation": label,
                                  "stage": stage or ("media" if media else "metadata"),
                                  "job_id": job_id, "source_id": source_id,
                                  "telegram_wait_seconds": error.seconds, "app_wait_seconds": round(deadline-now),
                                  "requests_last_60s": len(window), "media_calls_last_60s": sum(item[2] for item in window),
                                  "media_interval_seconds": self.db.setting("telegram_media_interval", 0.25),
                                  "lanes_per_file": self.db.setting("telegram_media_lanes", 8)}
                    self.db.set_setting("telegram_last_flood_diagnostic", diagnostic)
                    logging.getLogger("telegram_vault").warning(json.dumps(diagnostic))
                    self.db.event("flood_wait", f"{rpc or label} [{diagnostic["stage"]}]: Telegram {error.seconds}s; app {deadline-now:.0f}s; {len(window)} calls/60s", job_id=job_id, source_id=source_id)
                # Lower pressure after repeated FloodWait, persisted across restarts.
                self.db.set_setting(
                    "telegram_pace",
                    min(5, max(self.pace, self.db.setting("telegram_pace", self.pace)) * 1.5),
                )
                raise FloodPaused(deadline - now) from None
            finally:
                if not media:
                    self.next_request = time.monotonic() + max(
                        self.pace, self.db.setting("telegram_pace", self.pace)
                    )


def topic_id(message, forum):
    if not forum:
        return 0
    header = getattr(message, "reply_to", None)
    if header and getattr(header, "forum_topic", False):
        return (
            getattr(header, "reply_to_top_id", None)
            or getattr(header, "reply_to_msg_id", None)
            or 1
        )
    return 1


class TelethonProvider:
    mode = "real"

    def __init__(self, config, rate):
        self.config, self.rate = config, rate
        self.client = None
        self.status = "not_configured"
        self.callback = None
        self.album_cache = {}

    @property
    def status(self):
        if self._status == "connected" and self.client is not None:
            if not self.client.is_connected():
                self._status = "disconnected"
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    async def connect(self, callback):
        self.callback = callback
        if not self.config.api_id or not self.config.api_hash:
            return
        if self.client is None:
            Path(self.config.session_path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.client = TelegramClient(
                self.config.session_path,
                self.config.api_id,
                self.config.api_hash,
                flood_sleep_threshold=15,
                # Telegram login may require a DC migration before sending the code.
                # Allow bounded retries after migration; FloodWait still propagates.
                request_retries=2,
                raise_last_call_error=True,
                connection_retries=3,
                auto_reconnect=True,
                entity_cache_limit=1000,
            )
            self.client.add_event_handler(self._on_message, events.NewMessage())
            self.client.add_event_handler(self._on_message, events.MessageEdited())
        await self.client.connect()
        if not await self.rate.call(self.client.is_user_authorized):
            self.status = "login_required"
            return
        user = await self.rate.call(self.client.get_me)
        if not user:
            self.status = "login_required"
            return
        previous = self.rate.db.setting("telegram_account_id")
        if (
            previous
            and previous != user.id
            and self.rate.db.one("SELECT id FROM sources WHERE deleted=0 LIMIT 1")
        ):
            self.status = "account_mismatch"
            return
        self.rate.db.set_setting("telegram_account_id", user.id)
        self.rate.db.set_setting("telegram_premium", bool(getattr(user, "premium", False)))
        self.rate.db.set_setting("telegram_premium_checked_at", time.time())
        self.status = "connected"

    async def close(self):
        if self.client:
            await self.client.disconnect()

    def ready(self):
        if self.status != "connected":
            raise ConnectionError("telegram_not_connected")

    def metadata(self, message, chat_id, forum):
        file = message.file
        return Message(
            chat_id=chat_id,
            message_id=message.id,
            date=message.date.replace(tzinfo=timezone.utc).timestamp()
            if message.date.tzinfo is None
            else message.date.timestamp(),
            topic_id=topic_id(message, forum),
            file_id=str((message.document or message.photo).id)
            if (message.document or message.photo)
            else "",
            filename=(
                file.name
                or f"{'Video' if message.video else 'Photo' if message.photo else 'Document'}{file.ext or ''}"
            )
            if file
            else "",
            mime_type=(file.mime_type or "") if file else "",
            size=(file.size or 0) if file else 0,
            native_video=bool(message.video),
            caption=getattr(message, "message", "") or "",
        )

    async def named_metadata(self, message, chat_id, forum):
        result = self.metadata(message, chat_id, forum)
        grouped = getattr(message, "grouped_id", None)
        if not grouped:
            return result
        key = (chat_id, grouped)
        members = self.album_cache.get(key)
        if members is None or message.id not in members["ids"]:
            entity = await self.entity(chat_id)
            nearby = await self.rate.call(
                lambda: self.client.get_messages(
                    entity, ids=list(range(max(1, message.id - 10), message.id + 11))
                )
            )
            album = sorted(
                (item for item in nearby if item and getattr(item, "grouped_id", None) == grouped),
                key=lambda item: item.id,
            )
            if not album:
                raise MediaUnavailable("album_metadata_unavailable")
            members = {
                "ids": [item.id for item in album],
                "caption": next((item.message for item in album if item.message), ""),
            }
            self.album_cache[key] = members
            if len(self.album_cache) > 512:
                self.album_cache.pop(next(iter(self.album_cache)))
        result.album_id = members["ids"][0]
        result.album_index = members["ids"].index(message.id) + 1
        result.caption = result.caption or members["caption"]
        return result

    async def _on_message(self, event):
        if self.callback:
            # Callback handles only configured sources. Deleted-message events deliberately ignored.
            await self.callback(event.chat_id, event.message)

    async def list_sources(self):
        self.ready()
        result = []
        iterator = self.client.iter_dialogs()
        while True:
            try:
                dialog = await self.rate.call(lambda: anext(iterator), operation_name="iter_dialogs", stage="discovery")
            except StopAsyncIteration:
                break
            if dialog.is_group or dialog.is_channel:
                result.append(
                    dict(
                        chat_id=dialog.id,
                        name=dialog.name,
                        kind=("supergroup" if dialog.entity.megagroup else "channel")
                        if isinstance(dialog.entity, types.Channel)
                        else "group",
                        forum=bool(getattr(dialog.entity, "forum", False)),
                    )
                )
        return result

    async def resolve_source(self, reference):
        self.ready()
        reference = str(reference).strip()
        invite = None
        if reference.startswith(("https://", "http://")):
            url = urlsplit(reference)
            if url.hostname not in ("t.me", "telegram.me"):
                raise ValueError("Chỉ hỗ trợ link t.me hoặc telegram.me.")
            parts = url.path.strip("/").split("/")
            if parts[0] == "c" and len(parts) >= 2 and parts[1].isdigit():
                reference = -(10**12 + int(parts[1]))
            elif parts[0].startswith("+"):
                invite = parts[0][1:]
            elif parts[0] == "joinchat" and len(parts) == 2:
                invite = parts[1]
            else:
                reference = "@" + parts[0]
        elif re.fullmatch(r"-?\d+", reference):
            reference = int(reference)
        elif not re.fullmatch(r"@?[A-Za-z][A-Za-z0-9_]{3,}", reference):
            raise ValueError("Dán link group/channel, @username hoặc chat ID Telegram.")
        if isinstance(reference, int):
            peer_id, peer_type = utils.resolve_id(reference)
            reference = peer_type(peer_id)
        try:
            if invite is not None:
                result = await self.rate.call(
                    lambda: self.client(functions.messages.CheckChatInviteRequest(invite))
                )
                if not isinstance(result, types.ChatInviteAlready):
                    raise ValueError(
                        "Tài khoản chưa tham gia group/channel. Mở link trong Telegram và tham gia trước."
                    )
                entity = result.chat
            else:
                entity = await self.rate.call(lambda: self.client.get_entity(reference))
            if not isinstance(entity, (types.Chat, types.Channel)):
                raise ValueError("Nguồn phải là group hoặc channel Telegram.")
            if getattr(entity, "left", False) or getattr(entity, "kicked", False):
                raise ValueError(
                    "Tài khoản chưa tham gia hoặc không có quyền truy cập group/channel."
                )
            return dict(
                chat_id=utils.get_peer_id(entity),
                name=entity.title,
                kind=("supergroup" if entity.megagroup else "channel")
                if isinstance(entity, types.Channel)
                else "group",
                forum=bool(getattr(entity, "forum", False)),
            )
        except (errors.RPCError, ValueError) as error:
            if isinstance(error, FloodWaitError):
                raise
            if isinstance(error, errors.RPCError):
                raise ValueError(
                    "Không truy cập được group/channel. Kiểm tra link và quyền của tài khoản."
                ) from None
            raise

    async def entity(self, chat_id):
        self.ready()
        return await self.rate.call(lambda: self.client.get_input_entity(chat_id), operation_name="get_input_entity", stage="resolve")

    async def list_topics(self, chat_id):
        entity = await self.entity(chat_id)
        output = [dict(topic_id=1, name="General")]
        offset_date, offset_id, offset_topic = None, 0, 0
        seen = {1}
        while True:
            page = await self.rate.call(
                lambda: self.client(
                    functions.messages.GetForumTopicsRequest(
                        peer=entity,
                        offset_date=offset_date,
                        offset_id=offset_id,
                        offset_topic=offset_topic,
                        limit=100,
                    )
                )
            )
            fresh = [
                topic
                for topic in page.topics
                if getattr(topic, "id", 0) not in seen and hasattr(topic, "title")
            ]
            for topic in fresh:
                output.append(dict(topic_id=topic.id, name=topic.title))
                seen.add(topic.id)
            if not fresh or len(page.topics) < 100:
                break
            last = page.topics[-1]
            offset_topic, offset_id = last.id, getattr(last, "top_message", 0)
            last_message = next((m for m in page.messages if m.id == offset_id), None)
            offset_date = last_message.date if last_message else last.date
        return output

    async def latest_id(self, source):
        entity = await self.entity(source["chat_id"])
        messages = await self.rate.call(lambda: self.client.get_messages(entity, limit=1), operation_name="get_messages", stage="scan_latest")
        return messages[0].id if messages else 0

    async def scan(self, source, cursor, target, limit, recent=False):
        entity = await self.entity(source["chat_id"])
        iterator = self.client.iter_messages(
            entity,
            limit=limit,
            reverse=not recent,
            min_id=0 if recent else cursor,
            max_id=0 if recent else target + 1,
        )
        while True:
            try:
                message = await self.rate.call(lambda: anext(iterator), operation_name="iter_messages", stage="scan_recent" if recent else "scan_history", source_id=source.get("id"))
            except StopAsyncIteration:
                break
            yield await self.named_metadata(message, source["chat_id"], source["forum"])

    async def open_media_stream(self, job):
        entity = await self.entity(job["chat_id"])
        message = await self.rate.call(
            lambda: self.client.get_messages(entity, ids=job["message_id"]), operation_name="get_messages", stage="download_prepare", job_id=job.get("id"), source_id=job.get("source_id")
        )
        if (
            not message
            or not (message.document or message.photo)
            or str((message.document or message.photo).id) != job["telegram_file_id"]
        ):
            raise MediaUnavailable("media_deleted_or_replaced")
        chunk_size = 524288
        size = job["size"]
        lanes = min(max(1, min(8, int(self.rate.db.setting("telegram_media_lanes", 8)))),
                    max(1, (size + chunk_size - 1) // chunk_size))
        iterators = [
            self.client.iter_download(
                message.media,
                offset=lane * chunk_size,
                stride=lanes * chunk_size,
                chunk_size=chunk_size,
                request_size=chunk_size,
                file_size=size,
                limit=(size - lane * chunk_size + lanes * chunk_size - 1) // (lanes * chunk_size),
            )
            for lane in range(lanes)
        ]

        async def fetch_chunk(lane, offset):
            nonlocal message
            waiting = False
            failures = 0
            while True:
                try:
                    chunk = await self.rate.call(
                        lambda: anext(iterators[lane]), media=True,
                        operation_name="iter_download", stage="download_chunk",
                        job_id=job.get("id"), source_id=job.get("source_id"),
                        context={"offset":offset,"lane":lane,"file_size":size,"dc_id":getattr(message.document or message.photo,"dc_id",None)})
                    if offset == 0 and job.get("id") is not None:
                        self.rate.db.set_setting(f"media_no_progress:{job['id']}", 0)
                    if waiting:
                        self.rate.db.event("transfer_chunk_resumed", f"offset={offset}",
                                           job_id=job.get("id"), source_id=job.get("source_id"))
                    return chunk
                except (errors.FileReferenceExpiredError, errors.FilerefUpgradeNeededError):
                    self.rate.db.event("file_reference_refreshed", f"offset={offset}", job_id=job.get("id"))
                    try:
                        entity = await self.entity(job["chat_id"])
                        fresh_msg = await self.rate.call(
                            lambda: self.client.get_messages(entity, ids=job["message_id"]),
                            operation_name="get_messages", stage="refresh_file_reference",
                            job_id=job.get("id"), source_id=job.get("source_id")
                        )
                        if fresh_msg and (fresh_msg.document or fresh_msg.photo):
                            message = fresh_msg
                    except Exception:
                        pass
                    await iterators[lane].close()
                    iterators[lane] = self.client.iter_download(
                        message.media, offset=offset, stride=lanes * chunk_size,
                        chunk_size=chunk_size, request_size=chunk_size, file_size=size,
                        limit=(size-offset+lanes*chunk_size-1)//(lanes*chunk_size))
                except FloodPaused as error:
                    failures += 1
                    if failures >= 3:
                        self.rate.db.event("transfer_no_progress_deferred", f"No progress after 3 waits at offset={offset}; retry in >=30min",
                                           job_id=job.get("id"), source_id=job.get("source_id"))
                        key = f"media_no_progress:{job.get('id')}"
                        count = int(self.rate.db.setting(key, 0)) + 1
                        self.rate.db.set_setting(key, count)
                        if count >= 3:
                            raise MediaUnavailable("telegram_media_no_progress_review_required") from None
                        raise MediaDeferred(max(1800 if count == 1 else 7200, error.seconds)) from None
                    if not waiting:
                        self.rate.db.event("transfer_chunk_waiting", f"offset={offset}; pipeline retained",
                                           job_id=job.get("id"), source_id=job.get("source_id"))
                        waiting = True
                    # A failed iterator may have changed its internal offset.
                    # Recreate only this lane at the exact undelivered chunk.
                    await iterators[lane].close()
                    while True:
                        remaining = self.rate.db.setting("telegram_pause_until", 0) - time.time()
                        if remaining <= 0:
                            break
                        await asyncio.sleep(min(30, remaining))
                    iterators[lane] = self.client.iter_download(
                        message.media, offset=offset, stride=lanes * chunk_size,
                        chunk_size=chunk_size, request_size=chunk_size, file_size=size,
                        limit=(size-offset+lanes*chunk_size-1)//(lanes*chunk_size))

        def fetch(lane, offset):
            return asyncio.create_task(fetch_chunk(lane, offset))

        pending = [fetch(lane, lane * chunk_size) for lane in range(lanes)]
        try:
            for offset in range(0, size, chunk_size):
                lane = (offset // chunk_size) % lanes
                chunk = await pending[lane]
                pending[lane] = None
                expected = min(chunk_size, size - offset)
                if len(chunk) != expected:
                    raise MediaUnavailable("truncated_parallel_download")
                # Refill this lane while the ordered chunk drains to Drive.
                if offset + lanes * chunk_size < size:
                    pending[lane] = fetch(lane, offset + lanes * chunk_size)
                yield bytes(chunk)
        finally:
            tasks = [task for task in pending if task is not None]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.gather(
                *(iterator.close() for iterator in iterators), return_exceptions=True
            )


class MockTelegramProvider:
    """Explicit local test adapter; transfers still use real rclone crypt."""

    mode = "mock"
    status = "connected"

    def __init__(self, db=None):
        self.db = db
        self.callback = None
        self.groups = [
            dict(chat_id=-1001001, name="Local Video Archive", kind="supergroup", forum=True),
            dict(chat_id=-1001002, name="Field Notes", kind="group", forum=False),
        ]
        self.messages = {}
        stamp = time.time() - 86400
        for group in self.groups:
            self.messages[group["chat_id"]] = [
                Message(
                    group["chat_id"],
                    i,
                    stamp + i * 60,
                    topic_id=(1 if i % 2 else 42) if group["forum"] else 0,
                    file_id=f"local-{group['chat_id']}-{i}",
                    filename=f"sample_{i:02}.mp4",
                    mime_type="video/mp4",
                    size=(i % 4 + 1) * 1048576,
                    native_video=True,
                )
                for i in range(1, 13)
            ]

    async def connect(self, callback):
        self.callback = callback

    async def close(self):
        pass

    async def list_sources(self):
        return self.groups

    async def resolve_source(self, reference):
        source = next((s for s in self.groups if str(s["chat_id"]) == str(reference)), None)
        if not source:
            raise ValueError("Không tìm thấy nguồn mock.")
        return source

    async def list_topics(self, chat_id):
        return [dict(topic_id=1, name="General"), dict(topic_id=42, name="Studio clips")]

    async def latest_id(self, source):
        return max((m.message_id for m in self.messages.get(source["chat_id"], [])), default=0)

    async def scan(self, source, cursor, target, limit, recent=False):
        selected = self.messages.get(source["chat_id"], [])
        selected = (
            selected[-limit:][::-1]
            if recent
            else [m for m in selected if cursor < m.message_id <= target][:limit]
        )
        for message in selected:
            await asyncio.sleep(0)
            yield message

    async def open_media_stream(self, job):
        message = next(
            (
                m
                for m in self.messages[job["chat_id"]]
                if m.message_id == job["message_id"] and m.file_id == job["telegram_file_id"]
            ),
            None,
        )
        if not message and not job["telegram_file_id"].startswith(f"live-{job['chat_id']}-"):
            raise MediaUnavailable()
        size = message.size if message else job["size"]
        chunk = bytes(range(256)) * 2048
        for offset in range(0, size, len(chunk)):
            await asyncio.sleep(0.04)
            yield chunk[: min(len(chunk), size - offset)]

    async def emit(self, chat_id):
        messages = self.messages[chat_id]
        index = max(m.message_id for m in messages) + 1
        if self.db:
            saved = self.db.one(
                "SELECT MAX(message_id) AS n FROM messages WHERE chat_id=?", (chat_id,)
            )
            index = max(index, (saved["n"] or 0) + 1)
        message = Message(
            chat_id,
            index,
            time.time(),
            topic_id=1 if chat_id == -1001001 else 0,
            file_id=f"live-{chat_id}-{index}",
            filename=f"live_{index}.mp4",
            mime_type="video/mp4",
            size=2097152,
            native_video=True,
        )
        messages.append(message)
        await self.callback(chat_id, message)
