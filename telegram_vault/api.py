import asyncio
import hashlib
import hmac
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import psutil
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Config
from .engine import Engine
from .providers import FloodPaused
from .telegram_auth import TelegramAuth


AUTH_SESSION_EXPIRES = 253402300799  # No app-imposed expiry; explicit revocation still applies.
AUTH_COOKIE_MAX_AGE = 400 * 86400  # Browser-compatible persistent cookie, renewed on use.


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class SourceCreate(BaseModel):
    chat_id: int | None = None
    reference: str | None = Field(None, min_length=1, max_length=512)
    rights_confirmed: bool = False
    start: bool = False


class QueueControl(BaseModel):
    operation: str
    source_id: int | None = None
    topic_id: int | None = None
    job_id: int | None = None


class SourcePatch(BaseModel):
    enabled: bool | None = None
    min_size: int | None = Field(default=None, ge=0, le=2**53)
    max_size: int | None = Field(default=None, ge=0, le=2**53)
    date_after: float | None = Field(default=None, ge=0)
    date_before: float | None = Field(default=None, ge=0)
    extensions: str | None = Field(
        default=None, max_length=200, pattern=r"^[a-z0-9]+(,[a-z0-9]+)*$"
    )


class TopicSelection(BaseModel):
    all_topics: bool
    selected: list[int] = Field(default_factory=list, max_length=5000)


class TelegramCredentials(BaseModel):
    api_id: int = Field(gt=0, le=2147483647)
    api_hash: str = Field(pattern=r"^[a-fA-F0-9]{32}$")


class TelegramPhone(BaseModel):
    phone: str = Field(pattern=r"^\+[1-9][0-9]{6,14}$")


class TelegramCode(BaseModel):
    code: str = Field(pattern=r"^[0-9]{4,10}$")


class TelegramPassword(BaseModel):
    password: str = Field(min_length=1, max_length=512)


class SettingsPatch(BaseModel):
    concurrency: int | None = Field(default=None, ge=1, le=4)
    file_pause_enabled: bool | None = None
    file_pause_min_seconds: int | None = Field(default=None, ge=0, le=3600)
    file_pause_max_seconds: int | None = Field(default=None, ge=0, le=3600)
    download_bandwidth: int = Field(ge=0, le=2**40)
    upload_bandwidth: int = Field(ge=0, le=2**40)
    reconciliation_interval: int = Field(ge=30, le=86400)
    max_retries: int = Field(ge=1, le=20)
    verify_hash: bool = True


