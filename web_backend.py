import asyncio
import inspect
import importlib
import hashlib
import hmac
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    from aiogram.exceptions import TelegramRetryAfter
    from aiogram.types import Update
except ImportError:  # pragma: no cover - lightweight test fallback
    class TelegramRetryAfter(Exception):
        pass

    class Update:  # minimal placeholder for import-time test stubs
        pass
from dotenv import load_dotenv
try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:  # pragma: no cover - lightweight test fallback
    class _FallbackHTTPException(Exception):
        def __init__(self, status_code=500, detail=None, headers=None):
            super().__init__(detail or "")
            self.status_code = status_code
            self.detail = detail
            self.headers = headers or {}

    def Depends(*args, **kwargs):
        return None

    def Header(default=None, *args, **kwargs):
        return default

    class Request:  # minimal placeholder for import-time test stubs
        pass

    class FastAPI:  # pragma: no cover - lightweight test fallback
        def __init__(self, *args, **kwargs):
            self._routes = []

        def add_middleware(self, *args, **kwargs):
            return None

        def get(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("get", args, kwargs, func))
                return func
            return decorator

        def post(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("post", args, kwargs, func))
                return func
            return decorator

        def put(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("put", args, kwargs, func))
                return func
            return decorator

        def delete(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("delete", args, kwargs, func))
                return func
            return decorator

        def patch(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("patch", args, kwargs, func))
                return func
            return decorator

        def options(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("options", args, kwargs, func))
                return func
            return decorator

        def on_event(self, *args, **kwargs):
            def decorator(func):
                self._routes.append(("on_event", args, kwargs, func))
                return func
            return decorator

        def __getattr__(self, name):
            if name.lower() in {"get", "post", "put", "delete", "patch", "options", "head", "trace"}:
                def decorator_factory(*args, **kwargs):
                    def decorator(func):
                        self._routes.append((name.lower(), args, kwargs, func))
                        return func
                    return decorator
                return decorator_factory
            raise AttributeError(name)

    class CORSMiddleware:  # pragma: no cover - lightweight test fallback
        pass

    HTTPException = _FallbackHTTPException

from bot_links import normalize_bot_link_template
try:
    from bot_instance import bot, dp, set_commands
except ImportError:  # pragma: no cover - lightweight test fallback
    from bot_instance import bot

    dp = None

    def set_commands():
        return None
from database import db
try:
    from hidden_group_utils import (
        delete_hidden_code,
        delete_hidden_group,
        display_plan_name,
        list_hidden_codes,
        list_hidden_groups,
        list_hidden_redemptions,
        resolve_plan_groups,
        upsert_hidden_code,
        upsert_hidden_group,
    )
except ImportError:  # pragma: no cover - lightweight test fallback
    def display_plan_name(plan_name, user_id=None, language=None):
        return plan_name

    def resolve_plan_groups(plan_name):
        return []

    def delete_hidden_code(*args, **kwargs):
        return None

    def delete_hidden_group(*args, **kwargs):
        return None

    def list_hidden_codes(*args, **kwargs):
        return []

    def list_hidden_groups(*args, **kwargs):
        return []

    def list_hidden_redemptions(*args, **kwargs):
        return []

    def upsert_hidden_code(*args, **kwargs):
        return None

    def upsert_hidden_group(*args, **kwargs):
        return None
from helpers import bot_schedule_status, bot_runtime_state_audit, set_runtime_maintenance_override, runtime_maintenance_override
from helpers import create_background_task
try:
    from i18n import get_user_language, set_user_language
except ImportError:  # pragma: no cover - lightweight test fallback
    def get_user_language(user_id):
        return "vi"

    def set_user_language(user_id, language):
        return None
from supabase_store import supabase_store
try:
    from support_utils import (
        create_support_invite_link,
        explain_support_invite_error,
        get_or_create_support_ticket_for_user,
        mask_chat_id,
        normalize_support_message_direction,
        record_support_event,
        support_group_enabled,
        support_group_id,
        support_group_name,
        add_support_join_button,
        support_inbox_group_id,
        support_inbox_group_name,
    )
except ImportError:  # pragma: no cover - lightweight test fallback
    def create_support_invite_link(*args, **kwargs):
        return "", ""

    def explain_support_invite_error(*args, **kwargs):
        return ""

    async def get_or_create_support_ticket_for_user(*args, **kwargs):
        return None, False, ""

    def mask_chat_id(chat_id):
        return str(chat_id)

    def normalize_support_message_direction(value):
        return str(value or "").strip().lower() or "user_to_support"

    def record_support_event(*args, **kwargs):
        return None

    def support_group_enabled():
        return False

    def support_group_id():
        return ""

    def support_group_name():
        return ""
from vip_group_audit_utils import build_vip_group_audit_rows, build_vip_member_risk_rows
from stats_marketing_utils import build_marketing_stats_response
from config_aliases import canonical_config_key, canonicalize_config_rows, config_lookup_keys, config_write_items
from payment import payment_manager
try:
    from modules.mod_auto_payment_schedule import apply_auto_payment_schedule
except ImportError:  # pragma: no cover - lightweight test fallback
    def apply_auto_payment_schedule(*args, **kwargs):
        return None
from manual_order_helpers import should_skip_manual_active_code
from admin_notification_utils import admin_notification_from_support_event
from payment import PAYMENT_PROVIDER_SCHEMA, payment_manager
from duration_model import duration_days_from_key, is_lifetime_key, normalize_duration_key
from license_utils import (
    build_license_deeplink,
    license_flow_enabled,
    license_renewal_enabled,
    license_verify_required,
    load_license_plan_mapping,
    normalize_license_key,
    normalize_license_state,
    sign_license_request,
    verify_license_signature,
)

load_dotenv()

app = FastAPI(title="Hang Cú VIP Backend")
_booted = False
_missing_table_warnings: set[str] = set()
_last_webhook_reset_reason = ""
_webhook_failure_streak = 0
_webhook_reset_block_until = None
_webhook_reset_backoff_seconds = 0
_webhook_startup_retry_task = None
_marketing_stats_cache = {}
_marketing_stats_cache_ttl_seconds = max(30, int(os.getenv("MARKETING_STATS_CACHE_TTL_SECONDS", "60") or "60"))


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


def webhook_auto_heal_reasons():
    return {"missing_url", "url_mismatch", "invalid_url_scheme"}


def webhook_reset_cooldown_seconds():
    try:
        value = int(str(os.getenv("WEBHOOK_RESET_COOLDOWN_SECONDS", "120") or "120").strip())
        return max(30, value)
    except Exception:
        return 120


def webhook_reset_backoff_cap_seconds():
    try:
        value = int(str(os.getenv("WEBHOOK_RESET_BACKOFF_CAP_SECONDS", "1800") or "1800").strip())
        return max(120, value)
    except Exception:
        return 1800


def webhook_runtime_failure_limit():
    try:
        value = int(str(os.getenv("WEBHOOK_RUNTIME_FAILURE_LIMIT", "3") or "3").strip())
        return max(1, value)
    except Exception:
        return 3


def webhook_runtime_error_is_transient(exc) -> bool:
    text = str(exc or "").lower()
    transient_markers = (
        "timeout",
        "timed out",
        "request timeout",
        "temporarily unavailable",
        "connection reset",
        "connection aborted",
        "server disconnected",
        "network is unreachable",
        "name or service not known",
        "cannot connect",
    )
    return any(marker in text for marker in transient_markers)


def _parse_retry_after_seconds(error_text: str) -> int:
    text = str(error_text or "")
    match = re.search(r"retry in (\d+) seconds?", text, re.IGNORECASE)
    if not match:
        return 0
    try:
        return max(1, int(match.group(1)))
    except Exception:
        return 0


def webhook_reset_state_meta():
    return {
        "block_until": _webhook_reset_block_until.isoformat() if _webhook_reset_block_until else "",
        "backoff_seconds": int(_webhook_reset_backoff_seconds or 0),
        "wait_seconds": webhook_reset_wait_seconds(),
        "runtime_failure_limit": webhook_runtime_failure_limit(),
    }


def webhook_reset_wait_seconds() -> int:
    if not _webhook_reset_block_until:
        return 0
    return max(0, int((_webhook_reset_block_until - datetime.now()).total_seconds()))


def webhook_retry_wait_seconds() -> int:
    base = int(_webhook_reset_backoff_seconds or 0)
    if _webhook_reset_block_until:
        base = max(base, webhook_reset_wait_seconds())
    return max(5, base or webhook_reset_cooldown_seconds())


def _bot_delivery_secret():
    return str(
        os.getenv("BOT_LICENSE_CALLBACK_SECRET", "")
        or os.getenv("LICENSE_BOT_CALLBACK_SECRET", "")
        or os.getenv("WEB_PAYMENT_SECRET", "")
        or os.getenv("BOT_WEB_HMAC_SECRET", "")
        or ""
    ).strip()


def _verify_bot_delivery_signature(body: dict) -> bool:
    secret = _bot_delivery_secret()
    if not secret:
        return False
    message = "|".join(
        [
            str(body.get("orderId") or ""),
            str(body.get("telegramUserId") or ""),
            str(body.get("timestamp") or ""),
            str(body.get("nonce") or ""),
        ]
    )
    expected = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return expected == str(body.get("signature") or "").strip()


