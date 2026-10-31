import argparse
import asyncio
import fcntl
import json
import os
import time
import uuid
from pathlib import Path

import psutil
from telethon import TelegramClient, functions

from .config import Config
from .rate import TelegramRateController
from .storage import RcloneCryptStorage


def client():
    config = Config.from_env()
    if not config.api_id or not config.api_hash:
        raise ValueError("Set Telegram API credentials privately before login")
    session = Path(config.session_path)
    session.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    return TelegramClient(
        str(session),
        config.api_id,
        config.api_hash,
        flood_sleep_threshold=0,
        request_retries=0,
    )


async def synthetic(size):
    chunk = bytes(range(256)) * 2048
    for offset in range(0, size, len(chunk)):
        yield chunk[: min(len(chunk), size - offset)]


async def transfer(storage, chunks, size):
    run_id = uuid.uuid4().hex
    temporary = f"TelegramVault_TEST/.incomplete/{run_id}"
    final = f"TelegramVault_TEST/verified/{run_id}.bin"
    started = time.monotonic()
    peak = 0
    stopped = asyncio.Event()

    async def monitor():
        nonlocal peak
        process = psutil.Process()
        while not stopped.is_set():
            family = [process, *process.children(recursive=True)]
            rss = 0
            for member in family:
                try:
                    rss += member.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            peak = max(peak, rss)
            await asyncio.sleep(0.05)

    task = asyncio.create_task(monitor())
    try:
        digest = await storage.put_stream(temporary, chunks, size)
        if await storage.hash_stream(temporary) != digest:
            raise ValueError("Decrypted SHA-256 mismatch; object stays incomplete")
        await storage.command(
            "moveto", storage.target(temporary), storage.target(final), "--immutable"
        )
        if (await storage.stat(final))["Size"] != size:
            raise ValueError("Final destination verification failed")
        elapsed = time.monotonic() - started
        report = dict(
            status="VERIFIED",
            path=final,
            bytes=size,
            seconds=round(elapsed, 3),
            average_bytes_per_second=int(size / elapsed),
            peak_process_tree_rss_bytes=peak,
            plaintext_sha256=digest,
            full_plaintext_disk_file=False,
            note="RSS includes Python and rclone; duration includes decrypt verification. Local crypt backend stores encrypted payload on disk.",
        )
        reports = Path("data/reports")
        reports.mkdir(parents=True, exist_ok=True, mode=0o700)
        (reports / f"{run_id}.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        stopped.set()
        await task


async def run(args):
    if args.command in ("synthetic", "poc", "doctor"):
        config = os.environ.get("RCLONE_CONFIG")
        if not config:
            raise ValueError("Set RCLONE_CONFIG to a chmod 600 config file")
        storage = RcloneCryptStorage(
            config, os.getenv("RCLONE_REMOTE", "crypt:"), os.getenv("RCLONE_BINARY", "rclone")
        )
        if args.command == "doctor":
            await storage.command("lsd", storage.remote)
            print("rclone crypt config + read-only connectivity: OK")
            return
        if args.command == "synthetic":
            await transfer(storage, synthetic(args.bytes), args.bytes)
            return
    config = Config.from_env()
    lock = open(config.database_path + ".lock", "a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise ValueError("Stop service before using account CLI commands") from None
    try:
        tg = client()
    except BaseException:
        lock.close()
        raise
    rate = TelegramRateController()
    try:
        if args.command == "login":
            await tg.start()  # CLI alternative; uses the same private session as web sign-in.
            print("Session persisted. Keep data/session private.")
            return
        await tg.connect()
        if not await tg.is_user_authorized():
            raise ValueError("Run telegram-vault login in a terminal first")
        if args.command == "sources":
            # iter_dialogs internally paginates; gate each returned iterator step.
            iterator = tg.iter_dialogs()
            while True:
                try:
                    dialog = await rate.call(lambda: anext(iterator))
                except StopAsyncIteration:
                    break
                if dialog.is_group:
                    print(
                        json.dumps(
                            dict(
                                id=dialog.id,
                                name=dialog.name,
                                forum=bool(getattr(dialog.entity, "forum", False)),
                            ),
                            ensure_ascii=False,
                        )
                    )
            return
        entity = await rate.call(lambda: tg.get_entity(args.chat))
        if args.command == "topics":
            result = await rate.call(
                lambda: tg(
                    functions.messages.GetForumTopicsRequest(
                        peer=entity, offset_date=None, offset_id=0, offset_topic=0, limit=100
                    )
                )
            )
            for topic in result.topics:
                print(json.dumps(dict(id=topic.id, title=topic.title), ensure_ascii=False))
            print("POC lists first 100 topics; full pagination belongs to core phase.")
            return
        message = await rate.call(lambda: tg.get_messages(entity, ids=args.message))
        if not message or not message.file or not message.document:
            raise ValueError("Message has no downloadable document/video")
        if not (message.video or (message.file.mime_type or "").startswith("video/")):
            raise ValueError("POC accepts video only")
        size = message.file.size
        if not size or size <= 0:
            raise ValueError("Known positive media size required for rcat --size")

        async def chunks():
            iterator = tg.iter_download(message.media, request_size=524288)
            try:
                while True:
                    try:
                        yield bytes(await rate.call(lambda: anext(iterator)))
                    except StopAsyncIteration:
                        break
            finally:
                await iterator.close()

        await transfer(storage, chunks(), size)
    finally:
        await tg.disconnect()
        lock.close()


def main():
    os.umask(0o077)
    from dotenv import load_dotenv

    load_dotenv(override=False)
    parser = argparse.ArgumentParser(
        description="Vault Bridge backup service and administrator CLI"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("login", "sources", "doctor"):
        commands.add_parser(name)
    for name in ("init-admin", "status", "scan", "retry-failed", "reconcile", "backup-db"):
        command = commands.add_parser(name)
        if name == "scan":
            command.add_argument("--source", type=int)
            command.add_argument("--full", action="store_true")
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.getenv("APP_PORT", "8080")))
    topics = commands.add_parser("topics")
    topics.add_argument("chat", type=int)
    poc = commands.add_parser("poc")
    poc.add_argument("chat", type=int)
    poc.add_argument("message", type=int)
    bench = commands.add_parser("synthetic")
    bench.add_argument("--bytes", type=int, default=256 * 1024 * 1024)
    args = parser.parse_args()
    if args.command in (
        "serve",
        "init-admin",
        "status",
        "scan",
        "retry-failed",
        "reconcile",
        "backup-db",
    ):
        from .admin import execute

        execute(args)
        return
    if args.command == "synthetic" and args.bytes <= 0:
        parser.error("--bytes must be positive")
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print(
            "Stopped. Incomplete encrypted objects remain under TEST/.incomplete; retry uses a new path."
        )
    except Exception as error:
        # Avoid dumping provider errors containing credentials, phone, or remote names.
        parser.exit(
            1,
            f"Operation failed ({type(error).__name__}). Check setup; no object marked verified.\n",
        )


if __name__ == "__main__":
    main()