def create_app(config=None, engine=None):
    config = config or Config.from_env()
    engine = engine or Engine(config)
    db = engine.db
    telegram_auth = TelegramAuth(engine)
    ph = PasswordHasher()
    # No queued hash backlog. A slot is held until the thread really finishes,
    # including when the HTTP client cancels its request.
    hash_tasks = set()
    hash_limit = 2

    async def verify_password(password_hash, password):
        if len(hash_tasks) >= hash_limit:
            raise HTTPException(
                429, "Authentication busy. Try again shortly.", headers={"Retry-After": "1"}
            )
        task = asyncio.create_task(asyncio.to_thread(ph.verify, password_hash, password))
        hash_tasks.add(task)

        def finished(done):
            hash_tasks.discard(done)
            if not done.cancelled():
                done.exception()

        task.add_done_callback(finished)
        return await asyncio.shield(task)

    @asynccontextmanager
    async def lifespan(app):
        for key, value in db.setting("runtime_settings", {}).items():
            if hasattr(config, key):
                setattr(config, key, value)
        if engine.storage:
            engine.storage.upload_bandwidth = (
                max(1, config.upload_bandwidth // config.concurrency)
                if config.upload_bandwidth
                else 0
            )
        await engine.start()
        try:
            yield
        finally:
            await engine.stop()

    app = FastAPI(
        title="Vault Bridge",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.engine = engine

    @app.middleware("http")
    async def security_headers(request, call_next):
        try:
            length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        if length > 65536:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        if request.method in ("POST", "PUT", "PATCH"):
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 65536:
                    return JSONResponse({"detail": "Request too large"}, status_code=413)
                body.extend(chunk)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            }
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def origin_check(request):
        origin = request.headers.get("origin")
        if origin and origin != config.app_url:
            raise HTTPException(403, "Origin rejected")
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Cross-site request rejected")

    async def authenticated(request: Request, response: Response):
        token = request.cookies.get("vault_session", "")
        row = (
            db.one(
                "SELECT * FROM auth_sessions WHERE token_hash=? AND expires_at>?",
                (hashlib.sha256(token.encode()).hexdigest(), time.time()),
            )
            if token
            else None
        )
        if not row:
            raise HTTPException(401, "Sign in required")
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin_check(request)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), row["csrf"]):
                raise HTTPException(403, "CSRF token rejected")
        if row["expires_at"] != AUTH_SESSION_EXPIRES:
            db.execute("UPDATE auth_sessions SET expires_at=? WHERE token_hash=?",
                       (AUTH_SESSION_EXPIRES, row["token_hash"]))
        response.set_cookie("vault_session", token, max_age=AUTH_COOKIE_MAX_AGE,
                            httponly=True, secure=config.secure_cookie, samesite="strict", path="/")
        return row

    def source_or_404(source_id):
        source = db.one("SELECT * FROM sources WHERE id=? AND deleted=0", (source_id,))
        if not source:
            raise HTTPException(404, "Source not found")
        return source

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Pydantic's default details include submitted input (possibly secrets).
        return JSONResponse(
            {"detail": "Thông tin chưa hợp lệ. Kiểm tra định dạng và độ dài các trường."},
            status_code=422,
        )

    @app.exception_handler(ValueError)
    async def value_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=409)

    @app.exception_handler(FloodPaused)
    async def flood_error(request, error):
        return JSONResponse(
            {"detail": f"Telegram paused. Retry after {int(error.seconds) + 1} seconds."},
            status_code=429,
            headers={"Retry-After": str(int(error.seconds) + 1)},
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        db.event("api_operation_failed", type(error).__name__)
        return JSONResponse(
            {"detail": "Operation unavailable. Check connection and event history."},
            status_code=503,
        )

    @app.get("/api/health")
    async def health():
        # Public endpoint has no account or configuration details and makes no network requests.
        try:
            db.one("SELECT 1 AS ok")
        except Exception:
            return JSONResponse({"app": "degraded", "sqlite": "unavailable"}, status_code=503)
        if not engine.ready():
            return JSONResponse({"app": "degraded", "sqlite": "ok"}, status_code=503)
        return {"app": "ok", "sqlite": "ok"}

    @app.post("/api/auth/login")
    async def login(body: Login, request: Request, response: Response):
        origin_check(request)
        host = urlsplit(config.app_url).hostname
        if not config.secure_cookie and host not in ("localhost", "127.0.0.1", "::1"):
            raise HTTPException(503, "Enable secure cookies and HTTPS for remote access")
        password_hash = config.password_hash or db.setting("admin_password_hash", "")
        if not password_hash:
            raise HTTPException(503, "Run telegram-vault init-admin in a terminal first")
        client = hashlib.sha256(
            (request.client.host if request.client else "unknown").encode()
        ).hexdigest()
        attempt = db.one("SELECT * FROM login_attempts WHERE client=?", (client,))
        if attempt and attempt["reset_at"] > time.time() and attempt["count"] >= 5:
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
        db.execute(
            """INSERT INTO login_attempts VALUES(?,1,?) ON CONFLICT(client) DO UPDATE SET
            count=CASE WHEN reset_at<? THEN 1 ELSE count+1 END,
            reset_at=CASE WHEN reset_at<? THEN excluded.reset_at ELSE reset_at END""",
            (client, time.time() + 900, time.time(), time.time()),
        )
        valid = False
        try:
            # Offload Argon2 CPU/memory work; avoid blocking transfers and scans.
            valid = await verify_password(password_hash, body.password)
        except (VerificationError, InvalidHashError):
            pass
        if not valid or not hmac.compare_digest(body.username, config.username):
            raise HTTPException(401, "Invalid username or password")
        db.execute("DELETE FROM login_attempts WHERE client=?", (client,))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.execute(
            "INSERT INTO auth_sessions VALUES(?,?,?)",
            (hashlib.sha256(token.encode()).hexdigest(), csrf, AUTH_SESSION_EXPIRES),
        )
        response.set_cookie(
            "vault_session",
            token,
            max_age=AUTH_COOKIE_MAX_AGE,
            httponly=True,
            secure=config.secure_cookie,
            samesite="strict",
            path="/",
        )
        return {"username": config.username, "csrf": csrf}

    @app.get("/api/auth/me")
    async def me(session=Depends(authenticated)):
        return {"username": config.username, "csrf": session["csrf"]}

    @app.post("/api/auth/logout")
    async def logout(response: Response, session=Depends(authenticated)):
        db.execute("DELETE FROM auth_sessions WHERE token_hash=?", (session["token_hash"],))
        response.delete_cookie("vault_session", path="/")
        return {"ok": True}

    protected = [Depends(authenticated)]

    @app.get("/api/telegram/auth")
    async def telegram_status(session=Depends(authenticated)):
        return telegram_auth.status(session["token_hash"])

    @app.get("/api/telegram/rate-status", dependencies=protected)
    async def telegram_rate_status():
        return {"transport_mode": "bounded_inflight_v3" if engine.rate.transport_v3 else "paced_v2",
                "max_inflight_media": 2 if engine.rate.transport_v3 else None,
                "media_interval_seconds": db.setting("telegram_media_interval", 0.25),
                "lanes_per_file": db.setting("telegram_media_lanes", 8),
                "wait_remaining_seconds": max(0, int(db.setting("telegram_pause_until", 0) - time.time())),
                "last_flood": db.setting("telegram_last_flood_diagnostic"),
                "premium": db.setting("telegram_premium"),
                "premium_checked_at": db.setting("telegram_premium_checked_at"),
                "measurements_since_start": engine.rate.metrics}

    @app.post("/api/telegram/credentials")
    async def telegram_credentials(body: TelegramCredentials, session=Depends(authenticated)):
        return await telegram_auth.perform(
            "credentials", session["token_hash"], **body.model_dump()
        )

    @app.post("/api/telegram/send-code")
    async def telegram_send(body: TelegramPhone, session=Depends(authenticated)):
        return await telegram_auth.perform("send", session["token_hash"], **body.model_dump())

    @app.post("/api/telegram/verify-code")
    async def telegram_code(body: TelegramCode, session=Depends(authenticated)):
        return await telegram_auth.perform("code", session["token_hash"], **body.model_dump())

    @app.post("/api/telegram/verify-password")
    async def telegram_password(body: TelegramPassword, session=Depends(authenticated)):
        return await telegram_auth.perform("password", session["token_hash"], **body.model_dump())

    @app.post("/api/telegram/cancel")
    async def telegram_cancel(session=Depends(authenticated)):
        return await telegram_auth.perform("cancel", session["token_hash"])

    @app.post("/api/telegram/logout")
    async def telegram_logout(session=Depends(authenticated)):
        return await telegram_auth.perform("logout", session["token_hash"])

    @app.get("/api/status", dependencies=protected)
    async def status():
        counts = {
            row["status"]: {"count": row["count"], "bytes": row["bytes"]}
            for row in db.rows("SELECT * FROM stats")
        }
        return {
            "telegram": engine.provider.status,
            "telegram_mode": engine.provider.mode,
            "storage": engine.storage_health if engine.storage else {"state": engine.storage_error},
            "counts": counts,
            "sources": db.one("SELECT COUNT(*) AS n FROM sources WHERE deleted=0")["n"],
            "topics": db.one(
                "SELECT COUNT(*) AS n FROM topics t JOIN sources s ON s.id=t.source_id WHERE s.deleted=0"
            )["n"],
            "uptime": time.time() - engine.started,
            "telegram_pause_until": db.setting("telegram_pause_until", 0),
            "storage_pause_until": db.setting("storage_pause_until", 0),
            "transfer_pause_until": db.setting("transfer_pause_until", 0),
            "scheduler_paused": db.setting("scheduler_paused", False),
            "download_speed": sum(p["speed"] for p in engine.progress.values()),
            "upload_speed": None,
            "downloaded_bytes": db.setting("downloaded_total", 0),
            "uploaded_bytes": db.setting("uploaded_total", 0),
            "active": len(engine.active),
            "stream_retry": "from_beginning",
        }

    @app.get("/api/system/status", dependencies=protected)
    async def system_status():
        process = psutil.Process()
        rss = process.memory_info().rss
        for child in process.children(recursive=True):
            try:
                rss += child.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        disk = psutil.disk_usage(config.data_dir)
        return {
            "ram_bytes": rss,
            "disk_free_bytes": disk.free,
            "disk_total_bytes": disk.total,
            "uptime": time.time() - engine.started,
            "workers": config.concurrency,
        }

    @app.get("/api/discovery", dependencies=protected)
    async def discovery():
        return {"items": await engine.discover()}

    @app.get("/api/sources", dependencies=protected)
    async def sources(limit: int = Query(25, ge=1, le=100), cursor: int = Query(0, ge=0)):
        rows = db.rows(
            "SELECT * FROM sources WHERE deleted=0 AND id>? ORDER BY id LIMIT ?",
            (cursor, limit + 1),
        )
        next_cursor = rows[limit - 1]["id"] if len(rows) > limit else None
        for row in rows[:limit]:
            row["counts"] = {
                item["status"]: item["n"]
                for item in db.rows(
                    "SELECT j.status,COUNT(*) AS n FROM jobs j JOIN media m ON m.id=j.media_id WHERE m.source_id=? GROUP BY j.status",
                    (row["id"],),
                )
            }
            row["topic_count"] = db.one(
                "SELECT COUNT(*) AS n FROM topics WHERE source_id=?", (row["id"],)
            )["n"]
            row["selected_topic_count"] = db.one(
                "SELECT COUNT(*) AS n FROM topics WHERE source_id=? AND selected=1", (row["id"],)
            )["n"]
            counts = row["counts"]
            active = counts.get("TRANSFERRING", 0) + counts.get("VERIFYING", 0)
            queued = counts.get("QUEUED", 0) + counts.get("RETRY_WAIT", 0)
            if db.setting("scheduler_paused", False):
                stage, label, detail = (
                    "global_paused",
                    "Hệ thống đang tạm dừng",
                    "Nhấn Tiếp tục toàn hệ thống để mở lại lịch.",
                )
            elif row["paused"] or not row["enabled"]:
                stage = "ready" if not row["scanned"] and not counts else "paused"
                label = "Chưa bắt đầu" if stage == "ready" else "Đã tạm dừng"
                detail = (
                    "Nhấn Bắt đầu backup để quét và tự tải file phù hợp."
                    if stage == "ready"
                    else "Nhấn Tiếp tục để chạy lại; file chưa xong sẽ tải lại từ đầu."
                )
            elif engine.provider.status != "connected":
                stage, label, detail = (
                    "telegram",
                    "Chờ kết nối Telegram",
                    "Mở Kết nối Telegram để đăng nhập hoặc kiểm tra tài khoản.",
                )
            elif not row["all_topics"] and not row["selected_topic_count"]:
                stage, label, detail = (
                    "topics",
                    "Chưa chọn topic",
                    "Chọn ít nhất một topic hoặc bật Backup tất cả topics.",
                )
            elif row["scan_error"]:
                stage, label, detail = (
                    "scan_error",
                    "Quét gặp lỗi",
                    "Xem lỗi bên dưới; kiểm tra kết nối rồi yêu cầu quét lại.",
                )
            elif row["scan_target"] is not None:
                stage, label, detail = (
                    "scanning",
                    "Đang quét tin nhắn",
                    "File phù hợp được đưa vào hàng đợi và tải trong lúc quét.",
                )
            elif row["scan_requested"]:
                stage, label, detail = (
                    "scan_queued",
                    "Đã lên lịch quét",
                    "Scanner sẽ xử lý nguồn này ở lượt tiếp theo; không cần bấm Quét nhiều lần.",
                )
            elif active:
                stage, label, detail = (
                    "transferring",
                    "Đang truyền file",
                    "Xem tiến độ từng file ở Đang truyền.",
                )
            elif queued:
                stage, label, detail = (
                    "queued",
                    "Có file trong hàng đợi",
                    "Worker tự lấy file khi hết thời gian nghỉ hoặc giới hạn chờ.",
                )
            elif counts.get("FAILED", 0):
                stage, label, detail = (
                    "failed",
                    "Có file cần xử lý",
                    "Mở Cần xử lý để xem lỗi và thử lại.",
                )
            else:
                stage, label = "watching", "Đang theo dõi file mới"
                detail = (
                    "Đã quét xong lượt hiện tại; nội dung mới phù hợp sẽ tự được backup."
                    if counts
                    else "Đã quét xong nhưng chưa có file phù hợp. Kiểm tra loại file, kích thước, ngày và topics."
                )
            row["flow"] = {
                "stage": stage,
                "label": label,
                "detail": detail,
                "active": active,
                "queued": queued,
                "rest_until": max(
                    db.setting("transfer_pause_until", 0),
                    db.setting("telegram_pause_until", 0),
                    db.setting("storage_pause_until", 0),
                ),
            }
            row["active_files"] = db.rows(
                "SELECT j.id,j.downloaded,j.status,m.remote_path,m.size,m.original_filename FROM jobs j JOIN media m ON m.id=j.media_id WHERE m.source_id=? AND j.status IN ('TRANSFERRING','VERIFYING') LIMIT 2",
                (row["id"],),
            )
            for job in row["active_files"]:
                job["speed"] = engine.progress.get(job["id"], {}).get("speed", 0)
        return {"items": rows[:limit], "next_cursor": next_cursor}

    @app.post("/api/sources", dependencies=protected)
    async def add_source(body: SourceCreate):
        if not body.rights_confirmed:
            raise HTTPException(
                422, "Xác nhận bạn có quyền sao chép nội dung của nguồn này trước khi thêm."
            )
        if body.reference is None and body.chat_id is None:
            raise HTTPException(422, "Dán link hoặc chọn group trước khi thêm.")
        if body.start and db.setting("scheduler_paused", False):
            raise HTTPException(
                409,
                "Hệ thống đang tạm dừng tất cả. Tiếp tục toàn hệ thống trước khi bắt đầu nguồn mới.",
            )
        source_id = await engine.add_source(body.reference or body.chat_id)
        if body.start:
            db.execute(
                "UPDATE sources SET paused=0,enabled=1,scan_requested=1,scan_error=NULL WHERE id=?",
                (source_id,),
            )
        db.set_setting(f"source_rights_confirmed:{source_id}", time.time())
        db.event("source_rights_confirmed", source_id=source_id)
        return source_or_404(source_id)

    @app.get("/api/sources/{source_id}", dependencies=protected)
    async def get_source(source_id: int):
        return source_or_404(source_id)

    @app.patch("/api/sources/{source_id}", dependencies=protected)
    async def patch_source(source_id: int, body: SourcePatch):
        source = source_or_404(source_id)
        updates = body.model_dump(exclude_unset=True)
        if any(
            updates.get(key) is None
            for key in ("enabled", "min_size", "max_size", "extensions")
            if key in updates
        ):
            raise HTTPException(422, "These settings cannot be null")
        merged = {**source, **updates}
        if merged["max_size"] and merged["max_size"] < merged["min_size"]:
            raise HTTPException(422, "Maximum size must be at least minimum size")
        if (
            merged["date_after"]
            and merged["date_before"]
            and merged["date_after"] > merged["date_before"]
        ):
            raise HTTPException(422, "Date range is reversed")
        if updates:
            db.execute(
                f"UPDATE sources SET {','.join(f'{key}=?' for key in updates)} WHERE id=?",
                (*updates.values(), source_id),
            )
        return source_or_404(source_id)

    @app.delete("/api/sources/{source_id}", dependencies=protected)
    async def remove_source(source_id: int):
        source_or_404(source_id)
        return await engine.control_scope("delete", source_id=source_id)

    @app.post("/api/sources/{source_id}/pause", dependencies=protected)
    async def pause_source(source_id: int):
        source_or_404(source_id)
        return await engine.control_scope("pause", source_id=source_id)

    @app.post("/api/sources/{source_id}/resume", dependencies=protected)
    async def resume_source(source_id: int):
        source_or_404(source_id)
        db.execute(
            "UPDATE sources SET paused=0,enabled=1,scan_requested=1,scan_error=NULL WHERE id=?",
            (source_id,),
        )
        db.event("source_resumed", source_id=source_id)
        return {"ok": True}

    @app.post("/api/sources/{source_id}/scan", dependencies=protected)
    async def scan_source(source_id: int, full: bool = False):
        source = source_or_404(source_id)
        if source["paused"] or db.setting("scheduler_paused", False):
            raise HTTPException(
                409,
                "Nguồn hoặc hệ thống đang tạm dừng. Nhấn Bắt đầu backup/Tiếp tục trước khi quét.",
            )
        db.execute(
            "UPDATE sources SET scan_generation=scan_generation+1,scan_requested=1,scan_error=NULL,scan_target=NULL,scan_cursor=CASE WHEN ? THEN 0 ELSE scan_cursor END WHERE id=?",
            (full, source_id),
        )
        return {"ok": True}

    @app.get("/api/sources/{source_id}/topics", dependencies=protected)
    async def topics(
        source_id: int, limit: int = Query(100, ge=1, le=100), cursor: int = Query(-1, ge=-1)
    ):
        source_or_404(source_id)
        rows = db.rows(
            "SELECT t.*,(SELECT COUNT(*) FROM media m WHERE m.source_id=t.source_id AND m.topic_id=t.topic_id) AS videos FROM topics t WHERE source_id=? AND topic_id>? ORDER BY topic_id LIMIT ?",
            (source_id, cursor, limit + 1),
        )
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["topic_id"] if len(rows) > limit else None,
        }

    @app.put("/api/sources/{source_id}/topics", dependencies=protected)
    async def save_topics(source_id: int, body: TopicSelection):
        source_or_404(source_id)
        if any(
            not db.one(
                "SELECT topic_id FROM topics WHERE source_id=? AND topic_id=?", (source_id, topic)
            )
            for topic in body.selected
        ):
            raise HTTPException(422, "Unknown topic")
        with db.transaction():
            db.execute(
                "UPDATE sources SET all_topics=?,scan_generation=scan_generation+1,scan_requested=1,scan_cursor=0,scan_target=NULL WHERE id=?",
                (body.all_topics, source_id),
            )
            db.execute(
                "UPDATE topics SET selected=? WHERE source_id=?", (body.all_topics, source_id)
            )
            for topic in body.selected:
                db.execute(
                    "UPDATE topics SET selected=1 WHERE source_id=? AND topic_id=?",
                    (source_id, topic),
                )
        return {"ok": True, "backups_retained": True}

    @app.post("/api/sources/{source_id}/topics/refresh", dependencies=protected)
    async def refresh_topics(source_id: int):
        source_or_404(source_id)
        await engine.refresh_topics(source_id)
        return {"ok": True}

    @app.get("/api/jobs", dependencies=protected)
    async def jobs(
        status: str = "",
        q: str = "",
        source_id: int | None = None,
        limit: int = Query(25, ge=1, le=100),
        cursor: int = Query(0, ge=0),
    ):
        is_completed = (status == "COMPLETED")
        conditions = []
        parameters = []
        if not is_completed:
            conditions.append("(?=0 OR j.id<?)")
            parameters.extend([cursor, cursor])
        if status:
            values = status.split(",")
            from .models import STATUSES

            if not set(values) <= STATUSES:
                raise HTTPException(422, "Unknown status")
            conditions.append(f"j.status IN ({','.join('?' for _ in values)})")
            parameters.extend(values)
        if source_id is not None:
            conditions.append("m.source_id=?")
            parameters.append(source_id)
        if q.strip():
            conditions.append(
                "(instr(lower(m.original_filename),lower(?))>0 OR instr(lower(m.remote_path),lower(?))>0)"
            )
            parameters.extend([q.strip(), q.strip()])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        if is_completed:
            order_clause = "ORDER BY j.completed_at DESC, j.id DESC"
            limit_clause = "LIMIT ? OFFSET ?"
            query_params = (*parameters, limit + 1, cursor)
        else:
            order_clause = "ORDER BY j.id DESC"
            limit_clause = "LIMIT ?"
            query_params = (*parameters, limit + 1)

        rows = db.rows(
            f"""SELECT j.*,m.original_filename,m.size,m.source_id,m.message_id,m.topic_id,
            m.remote_path,m.plaintext_sha256,s.name AS source_name,t.name AS topic_name
            FROM jobs j JOIN media m ON m.id=j.media_id JOIN sources s ON s.id=m.source_id
            JOIN topics t ON t.source_id=s.id AND t.topic_id=m.topic_id
            {where_clause} {order_clause} {limit_clause}""",
            query_params,
        )
        for row in rows:
            row["download_speed"] = engine.progress.get(row["id"], {}).get("speed", 0)
            row["downstream_write_seconds"] = engine.progress.get(row["id"], {}).get("downstream_wait_seconds", 0)
            row["upload_progress_known"] = row["status"] in ("VERIFYING", "COMPLETED")
        if is_completed:
            next_cursor = (cursor + limit) if len(rows) > limit else None
        else:
            next_cursor = rows[limit - 1]["id"] if len(rows) > limit else None
        return {
            "items": rows[:limit],
            "next_cursor": next_cursor,
        }

    @app.get("/api/transfers", dependencies=protected)
    async def transfers():
        return await jobs(status="TRANSFERRING,VERIFYING", limit=100, cursor=0)

    @app.post("/api/queue/control", dependencies=protected)
    async def queue_control(body: QueueControl):
        return await engine.control_scope(**body.model_dump())

    @app.post("/api/jobs/{job_id}/{action}", dependencies=protected)
    async def job_action(job_id: int, action: str):
        if action not in ("retry", "cancel", "skip"):
            raise HTTPException(404, "Unknown action")
        engine.control_job(job_id, action)
        return {"ok": True}

    @app.post("/api/retry-failed", dependencies=protected)
    async def retry_failed():
        count = 0
        for row in db.rows("SELECT id FROM jobs WHERE status='FAILED' LIMIT 1000"):
            engine.control_job(row["id"], "retry")
            count += 1
        return {"retried": count, "note": "At most 1000 per request"}

    @app.get("/api/events", dependencies=protected)
    async def event_history(limit: int = Query(30, ge=1, le=100), cursor: int = Query(0, ge=0)):
        rows = db.rows(
            "SELECT * FROM events WHERE (?=0 OR id<?) ORDER BY id DESC LIMIT ?",
            (cursor, cursor, limit + 1),
        )
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @app.get("/api/storage/status", dependencies=protected)
    async def storage_status():
        return {
            "remote": config.remote,
            "root": config.storage_root,
            "state": engine.storage_health["state"] if engine.storage else engine.storage_error,
            "content_encrypted": bool(engine.storage),
            "filenames_encrypted": bool(engine.storage),
            "directories_encrypted": bool(engine.storage),
            "checked_at": engine.storage_health["checked_at"],
            "usage": None,
            "backend": "rclone crypt",
            "verification": "sha256" if config.verify_hash else "size",
        }

    @app.post("/api/storage/check", dependencies=protected)
    async def check_storage():
        return await engine.probe_storage()

    @app.post("/api/storage/reconcile", dependencies=protected)
    async def storage_reconcile():
        if db.setting("reconcile_running", False):
            raise HTTPException(409, "Reconciliation is already running")
        db.set_setting("reconcile_running", True)

        async def run():
            try:
                db.set_setting("last_reconcile_result", await engine.reconcile())
            except Exception as error:
                db.event("reconciliation_failed", type(error).__name__)
            finally:
                db.set_setting("reconcile_running", False)

        task = asyncio.create_task(run())
        engine.tasks.append(task)
        return {"ok": True}

    @app.get("/api/settings", dependencies=protected)
    async def settings():
        return {
            "download_bandwidth": config.download_bandwidth,
            "upload_bandwidth": config.upload_bandwidth,
            "reconciliation_interval": config.reconciliation_interval,
            "max_retries": config.max_retries,
            "verify_hash": config.verify_hash,
            "file_pause_enabled": config.file_pause_enabled,
            "file_pause_min_seconds": config.file_pause_min_seconds,
            "file_pause_max_seconds": config.file_pause_max_seconds,
            "transfer_pause_until": db.setting("transfer_pause_until", 0),
            "scheduler_paused": db.setting("scheduler_paused", False),
            "concurrency": config.concurrency,
            "telegram_request_pace": max(
                config.request_pace, db.setting("telegram_pace", config.request_pace)
            ),
            "telegram_mode": config.telegram_mode,
            "transfer_mode": "stream",
            "reconcile_running": db.setting("reconcile_running", False),
            "last_reconcile_result": db.setting("last_reconcile_result"),
            "secure_cookie": config.secure_cookie,
            "auth": "Argon2id + HttpOnly session + CSRF",
        }

    @app.patch("/api/settings", dependencies=protected)
    async def update_settings(body: SettingsPatch):
        values = body.model_dump(exclude_none=True)
        minimum = values.get("file_pause_min_seconds", config.file_pause_min_seconds)
        maximum = values.get("file_pause_max_seconds", config.file_pause_max_seconds)
        if minimum > maximum:
            raise HTTPException(422, "Thời gian nghỉ tối thiểu phải nhỏ hơn hoặc bằng tối đa.")
        with db.transaction():
            db.set_setting("runtime_settings", {**db.setting("runtime_settings", {}), **values})
            if values.get("file_pause_enabled") is False:
                db.set_setting("transfer_pause_until", 0)
        for key, value in values.items():
            setattr(config, key, value)
        if "concurrency" in values:
            engine.set_concurrency(config.concurrency)
        if engine.storage:
            engine.storage.upload_bandwidth = (
                max(1, config.upload_bandwidth // config.concurrency)
                if config.upload_bandwidth
                else 0
            )
        db.event("settings_updated")
        return await settings()

    @app.post("/api/demo/emit/{source_id}", dependencies=protected)
    async def demo_emit(source_id: int):
        if config.telegram_mode != "mock":
            raise HTTPException(404)
        await engine.provider.emit(source_or_404(source_id)["chat_id"])
        return {"ok": True}

    dist = Path(config.frontend_dir)
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    async def frontend(path: str):
        if path.startswith("api/") or path.startswith("assets/"):
            raise HTTPException(404)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html")
        return JSONResponse(
            {"detail": "Build frontend: cd frontend && npm ci && npm run build"}, status_code=503
        )

    return app