async def _handle_bot_payment_status(body: dict):
    bot_order_id = str(body.get("botOrderId") or "").strip()
    web_order_id = str(body.get("orderId") or "").strip()
    timestamp = body.get("timestamp")
    nonce = str(body.get("nonce") or "").strip()
    if not bot_order_id or not web_order_id or not timestamp or not nonce or not body.get("signature"):
        raise HTTPException(status_code=400, detail="Missing payment callback fields")
    if not _verify_bot_delivery_signature(body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    if not getattr(supabase_store, "enabled", False):
        raise HTTPException(status_code=503, detail="Bot order store unavailable")
    bot_order = supabase_store.get_order(bot_order_id) or {}
    if not bot_order:
        raise HTTPException(status_code=404, detail="Bot order not found")
    metadata = dict(bot_order.get("metadata") or {})
    # payment_status is only the provider result. Keep retrying until the
    # delivery processor records its durable completion marker.
    if metadata.get("bot_delivery_notified_at"):
        return {"success": True, "duplicate": True, "botOrderId": bot_order_id}
    metadata.update({
        "web_delivery_claimed_at": _now_iso(),
        "web_order_id": web_order_id,
        "web_order_number": str(body.get("orderNumber") or ""),
        "payment_provider": str(body.get("paymentProvider") or ""),
        "payment_status": "PAID",
        "payment_session_id": str(body.get("paymentSessionId") or bot_order_id),
    })
    supabase_store.patch_order(bot_order_id, {"metadata": metadata})
    supabase_store.mark_order_paid(bot_order_id, _now_iso(), None)
    print(f"[payment-status] bot_order_paid botOrderId={bot_order_id} webOrderId={web_order_id} provider={body.get('paymentProvider') or 'n/a'}")

    # Acknowledge payment before the slower license/group-link worker starts.
    # The marker prevents duplicate webhook deliveries from sending this twice.
    telegram_user_id = str(
        body.get("telegramUserId")
        or bot_order.get("telegram_user_id")
        or metadata.get("telegramUserId")
        or ""
    ).strip()
    if telegram_user_id and not metadata.get("payment_status_notified_at"):
        try:
            language = get_user_language(telegram_user_id)
            if language == "en":
                payment_message = (
                    "✅ <b>Payment confirmed!</b>\n\n"
                    "Your license is being prepared. Please wait a moment; "
                    "the bot will send your license and VIP access link next."
                )
            else:
                payment_message = (
                    "✅ <b>Thanh toán thành công!</b>\n\n"
                    "Hệ thống đang cấp license. Vui lòng chờ một chút, "
                    "bot sẽ gửi mã license và link vào nhóm VIP ngay sau đó."
                )
            await bot.send_message(
                chat_id=int(telegram_user_id),
                text=payment_message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            metadata["payment_status_notified_at"] = _now_iso()
            supabase_store.patch_order(bot_order_id, {"metadata": metadata})
            print(f"[payment-status] acknowledgement_sent botOrderId={bot_order_id} telegramUserId={telegram_user_id}")
        except Exception as exc:
            # Do not turn a confirmed payment into a failed webhook because a
            # Telegram acknowledgement temporarily failed. Delivery remains queued.
            print(f"[payment-status] acknowledgement_failed botOrderId={bot_order_id} telegramUserId={telegram_user_id or 'none'} error={exc}")

    from processor import process_successful_payment
    create_background_task(
        process_successful_payment(bot_order_id),
        name=f"payment_delivery_{bot_order_id}",
        context="web_payment_callback",
    )
    print(f"[payment-status] delivery_queued botOrderId={bot_order_id} webOrderId={web_order_id}")
    return {"success": True, "botOrderId": bot_order_id, "status": "PAID", "delivery": "queued"}


@app.post("/payment-status")
@app.post("/api/payment-status")
async def payment_status(request: Request):
    if not license_flow_enabled():
        raise HTTPException(status_code=503, detail="license flow disabled")
    return await _handle_bot_payment_status(await request.json())


def _backend_timezone():
    timezone_name = os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _marketing_range_window(period: str, now: datetime | None = None):
    current_now = now or datetime.now(_backend_timezone())
    if period == "today":
        current_start = current_now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start - timedelta(days=1)
    elif period == "7d":
        current_start = current_now - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)
    elif period == "year":
        current_start = current_now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start.replace(year=current_start.year - 1)
    else:
        current_start = current_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_start = (current_start.replace(day=1) - timedelta(days=1)).replace(day=1)
    return previous_start, current_now


def _backend_text(value):
    return str(value or "").strip()


def _backend_payload_text(payload, *keys):
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        text = _backend_text(payload.get(key))
        if text:
            return text
    return ""


def _backend_day_key(value):
    raw = _backend_text(value)
    if not raw:
        return "UNKNOWN"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            local = parsed.astimezone(_backend_timezone())
        else:
            local = parsed.replace(tzinfo=_backend_timezone())
        return local.strftime("%Y-%m-%d")
    except Exception:
        return "UNKNOWN"


def _backend_parse_datetime(value):
    raw = _backend_text(value)
    if not raw:
        return datetime.min.replace(tzinfo=_backend_timezone())
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed
        return parsed.replace(tzinfo=_backend_timezone())
    except Exception:
        return datetime.min.replace(tzinfo=_backend_timezone())


def _backend_humanize_event_type(value):
    text = _backend_text(value).replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else "event"


def _looks_like_public_image_url(value: str) -> bool:
    text = _backend_text(value)
    return bool(re.match(r"^https?://", text, re.IGNORECASE))


async def _validate_img_me_value(value: str) -> tuple[bool, str]:
    text = _backend_text(value)
    if not text:
        return True, ""
    if _looks_like_public_image_url(text):
        try:
            def _probe():
                req = urllib.request.Request(text)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    content_type = str(resp.headers.get("Content-Type", "")).lower()
                    if content_type and not content_type.startswith("image/"):
                        return False, "URL không phải ảnh"
                    return True, ""

            return await asyncio.to_thread(_probe)
        except Exception as exc:
            return False, f"URL ảnh không hợp lệ: {exc}"
    try:
        await bot.get_file(text)
        return True, ""
    except Exception as exc:
        error_text = str(exc).lower()
        if "wrong file identifier" in error_text or "http url specified" in error_text or "can't parse file" in error_text:
            return False, str(exc)
        return False, str(exc)


async def retry_telegram_webhook_background(*, initial_delay=0):
    if initial_delay:
        await asyncio.sleep(max(0, int(initial_delay)))

    while True:
        try:
            result = await ensure_telegram_webhook(force=True)
            if result.get("ok"):
                print(
                    f"✅ Telegram webhook retry succeeded ({result.get('reason', 'forced')})"
                )
                return

            reason = str(result.get("reason") or "").strip()
            wait_seconds = webhook_retry_wait_seconds()
            if result.get("maintenance_required"):
                set_runtime_maintenance_override(
                    True,
                    reason=f"Webhook retry pending ({reason}). Retry after {wait_seconds}s.",
                    source="webhook",
                )
            print(f"🕒 Telegram webhook retry pending reason={reason} retry_in={wait_seconds}s")
            await asyncio.sleep(wait_seconds)
        except TelegramRetryAfter as exc:
            wait_seconds = max(1, int(getattr(exc, "retry_after", 1) or 1))
            _backoff = max(wait_seconds, webhook_retry_wait_seconds())
            set_runtime_maintenance_override(
                True,
                reason=f"Telegram SetWebhook rate limited. Retry after {_backoff}s.",
                source="webhook",
            )
            print(f"⚠️ Telegram webhook rate limited in background; retrying in {_backoff}s.")
            await asyncio.sleep(_backoff)
        except Exception as exc:
            wait_seconds = webhook_retry_wait_seconds()
            if not webhook_runtime_error_is_transient(exc) or _webhook_failure_streak >= webhook_runtime_failure_limit():
                set_runtime_maintenance_override(
                    True,
                    reason=f"Webhook retry error: {exc}",
                    source="webhook",
                )
            print(f"⚠️ Telegram webhook retry error: {exc}. Retry in {wait_seconds}s.")
            await asyncio.sleep(wait_seconds)


def _allowed_origins():
    raw = os.getenv("ADMIN_ALLOWED_ORIGINS", "")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(x_admin_secret: str | None = Header(default=None)):
    expected = os.getenv("ADMIN_SECRET")
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured")
    if x_admin_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    return True


def is_missing_supabase_table_error(exc: Exception, table_name: str) -> bool:
    text = str(exc)
    return table_name in text and ("PGRST205" in text or "Could not find the table" in text)


def is_missing_supabase_runtime_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "missing supabase_url" in text or "missing supabase_service_role_key" in text


def warn_missing_table_once(table_name: str, exc: Exception):
    if table_name in _missing_table_warnings:
        return
    _missing_table_warnings.add(table_name)
    print(f"⚠️ Supabase thiếu bảng {table_name}. Hãy chạy migration SQL trong thư mục supabase. Chi tiết: {exc}")


def telegram_startup_skipped():
    return str(os.getenv("SKIP_TELEGRAM_STARTUP", "")).strip().lower() in {"1", "true", "yes", "on"}


def webhook_watch_interval_seconds():
    try:
        value = int(str(os.getenv("WEBHOOK_WATCH_INTERVAL_SECONDS", "300") or "300").strip())
        return max(60, value)
    except Exception:
        return 300


def webhook_problem_reason(info, expected_url: str):
    if not info:
        return "unavailable"
    actual_url = str(getattr(info, "url", "") or "").strip()
    if not actual_url:
        return "missing_url"
    if expected_url and actual_url != expected_url:
        return "url_mismatch"
    if actual_url and not actual_url.startswith("https://"):
        return "invalid_url_scheme"
    last_error_message = str(getattr(info, "last_error_message", "") or "").strip()
    pending_update_count = int(getattr(info, "pending_update_count", 0) or 0)
    if last_error_message and pending_update_count > 0:
        return "telegram_error"
    return ""


def empty_webhook_info(error_message=""):
    return {
        "url": "",
        "has_custom_certificate": False,
        "pending_update_count": 0,
        "last_error_message": str(error_message or ""),
        "max_connections": 0,
        "allowed_updates": [],
    }


async def ensure_telegram_webhook(*, force=False):
    global _last_webhook_reset_reason, _webhook_failure_streak, _webhook_reset_block_until, _webhook_reset_backoff_seconds
    webhook_url = str(os.getenv("WEBHOOK_URL") or "").strip()
    webhook_secret = str(os.getenv("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    if not webhook_url or telegram_startup_skipped():
        set_runtime_maintenance_override(False, source="webhook")
        return {"ok": False, "reason": "disabled", "info": None}

    try:
        now = datetime.now()
        info = await bot.get_webhook_info()
        reason = webhook_problem_reason(info, webhook_url)
        if not force and not reason:
            _webhook_failure_streak = 0
            _webhook_reset_backoff_seconds = 0
            _webhook_reset_block_until = None
            set_runtime_maintenance_override(False, source="webhook")
            return {"ok": True, "reason": "healthy", "info": info}

        if reason and reason not in webhook_auto_heal_reasons():
            _webhook_failure_streak += 1
            maintenance_required = _webhook_failure_streak >= webhook_runtime_failure_limit()
            if maintenance_required:
                set_runtime_maintenance_override(
                    True,
                    reason=f"Webhook unhealthy ({reason}). Auto-reset skipped to avoid SetWebhook spam.",
                    source="webhook",
                )
            else:
                set_runtime_maintenance_override(False, source="webhook")
            return {"ok": False, "reason": reason, "info": info, "maintenance_required": maintenance_required}

        if _webhook_reset_block_until and now < _webhook_reset_block_until:
            wait_seconds = max(1, int((_webhook_reset_block_until - now).total_seconds()))
            maintenance_required = _webhook_failure_streak >= webhook_runtime_failure_limit()
            if maintenance_required:
                set_runtime_maintenance_override(
                    True,
                    reason=f"Webhook reset cooldown active. Retry after {wait_seconds}s.",
                    source="webhook",
                )
            return {"ok": False, "reason": f"cooldown:{wait_seconds}", "info": info, "maintenance_required": maintenance_required}

        await bot.delete_webhook(drop_pending_updates=False)
        await bot.set_webhook(
            webhook_url,
            secret_token=webhook_secret or None,
            drop_pending_updates=False,
            allowed_updates=dp.resolve_used_update_types(),
        )
        refreshed = await bot.get_webhook_info()
        refreshed_reason = webhook_problem_reason(refreshed, webhook_url)
        if refreshed_reason:
            _webhook_failure_streak += 1
            set_runtime_maintenance_override(
                True,
                reason=f"Webhook auto-heal failed ({refreshed_reason}). Bot moved to maintenance to protect pricing/menu flows.",
                source="webhook",
            )
            return {"ok": False, "reason": refreshed_reason, "info": refreshed}
        reset_reason = reason or "forced"
        _last_webhook_reset_reason = reset_reason
        _webhook_failure_streak = 0
        _webhook_reset_backoff_seconds = 0
        _webhook_reset_block_until = now + timedelta(seconds=webhook_reset_cooldown_seconds())
        set_runtime_maintenance_override(False, source="webhook")
        print(f"🔁 Telegram webhook reset reason={reset_reason} url={webhook_url}")
        return {"ok": True, "reason": reset_reason, "info": refreshed}
    except Exception as exc:
        _webhook_failure_streak += 1
        retry_after = _parse_retry_after_seconds(str(exc))
        base_backoff = retry_after or webhook_reset_cooldown_seconds()
        _webhook_reset_backoff_seconds = min(
            webhook_reset_backoff_cap_seconds(),
            max(base_backoff, (_webhook_reset_backoff_seconds * 2) if _webhook_reset_backoff_seconds else base_backoff),
        )
        _webhook_reset_block_until = datetime.now() + timedelta(seconds=_webhook_reset_backoff_seconds)
        is_transient = webhook_runtime_error_is_transient(exc)
        maintenance_required = (not is_transient) or _webhook_failure_streak >= webhook_runtime_failure_limit()
        if maintenance_required:
            set_runtime_maintenance_override(True, reason=f"Webhook runtime error: {exc}", source="webhook")
        else:
            set_runtime_maintenance_override(False, source="webhook")
            print(
                "⚠️ Telegram webhook transient error; keep bot online "
                f"streak={_webhook_failure_streak}/{webhook_runtime_failure_limit()} "
                f"retry_in={_webhook_reset_backoff_seconds}s error={exc}"
            )
        return {
            "ok": False,
            "reason": "transient_runtime_error" if is_transient else "runtime_error",
            "info": None,
            "error": str(exc),
            "maintenance_required": maintenance_required,
        }


async def webhook_watch_worker():
    print("🪝 Webhook watch worker đã khởi động.")
    while True:
        try:
            result = await ensure_telegram_webhook(force=False)
            if result.get("reason") not in {"healthy", "disabled", ""}:
                info = result.get("info")
                print(
                    f"🪝 Webhook auto-heal reason={result.get('reason')} "
                    f"pending={getattr(info, 'pending_update_count', 0) if info else 0} "
                    f"last_error={getattr(info, 'last_error_message', '') if info else ''}"
                )
        except Exception as exc:
            print(f"⚠️ Webhook watch worker lỗi: {exc}")
        await asyncio.sleep(webhook_watch_interval_seconds())


def backend_timezone():
    try:
        timezone_name = str(db.get_config("BOT_TIMEZONE", os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh")) or "").strip()
    except Exception as exc:
        if is_missing_supabase_runtime_error(exc):
            timezone_name = ""
        else:
            raise
    if not timezone_name:
        timezone_name = str(os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def now_local():
    return datetime.now(backend_timezone())


def parse_manual_expire_at(value: str | None):
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace(",", " ").strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = None
        for fmt in (
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%H:%M %d/%m/%Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(normalized, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            raise
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=backend_timezone())
    return parsed.astimezone(backend_timezone())


def format_manual_expire_at(value: str | None):
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = parse_manual_expire_at(raw)
    except Exception:
        return raw
    if not parsed:
        return raw
    return parsed.strftime("%H:%M %d/%m/%Y")


def order_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=backend_timezone())
        return parsed.astimezone(backend_timezone())
    except Exception:
        try:
            return parse_manual_expire_at(raw)
        except Exception:
            return None


def order_is_lifetime(plan_name: str | None):
    text = str(plan_name or "").lower()
    return any(token in text for token in ("trọn đời", "tron doi", "lifetime", "life", "vĩnh viễn", "vinh vien"))


def resolve_manual_order_plan(body: dict[str, object]) -> tuple[str, dict[str, str]]:
    """Resolve manual-order entitlement and keep custom duration separate from plan identity."""
    mode = str(body.get("plan_mode") or "").strip().upper()
    if mode != "CUSTOM_DURATION":
        plan_name = str(body.get("plan_name") or "").strip()
        return plan_name, {}
    if str(safe_db_config("MANUAL_CUSTOM_DURATION_ENABLED", "ON") or "ON").strip().upper() not in {"ON", "1", "TRUE", "YES"}:
        raise HTTPException(status_code=409, detail="Gói tùy chỉnh đang tạm tắt để bảo trì.")

    entitlement_type = str(body.get("entitlement_type") or "").strip().upper()
    entitlement_key = str(body.get("entitlement_key") or "").strip()
    if entitlement_type == "ALL_ACCESS":
        base_name = str(safe_db_config("PLAN_ALL_ACCESS_30D", safe_db_config("PLAN_COMBO_30D", "All Access 30 Ngày")) or "All Access 30 Ngày").strip()
        base_name = re.sub(r"\s+30\s*(?:ngày|days|d)\b", "", base_name, flags=re.IGNORECASE).strip() or "All Access"
        return f"{base_name} - Tùy chỉnh", {
            "manual_plan_mode": mode,
            "entitlement_type": entitlement_type,
            "entitlement_key": "FULL",
        }
    if entitlement_type == "GROUP_COLLECTION" and entitlement_key:
        group_name = str(safe_db_config(f"BTN_G{entitlement_key}", "") or "").strip()
        if not group_name and entitlement_key.upper().startswith("G"):
            group_name = str(safe_db_config(f"BTN_G{entitlement_key[1:]}", "") or "").strip()
        if group_name:
            return f"{group_name} - Tùy chỉnh", {
                "manual_plan_mode": mode,
                "entitlement_type": entitlement_type,
                "entitlement_key": entitlement_key,
            }
    raise HTTPException(status_code=400, detail="Gói tùy chỉnh cần chọn All Access hoặc Group/Collection hợp lệ.")


def resolve_manual_order_duration_days(plan_name: str | None, duration_days: int, *, telegram_user_id: str = "", full_name: str = ""):
    raw_duration_days = duration_days
    if not order_is_lifetime(plan_name) and duration_days > 365:
        print(
            "⚠️ Manual order duration clamped to 30 days because non-lifetime plan exceeded safety limit: "
            f"user_id={telegram_user_id or '-'} | full_name={full_name or '-'} | plan_name={plan_name or '-'} | "
            f"raw_duration_days={raw_duration_days}"
        )
        return 30
    return duration_days


def order_is_active(order):
    if str(order.get("status") or "").upper() != "PAID":
        return False
    if order_is_lifetime(order.get("plan_name")):
        return True
    expire_at = order_datetime(order.get("expire_at"))
    return bool(expire_at and expire_at >= now_local())


def days_until_order_expire(order):
    expire_at = order_datetime(order.get("expire_at"))
    if not expire_at:
        return 999999
    delta = expire_at - now_local()
    return int(delta.total_seconds() // 86400)


def build_customer_search_summary(query: str, limit: int = 30):
    rows = supabase_store.search_customer_orders(query, limit=limit)
    grouped: dict[str, dict[str, object]] = {}
    for order in rows:
        telegram_id = str(order.get("telegram_user_id") or "").strip()
        if not telegram_id:
            continue
        item = grouped.setdefault(telegram_id, {"id": telegram_id, "name": order.get("full_name") or telegram_id, "orders": []})
        if order.get("full_name"):
            item["name"] = order.get("full_name")
        item["orders"].append(order)

    try:
        reminder_days = int(float(str(db.get_config("REMINDER_DAYS", "3") or 3)))
    except (TypeError, ValueError):
        reminder_days = 3
    results = []
    for item in grouped.values():
        orders = sorted(item["orders"], key=lambda order: str(order.get("created_at") or ""), reverse=True)
        paid_orders = [order for order in orders if str(order.get("status") or "").upper() == "PAID"]
        active_orders = [order for order in paid_orders if order_is_active(order)]
        latest_expire = sorted([str(order.get("expire_at") or "") for order in paid_orders if order.get("expire_at")], reverse=True)
        expiring_within_window = any(
            str(order.get("status") or "").upper() == "PAID"
            and not order_is_lifetime(order.get("plan_name"))
            and 0 <= days_until_order_expire(order) <= reminder_days
            for order in orders
        )
        has_paid = bool(paid_orders)
        status = "active" if active_orders else "expiring" if expiring_within_window else "expired" if has_paid else "no_paid"
        blacklist_entry = None
        try:
            entry = supabase_store.get_blacklist_entry(str(item["id"]))
            if entry and entry.get("is_active"):
                blacklist_entry = entry
        except Exception as exc:
            if not is_missing_supabase_table_error(exc, "security_blacklist"):
                print(f"⚠️ Không đọc được blacklist khi lookup khách {item['id']}: {exc}")
        results.append({
            "id": item["id"],
            "name": item["name"],
            "orders": orders,
            "paidOrders": paid_orders,
            "activeOrders": active_orders,
            "latestExpire": latest_expire[0] if latest_expire else "",
            "blacklistEntry": blacklist_entry,
            "isBlacklisted": bool(blacklist_entry),
            "hasPaidOrder": has_paid,
            "hasActiveOrder": bool(active_orders),
            "activeOrderCount": len(active_orders),
            "paidOrderCount": len(paid_orders),
            "latestExpireText": format_manual_expire_at(latest_expire[0]) if latest_expire else "-",
            "latestExpireOrder": active_orders[0] if active_orders else paid_orders[0] if paid_orders else None,
            "status": status,
            "statusText": "Đang còn hạn" if status == "active" else "Sắp hết hạn" if status == "expiring" else "Hết hạn / chờ kick" if status == "expired" else "Chưa PAID",
        })
    results.sort(key=lambda item: str((item.get("orders") or [{}])[0].get("created_at") or ""), reverse=True)
    return results


def normalize_template_text(value: str | None):
    return str(value or "").replace("\\n", "\n").strip()


def safe_db_config(key: str, default: str = ""):
    try:
        return db.get_config(key, default) or default
    except Exception as exc:
        message = str(exc)
        if "Missing SUPABASE_URL" in message or "Missing SUPABASE_SERVICE_ROLE_KEY" in message:
            return default
        raise


def safe_support_group_name(default: str = "Nhóm hỗ trợ"):
    try:
        return support_group_name()
    except Exception:
        return default


def render_manual_order_support_text(template: str, context: dict[str, object]):
    text = normalize_template_text(template)
    if not text:
        text = "💬 {support_group_name}:\n{support_link}"
    values = {
        "order_id": context.get("order_id", ""),
        "telegram_user_id": context.get("telegram_user_id", ""),
        "full_name": context.get("full_name", ""),
        "plan_name": context.get("plan_name", ""),
        "expire_at": format_manual_expire_at(context.get("expire_at", "")),
        "links_text": context.get("links_text", ""),
        "support_group_name": context.get("support_group_name", ""),
        "support_link": context.get("support_link", ""),
        "support_error": context.get("support_error", ""),
    }
    for key, value in values.items():
        text = text.replace(f"{{{key}}}", str(value or ""))
    return text.strip()


def render_manual_order_info_text(context: dict[str, object]):
    template = normalize_template_text(safe_db_config(
        "MANUAL_ORDER_INFO_TEMPLATE",
        "🧾 Đơn hàng: {order_id}\n👤 Khách hàng: {full_name} - ID: {telegram_user_id}\n📦 Gói: {plan_name}\n⏳ Hạn dùng: {expire_at}",
    ) or "")
    values = {
        "order_id": context.get("order_id", ""),
        "telegram_user_id": context.get("telegram_user_id", ""),
        "full_name": context.get("full_name", ""),
        "plan_name": context.get("plan_name", ""),
        "expire_at": format_manual_expire_at(context.get("expire_at", "")),
    }
    for key, value in values.items():
        template = template.replace(f"{{{key}}}", str(value or ""))
    return template.strip()


def render_manual_order_message_text(template: str, context: dict[str, object]):
    text = normalize_template_text(template)
    if not text:
        text = "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}\n\n{support_text}"
    values = {
        "order_id": context.get("order_id", ""),
        "telegram_user_id": context.get("telegram_user_id", ""),
        "full_name": context.get("full_name", ""),
        "plan_name": context.get("plan_name", ""),
        "expire_at": format_manual_expire_at(context.get("expire_at", "")),
        "order_text": context.get("order_text", ""),
        "success_text": context.get("success_text", ""),
        "bot_link_title": context.get("bot_link_title", ""),
        "bot_link_subtitle": context.get("bot_link_subtitle", ""),
        "activation_url": context.get("activation_url", ""),
        "links_text": context.get("links_text", ""),
        "support_text": context.get("support_text", ""),
        "support_group_name": context.get("support_group_name", ""),
        "support_link": context.get("support_link", ""),
        "support_error": context.get("support_error", ""),
    }
    for key, value in values.items():
        text = text.replace(f"{{{key}}}", str(value or ""))
    return text.strip()


def render_activation_text(template_key: str, default_text: str, context: dict[str, object]):
    template = normalize_template_text(safe_db_config(template_key, default_text) or default_text)
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value or ""))
    return template.strip()


def strip_html_text(value: str):
    text = str(value or "")
    return re.sub(r"<br\s*/?>", "\n", re.sub(r"</p>", "\n", re.sub(r"<[^>]+>", "", text, flags=re.IGNORECASE), flags=re.IGNORECASE), flags=re.IGNORECASE).strip()


def normalize_manual_order_link_template(value: str):
    return normalize_bot_link_template(value, default_payload="act_{code}")


def normalize_manual_order_join_template(value: str):
    template = str(value or "").strip()
    default_template = "{order_text}\n\n{bot_link_title}\n{links_text}\n\n{bot_link_subtitle}\n\n{support_text}"
    if not template:
        return default_template
    if any(signal in template for signal in ("{success_text}", "actmsg_", "Đơn của bạn đã được xác minh")):
        return default_template
    return template


def build_manual_activation_url(code: str):
    template = normalize_manual_order_link_template(safe_db_config("MANUAL_ORDER_LINK_TEMPLATE", "") or "")
    return template.replace("{code}", str(code or "").strip())


def auto_payment_config_key(key: str):
    normalized = str(key or "").strip().upper()
    return normalized.startswith("AUTO_PAYMENT_")


def refresh_auto_payment_schedule_if_needed(keys):
    changed = any(auto_payment_config_key(key) for key in keys or [])
    if not changed:
        return None
    try:
        return apply_auto_payment_schedule()
    except Exception as exc:
        print(f"⚠️ Không refresh được auto payment schedule ngay sau khi lưu config: {exc}")
        return None


def build_manual_order_message_url(code: str):
    template = normalize_manual_order_link_template(safe_db_config("MANUAL_ORDER_MESSAGE_LINK_TEMPLATE", "") or "")
    if "start=act_{code}" in template:
        template = template.replace("start=act_{code}", "start=act_{code}")
    elif "start={code}" in template:
        template = template.replace("start={code}", "start=act_{code}")
    return template.replace("{code}", str(code or "").strip())


def build_manual_order_join_message_text(context: dict[str, object]):
    text = render_manual_order_message_text(
        normalize_manual_order_join_template(safe_db_config("MANUAL_ORDER_JOIN_TEMPLATE", "") or ""),
        {
            **context,
            "activation_url": context.get("activation_url", ""),
            "message_url": context.get("message_url", ""),
            "links_text": context.get("links_text", ""),
            "support_text": context.get("support_text", ""),
        },
    )
    support_link = str(context.get("support_link", "") or "").strip()
    support_group_name = str(context.get("support_group_name", "") or "").strip()
    if support_link and support_link not in text:
        support_block = f"💬 {support_group_name or safe_support_group_name()}:\n{support_link}"
        text = f"{text}\n\n{support_block}".strip()
    return strip_html_text(text)


def build_manual_order_delivery_text(context: dict[str, object]):
    success_text = render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {})
    order_text = render_manual_order_info_text(context)
    partial_text = str(context.get("partial_text", "") or "").strip()
    support_text = str(context.get("support_text", "") or "").strip()
    links_text = str(context.get("links_text", "") or "").strip()
    default_text = "{success_text}\n\n{order_text}\n\n{links_text}\n\n{partial_text}\n\n{support_text}"
    template = str(safe_db_config("MANUAL_ORDER_DELIVERY_TEMPLATE", default_text) or default_text).strip()
    text = render_manual_order_message_text(template, {
        **context,
        "success_text": success_text,
        "order_text": order_text,
        "links_text": links_text,
        "partial_text": partial_text,
        "support_text": support_text,
    })
    return strip_html_text(text)


def license_plan_map():
    mapping = load_license_plan_mapping(db)
    return {
        code: {
            "groups": list(plan.groups),
            "duration_days": plan.duration_days,
            "allow_renew": plan.allow_renew,
        }
        for code, plan in mapping.items()
    }


def normalize_license_link_template(value: str):
    template = normalize_bot_link_template(value, default_payload="lic_{code}")
    if "start=act_{code}" in template:
        template = template.replace("start=act_{code}", "start=lic_{code}")
    elif "start={code}" in template:
        template = template.replace("start={code}", "start=lic_{code}")
    return template


def build_license_activation_url(license_key: str):
    template = normalize_license_link_template(safe_db_config("LICENSE_LINK_TEMPLATE", "") or "")
    return template.replace("{code}", normalize_license_key(license_key))


def _license_payload_from_request(body: dict[str, object]) -> dict[str, object]:
    return {
        "license_key": normalize_license_key(body.get("license_key", "")),
        "telegram_user_id": str(body.get("telegram_user_id", "")).strip(),
        "timestamp": int(body.get("timestamp") or 0) or int(datetime.now(tz=backend_timezone()).timestamp()),
        "nonce": str(body.get("nonce", "")).strip(),
    }


async def build_manual_order_result(body: dict[str, object]) -> dict[str, object]:
    timing_enabled = str(os.getenv("MANUAL_ORDER_TIMING_LOG", "1")).strip().lower() not in {"0", "false", "off", "no"}
    timing_started_at = time.perf_counter()
    timing_marks: list[tuple[str, float]] = []
    def mark(label: str):
        if timing_enabled:
            timing_marks.append((label, time.perf_counter()))

    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    plan_name, manual_plan_metadata = resolve_manual_order_plan(body)
    note = str(body.get("note", "")).strip()
    coupon_code = str(body.get("coupon_code", "")).strip().upper()
    skip_join_link = str(body.get("skip_join_link", "")).lower() == "true" or body.get("skip_join_link") is True
    fast_mode = str(body.get("fast_mode", "")).lower() == "true" or body.get("fast_mode") is True
    skip_active_code = should_skip_manual_active_code(body)
    activation_code = "" if skip_active_code else (str(body.get("activation_code", "")).strip().upper() or generate_activation_code())
    activation_url = build_manual_activation_url(activation_code) if activation_code else ""

    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="Cần nhập Telegram ID.")
    if not plan_name:
        raise HTTPException(status_code=400, detail="Cần chọn hoặc nhập tên gói.")
    try:
        user_id = int(telegram_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Telegram ID phải là số.")

    try:
        blacklist_entry = supabase_store.get_blacklist_entry(telegram_user_id)
    except Exception as exc:
        blacklist_entry = None
        print(f"⚠️ Không đọc được blacklist khi tạo đơn thủ công cho {telegram_user_id}: {exc}")
    if blacklist_entry and blacklist_entry.get("is_active"):
        reason = str(blacklist_entry.get("reason") or "Không rõ lý do").strip()
        raise HTTPException(status_code=403, detail=f"Khách đang bị blacklist: {reason}")

    db.reload_config(force=False)
    groups = resolve_plan_groups(plan_name)
    if not groups:
        raise HTTPException(status_code=400, detail="Tên gói chưa khớp collection nào. Kiểm tra tên gói hoặc cấu hình BTN_G/ID_G.")

    try:
        amount = float(str(body.get("amount", "0") or 0))
    except (TypeError, ValueError):
        amount = 0.0

    user_language = get_user_language(user_id)
    default_currency = "VND"
    preferred_provider = payment_manager.preferred_provider(user_language) or ("PAYPAL" if user_language == "en" else "PAYOS")
    payment_currency = str(body.get("payment_currency") or default_currency).strip().upper() or default_currency
    payment_provider = str(body.get("payment_provider") or preferred_provider).strip().upper() or preferred_provider
    if payment_provider == "MANUAL" and user_language == "en":
        payment_provider = preferred_provider
    inferred_language = infer_language_from_payment_context(
        payment_currency=payment_currency,
        payment_provider=payment_provider,
        raw_data=body,
    )
    if inferred_language:
        set_user_language(user_id, inferred_language)
    mark("context")

    expire_at = parse_manual_expire_at(body.get("expire_at"))
    if expire_at is None:
        try:
            default_duration = "1" if manual_plan_metadata.get("manual_plan_mode") == "CUSTOM_DURATION" else "30"
            duration_days = int(float(str(body.get("duration_days", default_duration) or default_duration)))
        except (TypeError, ValueError):
            duration_days = 1 if manual_plan_metadata.get("manual_plan_mode") == "CUSTOM_DURATION" else 30
        if duration_days <= 0:
            duration_days = 3650 if order_is_lifetime(plan_name) else (1 if manual_plan_metadata.get("manual_plan_mode") == "CUSTOM_DURATION" else 30)
        if manual_plan_metadata.get("manual_plan_mode") == "CUSTOM_DURATION":
            if duration_days > 3650:
                raise HTTPException(status_code=400, detail="Số ngày tùy chỉnh phải từ 1 đến 3650 ngày.")
        else:
            duration_days = resolve_manual_order_duration_days(
                plan_name,
                duration_days,
                telegram_user_id=telegram_user_id,
                full_name=full_name,
            )
        expire_at = now_local() + timedelta(days=duration_days)

    paid_at = now_local()
    order_id = str(int(time.time() * 1000))
    sale_id = str(body.get("sale_id") or "MANUAL").strip().upper()
    message_template = str(safe_db_config(
        "MANUAL_ORDER_MESSAGE_TEMPLATE",
        "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}",
    ) or "").strip()
    join_template = str(safe_db_config(
        "MANUAL_ORDER_JOIN_TEMPLATE",
        "{order_text}\n\n{bot_link_title}\n{links_text}\n\n{bot_link_subtitle}\n\n{support_text}",
    ) or "").strip()
    mark("render_defaults")
    try:
        write_started_at = time.perf_counter()
        supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=telegram_user_id,
            full_name=full_name or telegram_user_id,
            plan_name=plan_name,
            amount=amount,
            note=note,
            sale_id=sale_id,
            original_amount=body.get("original_amount", amount),
            coupon_code=coupon_code,
            payment_currency=payment_currency,
            payment_provider=payment_provider,
            metadata={
                "manual_order": True,
                "payment_currency": payment_currency,
                "payment_provider": payment_provider,
                "language": user_language,
                "note": note,
                **manual_plan_metadata,
            },
        )
        order_data = supabase_store.mark_order_paid(
            order_id,
            paid_at=paid_at.isoformat(timespec="seconds"),
            expire_at=expire_at.isoformat(timespec="seconds"),
        )
        if timing_enabled:
            print(f"[manual-order-timing] order_write order_id={order_id} supabase_write_ms={((time.perf_counter() - write_started_at) * 1000):.1f}")
    except Exception as exc:
        if not (is_missing_supabase_table_error(exc, "orders") or is_missing_supabase_runtime_error(exc)):
            raise
        print(f"⚠️ Bỏ qua lưu đơn thủ công vào Supabase vì thiếu bảng/env: {exc}")
        order_data = []

    try:
        from modules.mod_coupon import build_invite_links
    except ImportError:  # pragma: no cover - lightweight test fallback
        async def build_invite_links(*args, **kwargs):
            return "", "", [], []

    support_link, support_error = None, ""
    links_text = ""
    group_names = []
    failed_groups = []
    invite_results = []
    support_text = ""

    if not skip_join_link and not fast_mode:
        links_started_at = time.perf_counter()
        support_link, support_error = await _maybe_await(create_support_invite_link(user_id))
        try:
            links_text, group_names, failed_groups, invite_results = await build_invite_links(user_id, plan_name)
        except Exception as exc:
            print(f"⚠️ Không build được join links cho manual order {order_id}: {exc}")
        if support_link:
            support_text = render_manual_order_support_text("💬 {support_group_name}:\n{support_link}", {
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "full_name": full_name,
                "plan_name": plan_name,
                "expire_at": expire_at.isoformat(timespec="seconds"),
                "support_group_name": safe_support_group_name(),
                "support_link": support_link,
                "support_error": "",
            })
        elif support_error:
            support_text = render_activation_text(
                "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
                "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
                {
                    "support_group_name": safe_support_group_name(),
                    "support_error": support_error,
                },
            )
        if timing_enabled:
            print(f"[manual-order-timing] join_links order_id={order_id} render_and_links_ms={((time.perf_counter() - links_started_at) * 1000):.1f}")
    elif timing_enabled:
        print(f"[manual-order-timing] join_links order_id={order_id} skipped=1")

    order_text = render_manual_order_info_text({
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at.isoformat(timespec="seconds"),
    })
    mark("order_text")

    if not skip_active_code:
        try:
            activation_started_at = time.perf_counter()
            supabase_store.create_order_activation_code(
                code=activation_code,
                order_id=order_id,
                telegram_user_id=telegram_user_id,
                full_name=full_name or telegram_user_id,
                plan_name=plan_name,
                expire_at=expire_at.isoformat(timespec="seconds"),
                activation_url=activation_url,
                raw_data={
                    "manual_order": True,
                    "order_id": order_id,
                    "telegram_user_id": telegram_user_id,
                    "plan_name": plan_name,
                    **manual_plan_metadata,
                    "expire_at": expire_at.isoformat(timespec="seconds"),
                },
            )
            if timing_enabled:
                print(f"[manual-order-timing] activation_code order_id={order_id} supabase_write_ms={((time.perf_counter() - activation_started_at) * 1000):.1f}")
        except Exception as exc:
            if not (is_missing_supabase_table_error(exc, "order_activation_codes") or is_missing_supabase_runtime_error(exc)):
                raise
            print(f"⚠️ Bỏ qua lưu activation code vì thiếu bảng/env Supabase: {exc}")

    try:
        supabase_store.record_support_event(
            "manual_order_created",
            telegram_user_id,
            full_name=full_name,
            order_id=order_id,
            plan_name=plan_name,
            raw_data={
                **manual_plan_metadata,
                "plan_name": plan_name,
                "amount": amount,
                "coupon_code": coupon_code,
                "note": note,
                "activation_code": activation_code,
                "activation_url": activation_url,
                "support_link_created": bool(support_link),
                "support_error": support_error,
            },
        )
    except Exception as exc:
        if not (is_missing_supabase_table_error(exc, "support_events") or is_missing_supabase_runtime_error(exc)):
            print(f"⚠️ Không ghi được manual_order_created: {exc}")
        else:
            print(f"⚠️ Bỏ qua ghi manual_order_created vì thiếu bảng/env Supabase: {exc}")
    if timing_enabled:
        total_ms = (time.perf_counter() - timing_started_at) * 1000
        print("[manual-order-timing] total order_id=%s total_ms=%.1f marks=%s" % (
            order_id,
            total_ms,
            ", ".join(f"{label}:{(ts - timing_started_at) * 1000:.1f}" for label, ts in timing_marks),
        ))

    return {
        "order_id": order_id,
        "order": order_data[0] if isinstance(order_data, list) and order_data else None,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name,
        "plan_name": plan_name,
        **manual_plan_metadata,
        "amount": amount,
        "note": note,
        "payment_currency": payment_currency,
        "payment_provider": payment_provider,
        "paid_at": paid_at.isoformat(timespec="seconds"),
        "expire_at": format_manual_expire_at(expire_at.isoformat(timespec="seconds")),
        "expire_at_iso": expire_at.isoformat(timespec="seconds"),
        "group_names": ", ".join(group_names),
        "links_text": links_text,
        "activation_code": activation_code,
        "activation_url": activation_url,
        "manual_order_message_url": build_manual_order_message_url(activation_code),
        "support_link": support_link,
        "support_error": support_error,
        "support_text": support_text,
        "bot_link_title": render_activation_text("MANUAL_ORDER_LINK_TITLE", "🔗 Active code", {}),
        "manual_order_message_title": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_TITLE", "💬 Tin nhắn active code", {}),
        "manual_order_join_title": render_activation_text("MANUAL_ORDER_JOIN_LINK_TITLE", "💬 Link tham gia nhóm", {}),
        "bot_link_subtitle": render_activation_text("MANUAL_ORDER_LINK_SUBTITLE", "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", {}),
        "manual_order_message_subtitle": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_SUBTITLE", "Dùng link này để mở bot và nhận toàn bộ nội dung xác nhận đơn.", {}),
        "manual_order_join_subtitle": render_activation_text("MANUAL_ORDER_JOIN_LINK_SUBTITLE", "Dùng tin này để gửi khách toàn bộ link tham gia nhóm trong đơn.", {}),
        "bot_link_button_label": render_activation_text("MANUAL_ORDER_LINK_BUTTON_LABEL", "Gen active code", {}),
        "manual_order_message_button_label": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_BUTTON_LABEL", "Copy tin active code", {}),
        "manual_order_join_button_label": render_activation_text("MANUAL_ORDER_JOIN_LINK_BUTTON_LABEL", "Copy tin tham gia", {}),
        "bot_link_success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {}),
        "bot_link_processing_text": render_activation_text("MANUAL_ORDER_LINK_PROCESSING_TEXT", "⏳ Bot đang xác minh đơn và tạo link nhóm...", {}),
            "manual_order_text": "" if skip_active_code else render_manual_order_message_text(message_template, {
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "full_name": full_name or telegram_user_id,
                "plan_name": plan_name,
                "expire_at": expire_at.isoformat(timespec="seconds"),
                "order_text": order_text,
            "success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {}),
            "bot_link_title": render_activation_text("MANUAL_ORDER_LINK_TITLE", "🔗 Active code", {}),
            "bot_link_subtitle": render_activation_text("MANUAL_ORDER_LINK_SUBTITLE", "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", {}),
            "activation_url": activation_url,
            "message_url": build_manual_order_message_url(activation_code) if activation_code else "",
            "links_text": links_text,
            "support_text": support_text,
            "support_group_name": safe_support_group_name(),
            "support_link": support_link,
            "support_error": support_error,
            "activation_code": activation_code,
        }),
            "manual_order_join_text": "" if skip_join_link or fast_mode else build_manual_order_join_message_text({
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "full_name": full_name or telegram_user_id,
                "plan_name": plan_name,
                "expire_at": expire_at.isoformat(timespec="seconds"),
                "order_text": order_text,
                "bot_link_title": render_activation_text("MANUAL_ORDER_JOIN_LINK_TITLE", "💬 Link tham gia nhóm", {}),
                "bot_link_subtitle": render_activation_text("MANUAL_ORDER_JOIN_LINK_SUBTITLE", "Dùng tin này để gửi khách toàn bộ link tham gia nhóm trong đơn.", {}),
                "activation_url": activation_url,
                "message_url": "",
                "links_text": links_text,
                "support_text": support_text,
                "support_group_name": safe_support_group_name(),
                "support_link": support_link,
                "support_error": support_error,
            }),
    }


def infer_language_from_payment_context(*, payment_currency="", payment_provider="", raw_data=None):
    raw = raw_data if isinstance(raw_data, dict) else {}
    raw_language = str(raw.get("language") or "").strip().lower()
    if raw_language in {"vi", "en"}:
        return raw_language
    currency = str(payment_currency or raw.get("payment_currency") or "").strip().upper()
    provider = str(payment_provider or raw.get("payment_provider") or "").strip().upper()
    if currency == "USD" or provider in {"PAYPAL", "NOWPAYMENTS", "TRON_USDT", "BINANCE_PAY"}:
        return "en"
    if currency == "VND" or provider == "PAYOS":
        return "vi"
    return None


def generate_activation_code(length: int = 6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    import secrets

    return "".join(secrets.choice(alphabet) for _ in range(max(4, length)))


def normalize_chat_id(value):
    raw = str(value or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def support_event_time(event):
    return str((event or {}).get("created_at") or "")


def latest_event(events, event_type, user_id, order_id=None, chat_id=None):
    user_id = str(user_id or "")
    order_id = str(order_id or "") if order_id is not None else None
    chat_id = normalize_chat_id(chat_id) if chat_id is not None else None
    matches = [
        event
        for event in events
        if event.get("event_type") == event_type
        and str(event.get("telegram_user_id") or "") == user_id
        and (order_id is None or str(event.get("order_id") or "") == order_id)
        and (chat_id is None or normalize_chat_id(event.get("chat_id")) == chat_id)
    ]
    matches.sort(key=support_event_time, reverse=True)
    return matches[0] if matches else None


def support_event_error(event):
    raw_data = (event or {}).get("raw_data") or {}
    if isinstance(raw_data, dict):
        return str(raw_data.get("error") or raw_data.get("message") or "").strip()
    return str(raw_data or "").strip()


def member_status_value(member):
    raw_status = getattr(member, "status", "")
    return str(getattr(raw_status, "value", raw_status)).lower()


async def member_live_state(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=int(user_id))
        status = member_status_value(member)
        present = status not in {"left", "kicked", "banned"}
        if hasattr(member, "is_member") and member.is_member is False:
            present = False
        return {"checked": True, "present": present, "status": status, "error": ""}
    except Exception as exc:
        text = str(exc)
        lower = text.lower()
        if "user not found" in lower or "participant_id_invalid" in lower:
            return {"checked": True, "present": False, "status": "left", "error": ""}
        return {"checked": True, "present": None, "status": "unknown", "error": text}


def group_label_for_chat_id(chat_id):
    target = normalize_chat_id(chat_id)
    for group_no in range(1, 101):
        gid = normalize_chat_id(db.get_config(f"ID_G{group_no}", ""))
        if gid and gid == target:
            return db.get_config(f"BTN_G{group_no}", f"G{group_no}")
    for hidden_group in list_hidden_groups(include_inactive=True):
        gid = normalize_chat_id(hidden_group.get("chat_id"))
        if gid and gid == target:
            return hidden_group.get("name") or hidden_group.get("id") or target
    return target or "-"


def resolve_order_display_label(order, support_events):
    user_id = str(order.get("telegram_user_id") or "")
    direct = str(order.get("full_name") or "").strip()
    if direct and direct != "-":
        return direct
    for event in support_events:
        if str(event.get("telegram_user_id") or "") != user_id:
            continue
        name = str(event.get("full_name") or event.get("username") or "").strip()
        if name and name != "-":
            return name
    return user_id


def order_display_name(order, support_events):
    return resolve_order_display_label(order, support_events)


async def build_kick_audit_rows(live=False, order_id_filter="", user_id_filter="", chat_id_filter="", updated_after: str | None = None):
    from scheduler import parse_expire_datetime, plan_group_ids, user_active_group_ids

    db.reload_config(force=False)
    now = now_local().replace(tzinfo=None)
    try:
        orders = supabase_store.list_scheduler_orders(limit=5000, updated_after=updated_after)
    except TypeError:
        orders = supabase_store.list_scheduler_orders(limit=5000)
    users_data = [supabase_store.order_to_sheet_row(order) for order in orders]
    try:
        try:
            support_events = supabase_store.list_support_events(limit=5000, updated_after=updated_after)
        except TypeError:
            support_events = supabase_store.list_support_events(limit=5000)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_events"):
            warn_missing_table_once("support_events", exc)
            support_events = []
        else:
            raise
    try:
        try:
            renewal_kick_tasks = supabase_store.list_renewal_kick_tasks(limit=5000)
        except TypeError:
            renewal_kick_tasks = supabase_store.list_renewal_kick_tasks(limit=5000)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_tasks"):
            warn_missing_table_once("renewal_kick_tasks", exc)
            renewal_kick_tasks = []
        else:
            raise

    rows = []
    for order in orders:
        order_id = str(order.get("order_id") or "")
        user_id = str(order.get("telegram_user_id") or "")
        if order_id_filter and order_id != str(order_id_filter):
            continue
        if user_id_filter and user_id != str(user_id_filter):
            continue

        plan_name = str(order.get("plan_name") or "")
        display_name = resolve_order_display_label(order, support_events)
        raw_expire_at = order.get("expire_at")
        expire_at = parse_expire_datetime(raw_expire_at)
        if raw_expire_at and not expire_at:
            rows.append({
                "audit_id": f"{order_id}:INVALID_EXPIRE_AT",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": raw_expire_at,
                "group_id": "",
                "group_name": "Chưa kiểm tra được",
                "status": "INVALID_EXPIRE_AT",
                "status_label": "Lỗi ngày hết hạn",
                "needs_action": True,
                "latest_kick_at": "",
                "latest_error": f"Không đọc được expire_at: {raw_expire_at}",
                "live_checked": False,
                "live_status": "",
                "live_present": None,
            })
            continue
        if not expire_at or expire_at > now:
            continue

        current_group_ids = [normalize_chat_id(item) for item in plan_group_ids(plan_name)]
        active_group_ids = {normalize_chat_id(item) for item in user_active_group_ids(user_id, order_id, users_data, now)}

        if not current_group_ids:
            rows.append({
                "audit_id": f"{order_id}:NO_GROUP",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": order.get("expire_at"),
                "group_id": "",
                "group_name": "Không map được group",
                "status": "NO_GROUP",
                "status_label": "Không map được group",
                "needs_action": True,
                "latest_kick_at": "",
                "latest_error": "Tên gói không khớp BTN_G/ID_G.",
                "live_checked": False,
                "live_status": "",
                "live_present": None,
            })
            continue

        for gid in current_group_ids:
            if chat_id_filter and normalize_chat_id(chat_id_filter) != gid:
                continue

            retained = gid in active_group_ids
            retained_orders = []
            if retained:
                for other_order in orders:
                    other_order_id = str(other_order.get("order_id") or "")
                    other_user_id = str(other_order.get("telegram_user_id") or "")
                    if other_order_id == order_id or other_user_id != user_id:
                        continue
                    if str(other_order.get("status") or "").upper() != "PAID":
                        continue
                    other_expire = parse_expire_datetime(other_order.get("expire_at"))
                    other_plan = str(other_order.get("plan_name") or "")
                    if (other_expire and other_expire > now) or (other_expire is None and other_plan):
                        if gid in {normalize_chat_id(item) for item in plan_group_ids(other_plan)}:
                            retained_orders.append(other_order_id)
                retained_orders = sorted({item for item in retained_orders if item})
            latest_order_kick = latest_event(support_events, "member_kicked", user_id, order_id, gid)
            latest_group_kick = latest_event(support_events, "member_kicked", user_id, None, gid)
            latest_kick = latest_order_kick or latest_group_kick
            latest_fail = latest_event(support_events, "member_kick_failed", user_id, order_id, gid)
            latest_close = latest_event(support_events, "member_kick_closed", user_id, order_id, gid) or latest_event(support_events, "member_kick_closed", user_id, None, gid)
            latest_kick_queue = latest_event(support_events, "renewal_kick_queued", user_id, order_id, gid)
            latest_kick_processing = latest_event(support_events, "renewal_kick_processing", user_id, order_id, gid)
            latest_kick_confirmed = latest_event(support_events, "renewal_kick_confirmed", user_id, order_id, gid)
            latest_kick_failed = latest_event(support_events, "renewal_kick_failed", user_id, order_id, gid)
            task_match = next((task for task in renewal_kick_tasks if str(task.get("order_id") or "") == order_id and str(task.get("group_id") or "") == gid), None)
            task_state = str((task_match or {}).get("state") or "").strip().lower()

            latest_kick_state = ""
            for candidate in (latest_kick_confirmed, latest_close, latest_kick_failed, latest_fail, latest_kick_processing, latest_kick_queue, latest_kick, latest_order_kick, latest_group_kick):
                raw_data = (candidate or {}).get("raw_data") or {}
                if isinstance(raw_data, dict) and raw_data.get("kick_state"):
                    latest_kick_state = str(raw_data.get("kick_state") or "").strip().lower()
                    break
            if not latest_kick_state:
                if latest_kick_confirmed:
                    latest_kick_state = "done"
                if latest_close:
                    latest_kick_state = "done"
                elif latest_kick_failed:
                    latest_kick_state = "error"
                elif latest_fail:
                    latest_kick_state = "error"
                elif latest_kick_processing:
                    latest_kick_state = "processing"
                elif latest_kick_queue:
                    latest_kick_state = "queued"
            if task_state and task_state not in {"", "queued"}:
                latest_kick_state = task_state

            live_state = {"checked": False, "present": None, "status": "", "error": ""}
            should_live_check = live and not latest_kick_state == "done" and (retained or latest_fail or not latest_kick or task_state in {"processing", "pending_confirm", "retry_pending"})
            if should_live_check:
                live_state = await member_live_state(gid, user_id)

            status = (
                "ACTIVE_RETAINED"
                if retained
                else "DONE"
                if latest_kick_state == "done"
                else "ERROR"
                if latest_kick_state == "error"
                else "PROCESSING"
                if latest_kick_state == "processing"
                else "PENDING_CONFIRM"
                if latest_kick_state == "pending_confirm"
                else "RETRY_PENDING"
                if latest_kick_state == "retry_pending"
                else "BLOCKED"
                if latest_kick_state == "blocked_active_order"
                else "REVIEW_REQUIRED"
                if latest_kick_state == "review_required"
                else "UNMAPPED_GROUP"
                if latest_kick_state == "unmapped_group"
                else "QUEUED"
                if latest_kick_state == "queued"
                else "KICKED"
                if latest_kick
                else "WAITING_KICK"
            )
            status_label = (
                "Còn quyền active"
                if retained
                else "Đã kick xong"
                if latest_kick_state == "done"
                else "Lỗi kick"
                if latest_kick_state == "error"
                else "Đang kick"
                if latest_kick_state == "processing"
                else "Đã xếp hàng kick"
                if latest_kick_state == "queued"
                else "Đang chờ xác nhận"
                if latest_kick_state == "pending_confirm"
                else "Chờ thử lại"
                if latest_kick_state == "retry_pending"
                else "Bị giữ bởi đơn active khác"
                if latest_kick_state == "blocked_active_order"
                else "Cần xử lý"
                if latest_kick_state == "review_required"
                else "Không map được group"
                if latest_kick_state == "unmapped_group"
                else "Đã kick cùng group"
                if latest_kick and latest_kick is not latest_order_kick
                else "Đã kick"
                if latest_kick
                else "Chờ kick"
            )
            needs_action = not retained and latest_kick_state not in {"done"} and latest_kick_state != "error" and not latest_kick
            if latest_kick_state in {"error", "queued", "processing", "pending_confirm", "retry_pending", "blocked_active_order", "review_required", "unmapped_group"}:
                needs_action = True
            if latest_kick_state == "done":
                needs_action = False

            if live_state["checked"]:
                if live_state["error"]:
                    status = "CHECK_ERROR"
                    status_label = "Lỗi kiểm tra live"
                    needs_action = True
                elif not retained and latest_kick and live_state["present"]:
                    status = "REJOINED"
                    status_label = "Đã join lại / cần kick lại"
                    needs_action = True
                elif not retained and not latest_kick and live_state["present"] is False:
                    status = "LEFT_NO_LOG"
                    status_label = "Không còn trong group nhưng thiếu log kick"
                    needs_action = False
                elif not retained and not latest_kick and live_state["present"]:
                    status = "WAITING_KICK"
                    status_label = "Chờ kick"
                    needs_action = True

            rows.append({
                "audit_id": f"{order_id}:{gid}",
                "customer_name": display_name,
                "telegram_user_id": user_id,
                "order_id": order_id,
                "plan_name": plan_name,
                "expire_at": order.get("expire_at"),
                "group_id": gid,
                "group_name": group_label_for_chat_id(gid),
                "status": status,
                "status_label": status_label,
                "needs_action": needs_action,
                "latest_kick_at": (latest_kick or {}).get("created_at") or "",
                "latest_error": support_event_error(latest_fail),
                "live_checked": live_state["checked"],
                "live_status": live_state["status"],
                "live_present": live_state["present"],
                "kick_state": latest_kick_state or ("done" if latest_kick else ""),
                "retained_reason": (
                    f"Còn {len(retained_orders)} đơn active khác giữ group"
                    if retained and retained_orders
                    else "Còn đơn active khác giữ group"
                    if retained
                    else ""
                ),
                "retained_orders": retained_orders,
            })

    priority = {"INVALID_EXPIRE_AT": 0, "NO_GROUP": 1, "WAITING_KICK": 2, "REJOINED": 3, "CHECK_ERROR": 4, "LEFT_NO_LOG": 5, "ACTIVE_RETAINED": 6, "KICKED": 7}
    rows.sort(key=lambda item: (priority.get(item["status"], 9), str(item.get("expire_at") or "")))
    return rows


def parse_chat_id(value):
    raw = normalize_chat_id(value)
    if not raw:
        raise ValueError("Thiếu group ID.")
    try:
        return int(raw)
    except ValueError:
        return raw


def load_all_modules():
    loaded_count = 0
    module_dir = "modules"
    excluded_modules = set()
    if not os.path.exists(module_dir):
        return loaded_count

    for filename in os.listdir(module_dir):
        if not filename.startswith("mod_") or not filename.endswith(".py"):
            continue
        module_name = filename[:-3]
        if module_name in excluded_modules:
            print(f"⏭ Bỏ qua module đã tắt: {module_name}")
            continue
        try:
            module = importlib.import_module(f"{module_dir}.{module_name}")
            if hasattr(module, "router"):
                dp.include_router(module.router)
                loaded_count += 1
        except Exception as exc:
            print(f"❌ Lỗi khi nạp module {module_name}: {exc}")
    return loaded_count


async def start_background_workers():
    try:
        from modules.mod_maintenance import maintenance_worker
    except Exception:
        maintenance_worker = None

    try:
        from scheduler import main as scheduler_worker
    except Exception:
        scheduler_worker = None

    try:
        from processor import binance_pay_polling_worker
    except Exception:
        binance_pay_polling_worker = None

    try:
        from modules.mod_coupon import coupon_cleanup_worker
    except Exception:
        coupon_cleanup_worker = None

    try:
        from modules.mod_campaigns import campaign_worker
    except Exception:
        campaign_worker = None

    try:
        from modules.mod_channel_publisher import channel_publisher_worker
    except Exception:
        channel_publisher_worker = None

    try:
        from modules.mod_runtime_state import bot_runtime_worker
    except Exception:
        bot_runtime_worker = None

    try:
        from modules.mod_auto_payment_schedule import auto_payment_schedule_worker
    except Exception:
        auto_payment_schedule_worker = None

    if maintenance_worker:
        create_background_task(maintenance_worker(), name="maintenance_worker", context="web_backend")
    if scheduler_worker:
        create_background_task(scheduler_worker(), name="scheduler_worker", context="web_backend")
    if binance_pay_polling_worker:
        create_background_task(binance_pay_polling_worker(), name="binance_pay_polling_worker", context="web_backend")
    if coupon_cleanup_worker:
        create_background_task(coupon_cleanup_worker(), name="coupon_cleanup_worker", context="web_backend")
    if campaign_worker:
        create_background_task(campaign_worker(), name="campaign_worker", context="web_backend")
    if channel_publisher_worker:
        create_background_task(channel_publisher_worker(), name="channel_publisher_worker", context="web_backend")
    if bot_runtime_worker:
        create_background_task(bot_runtime_worker(), name="bot_runtime_worker", context="web_backend")
    if auto_payment_schedule_worker:
        create_background_task(auto_payment_schedule_worker(), name="auto_payment_schedule_worker", context="web_backend")
    create_background_task(webhook_watch_worker(), name="webhook_watch_worker", context="web_backend")


@app.on_event("startup")
async def startup():
    global _booted
    if _booted:
        return

    db.connect()
    if getattr(supabase_store, "enabled", False):
        supabase_store.connect()
    webhook_url = os.getenv("WEBHOOK_URL")
    skip_telegram_startup = str(os.getenv("SKIP_TELEGRAM_STARTUP", "")).strip().lower() in {"1", "true", "yes", "on"}
    if webhook_url and not skip_telegram_startup:
        await set_commands()
    else:
        print("⚠️ Bỏ qua set_commands() khi chạy local hoặc chưa cấu hình WEBHOOK_URL.")
    try:
        from helpers import setup_bot_availability

        setup_bot_availability(dp)
    except Exception as exc:
        print(f"⚠️ Không thể bật lịch hoạt động bot: {exc}")
    try:
        from analytics import setup_analytics

        setup_analytics(dp)
    except Exception as exc:
        print(f"⚠️ Không thể bật analytics middleware: {exc}")
    load_all_modules()
    await start_background_workers()

    if webhook_url:
        global _webhook_startup_retry_task
        if not _webhook_startup_retry_task or _webhook_startup_retry_task.done():
            _webhook_startup_retry_task = create_background_task(
                retry_telegram_webhook_background(initial_delay=0),
                name="telegram_webhook_startup_retry",
                context="webhook",
            )
            print("🕒 Telegram webhook startup queued in background.")
    else:
        print("⚠️ WEBHOOK_URL chưa được cấu hình, backend chỉ chạy API/health.")

    _booted = True


@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()


@app.get("/health")
async def health():
    return {
        "ok": True,
        "supabase": supabase_store.enabled,
        "webhook_url_configured": bool(os.getenv("WEBHOOK_URL")),
        "webhook_last_reset_reason": _last_webhook_reset_reason,
        "webhook_failure_streak": _webhook_failure_streak,
        "runtime_maintenance_override": runtime_maintenance_override(),
        "webhook_reset_state": webhook_reset_state_meta(),
    }


@app.get("/")
async def root():
    return {"ok": True, "service": "hang-cu-vip-backend"}


@app.get("/admin-api/webhook-info", dependencies=[Depends(require_admin)])
async def admin_webhook_info():
    info_error = ""
    try:
        info = await bot.get_webhook_info()
    except Exception as exc:
        info_error = str(exc)
        info = empty_webhook_info(info_error)
    return {
        "data": info,
        "meta": {
            "expected_url": str(os.getenv("WEBHOOK_URL") or "").strip(),
            "last_reset_reason": _last_webhook_reset_reason,
            "failure_streak": _webhook_failure_streak,
            "problem_reason": f"info_unavailable: {info_error}" if info_error else webhook_problem_reason(info, str(os.getenv("WEBHOOK_URL") or "").strip()),
            "maintenance_override": runtime_maintenance_override(),
            "reset_state": webhook_reset_state_meta(),
        },
    }


@app.get("/admin-api/bot-schedule-status", dependencies=[Depends(require_admin)])
async def admin_bot_schedule_status():
    return {"data": bot_schedule_status()}


@app.get("/admin-api/bot-runtime-state", dependencies=[Depends(require_admin)])
async def admin_bot_runtime_state():
    return {"data": bot_schedule_status()}


@app.get("/admin-api/bot-runtime-state/audit", dependencies=[Depends(require_admin)])
async def admin_bot_runtime_state_audit():
    return {"data": bot_runtime_state_audit()}


@app.post("/admin-api/webhook-reset", dependencies=[Depends(require_admin)])
async def admin_webhook_reset():
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(status_code=503, detail="WEBHOOK_URL is not configured")
    result = await ensure_telegram_webhook(force=True)
    return {
        "data": result.get("info"),
        "meta": {
            "expected_url": str(webhook_url).strip(),
            "last_reset_reason": _last_webhook_reset_reason,
            "problem_reason": webhook_problem_reason(result.get("info"), str(webhook_url).strip()) if result.get("info") else "",
            "reset_state": webhook_reset_state_meta(),
        },
    }


@app.post("/admin-api/webhook-clear-maintenance", dependencies=[Depends(require_admin)])
async def admin_webhook_clear_maintenance():
    wait_seconds = webhook_reset_wait_seconds()
    if wait_seconds > 0:
        raise HTTPException(status_code=409, detail=f"Webhook cooldown still active. Retry after {wait_seconds}s.")
    set_runtime_maintenance_override(False, reason="", source="webhook")
    info_error = ""
    try:
        info = await bot.get_webhook_info()
    except Exception as exc:
        info_error = str(exc)
        info = empty_webhook_info(info_error)
    return {
        "data": info,
        "meta": {
            "expected_url": str(os.getenv("WEBHOOK_URL") or "").strip(),
            "last_reset_reason": _last_webhook_reset_reason,
            "failure_streak": _webhook_failure_streak,
            "problem_reason": f"info_unavailable: {info_error}" if info_error else webhook_problem_reason(info, str(os.getenv("WEBHOOK_URL") or "").strip()),
            "maintenance_override": runtime_maintenance_override(),
            "reset_state": webhook_reset_state_meta(),
        },
    }


@app.post("/payment-webhooks/nowpayments")
async def nowpayments_webhook(request: Request):
    secret = os.getenv("NOWPAYMENTS_IPN_SECRET") or str(db.get_config("NOWPAYMENTS_IPN_SECRET", "") or "")
    signature = request.headers.get("x-nowpayments-sig") or request.headers.get("X-NOWPAYMENTS-SIG")
    raw_body = await request.body()
    if not payment_manager.nowpayments.verify_ipn_signature(raw_body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid NOWPayments signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid NOWPayments payload")

    order_id = str(payload.get("order_id") or payload.get("orderId") or "").strip()
    payment_id = str(payload.get("payment_id") or payload.get("invoice_id") or payload.get("id") or "").strip()
    raw_status = str(payload.get("payment_status") or payload.get("status") or "").strip()
    status = payment_manager.nowpayments.normalize_status(raw_status)
    if not order_id:
        raise HTTPException(status_code=400, detail="NOWPayments payload missing order_id")

    order = supabase_store.get_order(order_id) if supabase_store.enabled else None
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.get("payment_provider") or "").upper() != "NOWPAYMENTS":
        raise HTTPException(status_code=400, detail="Order provider mismatch")

    try:
        existing_metadata = order.get("metadata") if isinstance(order.get("metadata"), dict) else {}
        supabase_store.update_order_fields(order_id, {
            "metadata": {
                **existing_metadata,
                "nowpayments_last_status": raw_status,
                "nowpayments_payment_id": payment_id,
                "nowpayments_ipn_at": now_local().isoformat(timespec="seconds"),
            },
        })
    except Exception as exc:
        print(f"⚠️ Không lưu được metadata IPN NOWPayments cho đơn {order_id}: {exc}")

    if status == "PAID":
        from processor import process_successful_payment

        await process_successful_payment(order_id)
    elif raw_status.lower() in {"failed", "expired", "refunded"} and str(order.get("status", "")).upper() == "PENDING":
        try:
            supabase_store.expire_pending_order(order_id)
        except Exception as exc:
            print(f"⚠️ Không cập nhật EXPIRED cho đơn NOWPayments {order_id}: {exc}")

    return {"ok": True, "order_id": order_id, "status": status, "raw_status": raw_status}


@app.post("/payment-webhooks/binance-pay/scan", dependencies=[Depends(require_admin)])
async def binance_pay_scan():
    if not payment_manager.binance_pay.enabled:
        return {"ok": False, "status": "disabled", "matched": [], "delivered": []}

    matched = await asyncio.to_thread(payment_manager.scan_pending_orders, "BINANCE_PAY")
    delivered = []
    for order_id in matched:
        try:
            from processor import process_successful_payment

            await process_successful_payment(order_id)
            delivered.append(order_id)
        except Exception as exc:
            print(f"⚠️ Lỗi giao hàng Binance Pay cho đơn {order_id}: {exc}")
    return {"ok": True, "matched": matched, "delivered": delivered}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if expected:
        received = request.headers.get("x-telegram-bot-api-secret-token")
        if received != expected:
            raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Telegram webhook payload")

    try:
        update = Update.model_validate(payload, context={"bot": bot})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Telegram webhook update")
    update_type = getattr(update, "event_type", None) or "unknown"
    message = getattr(update, "message", None)
    message_text = str(getattr(message, "text", "") or "").replace("\n", " ")[:120] if message else ""
    entity_types = []
    if message and getattr(message, "entities", None):
        entity_types = [getattr(entity, "type", "") for entity in message.entities]
    print(f"📨 webhook update received: type={update_type} text={message_text} entities={entity_types}")
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/admin-api/orders", dependencies=[Depends(require_admin)])
async def admin_orders(limit: int = 200, updated_after: str | None = None):
    return {"data": supabase_store.list_orders(limit=limit, updated_after=updated_after)}


@app.get("/admin-api/dashboard-summary", dependencies=[Depends(require_admin)])
async def admin_dashboard_summary():
    try:
        return {
            "data": {
                "orders_total": supabase_store.count_rows("orders"),
                "orders_paid": supabase_store.count_rows("orders", params={"status": "eq.PAID"}),
                "orders_pending": supabase_store.count_rows("orders", params={"status": "eq.PENDING"}),
                "activation_codes": supabase_store.count_rows("order_activation_codes"),
                "support_events": supabase_store.count_rows("support_events"),
                "activity_events": supabase_store.count_rows("analytics_events"),
                "coupons": supabase_store.count_rows("coupons"),
                "hidden_groups": supabase_store.count_rows("hidden_groups"),
                "hidden_codes": supabase_store.count_rows("hidden_codes"),
                "blacklist_active": supabase_store.count_rows("security_blacklist", params={"is_active": "eq.true"}),
                "broadcast_campaigns": supabase_store.count_rows("broadcast_campaigns"),
                "channel_posts": supabase_store.count_rows("channel_posts"),
            }
        }
    except Exception as exc:
        print(f"⚠️ Không dựng được dashboard summary: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được dashboard summary: {exc}")


@app.get("/admin-api/dashboard-overview", dependencies=[Depends(require_admin)])
async def admin_dashboard_overview():
    try:
        now = now_local()
        orders = supabase_store.list_orders(limit=50)
        support_events = supabase_store.list_support_events(limit=25)
        activity_events = supabase_store.list_analytics_events(limit=25)

        recent_orders = [
            {
                "order_id": order.get("order_id") or "",
                "telegram_user_id": order.get("telegram_user_id") or "",
                "full_name": order.get("full_name") or "",
                "plan_name": order.get("plan_name") or "",
                "amount": order.get("amount"),
                "status": order.get("status") or "",
                "created_at": order.get("created_at") or "",
                "expire_at": order.get("expire_at") or "",
                "payment_currency": order.get("payment_currency") or "",
                "payment_provider": order.get("payment_provider") or "",
            }
            for order in orders[:10]
        ]
        top_paid_orders = [order for order in orders if _backend_text(order.get("status")).upper() == "PAID"]
        paid_order_count = len(top_paid_orders)
        pending_order_count = len([order for order in orders if _backend_text(order.get("status")).upper() == "PENDING"])
        overview_trend = []
        for order in top_paid_orders:
            created = _backend_parse_datetime(order.get("created_at"))
            label = created.astimezone(_backend_timezone()).strftime("%d/%m") if created else "-"
            overview_trend.append({
                "label": label,
                "order_id": order.get("order_id") or "",
                "plan_name": order.get("plan_name") or "",
                "value": float(order.get("amount") or 0),
                "vip": order.get("telegram_user_id") or "",
            })
        recent_user_activity = []
        for event in activity_events[:10]:
            payload = event.get("payload") or {}
            chat_type = _backend_text(payload.get("chat_type")).lower()
            if chat_type in {"group", "supergroup", "channel"}:
                continue
            recent_user_activity.append({
                "id": event.get("id"),
                "event_name": event.get("event_name"),
                "telegram_user_id": event.get("telegram_user_id"),
                "payload": payload,
                "created_at": event.get("created_at"),
            })
            if len(recent_user_activity) >= 10:
                break
        recent_notifications = []
        for event in support_events:
            if event.get("event_type") not in {
                "manual_order_created",
                "manual_activation_link_generated",
                "manual_activation_link_failed",
                "activation_link_cleanup_done",
                "activation_link_cleanup_failed",
                "expired_notice_sent",
                "renewal_reminder_sent",
                "member_kicked",
                "member_muted",
                "member_unmuted",
                "support_joined",
                "support_left",
                "vip_joined",
                "vip_left",
            }:
                continue
            recent_notifications.append({
                "id": event.get("id"),
                "event_type": event.get("event_type"),
                "telegram_user_id": event.get("telegram_user_id"),
                "full_name": event.get("full_name"),
                "plan_name": event.get("plan_name"),
                "order_id": event.get("order_id"),
                "raw_data": event.get("raw_data") or {},
                "created_at": event.get("created_at"),
            })
            if len(recent_notifications) >= 10:
                break
        expiring_customers = []
        for order in orders:
            if _backend_text(order.get("status")).upper() != "PAID":
                continue
            if order_is_lifetime(order.get("plan_name")):
                continue
            expire_at = order_datetime(order.get("expire_at"))
            if not expire_at:
                continue
            days_remaining = int((expire_at.date() - now.date()).days)
            if 0 <= days_remaining <= 3:
                expiring_customers.append({
                    "order_id": order.get("order_id") or "",
                    "telegram_user_id": order.get("telegram_user_id") or "",
                    "full_name": order.get("full_name") or "",
                    "plan_name": order.get("plan_name") or "",
                    "expire_at": order.get("expire_at") or "",
                    "days_remaining": days_remaining,
                })
            if len(expiring_customers) >= 10:
                break
        health_alerts = []
        health_alerts.append({"title": "Webhook", "detail": "Xem trạng thái ở khối trên", "tone": "good"})
        health_alerts.append({"title": "Bot", "detail": "Sẵn sàng", "tone": "good"})
        health_alerts.append({"title": "Đơn chờ", "detail": f"{pending_order_count} đơn đang chờ", "tone": "warning" if pending_order_count else "good"})
        health_alerts.append({"title": "Sắp hết hạn", "detail": f"{len(expiring_customers)} khách trong khung nhắc", "tone": "warning" if expiring_customers else "good"})
        priority_alerts = []
        if pending_order_count:
            priority_alerts.append({"title": "Đơn đang chờ", "detail": f"{pending_order_count} đơn chưa chốt trạng thái", "tone": "warning"})
        if expiring_customers:
            priority_alerts.append({"title": "Khách sắp hết hạn", "detail": f"{len(expiring_customers)} khách cần nhắc gia hạn", "tone": "warning"})
        return {
            "data": {
                "recent_orders": recent_orders,
                "recent_user_activity": recent_user_activity,
                "recent_notifications": recent_notifications,
                "expiring_customers": expiring_customers,
                "health_alerts": health_alerts[:5],
                "priority_alerts": priority_alerts[:4],
                "trend_points": overview_trend[:10],
                "counts": {
                    "orders": len(orders),
                    "paid_orders": paid_order_count,
                    "pending_orders": pending_order_count,
                    "support_events": len(support_events),
                    "activity_events": len(activity_events),
                },
            }
        }
    except Exception as exc:
        print(f"⚠️ Không dựng được dashboard overview: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được dashboard overview: {exc}")


@app.get("/admin-api/marketing-stats", dependencies=[Depends(require_admin)])
async def admin_marketing_stats(range: str = "month"):
    try:
        safe_range = range if range in {"today", "7d", "month", "year"} else "month"
        latest_updated_at = supabase_store.latest_order_updated_at() or ""
        cache_key = f"{safe_range}:{latest_updated_at}"
        cached = _marketing_stats_cache.get(cache_key)
        now_ts = time.time()
        if cached and cached.get("expires_at", 0) > now_ts:
            return {"data": cached["payload"]}

        try:
            supabase_store.refresh_marketing_stats_rollups()
        except Exception as exc:
            print(f"⚠️ Không refresh được marketing rollups: {exc}")

        previous_start, current_end = _marketing_range_window(safe_range)
        limit_map = {"today": 400, "7d": 1200, "month": 2200, "year": 5000}
        orders = supabase_store.list_orders(limit=limit_map[safe_range], created_at_gte=previous_start.isoformat(), created_at_lt=current_end.isoformat())
        payload = build_marketing_stats_response(orders, tz=_backend_timezone(), period=safe_range)
        _marketing_stats_cache[cache_key] = {"expires_at": now_ts + _marketing_stats_cache_ttl_seconds, "payload": payload}
        return {"data": payload}
    except Exception as exc:
        print(f"⚠️ Không dựng được marketing stats: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được marketing stats: {exc}")


@app.get("/admin-api/notifications", dependencies=[Depends(require_admin)])
async def admin_notifications(limit: int = 20):
    try:
        safe_limit = max(1, min(100, int(limit or 20)))
        rows = supabase_store.list_support_events(limit=min(100, max(50, safe_limit * 4)))
        notifications = []
        order_count = 0
        message_count = 0
        for event in rows:
            item = admin_notification_from_support_event(event)
            if not item:
                continue
            notifications.append(item)
            if item["kind"] == "order":
                order_count += 1
            else:
                message_count += 1
            if len(notifications) >= safe_limit:
                break
        return {
            "data": {
                "notifications": notifications,
                "counts": {
                    "total": len(notifications),
                    "orders": order_count,
                    "messages": message_count,
                },
            }
        }
    except Exception as exc:
        print(f"⚠️ Không dựng được admin notifications: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được admin notifications: {exc}")


@app.patch("/admin-api/orders/{order_id}", dependencies=[Depends(require_admin)])
async def admin_update_order(order_id: str, request: Request):
    body = await request.json()
    data = supabase_store.update_order_fields(order_id, body)
    return {"data": data}


@app.delete("/admin-api/orders/{order_id}", dependencies=[Depends(require_admin)])
async def admin_delete_order(order_id: str):
    order = supabase_store.get_order(order_id)
    if not order:
        return {"data": []}
    data = supabase_store.delete_order(order_id)
    try:
        plan_label = display_plan_name(order.get("plan_name"), order.get("telegram_user_id"))
        supabase_store.record_support_event(
            "order_deleted",
            order.get("telegram_user_id"),
            full_name=order.get("full_name"),
            order_id=order_id,
            plan_name=plan_label,
            raw_data={
                "plan_name_raw": order.get("plan_name"),
                "amount": order.get("amount"),
                "status": order.get("status"),
                "note": order.get("note"),
                "payment_provider": order.get("payment_provider"),
                "payment_currency": order.get("payment_currency"),
                "deleted_at": datetime.now(tz=backend_timezone()).isoformat(timespec="seconds"),
            },
        )
    except Exception as exc:
        if not is_missing_supabase_table_error(exc, "support_events"):
            print(f"⚠️ Không ghi được order_deleted: {exc}")
    return {"data": data}


@app.post("/admin-api/manual-orders", dependencies=[Depends(require_admin)])
async def admin_create_manual_order(request: Request):
    result = await build_manual_order_result(await request.json())
    return {"data": result}

@app.post("/admin-api/manual-orders/gen-act", dependencies=[Depends(require_admin)])
async def admin_generate_manual_active_code(request: Request):
    timing_enabled = str(os.getenv("MANUAL_ORDER_TIMING_LOG", "1")).strip().lower() not in {"0", "false", "off", "no"}
    timing_started_at = time.perf_counter()
    body = await request.json()
    order_id = str(body.get("order_id", "")).strip()
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    plan_name = str(body.get("plan_name", "")).strip()
    expire_at_str = str(body.get("expire_at", "")).strip()
    expire_at_iso = str(body.get("expire_at_iso", "")).strip()

    if not order_id or not telegram_user_id or not plan_name:
        raise HTTPException(status_code=400, detail="Thiếu thông tin đơn hàng.")

    activation_code = generate_activation_code()
    activation_url = build_manual_activation_url(activation_code)

    try:
        write_started_at = time.perf_counter()
        supabase_store.create_order_activation_code(
            code=activation_code,
            order_id=order_id,
            telegram_user_id=telegram_user_id,
            full_name=full_name or telegram_user_id,
            plan_name=plan_name,
            expire_at=expire_at_iso or expire_at_str,
            activation_url=activation_url,
            raw_data={
                "manual_order": True,
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "plan_name": plan_name,
                "expire_at": expire_at_iso or expire_at_str,
            },
        )
    except Exception as exc:
        if not (is_missing_supabase_table_error(exc, "order_activation_codes") or is_missing_supabase_runtime_error(exc)):
            raise
        print(f"⚠️ Bỏ qua lưu activation code vì thiếu bảng/env Supabase: {exc}")
    if timing_enabled:
        print(f"[manual-order-timing] gen_active_code order_id={order_id} supabase_write_ms={((time.perf_counter() - write_started_at) * 1000):.1f}")

    message_template = str(safe_db_config(
        "MANUAL_ORDER_MESSAGE_TEMPLATE",
        "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}",
    ) or "").strip()

    order_text = render_manual_order_info_text({
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
    })

    manual_order_text = render_manual_order_message_text(message_template, {
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
        "order_text": order_text,
        "success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {}),
        "bot_link_title": render_activation_text("MANUAL_ORDER_LINK_TITLE", "🔗 Active code", {}),
        "bot_link_subtitle": render_activation_text("MANUAL_ORDER_LINK_SUBTITLE", "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", {}),
        "activation_url": activation_url,
        "message_url": build_manual_order_message_url(activation_code),
        "links_text": "",
        "support_text": "",
        "support_group_name": safe_support_group_name(),
        "support_link": "",
        "support_error": "",
        "activation_code": activation_code,
    })
    if timing_enabled:
        print(f"[manual-order-timing] gen_active_code order_id={order_id} render_ms={((time.perf_counter() - timing_started_at) * 1000):.1f}")

    return {
        "data": {
            "activation_code": activation_code,
            "activation_url": activation_url,
            "manual_order_message_url": build_manual_order_message_url(activation_code),
            "manual_order_text": manual_order_text,
        }
    }

@app.post("/admin-api/manual-orders/gen-join", dependencies=[Depends(require_admin)])
async def admin_generate_manual_join_link(request: Request):
    body = await request.json()
    order_id = str(body.get("order_id", "")).strip()
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    plan_name = str(body.get("plan_name", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    expire_at_str = str(body.get("expire_at", "")).strip()
    activation_code = str(body.get("activation_code", "")).strip()
    
    if not order_id or not telegram_user_id or not plan_name:
        raise HTTPException(status_code=400, detail="Thiếu thông tin đơn hàng để tạo link (order_id, telegram_user_id, plan_name).")
        
    try:
        user_id = int(telegram_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Telegram ID phải là số.")
        
    from modules.mod_coupon import build_invite_links

    try:
        support_link, support_error = await _maybe_await(create_support_invite_link(user_id))
    except Exception as exc:
        if not (is_missing_supabase_table_error(exc, "support_events") or is_missing_supabase_runtime_error(exc)):
            raise
        print(f"⚠️ Bỏ qua tạo support link vì thiếu bảng/env Supabase: {exc}")
        support_link, support_error = None, ""
    links_text = ""
    group_names = []
    failed_groups = []
    invite_results = []
    try:
        links_text, group_names, failed_groups, invite_results = await build_invite_links(user_id, plan_name)
    except Exception as exc:
        if not is_missing_supabase_runtime_error(exc):
            print(f"⚠️ Không build được join links cho manual order {order_id}: {exc}")
        
    if support_link:
        support_text = render_manual_order_support_text("💬 {support_group_name}:\n{support_link}", {
            "order_id": order_id,
            "telegram_user_id": telegram_user_id,
            "full_name": full_name,
            "plan_name": plan_name,
            "expire_at": expire_at_str,
            "support_group_name": safe_support_group_name(),
            "support_link": support_link,
            "support_error": "",
        })
    elif support_error:
        support_text = render_activation_text(
            "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
            "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
            {
                "support_group_name": safe_support_group_name(),
                "support_error": support_error,
            },
        )
    else:
        support_text = ""
        
    order_text = render_manual_order_info_text({
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
    })
    
    activation_url = build_manual_activation_url(activation_code)
    manual_order_join_text = build_manual_order_delivery_text({
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
        "links_text": links_text,
        "partial_text": "" if not failed_groups else render_activation_text(
            "MANUAL_ORDER_LINK_PARTIAL_TEXT",
            "⚠️ Một số nhóm chưa tạo được link: {failed_groups}",
            {"failed_groups": ", ".join(failed_groups)},
        ),
        "support_text": support_text,
        "support_group_name": safe_support_group_name(),
        "support_link": support_link,
        "support_error": support_error,
        "activation_code": activation_code,
    })
    
    return {
        "data": {
            "links_text": links_text,
            "support_text": support_text,
            "support_link": support_link,
            "support_error": support_error,
            "manual_order_join_text": strip_html_text(manual_order_join_text),
        }
    }


@app.post("/admin-api/licenses/gen-link", dependencies=[Depends(require_admin)])
async def admin_generate_license_link(request: Request):
    body = await request.json()
    license_key = normalize_license_key(body.get("license_key", ""))
    if not license_key:
        raise HTTPException(status_code=400, detail="Thiếu license_key.")
    return {"data": {"license_key": license_key, "activation_url": build_license_activation_url(license_key)}}


@app.post("/admin-api/licenses", dependencies=[Depends(require_admin)])
async def admin_create_license(request: Request):
    body = await request.json()
    license_key = normalize_license_key(body.get("license_key", "") or body.get("license", ""))
    order_id = str(body.get("order_id", "")).strip()
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    plan_code = str(body.get("plan_code", "")).strip().upper()
    if not license_key or not order_id or not telegram_user_id or not plan_code:
        raise HTTPException(status_code=400, detail="Thiếu thông tin license.")
    plan = license_plan_map().get(plan_code)
    if not plan:
        raise HTTPException(status_code=400, detail="plan_code không hợp lệ.")
    data = supabase_store.create_license_record(
        license_key=license_key,
        order_id=order_id,
        telegram_user_id=telegram_user_id,
        full_name=str(body.get("full_name", "")).strip(),
        plan_code=plan_code,
        plan_slug=str(body.get("plan_slug", "")).strip(),
        status=str(body.get("status", "issued")).strip().lower(),
        expires_at=body.get("expires_at") or body.get("ends_at"),
        is_lifetime=bool(body.get("is_lifetime", False)),
        source=str(body.get("source", "web")).strip().lower() or "web",
        activated_at=body.get("activated_at"),
        last_verified_at=body.get("last_verified_at"),
        group_ids=body.get("group_ids") or plan["groups"],
        binding_state=str(body.get("binding_state", "unbound")).strip().lower(),
        raw_data=body.get("raw_data") or {
            "license_plan_code": plan_code,
            "license_plan_slug": body.get("plan_slug", ""),
        },
    )
    return {"data": data}


@app.get("/admin-api/licenses", dependencies=[Depends(require_admin)])
async def admin_list_licenses(limit: int = 200):
    return {"data": supabase_store.list_license_records(limit=limit)}


@app.patch("/admin-api/licenses/{license_key}", dependencies=[Depends(require_admin)])
async def admin_update_license(license_key: str, request: Request):
    body = await request.json()
    return {"data": supabase_store.update_license_record(license_key, body)}


@app.get("/admin-api/license-sessions", dependencies=[Depends(require_admin)])
async def admin_list_license_sessions(limit: int = 200):
    return {"data": supabase_store.list_license_sessions(limit=limit)}


@app.get("/admin-api/license-audits", dependencies=[Depends(require_admin)])
async def admin_list_license_audits(limit: int = 500):
    rows = supabase_store._request(
        "GET",
        "license_audit_events",
        params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
    )
    return {"data": rows}


@app.post("/license/verify")
async def verify_license(request: Request):
    if not license_flow_enabled():
        raise HTTPException(status_code=404, detail="license flow disabled")
    body = await request.json()
    license_key = normalize_license_key(body.get("license_key", ""))
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    signature = str(body.get("signature", "")).strip()
    payload = _license_payload_from_request(body)
    if not license_key or not telegram_user_id:
        raise HTTPException(status_code=400, detail="Missing license_key or telegram_user_id")
    if license_verify_required() and not verify_license_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    record = supabase_store.get_license_record(license_key)
    session_payload = {
        "license_key": license_key,
        "telegram_user_id": telegram_user_id,
        "request_payload": payload,
        "signature_valid": bool(not license_verify_required() or verify_license_signature(payload, signature)),
        "verified_at": datetime.now(tz=backend_timezone()).isoformat(),
        "result_status": "pending" if not record else normalize_license_state(record.get("status") or "issued"),
    }
    try:
        supabase_store.create_license_session(session_payload)
    except Exception as exc:
        print(f"⚠️ Không tạo được license session {license_key}: {exc}")
    if not record:
        try:
            supabase_store.record_license_audit(
                {
                    "license_key": license_key,
                    "telegram_user_id": telegram_user_id,
                    "event_type": "license_verify_pending",
                    "result": "pending",
                    "raw_data": {"request": payload},
                    "created_at": datetime.now(tz=backend_timezone()).isoformat(),
                }
            )
        except Exception:
            pass
        return {"success": True, "data": {"status": "pending", "license_plan_code": "", "license_plan_slug": "", "is_lifetime": False}}
    if record.get("telegram_user_id") and str(record.get("telegram_user_id")) != telegram_user_id:
        try:
            supabase_store.record_license_audit(
                {
                    "license_key": license_key,
                    "telegram_user_id": telegram_user_id,
                    "event_type": "license_verify_redeemed",
                    "result": "redeemed",
                    "raw_data": {"record_user_id": record.get("telegram_user_id")},
                    "created_at": datetime.now(tz=backend_timezone()).isoformat(),
                }
            )
        except Exception:
            pass
        return {"success": True, "data": {"status": "redeemed", "license_plan_code": record.get("plan_code") or "", "license_plan_slug": record.get("plan_slug") or "", "is_lifetime": bool(record.get("is_lifetime")), "telegram_user_id": record.get("telegram_user_id")}}
    now_iso = datetime.now(tz=backend_timezone()).isoformat()
    data = {
        "license_plan_code": record.get("plan_code") or "",
        "license_plan_slug": record.get("plan_slug") or "",
        "status": normalize_license_state(record.get("status") or "issued"),
        "starts_at": record.get("activated_at") or now_iso,
        "ends_at": record.get("expires_at") or "",
        "is_lifetime": bool(record.get("is_lifetime")),
    }
    try:
        supabase_store.update_license_record(
            license_key,
            {
                "last_verified_at": now_iso,
                "status": "active" if data["status"] in {"issued", "redeemed", "active"} else data["status"],
                "telegram_user_id": telegram_user_id,
            },
        )
    except Exception as exc:
        print(f"⚠️ Không cập nhật last_verified_at cho license {license_key}: {exc}")
    try:
        supabase_store.record_license_audit(
            {
                "license_key": license_key,
                "telegram_user_id": telegram_user_id,
                "event_type": "license_verify_success",
                "result": data["status"],
                "plan_code": data["license_plan_code"],
                "raw_data": data,
                "created_at": now_iso,
            }
        )
    except Exception:
        pass
    return {"success": True, "data": data}


@app.post("/license-delivery")
@app.post("/api/license-delivery")
async def license_delivery(request: Request):
    if not license_flow_enabled():
        raise HTTPException(status_code=503, detail="license flow disabled")
    body = await request.json()
    telegram_user_id = str(body.get("telegramUserId") or "").strip()
    order_id = str(body.get("orderId") or "").strip()
    bot_order_id = str(
        body.get("botOrderId")
        or body.get("sourceOrderId")
        or body.get("paymentSessionId")
        or ""
    ).strip()
    plan_code = str(body.get("planCode") or "").strip().upper()
    vip_plan_code = str(body.get("vipPlanCode") or body.get("requestedPlanCode") or "").strip().upper()
    plan_name = str(body.get("planName") or "").strip() or plan_code
    license_code = str(body.get("licenseCode") or "").strip().upper()
    expires_at = str(body.get("expiresAt") or "").strip()
    activation_url = str(body.get("activationUrl") or "").strip()
    timestamp = body.get("timestamp")
    nonce = str(body.get("nonce") or "").strip()
    signature = str(body.get("signature") or "").strip()

    # Bot-authoritative payment callback: the web only confirms payment. The
    # original bot order remains the sole source of plan, expiry and groups.
    integration_source = str(body.get("integrationSource") or "").strip().lower()
    is_bot_authoritative_callback = bool(bot_order_id) and (
        integration_source == "bot_checkout"
        or integration_source == "prive_bot"
        or integration_source.startswith("bot_")
        or integration_source.startswith("prive_bot_")
    )
    is_payment_status_callback = str(body.get("status") or "").strip().upper() == "PAID" and not plan_code and not license_code
    if is_payment_status_callback or is_bot_authoritative_callback:
        return await _handle_bot_payment_status(body)

    if not telegram_user_id or not order_id or not plan_code or not license_code:
        raise HTTPException(status_code=400, detail="Missing delivery fields")
    if not timestamp or not nonce or not signature:
        raise HTTPException(status_code=400, detail="Missing signature fields")
    if not _verify_bot_delivery_signature(body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if bot_order_id and getattr(supabase_store, "enabled", False):
        try:
            bot_order = supabase_store.get_order(bot_order_id) or {}
            source_metadata = dict(bot_order.get("metadata") or {})
            vip_plan_code = str(
                vip_plan_code
                or source_metadata.get("vipPlanCode")
                or source_metadata.get("requestedPlanCode")
                or source_metadata.get("plan_code")
                or bot_order.get("plan_code")
                or bot_order.get("plan_name")
                or ""
            ).strip().upper()
            bot_metadata = dict(bot_order.get("metadata") or {})
            bot_metadata["web_delivery_claimed_at"] = _now_iso()
            bot_metadata["web_order_id"] = order_id
            bot_metadata["web_order_number"] = str(body.get("orderNumber") or "")
            supabase_store.patch_order(bot_order_id, {"metadata": bot_metadata})
            supabase_store.mark_order_paid(bot_order_id, _now_iso(), None)
            print(f"[license-delivery] bot_order_paid botOrderId={bot_order_id} webOrderId={order_id}")
        except Exception as exc:
            print(f"[license-delivery] bot_order_paid_failed botOrderId={bot_order_id} webOrderId={order_id} error={exc}")

    snapshot_fields = {
        "planCode": plan_code or "n/a",
        "checkoutKind": str(body.get("checkoutKind") or "").strip() or "n/a",
        "paymentSessionId": str(body.get("paymentSessionId") or "").strip() or "n/a",
        "paymentProvider": str(body.get("paymentProvider") or "").strip() or "n/a",
        "locale": str(body.get("locale") or "").strip() or "n/a",
        "currency": str(body.get("currency") or "").strip().upper() or "n/a",
        "source": str(body.get("source") or "").strip() or "n/a",
        "integrationSource": str(body.get("integrationSource") or "").strip() or "n/a",
        "botOrderId": bot_order_id or "n/a",
        "correlationId": str(body.get("correlationId") or (f"bot:{bot_order_id}" if bot_order_id else "n/a")),
        "vipPlanCode": vip_plan_code or "n/a",
    }

    def build_delivery_snapshot_log(fields: dict[str, str]) -> str:
        ordered_keys = ["planCode", "checkoutKind", "paymentSessionId", "paymentProvider", "locale", "currency", "source", "integrationSource"]
        return (
            "📦 license_delivery snapshot "
            f"orderId={order_id} "
            f"botOrderId={fields.get('botOrderId', 'n/a')} "
            f"correlationId={fields.get('correlationId', 'n/a')} "
            f"vipPlanCode={fields.get('vipPlanCode', 'n/a')} "
            f"telegramUserId={telegram_user_id or 'n/a'} "
            f"licenseCode={license_code or 'n/a'} "
            + " ".join(f"{key}={fields.get(key, 'n/a')}" for key in ordered_keys)
        )

    print(build_delivery_snapshot_log(snapshot_fields))

    if getattr(supabase_store, "enabled", False):
        try:
            existing_order = supabase_store.get_order(order_id)
            existing_meta = dict(existing_order.get("metadata") or {}) if existing_order else {}
            if existing_meta.get("bot_delivery_notified_at") or (existing_order or {}).get("bot_delivery_notified_at"):
                return {
                    "success": True,
                    "duplicate": True,
                    "data": {
                        "order_id": order_id,
                        "telegram_user_id": telegram_user_id,
                        "plan_code": plan_code,
                        "license_code": license_code,
                    },
                }
        except Exception as exc:
            print(f"⚠️ Cannot inspect delivery idempotency for order {order_id}: {exc}")

    from modules.mod_coupon import build_invite_links

    group_text = ""
    group_names = ""
    failed_groups: list[str] = []
    invite_results = []
    try:
        group_text, group_names, failed_groups, invite_results = await build_invite_links(telegram_user_id, vip_plan_code or plan_code)
    except Exception as exc:
        print(f"⚠️ Cannot build invite links for order {order_id}: {exc}")

    shown_expiry = expires_at.replace("T", " ").replace("+00:00", "") if expires_at else "Đang hoạt động"
    from delivery_message import build_delivery_message

    locale = str(body.get("locale") or "vi").strip().lower()
    status_links = ""
    if group_names:
        status_links += f"👥 {group_names}\n\n"
    if group_text:
        status_links += group_text.strip()
    if failed_groups and not group_text:
        status_links = "⚠️ No invitation link is available yet." if locale.startswith("en") else "⚠️ Chưa có link tham gia, vui lòng thử lại sau."

    final_delivery_text = build_delivery_message(
        locale=locale,
        plan_name=display_plan_name(plan_name, telegram_user_id),
        expires_at=shown_expiry,
        license_code=license_code,
        links=status_links,
        support_name="support group" if locale.startswith("en") else "nhóm hỗ trợ",
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    keyboard = InlineKeyboardBuilder()
    try:
        await add_support_join_button(keyboard, int(telegram_user_id))
    except Exception as exc:
        print(f"⚠️ Cannot add support button for order {order_id}: {exc}")
    keyboard.row(InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_main"))

    try:
        await bot.send_message(
            chat_id=int(telegram_user_id),
            text=final_delivery_text,
            parse_mode="HTML",
            reply_markup=keyboard.as_markup(),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to notify telegram user: {exc}")

    if getattr(supabase_store, "enabled", False):
        try:
            existing_order = supabase_store.get_order(bot_order_id or order_id)
            existing_meta = dict(existing_order.get("metadata") or {}) if existing_order else {}
            notified_at = _now_iso()
            existing_meta["bot_delivery_notified_at"] = notified_at
            supabase_store.patch_order(bot_order_id or order_id, {
                "metadata": existing_meta,
            })
        except Exception as exc:
            print(f"⚠️ Cannot persist bot delivery notification for order {order_id}: {exc}")

    try:
        supabase_store.record_support_event(
            "license_delivery_notified",
            telegram_user_id,
            order_id=order_id,
            plan_name=plan_name,
            raw_data={
                "license_code": license_code,
                "activation_url": activation_url,
                "group_names": group_names,
                "failed_groups": failed_groups,
                "invite_results": invite_results,
            },
        )
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "order_id": order_id,
            "telegram_user_id": telegram_user_id,
            "plan_code": plan_code,
            "license_code": license_code,
            "group_names": group_names,
            "failed_groups": failed_groups,
            "duplicate": False,
        },
    }


@app.get("/admin-api/users", dependencies=[Depends(require_admin)])
async def admin_users(limit: int = 200):
    return {"data": supabase_store.list_users(limit=limit)}


@app.get("/admin-api/customers/search", dependencies=[Depends(require_admin)])
async def admin_customer_search(q: str = "", limit: int = 30):
    query = str(q or "").strip()
    if len(query) < 2:
        return {"data": []}
    return {"data": build_customer_search_summary(query, limit=limit)}


@app.get("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_config():
    rows = canonicalize_config_rows(supabase_store.get_config())
    img_me_row = None
    for row in rows or []:
        if canonical_config_key(row.get("key")) == "MANUAL_ORDER_LINK_TEMPLATE":
            row["value"] = normalize_manual_order_link_template(row.get("value"))
        if canonical_config_key(row.get("key")) == "MANUAL_ORDER_JOIN_TEMPLATE":
            row["value"] = normalize_manual_order_join_template(row.get("value"))
        if canonical_config_key(row.get("key")) == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
            row["value"] = normalize_manual_order_link_template(row.get("value"))
        if canonical_config_key(row.get("key")) == "IMG_ME":
            img_me_row = row
    if img_me_row is not None:
        ok, _reason = await _validate_img_me_value(img_me_row.get("value", ""))
        if not ok:
            supabase_store.delete_config("IMG_ME")
            db.cache_config.pop("IMG_ME", None)
            img_me_row["value"] = ""
    return {"data": rows}


@app.get("/admin-api/payment-schema", dependencies=[Depends(require_admin)])
async def admin_payment_schema():
    def _field(key: str, label: str, placeholder: str, help_text: str, kind: str = "input", options=None):
        item = {
            "key": key,
            "label": label,
            "placeholder": placeholder,
            "help": help_text,
        }
        if kind:
            item["kind"] = kind
        if options is not None:
            item["options"] = options
        return item

    rails = []
    for provider in payment_manager.supported_providers():
        schema = payment_manager.provider_schema(provider)
        label = {
            "PAYOS": "PayOS / VietQR",
            "PAYPAL": "PayPal",
            "CREEM": "Creem",
            "NOWPAYMENTS": "NOWPayments",
            "TRON_USDT": "USDT TRC20",
            "BINANCE_PAY": "Binance Pay",
        }.get(provider, provider)
        rails.append(
            {
                "provider": provider,
                "kind": "rail",
                "enabledKey": schema.get("enabled_key", ""),
                "enabledDefault": schema.get("enabled_default", "OFF"),
                "currency": schema.get("currency") or "",
                "priority": schema.get("priority", 999),
                "fields": [
                    _field(
                        schema.get("enabled_key", ""),
                        f"Bật {label}",
                        schema.get("enabled_default", "OFF"),
                        f"Bật/tắt cổng {label}.",
                        "select",
                        [{"label": "Bật", "value": "ON"}, {"label": "Tắt", "value": "OFF"}],
                    )
                ],
            }
        )

    actions = [
        {
            "provider": "WEB",
            "kind": "action",
            "enabledKey": PAYMENT_PROVIDER_SCHEMA["WEB"]["enabled_key"],
            "enabledDefault": PAYMENT_PROVIDER_SCHEMA["WEB"]["enabled_default"],
            "currency": "",
            "priority": PAYMENT_PROVIDER_SCHEMA["WEB"]["priority"],
            "fields": [
                _field(
                    "WEB_PAYMENT_ENABLED",
                    "Bật thanh toán web",
                    "OFF",
                    "Bật ON để bot hiển thị nút thanh toán web riêng và gọi sang Hangcu_web để lấy checkout link.",
                    "select",
                    [{"label": "Bật", "value": "ON"}, {"label": "Tắt", "value": "OFF"}],
                ),
                _field(
                    "WEB_PAYMENT_SECRET",
                    "Secret gọi web checkout",
                    "shared-secret",
                    "Secret dùng để ký request checkout gửi sang web. Nên khớp với WEB_PAYMENT_SECRET bên web.",
                ),
                _field(
                    "WEB_PAYMENT_LABEL_VI",
                    "Nhãn nút web (VI)",
                    "🌐 Thanh toán web",
                    "Nhãn hiển thị cho người dùng tiếng Việt trên nút web checkout.",
                ),
                _field(
                    "WEB_PAYMENT_LABEL_EN",
                    "Nhãn nút web (EN)",
                    "🌐 Web checkout",
                    "Nhãn hiển thị cho người dùng tiếng Anh trên nút web checkout.",
                ),
                _field("MANUAL_PAYMENT_ENABLED", "Bật chuyển khoản thủ công", "OFF", "Hiển thị action liên hệ admin để hướng dẫn chuyển khoản.", "select", [{"label": "Bật", "value": "ON"}, {"label": "Tắt", "value": "OFF"}]),
                _field("MANUAL_PAYMENT_LABEL_VI", "Nhãn nút chuyển khoản (VI)", "💬 Chuyển khoản / Liên hệ admin", "Nhãn nút liên hệ admin trong giao diện tiếng Việt."),
                _field("MANUAL_PAYMENT_LABEL_EN", "Manual transfer button (EN)", "💬 Contact admin", "Button label shown in English."),
                _field("MANUAL_PAYMENT_MESSAGE_VI", "Nội dung hướng dẫn chuyển khoản (VI)", "", "Tin nhắn gửi trước nút liên hệ admin."),
                _field("MANUAL_PAYMENT_MESSAGE_EN", "Manual transfer instructions (EN)", "", "Message shown before the contact button."),
                _field("MANUAL_SUPPORT_CONTACT_URL", "Link liên hệ admin (VI)", "https://t.me/...", "Có thể dùng {payload} để đính kèm thông tin gói/đơn."),
                _field("MANUAL_SUPPORT_CONTACT_URL_EN", "Admin contact link (EN)", "https://t.me/...", "Use {payload} to include order context."),
            ],
        }
    ]

    provider_options = [
        {"label": {
            "PAYOS": "PayOS / VietQR",
            "PAYPAL": "PayPal",
            "CREEM": "Creem",
            "NOWPAYMENTS": "NOWPayments",
            "TRON_USDT": "USDT TRC20",
            "BINANCE_PAY": "Binance Pay",
        }.get(provider, provider), "value": provider}
        for provider in payment_manager.supported_providers()
    ]
    routing = [
        {
            "key": "PAYMENT_PROVIDERS_VI",
            "label": "Cổng cho tiếng Việt",
            "kind": "multiselect",
            "options": provider_options,
            "help": "Chỉ chọn cổng thật muốn hiển thị cho người dùng tiếng Việt. Có thể gồm cổng USD như Creem/PayPal.",
        },
        {
            "key": "PAYMENT_PROVIDERS_EN",
            "label": "Providers for English",
            "kind": "multiselect",
            "options": provider_options,
            "help": "Only selected payment rails are shown to English users.",
        },
        {
            "key": "PAYMENT_PROVIDER_VI",
            "label": "Cổng mặc định tiếng Việt",
            "kind": "select",
            "options": provider_options,
            "help": "Cổng mặc định phải nằm trong danh sách tiếng Việt và đang bật.",
        },
        {
            "key": "PAYMENT_PROVIDER_EN",
            "label": "Default English provider",
            "kind": "select",
            "options": provider_options,
            "help": "The default provider must be enabled and included in the English list.",
        },
    ]

    return {
        "data": {
            "rails": rails,
            "actions": actions,
            "routing": routing,
        }
    }


@app.patch("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_set_config(key: str, request: Request):
    body = await request.json()
    normalized_key = canonical_config_key(key)
    value = body.get("value", "")
    if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
        value = normalize_manual_order_link_template(value)
    if normalized_key == "MANUAL_ORDER_JOIN_TEMPLATE":
        value = normalize_manual_order_join_template(value)
    if normalized_key == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
        value = normalize_manual_order_link_template(value)
    if normalized_key == "IMG_ME":
        ok, _reason = await _validate_img_me_value(value)
        if not ok:
            value = ""
    data = supabase_store.set_configs(config_write_items(normalized_key, value))
    for row in data or []:
        row_key = canonical_config_key(row.get("key"))
        if row_key:
            db.cache_config[row_key] = str(row.get("value") or "")
        if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_") or normalized_key.startswith("BOT_MENU_"):
            await set_commands()
    refresh_auto_payment_schedule_if_needed([normalized_key])
    return {"data": data}


@app.post("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_set_config_batch(request: Request):
    body = await request.json()
    items = body.get("items", body if isinstance(body, list) else [])
    normalized_items = []
    expanded_items = []
    for item in items:
        normalized_item = dict(item)
        normalized_key = canonical_config_key(normalized_item.get("key"))
        if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
            normalized_item["value"] = normalize_manual_order_link_template(normalized_item.get("value", ""))
        if normalized_key == "MANUAL_ORDER_JOIN_TEMPLATE":
            normalized_item["value"] = normalize_manual_order_join_template(normalized_item.get("value", ""))
        if normalized_key == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
            normalized_item["value"] = normalize_manual_order_link_template(normalized_item.get("value", ""))
        if normalized_key == "IMG_ME":
            ok, _reason = await _validate_img_me_value(normalized_item.get("value", ""))
            if not ok:
                normalized_item["value"] = ""
        normalized_items.append(normalized_item)
        expanded_items.extend(config_write_items(normalized_key, normalized_item.get("value", "")))
    deduped_items = list({str(item.get("key") or "").strip().upper(): item for item in expanded_items if str(item.get("key") or "").strip()}.values())
    data = supabase_store.set_configs(deduped_items)
    command_changed = False
    auto_payment_keys = []
    for item in normalized_items:
        normalized_key = canonical_config_key(item.get("key"))
        if not normalized_key:
            continue
        db.cache_config[normalized_key] = str(item.get("value", ""))
        if auto_payment_config_key(normalized_key):
            auto_payment_keys.append(normalized_key)
        if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_") or normalized_key.startswith("BOT_MENU_"):
            command_changed = True
    if command_changed:
        await set_commands()
    refresh_auto_payment_schedule_if_needed(auto_payment_keys)
    return {"data": data}


@app.delete("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_delete_config(key: str):
    lookup_keys = config_lookup_keys(key)
    data = []
    for item_key in lookup_keys:
        try:
            data.extend(supabase_store.delete_config(item_key) or [])
        except Exception:
            pass
    for item_key in lookup_keys:
        db.cache_config.pop(str(item_key).strip().upper(), None)
    refresh_auto_payment_schedule_if_needed(lookup_keys)
    return {"data": data}


@app.get("/admin-api/menu-pages", dependencies=[Depends(require_admin)])
async def admin_menu_pages():
    return {"data": supabase_store.list_menu_pages()}


@app.patch("/admin-api/menu-pages/{page_id}", dependencies=[Depends(require_admin)])
async def admin_set_menu_page(page_id: str, request: Request):
    body = await request.json()
    data = supabase_store.upsert_menu_page(
        page_id=page_id,
        image_url=body.get("image_url", ""),
        body=body.get("body", ""),
        layout=body.get("layout", ""),
    )
    db.reload_config(force=False)
    return {"data": data}


@app.delete("/admin-api/menu-pages/{page_id}", dependencies=[Depends(require_admin)])
async def admin_delete_menu_page(page_id: str):
    data = supabase_store.delete_menu_page(page_id)
    db.reload_config(force=False)
    return {"data": data}


@app.get("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_sale_rules():
    return {"data": supabase_store.list_sale_rules()}


@app.post("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_upsert_sale_rule(request: Request):
    body = await request.json()
    data = supabase_store.upsert_sale_rule(body)
    db.reload_config(force=False)
    return {"data": data}


@app.delete("/admin-api/sale-rules/{sale_id}", dependencies=[Depends(require_admin)])
async def admin_delete_sale_rule(sale_id: str):
    data = supabase_store.delete_sale_rule(sale_id)
    db.reload_config(force=False)
    return {"data": data}


@app.get("/admin-api/coupons", dependencies=[Depends(require_admin)])
async def admin_coupons():
    return {"data": supabase_store.list_coupons()}


@app.post("/admin-api/coupons", dependencies=[Depends(require_admin)])
async def admin_create_coupon(request: Request):
    body = await request.json()
    return {"data": supabase_store.create_coupon_from_sheet_row(body)}


@app.post("/admin-api/coupons/bulk", dependencies=[Depends(require_admin)])
async def admin_create_coupons_bulk(request: Request):
    body = await request.json()
    rows = body.get("items") if isinstance(body, dict) else body
    return {"data": supabase_store.create_coupons_from_sheet_rows(rows or [])}


@app.delete("/admin-api/coupons/{code}", dependencies=[Depends(require_admin)])
async def admin_delete_coupon(code: str):
    return {"data": supabase_store.delete_coupon(code)}


@app.get("/admin-api/hidden-groups", dependencies=[Depends(require_admin)])
async def admin_hidden_groups():
    return {"data": list_hidden_groups(include_inactive=True)}


@app.post("/admin-api/hidden-groups", dependencies=[Depends(require_admin)])
async def admin_upsert_hidden_group(request: Request):
    body = await request.json()
    try:
        return {"data": upsert_hidden_group(body)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/admin-api/hidden-groups/{hidden_group_id}", dependencies=[Depends(require_admin)])
async def admin_delete_hidden_group(hidden_group_id: str):
    return {"data": delete_hidden_group(hidden_group_id)}


@app.get("/admin-api/hidden-codes", dependencies=[Depends(require_admin)])
async def admin_hidden_codes():
    return {"data": list_hidden_codes(include_inactive=True)}


@app.post("/admin-api/hidden-codes", dependencies=[Depends(require_admin)])
async def admin_upsert_hidden_code(request: Request):
    body = await request.json()
    try:
        return {"data": upsert_hidden_code(body)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/admin-api/hidden-codes/{code}", dependencies=[Depends(require_admin)])
async def admin_delete_hidden_code(code: str):
    return {"data": delete_hidden_code(code)}


@app.get("/admin-api/hidden-redemptions", dependencies=[Depends(require_admin)])
async def admin_hidden_redemptions(limit: int = 500):
    return {"data": list_hidden_redemptions(limit=limit)}


@app.get("/admin-api/activation-codes", dependencies=[Depends(require_admin)])
async def admin_activation_codes(limit: int = 500):
    try:
        return {"data": supabase_store.list_order_activation_codes(limit=limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "order_activation_codes"):
            warn_missing_table_once("order_activation_codes", exc)
        else:
            print(f"⚠️ Không đọc được order_activation_codes: {exc}")
        return {"data": []}


@app.patch("/admin-api/activation-codes/{code}", dependencies=[Depends(require_admin)])
async def admin_update_activation_code(code: str, request: Request):
    body = await request.json()
    try:
        return {"data": supabase_store.update_order_activation_code(code, body)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "order_activation_codes"):
            warn_missing_table_once("order_activation_codes", exc)
            raise HTTPException(status_code=503, detail="order_activation_codes table is missing")
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/admin-api/activation-codes/{code}", dependencies=[Depends(require_admin)])
async def admin_delete_activation_code(code: str):
    return {"data": supabase_store.delete_order_activation_code(code)}


@app.post("/admin-api/activation-codes/{code}/regenerate", dependencies=[Depends(require_admin)])
async def admin_regenerate_activation_code(code: str):
    current = supabase_store.get_order_activation_code(code)
    if not current:
        raise HTTPException(status_code=404, detail="Activation code not found")

    next_code = generate_activation_code()
    while supabase_store.get_order_activation_code(next_code):
        next_code = generate_activation_code()
    next_url = build_manual_activation_url(next_code)
    try:
        data = supabase_store.regenerate_order_activation_code(code, new_code=next_code, activation_url=next_url)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "order_activation_codes"):
            warn_missing_table_once("order_activation_codes", exc)
            raise HTTPException(status_code=503, detail="order_activation_codes table is missing")
        raise HTTPException(status_code=500, detail=str(exc))
    return {"data": data}


@app.get("/admin-api/blacklist", dependencies=[Depends(require_admin)])
async def admin_blacklist(limit: int = 500):
    try:
        return {"data": supabase_store.list_blacklist(limit=limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "security_blacklist"):
            warn_missing_table_once("security_blacklist", exc)
        else:
            print(f"⚠️ Không đọc được security_blacklist: {exc}")
        return {"data": []}


@app.post("/admin-api/blacklist", dependencies=[Depends(require_admin)])
async def admin_upsert_blacklist(request: Request):
    body = await request.json()
    return {"data": supabase_store.upsert_blacklist(body)}


@app.delete("/admin-api/blacklist/{telegram_user_id}", dependencies=[Depends(require_admin)])
async def admin_delete_blacklist(telegram_user_id: str):
    return {"data": supabase_store.delete_blacklist(telegram_user_id)}


@app.get("/admin-api/support-events", dependencies=[Depends(require_admin)])
async def admin_support_events(limit: int = 1000, updated_after: str | None = None):
    try:
        safe_limit = max(1, min(int(limit or 1000), 2000))
        return {"data": supabase_store.list_support_events(limit=safe_limit, updated_after=updated_after)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_events"):
            warn_missing_table_once("support_events", exc)
        else:
            print(f"⚠️ Không đọc được support_events: {exc}")
        return {"data": []}


@app.get("/admin-api/customer-identity-history/{telegram_user_id}", dependencies=[Depends(require_admin)])
async def admin_customer_identity_history(telegram_user_id: str, limit: int = 50):
    try:
        safe_limit = max(1, min(int(limit or 50), 500))
        return {"data": supabase_store.get_customer_identity_history(telegram_user_id, limit=safe_limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "customer_identity_history"):
            warn_missing_table_once("customer_identity_history", exc)
        else:
            print(f"⚠️ Không đọc được customer_identity_history: {exc}")
        return {"data": []}


@app.get("/admin-api/support-cases", dependencies=[Depends(require_admin)])
async def admin_support_cases(query: str = "", limit: int = 20, status: str = "", message_limit: int = 20, updated_after: str | None = None):
    try:
        safe_limit = max(1, min(int(limit or 20), 50))
        safe_message_limit = max(1, min(int(message_limit or 20), 200))
        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"open", "closed"}:
            normalized_status = ""
        rows = (
            supabase_store.search_support_tickets(query, limit=safe_limit)
            if str(query or "").strip()
            else supabase_store.list_support_tickets(limit=safe_limit, status=normalized_status or None, updated_after=updated_after)
        )
        if normalized_status and str(query or "").strip():
            rows = [row for row in rows if str(row.get("status") or "").strip().lower() == normalized_status]
        message_rows = supabase_store.list_support_messages_for_tickets(
            [row.get("id") for row in rows],
            limit=safe_message_limit,
        )
        messages_by_ticket = {}
        for message in message_rows:
            messages_by_ticket.setdefault(str(message.get("ticket_id") or ""), []).append(message)
        data = [
            {"ticket": row, "messages": messages_by_ticket.get(str(row.get("id") or ""), [])[-safe_message_limit:]}
            for row in rows
        ]
        return {"data": data}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_tickets"):
            warn_missing_table_once("support_tickets", exc)
        else:
            print(f"⚠️ Không đọc được support cases: {exc}")
        return {"data": []}


@app.patch("/admin-api/support-cases/{ticket_id}", dependencies=[Depends(require_admin)])
async def admin_update_support_case(ticket_id: str, request: Request):
    body = await request.json()
    status = str(body.get("status") or "").strip().lower()
    if status not in {"open", "closed"}:
        raise HTTPException(status_code=400, detail="Trạng thái ticket không hợp lệ.")
    payload = {
        "status": status,
        "updated_at": datetime.now().isoformat(),
        "closed_at": datetime.now().isoformat() if status == "closed" else None,
    }
    try:
        updated = supabase_store.update_support_ticket(ticket_id, payload)
        return {"data": updated[0] if updated else None}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_tickets"):
            warn_missing_table_once("support_tickets", exc)
        raise HTTPException(status_code=500, detail=f"Không cập nhật được ticket: {exc}")


@app.get("/admin-api/kick-audit", dependencies=[Depends(require_admin)])
async def admin_kick_audit(live: bool = False, updated_after: str | None = None):
    try:
        return {"data": await build_kick_audit_rows(live=live, updated_after=updated_after)}
    except Exception as exc:
        print(f"⚠️ Không dựng được danh sách kiểm tra kick: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách kiểm tra kick: {exc}")


@app.get("/admin-api/renewal-kick-v2", dependencies=[Depends(require_admin)])
async def admin_renewal_kick_v2(updated_after: str | None = None):
    try:
        tasks = supabase_store.list_renewal_kick_tasks_v2(limit=5000)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_tasks_v2"):
            warn_missing_table_once("renewal_kick_tasks_v2", exc)
            return {"data": [], "group_tasks": [], "attempts": []}
        raise HTTPException(status_code=500, detail=f"Không đọc được renewal_kick_tasks_v2: {exc}")

    try:
        group_tasks = supabase_store.list_due_renewal_kick_group_tasks_v2(limit=5000)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_group_tasks_v2"):
            warn_missing_table_once("renewal_kick_group_tasks_v2", exc)
            group_tasks = []
        else:
            raise HTTPException(status_code=500, detail=f"Không đọc được renewal_kick_group_tasks_v2: {exc}")

    try:
        attempts = supabase_store._request(
            "GET",
            "renewal_kick_attempts_v2",
            params={"select": "*", "order": "started_at.desc", "limit": "2000"},
        )
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "renewal_kick_attempts_v2"):
            warn_missing_table_once("renewal_kick_attempts_v2", exc)
            attempts = []
        else:
            raise HTTPException(status_code=500, detail=f"Không đọc được renewal_kick_attempts_v2: {exc}")

    if updated_after:
        tasks = [row for row in tasks if str(row.get("updated_at") or row.get("last_transition_at") or "") >= updated_after]
        group_tasks = [row for row in group_tasks if str(row.get("updated_at") or row.get("last_transition_at") or "") >= updated_after]
        attempts = [row for row in attempts if str(row.get("started_at") or "") >= updated_after]

    return {"data": tasks, "group_tasks": group_tasks, "attempts": attempts}


@app.get("/admin-api/vip-group-audit", dependencies=[Depends(require_admin)])
async def admin_vip_group_audit(live: bool = False, updated_after: str | None = None):
    try:
        return {"data": await build_vip_group_audit_rows(live=live, updated_after=updated_after)}
    except Exception as exc:
        print(f"⚠️ Không dựng được danh sách quét nhóm hỗ trợ: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách quét nhóm hỗ trợ: {exc}")


@app.get("/admin-api/vip-member-audit", dependencies=[Depends(require_admin)])
async def admin_vip_member_audit(live: bool = False, risk_type: str = "ALL", updated_after: str | None = None):
    try:
        return {"data": await build_vip_member_risk_rows(live=live, risk_type_filter=risk_type, updated_after=updated_after)}
    except Exception as exc:
        print(f"⚠️ Không dựng được danh sách audit member VIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách audit member VIP: {exc}")


@app.post("/admin-api/kick-audit/kick", dependencies=[Depends(require_admin)])
async def admin_kick_audit_member(request: Request):
    body = await request.json()
    user_id = str(body.get("telegram_user_id") or "").strip()
    order_id = str(body.get("order_id") or "").strip()
    chat_id = normalize_chat_id(body.get("group_id"))
    plan_name = str(body.get("plan_name") or "").strip()
    customer_name = str(body.get("customer_name") or "").strip()

    if not user_id or not order_id or not chat_id:
        raise HTTPException(status_code=400, detail="Cần đủ Telegram ID, mã đơn và group ID để kick.")

    async def _kick_once():
        plan_label = display_plan_name(plan_name, user_id)
        parsed_chat_id = parse_chat_id(chat_id)
        await bot.ban_chat_member(chat_id=parsed_chat_id, user_id=int(user_id))
        await bot.unban_chat_member(chat_id=parsed_chat_id, user_id=int(user_id))
        record_support_event(
            "member_kicked",
            user_id,
            full_name=customer_name,
            chat_id=chat_id,
            chat_title=group_label_for_chat_id(chat_id),
            order_id=order_id,
            plan_name=plan_label,
            raw_data={"reason": "manual_kick_audit", "source": "dashboard", "plan_name_raw": plan_name, "kick_state": "done"},
        )
        record_support_event(
            "member_kick_closed",
            user_id,
            full_name=customer_name,
            chat_id=chat_id,
            chat_title=group_label_for_chat_id(chat_id),
            order_id=order_id,
            plan_name=plan_label,
            raw_data={"reason": "manual_kick_audit", "source": "dashboard", "closed_by": "admin", "plan_name_raw": plan_name, "kick_state": "done"},
        )
        return plan_label

    try:
        try:
            await asyncio.wait_for(_kick_once(), timeout=12)
        except asyncio.TimeoutError as exc:
            record_support_event(
                "member_kick_failed",
                user_id,
                full_name=customer_name,
                chat_id=chat_id,
                chat_title=group_label_for_chat_id(chat_id),
                order_id=order_id,
                plan_name=display_plan_name(plan_name, user_id),
                raw_data={"reason": "manual_kick_audit", "source": "dashboard", "error": "timeout", "kick_state": "error", "plan_name_raw": plan_name},
            )
            raise HTTPException(status_code=504, detail="Kick bị treo quá lâu. Vui lòng thử lại hoặc kiểm tra quyền bot.") from exc
    except Exception as exc:
        record_support_event(
            "member_kick_failed",
            user_id,
            full_name=customer_name,
            chat_id=chat_id,
            chat_title=group_label_for_chat_id(chat_id),
            order_id=order_id,
            plan_name=display_plan_name(plan_name, user_id),
            raw_data={"reason": "manual_kick_audit", "source": "dashboard", "error": str(exc), "kick_state": "error", "plan_name_raw": plan_name},
        )
        raise HTTPException(status_code=500, detail=f"Kick không thành công: {exc}")

    return {"data": await build_kick_audit_rows(live=True, order_id_filter=order_id, user_id_filter=user_id, chat_id_filter=chat_id)}


@app.post("/admin-api/vip-invite-links/cleanup", dependencies=[Depends(require_admin)])
async def admin_cleanup_vip_invite_links(request: Request):
    body = await request.json()
    group_id = str(body.get("group_id") or "").strip()
    force = bool(body.get("force", True))
    only_used = bool(body.get("only_used", False))
    try:
        from scheduler import cleanup_order_invite_links

        result = await cleanup_order_invite_links(group_id=group_id, force=force, only_used=only_used)
        return {"data": result}
    except Exception as exc:
        print(f"⚠️ Không dọn được link join VIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dọn được link join VIP: {exc}")


@app.get("/admin-api/activity-events", dependencies=[Depends(require_admin)])
async def admin_activity_events(limit: int = 5000):
    try:
        return {"data": supabase_store.list_analytics_events(limit=limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "analytics_events"):
            warn_missing_table_once("analytics_events", exc)
        else:
            print(f"⚠️ Không đọc được analytics_events: {exc}")
        return {"data": []}


@app.get("/admin-api/activity-log", dependencies=[Depends(require_admin)])
async def admin_activity_log(
    page: int = 1,
    limit: int = 80,
    query: str = "",
    direction: str = "all",
    type: str = "ALL",
    date: str = "ALL",
    updated_after: str | None = None,
):
    try:
        page = max(1, int(page or 1))
        limit = max(1, min(int(limit or 80), 200))
    except Exception:
        page = 1
        limit = 80

    query_text = _backend_text(query).lower()
    direction_value = _backend_text(direction).lower() or "all"
    type_value = _backend_text(type) or "ALL"
    date_value = _backend_text(date) or "ALL"
    today_key = _backend_day_key(datetime.now(_backend_timezone()))
    page_start = (page - 1) * limit
    page_end = page_start + limit
    chunk_size = max(100, min(limit * 4, 500))

    def matches(entry: dict) -> bool:
        if direction_value != "all" and entry["direction"] != direction_value:
            return False
        if type_value != "ALL" and entry["type"] != type_value:
            return False
        if date_value != "ALL" and _backend_day_key(entry["createdAt"]) != date_value:
            return False
        if query_text:
            haystack = " ".join(
                [
                    entry.get("type") or "",
                    entry.get("userId") or "",
                    entry.get("username") or "",
                    entry.get("fullName") or "",
                    entry.get("title") or "",
                    entry.get("detail") or "",
                ]
            ).lower()
            if query_text not in haystack:
                return False
        return True

    def normalize_activity(row: dict) -> dict | None:
        payload = row.get("payload") or {}
        chat_type = _backend_payload_text(payload, "chat_type").lower()
        if chat_type in {"group", "supergroup", "channel"}:
            return None
        message_text = _backend_payload_text(payload, "message_text")
        message_kind = _backend_payload_text(payload, "message_kind")
        event_type = _backend_payload_text(payload, "event_type") or _backend_text(row.get("event_name")) or "event"
        detail = message_text or _backend_payload_text(payload, "start_payload", "callback_data", "command", "chat_type")
        title_source = _backend_payload_text(payload, "source_ref", "activation_code") or _backend_humanize_event_type(event_type)
        detail_parts = [part for part in [message_kind, _backend_payload_text(payload, "chat_type"), f"#{_backend_payload_text(payload, 'message_id')}"] if part]
        detail_text = " • ".join(detail_parts) if message_text else detail
        return {
            "id": f"a-{row.get('id')}",
            "direction": "user",
            "type": event_type,
            "userId": _backend_text(row.get("telegram_user_id") or payload.get("user_id")),
            "username": _backend_payload_text(payload, "username"),
            "fullName": _backend_payload_text(payload, "full_name"),
            "title": f"Khách nhắn: {message_text}" if message_text else title_source,
            "detail": detail_text or "-",
            "createdAt": _backend_text(row.get("created_at")),
        }

    def normalize_support(row: dict) -> dict:
        raw_data = row.get("raw_data") if isinstance(row.get("raw_data"), dict) else {}
        reply_text = _backend_payload_text(raw_data, "reply_text")
        error_text = _backend_payload_text(raw_data, "error")
        activation_status = _backend_payload_text(raw_data, "activation_status").lower()
        activation_label = "OK" if activation_status == "ok" else "Partial" if activation_status == "partial" else "Failed" if activation_status == "failed" else ""
        failed_groups = _backend_payload_text(raw_data, "failed_groups")
        invite_results = _backend_payload_text(raw_data, "invite_results")
        detail_parts = [part for part in [error_text, _backend_text(row.get("plan_name")), _backend_text(row.get("chat_title")), _backend_text(row.get("order_id"))] if part]
        if activation_label:
            detail_parts.insert(0, f"Trạng thái: {activation_label}")
        if failed_groups:
            detail_parts.append(f"Lỗi group: {failed_groups}")
        if invite_results and invite_results not in detail_parts:
            detail_parts.append(f"Link: {invite_results}")
        return {
            "id": f"s-{row.get('id')}",
            "direction": "bot",
            "type": _backend_text(row.get("event_type")) or "event",
            "userId": _backend_text(row.get("telegram_user_id")),
            "username": _backend_text(row.get("username")),
            "fullName": _backend_text(row.get("full_name")) or _backend_text(row.get("chat_title")) or _backend_text(row.get("username")) or "-",
            "title": f"Admin trả lời: {reply_text}" if reply_text else _backend_humanize_event_type(row.get("event_type")),
            "detail": " • ".join(detail_parts) if detail_parts else "-",
            "createdAt": _backend_text(row.get("created_at")),
        }

    MAX_FETCH = 3000

    updated_after_value = _backend_text(updated_after)

    def fetch_activity(offset: int):
        if offset >= MAX_FETCH: return []
        rows = supabase_store.list_analytics_events_page(limit=min(chunk_size, MAX_FETCH - offset), offset=offset)
        if not updated_after_value:
            return rows
        return [row for row in rows if _backend_text(row.get("created_at")) > updated_after_value]

    def fetch_support(offset: int):
        if offset >= MAX_FETCH: return []
        rows = supabase_store.list_support_events_page(limit=min(chunk_size, MAX_FETCH - offset), offset=offset)
        if not updated_after_value:
            return rows
        return [row for row in rows if _backend_text(row.get("created_at")) > updated_after_value]

    sources = {
        "activity": {"offset": 0, "rows": [], "index": 0, "done": False, "fetch": fetch_activity},
        "support": {"offset": 0, "rows": [], "index": 0, "done": False, "fetch": fetch_support},
    }

    def refill(source_name: str):
        source = sources[source_name]
        while not source["done"] and source["index"] >= len(source["rows"]):
            batch = source["fetch"](source["offset"])
            source["offset"] += len(batch)
            source["rows"] = batch or []
            source["index"] = 0
            if not batch or len(batch) < chunk_size:
                source["done"] = True
            if not batch:
                return None
        if source["index"] < len(source["rows"]):
            return source["rows"][source["index"]]
        return None

    def take(source_name: str):
        source = sources[source_name]
        row = refill(source_name)
        if row is None:
            return None
        source["index"] += 1
        return row

    matched_total = 0
    summary = {"user": 0, "bot": 0, "today": 0}
    facet_types: set[str] = set()
    facet_dates: set[str] = set()
    page_rows: list[dict] = []

    loops = 0
    while loops < 6000:
        loops += 1
        activity_head = refill("activity")
        support_head = refill("support")
        if activity_head is None and support_head is None:
            break
        if support_head is None:
            chosen_source = "activity"
        elif activity_head is None:
            chosen_source = "support"
        else:
            chosen_source = "activity" if _backend_parse_datetime(activity_head.get("created_at")) >= _backend_parse_datetime(support_head.get("created_at")) else "support"

        raw_row = take(chosen_source)
        if raw_row is None:
            continue
        entry = normalize_activity(raw_row) if chosen_source == "activity" else normalize_support(raw_row)
        if not entry:
            continue
        facet_types.add(entry["type"])
        facet_dates.add(_backend_day_key(entry["createdAt"]))
        if not matches(entry):
            continue
        matched_total += 1
        if entry["direction"] == "user":
            summary["user"] += 1
        else:
            summary["bot"] += 1
        if _backend_day_key(entry["createdAt"]) == today_key:
            summary["today"] += 1
        if page_start <= matched_total - 1 < page_end:
            page_rows.append(entry)
        if matched_total > page_end:
            break

    return {
        "data": page_rows,
        "total": matched_total,
        "page": page,
        "limit": limit,
        "summary": summary,
        "facets": {
            "types": sorted(facet_types),
            "dates": sorted([item for item in facet_dates if item != "UNKNOWN"], reverse=True) + (["UNKNOWN"] if "UNKNOWN" in facet_dates else []),
        },
    }


@app.post("/admin-api/admin-replies", dependencies=[Depends(require_admin)])
async def admin_reply_to_customer(request: Request):
    body = await request.json()
    ticket_id = str(body.get("ticket_id") or "").strip()
    telegram_user_id = str(body.get("telegram_user_id") or "").strip()
    text = str(body.get("text") or "").strip()
    source_log_id = str(body.get("source_log_id") or "").strip()
    source_text = str(body.get("source_text") or "").strip()
    full_name = str(body.get("full_name") or "").strip()

    if not telegram_user_id.isdigit():
        raise HTTPException(status_code=400, detail="Telegram ID không hợp lệ.")
    if not text:
        raise HTTPException(status_code=400, detail="Nội dung trả lời đang trống.")
    if len(text) > 3500:
        raise HTTPException(status_code=400, detail="Nội dung trả lời quá dài, tối đa 3500 ký tự.")

    ticket = None
    try:
        if ticket_id:
            ticket = supabase_store.get_support_ticket_by_id(ticket_id)
            if ticket:
                telegram_user_id = str(ticket.get("telegram_user_id") or telegram_user_id).strip()
                full_name = str(ticket.get("full_name") or full_name).strip()
        if not ticket:
            ticket = supabase_store.get_support_ticket_by_user(telegram_user_id)
            if ticket:
                ticket_id = str(ticket.get("id") or ticket_id).strip()
                full_name = str(ticket.get("full_name") or full_name).strip()
        if not ticket:
            ticket, created_new, ticket_error = await get_or_create_support_ticket_for_user(
                telegram_user_id=telegram_user_id,
                full_name=full_name,
                subject=source_text or text or "Tin nhắn hỗ trợ",
                source="admin_reply",
                raw_data={
                    "source_log_id": source_log_id,
                    "source_text": source_text,
                    "created_by": "admin_cp",
                },
            )
            if ticket_error:
                print(f"⚠️ Không tự tạo support ticket cho {telegram_user_id} trước khi reply: {ticket_error}")
            if ticket:
                ticket_id = str(ticket.get("id") or ticket_id).strip()
                telegram_user_id = str(ticket.get("telegram_user_id") or telegram_user_id).strip()
                full_name = str(ticket.get("full_name") or full_name).strip()
    except Exception as exc:
        print(f"⚠️ Không đọc/tạo support ticket trước khi reply cho {telegram_user_id}: {exc}")

    try:
        sent = await bot.send_message(chat_id=int(telegram_user_id), text=text, disable_web_page_preview=True)
    except Exception as exc:
        try:
            supabase_store.record_support_event(
                "admin_reply_failed",
                telegram_user_id,
                full_name=full_name,
                raw_data={
                    "reply_text": text,
                    "source_log_id": source_log_id,
                    "source_text": source_text,
                    "error": str(exc),
                },
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Không gửi được tin nhắn cho khách: {exc}")

    created_message = None
    try:
        message_ticket_id = str(ticket.get("id") or ticket_id or "").strip()
        if message_ticket_id:
            created_rows = supabase_store.create_support_message(
                {
                    "ticket_id": message_ticket_id,
                    "direction": normalize_support_message_direction("support_to_user"),
                    "telegram_message_id": getattr(sent, "message_id", None),
                    "text": text,
                    "payload": {
                        "source": "admin_cp",
                        "source_log_id": source_log_id,
                        "source_text": source_text,
                        "created_by": "admin_cp",
                    },
                }
            )
            created_message = created_rows[0] if created_rows else None
            supabase_store.update_support_ticket(
                message_ticket_id,
                {
                    "status": "open",
                    "last_message_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            )
        supabase_store.record_support_event(
            "admin_reply_sent",
            telegram_user_id,
            full_name=full_name,
            raw_data={
                "reply_text": text,
                "source_log_id": source_log_id,
                "source_text": source_text,
                "sent_message_id": getattr(sent, "message_id", ""),
                "ticket_id": message_ticket_id,
            },
        )
    except Exception as exc:
        if not is_missing_supabase_table_error(exc, "support_events"):
            print(f"⚠️ Không ghi được admin_reply_sent: {exc}")

    return {
        "data": {
            "ok": True,
            "ticket_id": message_ticket_id,
            "message_id": getattr(sent, "message_id", None),
            "message": created_message,
        }
    }


def is_missing_campaign_table_error(exc: Exception) -> bool:
    text = str(exc)
    return any(
        is_missing_supabase_table_error(exc, table)
        for table in ("broadcast_campaigns", "broadcast_recipients", "broadcast_events")
    ) or ("broadcast_" in text and "PGRST205" in text)


def is_missing_channel_post_table_error(exc: Exception) -> bool:
    text = str(exc)
    return any(
        is_missing_supabase_table_error(exc, table)
        for table in ("channel_posts", "channel_post_events")
    ) or ("channel_post" in text and "PGRST205" in text)


@app.get("/admin-api/campaigns", dependencies=[Depends(require_admin)])
async def admin_campaigns(limit: int = 100, updated_after: str | None = None):
    try:
        return {"data": supabase_store.list_broadcast_campaigns(limit=limit, updated_after=updated_after)}
    except Exception as exc:
        if is_missing_campaign_table_error(exc):
            warn_missing_table_once("broadcast_campaigns", exc)
        else:
            print(f"⚠️ Không đọc được broadcast_campaigns: {exc}")
        return {"data": []}


@app.get("/admin-api/campaigns/preview", dependencies=[Depends(require_admin)])
async def admin_campaign_preview(segment: str = "ALL", plan_filter: str = "ALL", plan_match_scope: str = "ANY_PAID"):
    try:
        return {"data": supabase_store.preview_broadcast_recipients(segment=segment, plan_filter=plan_filter, plan_match_scope=plan_match_scope)}
    except Exception as exc:
        if is_missing_campaign_table_error(exc):
            warn_missing_table_once("broadcast_campaigns", exc)
        else:
            print(f"⚠️ Không preview được campaign recipients: {exc}")
        return {"data": {"total": 0, "counts": {}, "sample": []}}


@app.post("/admin-api/campaigns", dependencies=[Depends(require_admin)])
async def admin_create_campaign(request: Request):
    body = await request.json()
    try:
        return {"data": supabase_store.create_broadcast_campaign(body)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if is_missing_campaign_table_error(exc):
            warn_missing_table_once("broadcast_campaigns", exc)
            raise HTTPException(status_code=503, detail="Thiếu bảng campaign. Hãy chạy migration Supabase mới nhất.")
        raise


@app.get("/admin-api/campaigns/{campaign_id}/recipients", dependencies=[Depends(require_admin)])
async def admin_campaign_recipients(campaign_id: str, limit: int = 500, status: str | None = None):
    try:
        return {"data": supabase_store.list_broadcast_recipients(campaign_id, limit=limit, status=status)}
    except Exception as exc:
        if is_missing_campaign_table_error(exc):
            warn_missing_table_once("broadcast_recipients", exc)
        else:
            print(f"⚠️ Không đọc được broadcast_recipients: {exc}")
        return {"data": []}


@app.post("/admin-api/campaigns/{campaign_id}/start", dependencies=[Depends(require_admin)])
async def admin_start_campaign(campaign_id: str):
    return {"data": supabase_store.start_broadcast_campaign(campaign_id)}


@app.post("/admin-api/campaigns/{campaign_id}/pause", dependencies=[Depends(require_admin)])
async def admin_pause_campaign(campaign_id: str):
    return {"data": supabase_store.pause_broadcast_campaign(campaign_id)}


@app.post("/admin-api/campaigns/{campaign_id}/cancel", dependencies=[Depends(require_admin)])
async def admin_cancel_campaign(campaign_id: str):
    return {"data": supabase_store.cancel_broadcast_campaign(campaign_id)}


@app.get("/admin-api/channel-posts", dependencies=[Depends(require_admin)])
async def admin_channel_posts(limit: int = 200, status: str | None = None, updated_after: str | None = None):
    try:
        return {"data": supabase_store.list_channel_posts(limit=limit, status=status, updated_after=updated_after)}
    except Exception as exc:
        if is_missing_channel_post_table_error(exc):
            warn_missing_table_once("channel_posts", exc)
        else:
            print(f"⚠️ Không đọc được channel_posts: {exc}")
        return {"data": []}


@app.post("/admin-api/channel-posts", dependencies=[Depends(require_admin)])
async def admin_create_channel_post(request: Request):
    body = await request.json()
    try:
        data = supabase_store.create_channel_post(body)
        return {"data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if is_missing_channel_post_table_error(exc):
            warn_missing_table_once("channel_posts", exc)
            raise HTTPException(status_code=503, detail="Thiếu bảng đăng channel. Hãy chạy migration Supabase mới nhất.")
        raise


@app.patch("/admin-api/channel-posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_update_channel_post(post_id: str, request: Request):
    body = await request.json()
    try:
        data = supabase_store.patch_channel_post(post_id, body)
        return {"data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if is_missing_channel_post_table_error(exc):
            warn_missing_table_once("channel_posts", exc)
            raise HTTPException(status_code=503, detail="Thiếu bảng đăng channel. Hãy chạy migration Supabase mới nhất.")
        raise


@app.post("/admin-api/channel-posts/{post_id}/action", dependencies=[Depends(require_admin)])
async def admin_channel_post_action(post_id: str, request: Request):
    body = await request.json()
    action = str(body.get("action") or "").strip()
    try:
        row = supabase_store.channel_post_action(post_id, action, body)
        return {"data": row}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if is_missing_channel_post_table_error(exc):
            warn_missing_table_once("channel_posts", exc)
            raise HTTPException(status_code=503, detail="Thiếu bảng đăng channel. Hãy chạy migration Supabase mới nhất.")
        raise


@app.get("/admin-api/channel-posts/{post_id}/events", dependencies=[Depends(require_admin)])
async def admin_channel_post_events(post_id: str, limit: int = 200):
    try:
        return {"data": supabase_store.list_channel_post_events(post_id=post_id, limit=limit)}
    except Exception as exc:
        if is_missing_channel_post_table_error(exc):
            warn_missing_table_once("channel_post_events", exc)
        else:
            print(f"⚠️ Không đọc được channel_post_events: {exc}")
        return {"data": []}


@app.get("/admin-api/support-group-check", dependencies=[Depends(require_admin)])
async def admin_support_group_check():
    db.reload_config(force=False)
    gid = support_group_id()
    result = {
        "enabled": support_group_enabled(),
        "group_id": mask_chat_id(gid),
        "group_name": support_group_name(),
        "get_chat": {"ok": False, "message": ""},
        "bot_member": {"ok": False, "message": ""},
        "invite_link": {"ok": False, "message": ""},
    }
    if not gid:
        result["get_chat"]["message"] = "SUPPORT_GROUP_ID đang trống."
        return {"data": result}

    try:
        chat = await bot.get_chat(gid)
        result["get_chat"] = {
            "ok": True,
            "message": f"{getattr(chat, 'type', '')}: {getattr(chat, 'title', '') or getattr(chat, 'username', '') or gid}",
        }
    except Exception as exc:
        result["get_chat"]["message"] = explain_support_invite_error(exc, gid, "SUPPORT_GROUP_ID")
        return {"data": result}

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(gid, me.id)
        result["bot_member"] = {"ok": True, "message": str(getattr(member, "status", ""))}
    except Exception as exc:
        result["bot_member"]["message"] = explain_support_invite_error(exc, gid, "SUPPORT_GROUP_ID")

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=gid,
            member_limit=1,
            creates_join_request=False,
            name="support-dashboard-check",
        )
        result["invite_link"] = {"ok": True, "message": "Tạo link OK"}
        try:
            await bot.revoke_chat_invite_link(gid, invite.invite_link)
        except Exception as revoke_exc:
            print(f"⚠️ Không revoke được support diagnostic invite {mask_chat_id(gid)}: {revoke_exc}")
    except Exception as exc:
        result["invite_link"]["message"] = explain_support_invite_error(exc, gid)
    return {"data": result}
