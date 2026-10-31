"""Single-account web sign-in using the engine's existing Telethon client."""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path

from fastapi import HTTPException
from telethon import errors, types

from .providers import FloodPaused


def credentials_path(config):
    return config.data_dir / "telegram-api.json"


def read_credentials(data_dir):
    path = Path(data_dir) / "telegram-api.json"
    if not path.exists():
        return {}
    if path.stat().st_mode & 0o077:
        raise ValueError("Telegram API credentials require private file permissions")
    value = json.loads(path.read_text())
    return {"api_id": int(value["api_id"]), "api_hash": str(value["api_hash"])}


def save_credentials(config):
    path = credentials_path(config)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".telegram-api-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump({"api_id": config.api_id, "api_hash": config.api_hash}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class TelegramAuth:
    def __init__(self, engine):
        self.engine = engine
        self.phone = self.code_hash = self.owner = None
        self.step = None
        self.expires = 0
        self.attempts = 0
        self.busy = False

    def clear(self):
        self.phone = self.code_hash = self.owner = self.step = None
        self.expires = self.attempts = 0

    def status(self, owner):
        if self.expires and self.expires <= time.time() and not self.busy:
            self.clear()
        provider, config = self.engine.provider, self.engine.config
        return {
            "mode": provider.mode,
            "state": provider.status,
            "configured": bool(config.api_id and config.api_hash),
            "step": "connected"
            if provider.status == "connected"
            else self.step or ("phone" if config.api_id and config.api_hash else "credentials"),
            "phone": "••••" + self.phone[-4:] if self.phone and self.owner == owner else None,
            "expires_at": self.expires or None,
            "can_control": self.owner is None or self.owner == owner,
            "busy": self.busy,
            "retry_after": max(
                0,
                int(
                    max(
                        self.engine.db.setting("telegram_pause_until", 0),
                        self.engine.db.setting("telegram_auth_pause_until", 0),
                    )
                    - time.time()
                )
                + 1,
            ),
            "send_after": self.engine.db.setting("telegram_auth_send_after", 0),
        }

    async def perform(self, operation, owner, **values):
        self.status(owner)
        if self.engine.provider.mode != "real":
            raise HTTPException(409, "Đăng nhập Telegram chỉ dùng ở chế độ tài khoản thật.")
        if self.owner and self.owner != owner:
            raise HTTPException(409, "Một phiên quản trị khác đang đăng nhập Telegram.")
        if self.busy:
            raise HTTPException(409, "Đang xử lý yêu cầu Telegram. Vui lòng chờ.")
        if (
            max(
                self.engine.db.setting("telegram_auth_pause_until", 0),
                self.engine.db.setting("telegram_pause_until", 0),
            )
            > time.time()
        ):
            raise HTTPException(429, "Telegram đang giới hạn yêu cầu. Chờ rồi thử lại.")
        self.busy = True
        try:
            # Maintenance reconnect and discovery use this same engine lock.
            async with self.engine.operation_lock:
                async with asyncio.timeout(45):
                    await self._perform(operation, owner, **values)
            return {**self.status(owner), "busy": False}
        except FloodPaused as error:
            raise HTTPException(
                429,
                "Telegram yêu cầu chờ trước khi thử lại.",
                headers={"Retry-After": str(int(error.seconds) + 1)},
            ) from None
        except errors.SessionPasswordNeededError:
            self.step = "password"
            return {**self.status(owner), "busy": False}
        except (errors.PhoneCodeInvalidError, errors.PasswordHashInvalidError):
            raise HTTPException(
                422, "Mã OTP hoặc mật khẩu 2FA chưa đúng. Kiểm tra rồi thử lại."
            ) from None
        except errors.PhoneCodeExpiredError:
            self.clear()
            raise HTTPException(422, "Mã OTP đã hết hạn. Hãy gửi mã mới.") from None
        except (errors.PhoneNumberInvalidError, errors.PhoneNumberBannedError):
            raise HTTPException(422, "Số điện thoại không hợp lệ hoặc bị Telegram chặn.") from None
        except errors.ApiIdInvalidError:
            raise HTTPException(422, "API ID/API hash không hợp lệ.") from None
        except errors.RPCError:
            raise HTTPException(
                422, "Telegram từ chối yêu cầu. Kiểm tra thông tin và thử lại sau."
            ) from None
        except (TimeoutError, OSError):
            raise HTTPException(503, "Không kết nối được Telegram. Vui lòng thử lại.") from None
        finally:
            self.busy = False

    async def _perform(self, operation, owner, **values):
        engine, provider, config = self.engine, self.engine.provider, self.engine.config
        if operation == "credentials":
            if provider.status == "connected":
                raise HTTPException(409, "Hãy ngắt kết nối tài khoản trước khi đổi API.")
            await provider.close()
            provider.client = None
            self.clear()
            config.api_id, config.api_hash = values["api_id"], values["api_hash"]
            save_credentials(config)
            await provider.connect(engine.on_live)
            engine.db.event("telegram_api_configured")
            return
        if operation == "cancel":
            if provider.status == "connected":
                raise HTTPException(409, "Tài khoản đã kết nối. Dùng Ngắt kết nối để đăng xuất.")
            self.clear()
            await provider.close()
            provider.client = None
            provider.status = "login_required" if config.api_id else "not_configured"
            return
        if operation == "logout":
            if engine.active or engine.db.one(
                "SELECT id FROM sources WHERE deleted=0 AND enabled=1 AND paused=0 LIMIT 1"
            ):
                raise HTTPException(
                    409, "Tạm dừng tất cả nguồn và chờ transfer xong trước khi ngắt kết nối."
                )
            if provider.client:
                if not await engine.rate.call(provider.client.log_out):
                    raise HTTPException(503, "Telegram chưa xác nhận đăng xuất. Thử lại sau.")
                await provider.close()
            provider.client = None
            provider.status = "login_required"
            engine.last_discovery = []
            self.clear()
            engine.db.event("telegram_logged_out")
            return
        if provider.status == "connected":
            raise HTTPException(409, "Telegram đã kết nối.")
        if not config.api_id or not config.api_hash:
            raise HTTPException(409, "Lưu API ID/API hash trước khi gửi mã.")
        await provider.connect(engine.on_live)
        if provider.status == "account_mismatch":
            raise HTTPException(
                409,
                "Session thuộc tài khoản khác với nguồn đã lưu. Tạm dừng nguồn và ngắt kết nối trước khi tiếp tục.",
            )
        if provider.status == "connected":
            await self.finish()
            return
        if operation == "send":
            if time.time() < engine.db.setting("telegram_auth_send_after", 0):
                raise HTTPException(429, "Chờ ít nhất 60 giây giữa hai lần gửi mã.")
            # Persist before the call: reconnect/restart cannot bypass send throttling.
            engine.db.set_setting("telegram_auth_send_after", time.time() + 60)
            self.clear()
            self.owner, self.phone = owner, values["phone"]
            self.step, self.expires = "phone", time.time() + 600
            sent = await engine.rate.call(lambda: provider.client.send_code_request(self.phone))
            if isinstance(sent, types.auth.SentCodeSuccess):
                await self.finish()
                return
            self.code_hash = sent.phone_code_hash
            self.step, self.expires = "code", time.time() + 600
            return
        if operation not in ("code", "password") or self.step != operation:
            raise HTTPException(409, "Bước đăng nhập đã thay đổi. Gửi mã mới nếu phiên đã hết hạn.")
        if self.attempts >= 5:
            engine.db.set_setting("telegram_auth_pause_until", time.time() + 60)
            self.clear()
            raise HTTPException(429, "Đã thử quá nhiều lần. Chờ 60 giây rồi gửi mã mới.")
        self.attempts += 1
        provider.status = "authenticating"
        if operation == "code":
            await engine.rate.call(
                lambda: provider.client.sign_in(
                    phone=self.phone, code=values["code"], phone_code_hash=self.code_hash
                )
            )
        else:
            await engine.rate.call(lambda: provider.client.sign_in(password=values["password"]))
        await self.finish()

    async def finish(self):
        engine, provider = self.engine, self.engine.provider
        user = await engine.rate.call(provider.client.get_me)
        if not user:
            raise HTTPException(503, "Telegram chưa xác nhận tài khoản. Thử lại sau.")
        old = engine.db.setting("telegram_account_id")
        if (
            old
            and old != user.id
            and engine.db.one("SELECT id FROM sources WHERE deleted=0 LIMIT 1")
        ):
            await engine.rate.call(provider.client.log_out)
            await provider.close()
            provider.client = None
            provider.status = "login_required"
            self.clear()
            raise HTTPException(
                409,
                "Tài khoản khác với nguồn đã lưu. Xóa các nguồn cũ trước khi đổi tài khoản; backup được giữ lại.",
            )
        engine.db.set_setting("telegram_account_id", user.id)
        provider.status = "connected"
        engine.last_discovery = []
        engine.db.event("telegram_login_completed")
        self.clear()
