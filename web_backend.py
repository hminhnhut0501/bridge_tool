import asyncio
import importlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from bot_instance import bot, dp, set_commands
from database import db
from hidden_group_utils import (
    delete_hidden_code,
    delete_hidden_group,
    list_hidden_codes,
    list_hidden_groups,
    list_hidden_redemptions,
    resolve_plan_groups,
    upsert_hidden_code,
    upsert_hidden_group,
)
from helpers import bot_schedule_status, bot_runtime_state_audit, set_runtime_maintenance_override, runtime_maintenance_override
from helpers import create_background_task
from i18n import get_user_language, set_user_language
from supabase_store import supabase_store
from support_utils import (
    create_support_invite_link,
    explain_support_invite_error,
    mask_chat_id,
    record_support_event,
    support_group_enabled,
    support_group_id,
    support_group_name,
    support_inbox_group_id,
    support_inbox_group_name,
)
from vip_group_audit_utils import build_vip_group_audit_rows
from payment import payment_manager
from modules.mod_auto_payment_schedule import apply_auto_payment_schedule

load_dotenv()

app = FastAPI(title="Prive Bot Backend")
_booted = False
_missing_table_warnings: set[str] = set()
_last_webhook_reset_reason = ""
_webhook_failure_streak = 0
_webhook_reset_block_until = None
_webhook_reset_backoff_seconds = 0


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
    }


