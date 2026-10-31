import asyncio
import configparser
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


class StorageError(RuntimeError):
    def __init__(self, category="storage_unavailable", missing=False):
        super().__init__(category)
        self.category = category
        self.missing = missing


class UploadDigest(str):
    """Plaintext SHA-256 with an ephemeral rclone upload-checksum receipt."""

    def __new__(cls, value, verified_stat=None):
        result = super().__new__(cls, value)
        result.verified_stat = verified_stat
        return result


class RcloneCryptStorage:
    def __init__(
        self,
        config,
        remote="crypt:",
        binary="rclone",
        root="TelegramVault_TEST",
        upload_bandwidth=0,
    ):
        path = Path(config).expanduser()
        if not path.is_file() or path.stat().st_mode & 0o077:
            raise ValueError("rclone config must exist and have permissions 600")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path)
        name = remote.rstrip(":")
        if remote != name + ":" or name not in parser:
            raise ValueError("Use a named crypt remote without a path")
        section = parser[name]
        if (
            section.get("type") != "crypt"
            or section.get("filename_encryption", "standard") != "standard"
            or section.get("directory_name_encryption", "true") != "true"
        ):
            raise ValueError("Content, filename and directory encryption required")
        self.base = [binary, "--config", str(path), "--contimeout", "20s", "--timeout", "2m"]
        self.remote = remote
        if (
            len(PurePosixPath(root).parts) != 1
            or root in ("", ".", "..", "/")
            or "\\" in root
            or ":" in root
        ):
            raise ValueError("Storage root must be a single safe directory")
        self.root = root
        self.upload_bandwidth = upload_bandwidth

    def target(self, path):
        parts = PurePosixPath(path).parts
        if (
            not parts
            or parts[0] != self.root
            or any(p in ("..", ".") for p in path.split("/"))
            or "\\" in path
            or any(ord(c) < 32 for c in path)
        ):
            raise ValueError("Path must remain inside configured storage root")
        return self.remote + path

    async def command(self, *args, timeout=120):
        process = await self.spawn(
            *self.base, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            output, error = await asyncio.wait_for(process.communicate(), timeout)
            if process.returncode:
                category = self.error_category(error)
                raise StorageError(category, missing=process.returncode in (3, 4))
            return output
        finally:
            if process.returncode is None:
                await self.stop(process)

    @staticmethod
    async def error_tail(reader):
        tail = b""
        while chunk := await reader.read(1024):
            tail = (tail + chunk)[-8192:]
        return tail

    @staticmethod
    async def upload_error_tail(reader, path, receipt):
        tail, pending = b"", b""
        while chunk := await reader.read(1024):
            tail = (tail + chunk)[-8192:]
            pending = (pending + chunk)[-32768:]
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                try:
                    record = json.loads(line)
                    match = re.fullmatch(r"(md5|sha1|sha256) = ([0-9a-f]+) OK", record.get("msg", ""))
                    if (match and len(match[2]) == {"md5": 32, "sha1": 40, "sha256": 64}[match[1]]
                        and record.get("source", "").startswith("crypt/crypt.go:")
                        and record.get("object") == PurePosixPath(path).name):
                        receipt["matched"] = True
                except (ValueError, TypeError, AttributeError):
                    pass
        return tail

    @staticmethod
    def error_category(error, default="storage_unavailable"):
        # Keep raw stderr private: remote paths/tokens may occur in provider errors.
        message = error.lower()
        if any(x in message for x in (b"storagequotaexceeded", b"quota exceeded", b"storage quota")):
            return "google_storage_quota"
        if any(x in message for x in (b"invalid_grant", b"invalid credentials", b"unauthorized", b"401")):
            return "storage_auth_failed"
        if any(x in message for x in (b"429", b"ratelimitexceeded", b"rate limit", b"userratelimitexceeded")):
            return "google_rate_limit"
        if any(x in message for x in (b"permission", b"forbidden", b"403")):
            return "storage_access_denied"
        if any(x in message for x in (b"timeout", b"timed out", b"connection reset", b"connection refused", b"unexpected eof", b"no such host")):
            return "storage_network_error"
        return default

    @staticmethod
    async def spawn(*args, **kwargs):
        # Cancellation during process creation must not orphan a child before its handle is assigned.
        creation = asyncio.create_task(asyncio.create_subprocess_exec(*args, **kwargs))
        try:
            return await asyncio.shield(creation)
        except asyncio.CancelledError:
            process = await creation
            await RcloneCryptStorage.stop(process)
            raise

    @staticmethod
    async def stop(process):
        if process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                return
            try:
                await asyncio.wait_for(process.wait(), 5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

    async def exists(self, path):
        try:
            return await self.stat(path)
        except StorageError as error:
            if error.missing:
                return None
            raise

    async def move(self, source, destination):
        await self.command("moveto", self.target(source), self.target(destination), "--immutable")

    async def delete(self, path):
        # Caller may delete only a known job's unique incomplete path.
        if not path.startswith(self.root + "/.incomplete/"):
            raise ValueError("Automatic cleanup is restricted to incomplete objects")
        await self.command("deletefile", self.target(path))

    async def list(self, path):
        process = await self.spawn(
            *self.base,
            "lsf",
            self.target(path),
            "--recursive",
            "--files-only",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            while line := await process.stdout.readline():
                yield path.rstrip("/") + "/" + line.decode().rstrip("\r\n")
            await process.wait()
            if process.returncode not in (0, 3, 4):
                raise StorageError()
        finally:
            await self.stop(process)

    async def stat(self, path):
        return json.loads(await self.command("lsjson", self.target(path), "--stat"))

    async def put_stream(self, path, chunks, size, progress=None):
        process = await self.spawn(
            *self.base,
            "rcat",
            self.target(path),
            "--size",
            str(size),
            "--buffer-size",
            "1M",
            "--drive-chunk-size",
            "32M",
            "--transfers",
            "1",
            "--retries",
            "1",
            "--bwlimit",
            f"{self.upload_bandwidth}B" if self.upload_bandwidth else "off",
            "--log-level", "DEBUG", "--use-json-log", "--ignore-checksum=false",
            "--timeout", "0",  # Telegram can pause stdin for a full FloodWait.
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        receipt = {}
        errors = asyncio.create_task(self.upload_error_tail(process.stderr, path, receipt))
        digest, total = hashlib.sha256(), 0
        try:
            async for chunk in chunks:
                if len(chunk) > 524288:
                    raise ValueError("Chunk exceeds bounded reader contract")
                total += len(chunk)
                if total > size:
                    raise ValueError("Stream exceeds metadata size")
                digest.update(chunk)
                process.stdin.write(chunk)
                await asyncio.wait_for(process.stdin.drain(), 180)  # Bound blocked upload, not Telegram waits.
                if progress:
                    progress(total)
            if total != size:
                raise ValueError("Truncated Telegram stream")
            process.stdin.close()
            await asyncio.wait_for(process.wait(), 180)
            if process.returncode:
                raise StorageError(self.error_category(await errors, "upload_failed"))
            await errors
            stat = await self.stat(path)
            if stat["Size"] != size:
                raise ValueError("Remote logical size mismatch")
            return UploadDigest(digest.hexdigest(), stat if receipt.get("matched") else None)
        except asyncio.TimeoutError as error:
            raise StorageError("upload_stalled") from error
        except (BrokenPipeError, ConnectionResetError) as error:
            # rclone can close stdin before the producer finishes. Reap it and
            # classify its bounded stderr instead of hiding the actual failure.
            try:
                await asyncio.wait_for(process.wait(), 10)
            except asyncio.TimeoutError:
                await self.stop(process)
            raise StorageError(self.error_category(await errors, "upload_pipe_closed")) from error
        finally:
            await self.stop(process)
            await errors
            await chunks.aclose()

    async def hash_stream(self, path):
        process = await self.spawn(
            *self.base,
            "cat",
            self.target(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        errors = asyncio.create_task(self.error_tail(process.stderr))
        digest = hashlib.sha256()
        try:
            while chunk := await process.stdout.read(524288):
                digest.update(chunk)
            await process.wait()
            if process.returncode:
                raise StorageError(self.error_category(await errors, "decrypt_verification_failed"))
            return digest.hexdigest()
        finally:
            await self.stop(process)
            await errors