def webhook_reset_wait_seconds() -> int:
    if not _webhook_reset_block_until:
        return 0
    return max(0, int((_webhook_reset_block_until - datetime.now()).total_seconds()))


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
            set_runtime_maintenance_override(
                True,
                reason=f"Webhook unhealthy ({reason}). Auto-reset skipped to avoid SetWebhook spam.",
                source="webhook",
            )
            return {"ok": False, "reason": reason, "info": info}

        if _webhook_reset_block_until and now < _webhook_reset_block_until:
            wait_seconds = max(1, int((_webhook_reset_block_until - now).total_seconds()))
            set_runtime_maintenance_override(
                True,
                reason=f"Webhook reset cooldown active. Retry after {wait_seconds}s.",
                source="webhook",
            )
            return {"ok": False, "reason": f"cooldown:{wait_seconds}", "info": info}

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
        set_runtime_maintenance_override(True, reason=f"Webhook runtime error: {exc}", source="webhook")
        raise


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
    timezone_name = str(db.get_config("BOT_TIMEZONE", os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh")) or "").strip()
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
    parsed = parse_manual_expire_at(value)
    if not parsed:
        return str(value or "").strip()
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
    template = normalize_template_text(db.get_config(
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
    template = normalize_template_text(db.get_config(template_key, default_text) or default_text)
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value or ""))
    return template.strip()


def normalize_manual_order_link_template(value: str):
    template = str(value or "").strip()
    if not template:
        return "https://t.me/hangcuprivebot?start=act_{code}"
    if template.startswith("t.me/"):
        template = f"https://{template}"
    if "start=act_{code}" in template:
        return template
    if "start={code}" in template:
        return template.replace("start={code}", "start=act_{code}")
    return template


def build_manual_activation_url(code: str):
    template = normalize_manual_order_link_template(db.get_config("MANUAL_ORDER_LINK_TEMPLATE", "t.me/hangcuprivebot?start=act_{code}") or "")
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
    template = normalize_manual_order_link_template(db.get_config("MANUAL_ORDER_MESSAGE_LINK_TEMPLATE", "t.me/hangcuprivebot?start=actmsg_{code}") or "")
    if "start=act_{code}" in template:
        template = template.replace("start=act_{code}", "start=actmsg_{code}")
    elif "start={code}" in template:
        template = template.replace("start={code}", "start=actmsg_{code}")
    return template.replace("{code}", str(code or "").strip())


def build_manual_order_join_message_text(context: dict[str, object]):
    return render_manual_order_message_text(
        str(db.get_config("MANUAL_ORDER_JOIN_TEMPLATE", "") or ""),
        {
            **context,
            "activation_url": context.get("activation_url", ""),
            "message_url": context.get("message_url", ""),
            "links_text": context.get("links_text", ""),
            "support_text": context.get("support_text", ""),
        },
    )


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


def order_display_name(order, support_events):
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


async def build_kick_audit_rows(live=False, order_id_filter="", user_id_filter="", chat_id_filter=""):
    from scheduler import parse_expire_datetime, plan_group_ids, user_active_group_ids

    db.reload_config(force=True)
    now = now_local().replace(tzinfo=None)
    orders = supabase_store.list_scheduler_orders(limit=5000)
    users_data = [supabase_store.order_to_sheet_row(order) for order in orders]
    try:
        support_events = supabase_store.list_support_events(limit=5000)
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_events"):
            warn_missing_table_once("support_events", exc)
            support_events = []
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
        display_name = order_display_name(order, support_events)
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

            live_state = {"checked": False, "present": None, "status": "", "error": ""}
            if live:
                live_state = await member_live_state(gid, user_id)

            status = "ACTIVE_RETAINED" if retained else "KICKED" if latest_kick else "WAITING_KICK"
            status_label = (
                "Còn quyền active"
                if retained
                else "Đã kick cùng group"
                if latest_kick and latest_kick is not latest_order_kick
                else "Đã kick"
                if latest_kick
                else "Chờ kick"
            )
            needs_action = not retained and not latest_kick

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
    if not os.path.exists(module_dir):
        return loaded_count

    for filename in os.listdir(module_dir):
        if not filename.startswith("mod_") or not filename.endswith(".py"):
            continue
        module_name = filename[:-3]
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
    if supabase_store.enabled:
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
        result = await ensure_telegram_webhook(force=True)
        print(f"✅ Telegram webhook ready: {webhook_url} ({result.get('reason', 'forced')})")
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
    return {"ok": True, "service": "prive-bot-backend"}


@app.get("/admin-api/webhook-info", dependencies=[Depends(require_admin)])
async def admin_webhook_info():
    info = await bot.get_webhook_info()
    return {
        "data": info,
        "meta": {
            "expected_url": str(os.getenv("WEBHOOK_URL") or "").strip(),
            "last_reset_reason": _last_webhook_reset_reason,
            "failure_streak": _webhook_failure_streak,
            "problem_reason": webhook_problem_reason(info, str(os.getenv("WEBHOOK_URL") or "").strip()),
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
    info = await bot.get_webhook_info()
    return {
        "data": info,
        "meta": {
            "expected_url": str(os.getenv("WEBHOOK_URL") or "").strip(),
            "last_reset_reason": _last_webhook_reset_reason,
            "failure_streak": _webhook_failure_streak,
            "problem_reason": webhook_problem_reason(info, str(os.getenv("WEBHOOK_URL") or "").strip()),
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
async def admin_orders(limit: int = 200):
    return {"data": supabase_store.list_orders(limit=limit)}


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
        supabase_store.record_support_event(
            "order_deleted",
            order.get("telegram_user_id"),
            full_name=order.get("full_name"),
            order_id=order_id,
            plan_name=order.get("plan_name"),
            raw_data={
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
    body = await request.json()
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    plan_name = str(body.get("plan_name", "")).strip()
    note = str(body.get("note", "")).strip()
    coupon_code = str(body.get("coupon_code", "")).strip().upper()
    activation_code = str(body.get("activation_code", "")).strip().upper() or generate_activation_code()
    activation_url = build_manual_activation_url(activation_code)

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

    db.reload_config(force=True)
    groups = resolve_plan_groups(plan_name)
    if not groups:
        raise HTTPException(status_code=400, detail="Tên gói chưa khớp group nào. Kiểm tra tên gói hoặc cấu hình BTN_G/ID_G.")

    try:
        amount = float(str(body.get("amount", "0") or 0))
    except (TypeError, ValueError):
        amount = 0.0

    user_language = get_user_language(user_id)
    default_currency = "USD" if user_language == "en" else "VND"
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

    expire_at = parse_manual_expire_at(body.get("expire_at"))
    if expire_at is None:
        try:
            duration_days = int(float(str(body.get("duration_days", "30") or 30)))
        except (TypeError, ValueError):
            duration_days = 30
        if duration_days <= 0:
            raise HTTPException(status_code=400, detail="Số ngày sử dụng phải lớn hơn 0, hoặc nhập ngày hết hạn cụ thể.")
        expire_at = now_local() + timedelta(days=duration_days)

    paid_at = now_local()
    order_id = str(int(time.time() * 1000))
    sale_id = str(body.get("sale_id") or "MANUAL").strip().upper()
    message_template = str(db.get_config(
        "MANUAL_ORDER_MESSAGE_TEMPLATE",
        "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}",
    ) or "").strip()
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
        },
    )
    order_data = supabase_store.mark_order_paid(
        order_id,
        paid_at=paid_at.isoformat(timespec="seconds"),
        expire_at=expire_at.isoformat(timespec="seconds"),
    )

    support_link, support_error = await create_support_invite_link(user_id)
    links_text = "\n".join([
        render_manual_order_support_text("🔗 {support_group_name}: {support_link}", {
            "support_group_name": support_group_name(),
            "support_link": support_link,
        }) if support_link else "",
    ]).strip()
    if support_link:
        support_text = render_manual_order_support_text("💬 {support_group_name}:\n{support_link}", {
            "order_id": order_id,
            "telegram_user_id": telegram_user_id,
            "full_name": full_name,
            "plan_name": plan_name,
            "expire_at": expire_at.isoformat(timespec="seconds"),
            "support_group_name": support_group_name(),
            "support_link": support_link,
            "support_error": "",
        })
    elif support_error:
        support_text = render_activation_text(
            "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
        "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
            {
                "support_group_name": support_group_name(),
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
        "expire_at": expire_at.isoformat(timespec="seconds"),
    })

    try:
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
                "expire_at": expire_at.isoformat(timespec="seconds"),
            },
        )
    except Exception as exc:
        if not is_missing_supabase_table_error(exc, "order_activation_codes"):
            raise
        print(f"⚠️ Bỏ qua lưu activation code vì thiếu bảng order_activation_codes: {exc}")

    try:
        supabase_store.record_support_event(
            "manual_order_created",
            telegram_user_id,
            full_name=full_name,
            order_id=order_id,
            plan_name=plan_name,
            raw_data={
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
        if not is_missing_supabase_table_error(exc, "support_events"):
            print(f"⚠️ Không ghi được manual_order_created: {exc}")

    return {
        "data": {
            "order_id": order_id,
            "order": order_data[0] if isinstance(order_data, list) and order_data else None,
            "telegram_user_id": telegram_user_id,
            "full_name": full_name,
            "plan_name": plan_name,
            "amount": amount,
            "note": note,
            "payment_currency": payment_currency,
            "payment_provider": payment_provider,
            "paid_at": paid_at.isoformat(timespec="seconds"),
            "expire_at": format_manual_expire_at(expire_at.isoformat(timespec="seconds")),
            "group_names": "",
            "links_text": links_text,
            "activation_code": activation_code,
            "activation_url": activation_url,
            "manual_order_message_url": build_manual_order_message_url(activation_code),
            "support_link": support_link,
            "support_error": support_error,
            "support_text": support_text,
            "bot_link_title": render_activation_text("MANUAL_ORDER_LINK_TITLE", "🔗 Active code", {}),
            "manual_order_message_title": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_TITLE", "💬 Link bot xác nhận", {}),
            "manual_order_join_title": render_activation_text("MANUAL_ORDER_JOIN_LINK_TITLE", "💬 Link bot đầy đủ", {}),
            "bot_link_subtitle": render_activation_text("MANUAL_ORDER_LINK_SUBTITLE", "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", {}),
            "manual_order_message_subtitle": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_SUBTITLE", "Dùng link này để mở bot và nhận toàn bộ nội dung xác nhận đơn.", {}),
            "manual_order_join_subtitle": render_activation_text("MANUAL_ORDER_JOIN_LINK_SUBTITLE", "Dùng tin này để gửi khách khi cần có sẵn link join group.", {}),
            "bot_link_button_label": render_activation_text("MANUAL_ORDER_LINK_BUTTON_LABEL", "Gen active code", {}),
            "manual_order_message_button_label": render_activation_text("MANUAL_ORDER_MESSAGE_LINK_BUTTON_LABEL", "Gen tin active code", {}),
            "manual_order_join_button_label": render_activation_text("MANUAL_ORDER_JOIN_LINK_BUTTON_LABEL", "Gen tin join group", {}),
            "bot_link_success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {}),
            "bot_link_processing_text": render_activation_text("MANUAL_ORDER_LINK_PROCESSING_TEXT", "⏳ Bot đang xác minh đơn và tạo link nhóm...", {}),
            "manual_order_text": render_manual_order_message_text(message_template, {
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
                "message_url": build_manual_order_message_url(activation_code),
                "links_text": links_text,
                "support_text": support_text,
                "support_group_name": support_group_name(),
                "support_link": support_link,
                "support_error": support_error,
                "activation_code": activation_code,
            }),
            "manual_order_join_text": build_manual_order_join_message_text({
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "full_name": full_name or telegram_user_id,
                "plan_name": plan_name,
                "expire_at": expire_at.isoformat(timespec="seconds"),
                "order_text": order_text,
                "success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {}),
                "bot_link_title": render_activation_text("MANUAL_ORDER_JOIN_LINK_TITLE", "💬 Link bot đầy đủ", {}),
                "bot_link_subtitle": render_activation_text("MANUAL_ORDER_JOIN_LINK_SUBTITLE", "Dùng tin này để gửi khách khi cần có sẵn link join group.", {}),
                "activation_url": activation_url,
                "message_url": "",
                "links_text": links_text,
                "support_text": support_text,
                "support_group_name": support_group_name(),
                "support_link": support_link,
                "support_error": support_error,
                "activation_code": activation_code,
            }),
            "failed_groups": [],
        }
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
    rows = supabase_store.get_config()
    for row in rows or []:
        if str(row.get("key") or "").strip().upper() == "MANUAL_ORDER_LINK_TEMPLATE":
            row["value"] = normalize_manual_order_link_template(row.get("value"))
        if str(row.get("key") or "").strip().upper() == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
            row["value"] = normalize_manual_order_link_template(row.get("value"))
    return {"data": rows}


@app.patch("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_set_config(key: str, request: Request):
    body = await request.json()
    normalized_key = str(key).strip().upper()
    value = body.get("value", "")
    if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
        value = normalize_manual_order_link_template(value)
    if normalized_key == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
        value = normalize_manual_order_link_template(value)
    data = supabase_store.set_config(key, value)
    db.cache_config[normalized_key] = str(value)
    normalized_key = str(key).strip().upper()
    if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_"):
        await set_commands()
    refresh_auto_payment_schedule_if_needed([normalized_key])
    return {"data": data}


@app.post("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_set_config_batch(request: Request):
    body = await request.json()
    items = body.get("items", body if isinstance(body, list) else [])
    normalized_items = []
    for item in items:
        normalized_item = dict(item)
        if str(normalized_item.get("key", "")).strip().upper() == "MANUAL_ORDER_LINK_TEMPLATE":
            normalized_item["value"] = normalize_manual_order_link_template(normalized_item.get("value", ""))
        if str(normalized_item.get("key", "")).strip().upper() == "MANUAL_ORDER_MESSAGE_LINK_TEMPLATE":
            normalized_item["value"] = normalize_manual_order_link_template(normalized_item.get("value", ""))
        normalized_items.append(normalized_item)
    data = supabase_store.set_configs(normalized_items)
    command_changed = False
    auto_payment_keys = []
    for item in normalized_items:
        normalized_key = str(item.get("key", "")).strip().upper()
        if not normalized_key:
            continue
        db.cache_config[normalized_key] = str(item.get("value", ""))
        if auto_payment_config_key(normalized_key):
            auto_payment_keys.append(normalized_key)
        if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_"):
            command_changed = True
    if command_changed:
        await set_commands()
    refresh_auto_payment_schedule_if_needed(auto_payment_keys)
    return {"data": data}


@app.delete("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_delete_config(key: str):
    data = supabase_store.delete_config(key)
    db.cache_config.pop(str(key).strip().upper(), None)
    refresh_auto_payment_schedule_if_needed([key])
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
    db.reload_config(force=True)
    return {"data": data}


@app.delete("/admin-api/menu-pages/{page_id}", dependencies=[Depends(require_admin)])
async def admin_delete_menu_page(page_id: str):
    data = supabase_store.delete_menu_page(page_id)
    db.reload_config(force=True)
    return {"data": data}


@app.get("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_sale_rules():
    return {"data": supabase_store.list_sale_rules()}


@app.post("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_upsert_sale_rule(request: Request):
    body = await request.json()
    data = supabase_store.upsert_sale_rule(body)
    db.reload_config(force=True)
    return {"data": data}


@app.delete("/admin-api/sale-rules/{sale_id}", dependencies=[Depends(require_admin)])
async def admin_delete_sale_rule(sale_id: str):
    data = supabase_store.delete_sale_rule(sale_id)
    db.reload_config(force=True)
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
async def admin_support_events(limit: int = 5000):
    try:
        return {"data": supabase_store.list_support_events(limit=limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_events"):
            warn_missing_table_once("support_events", exc)
        else:
            print(f"⚠️ Không đọc được support_events: {exc}")
        return {"data": []}


@app.get("/admin-api/support-cases", dependencies=[Depends(require_admin)])
async def admin_support_cases(query: str = "", limit: int = 20):
    try:
        rows = supabase_store.search_support_tickets(query, limit=limit)
        data = []
        for row in rows:
            messages = supabase_store.list_support_messages(row.get("id"), limit=20)
            data.append({"ticket": row, "messages": messages})
        return {"data": data}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "support_tickets"):
            warn_missing_table_once("support_tickets", exc)
        else:
            print(f"⚠️ Không đọc được support cases: {exc}")
        return {"data": []}


@app.get("/admin-api/kick-audit", dependencies=[Depends(require_admin)])
async def admin_kick_audit(live: bool = False):
    try:
        return {"data": await build_kick_audit_rows(live=live)}
    except Exception as exc:
        print(f"⚠️ Không dựng được danh sách kiểm tra kick: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách kiểm tra kick: {exc}")


@app.get("/admin-api/vip-group-audit", dependencies=[Depends(require_admin)])
async def admin_vip_group_audit(live: bool = False):
    try:
        return {"data": await build_vip_group_audit_rows(live=live)}
    except Exception as exc:
        print(f"⚠️ Không dựng được danh sách quét group VIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách quét group VIP: {exc}")


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

    try:
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
            plan_name=plan_name,
            raw_data={"reason": "manual_kick_audit", "source": "dashboard"},
        )
        record_support_event(
            "member_kick_closed",
            user_id,
            full_name=customer_name,
            chat_id=chat_id,
            chat_title=group_label_for_chat_id(chat_id),
            order_id=order_id,
            plan_name=plan_name,
            raw_data={"reason": "manual_kick_audit", "source": "dashboard", "closed_by": "admin"},
        )
    except Exception as exc:
        record_support_event(
            "member_kick_failed",
            user_id,
            full_name=customer_name,
            chat_id=chat_id,
            chat_title=group_label_for_chat_id(chat_id),
            order_id=order_id,
            plan_name=plan_name,
            raw_data={"reason": "manual_kick_audit", "source": "dashboard", "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=f"Kick không thành công: {exc}")

    return {"data": await build_kick_audit_rows(live=True, order_id_filter=order_id, user_id_filter=user_id, chat_id_filter=chat_id)}


@app.get("/admin-api/activity-events", dependencies=[Depends(require_admin)])
async def admin_activity_events(limit: int = 500):
    try:
        return {"data": supabase_store.list_analytics_events(limit=limit)}
    except Exception as exc:
        if is_missing_supabase_table_error(exc, "analytics_events"):
            warn_missing_table_once("analytics_events", exc)
        else:
            print(f"⚠️ Không đọc được analytics_events: {exc}")
        return {"data": []}


@app.post("/admin-api/admin-replies", dependencies=[Depends(require_admin)])
async def admin_reply_to_customer(request: Request):
    body = await request.json()
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

    try:
        supabase_store.record_support_event(
            "admin_reply_sent",
            telegram_user_id,
            full_name=full_name,
            raw_data={
                "reply_text": text,
                "source_log_id": source_log_id,
                "source_text": source_text,
                "sent_message_id": getattr(sent, "message_id", ""),
            },
        )
    except Exception as exc:
        if not is_missing_supabase_table_error(exc, "support_events"):
            print(f"⚠️ Không ghi được admin_reply_sent: {exc}")

    return {"data": {"ok": True, "message_id": getattr(sent, "message_id", None)}}


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
async def admin_campaigns(limit: int = 100):
    try:
        return {"data": supabase_store.list_broadcast_campaigns(limit=limit)}
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
async def admin_channel_posts(limit: int = 200, status: str | None = None):
    try:
        return {"data": supabase_store.list_channel_posts(limit=limit, status=status)}
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
    db.reload_config(force=True)
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
        result["get_chat"]["message"] = explain_support_invite_error(exc, gid, "SUPPORT_INBOX_GROUP_ID")
        return {"data": result}

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(gid, me.id)
        result["bot_member"] = {"ok": True, "message": str(getattr(member, "status", ""))}
    except Exception as exc:
        result["bot_member"]["message"] = explain_support_invite_error(exc, gid, "SUPPORT_INBOX_GROUP_ID")

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


@app.get("/admin-api/support-inbox-check", dependencies=[Depends(require_admin)])
async def admin_support_inbox_check():
    db.reload_config(force=True)
    gid = support_inbox_group_id()
    result = {
        "group_id": mask_chat_id(gid),
        "group_name": support_inbox_group_name(),
        "get_chat": {"ok": False, "message": ""},
        "bot_member": {"ok": False, "message": ""},
    }
    if not gid:
        result["get_chat"]["message"] = "SUPPORT_INBOX_GROUP_ID đang trống."
        return {"data": result}

    try:
        chat = await bot.get_chat(gid)
        result["get_chat"] = {
            "ok": True,
            "message": f"{getattr(chat, 'type', '')}: {getattr(chat, 'title', '') or getattr(chat, 'username', '') or gid}",
        }
    except Exception as exc:
        result["get_chat"]["message"] = explain_support_invite_error(exc, gid)
        return {"data": result}

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(gid, me.id)
        result["bot_member"] = {"ok": True, "message": str(getattr(member, "status", ""))}
    except Exception as exc:
        result["bot_member"]["message"] = explain_support_invite_error(exc, gid)

    return {"data": result}
