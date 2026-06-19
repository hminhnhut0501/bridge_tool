import asyncio
import importlib
import json
import os
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
from helpers import bot_schedule_status, bot_runtime_state_audit
from helpers import create_background_task
from supabase_store import supabase_store
from support_utils import create_support_invite_link, explain_support_invite_error, mask_chat_id, record_support_event, support_group_enabled, support_group_id, support_group_name
from vip_group_audit_utils import build_vip_group_audit_rows
from payment import payment_manager

load_dotenv()

app = FastAPI(title="Prive Bot Backend")
_booted = False
_missing_table_warnings: set[str] = set()


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
    return parsed.strftime("%H:%M %d/%m/%y")


def render_manual_order_support_text(template: str, context: dict[str, object]):
    text = str(template or "").strip()
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


def render_manual_order_message_text(template: str, context: dict[str, object]):
    text = str(template or "").strip()
    if not text:
        text = "{links_text}\n{support_text}"
    values = {
        "order_id": context.get("order_id", ""),
        "telegram_user_id": context.get("telegram_user_id", ""),
        "full_name": context.get("full_name", ""),
        "plan_name": context.get("plan_name", ""),
        "expire_at": format_manual_expire_at(context.get("expire_at", "")),
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
    template = str(db.get_config(template_key, default_text) or default_text).strip()
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value or ""))
    return template.strip()


def build_manual_activation_url(code: str):
    template = str(db.get_config("MANUAL_ORDER_LINK_TEMPLATE", "t.me/hangcuprivebot?start={code}") or "").strip()
    if not template:
        template = "t.me/hangcuprivebot?start={code}"
    return template.replace("{code}", str(code or "").strip())


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

    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if webhook_url:
        await bot.set_webhook(webhook_url, secret_token=webhook_secret or None, allowed_updates=dp.resolve_used_update_types())
        print(f"✅ Telegram webhook set: {webhook_url}")
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
    }


@app.get("/")
async def root():
    return {"ok": True, "service": "prive-bot-backend"}


@app.get("/admin-api/webhook-info", dependencies=[Depends(require_admin)])
async def admin_webhook_info():
    return {"data": await bot.get_webhook_info()}


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
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not webhook_url:
        raise HTTPException(status_code=503, detail="WEBHOOK_URL is not configured")
    await bot.set_webhook(
        webhook_url,
        secret_token=webhook_secret or None,
        drop_pending_updates=False,
        allowed_updates=dp.resolve_used_update_types(),
    )
    return {"data": await bot.get_webhook_info()}


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

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
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

    db.reload_config(force=True)
    groups = resolve_plan_groups(plan_name)
    if not groups:
        raise HTTPException(status_code=400, detail="Tên gói chưa khớp group nào. Kiểm tra tên gói hoặc cấu hình BTN_G/ID_G.")

    try:
        amount = float(str(body.get("amount", "0") or 0))
    except (TypeError, ValueError):
        amount = 0.0

    payment_currency = str(body.get("payment_currency") or "VND").strip().upper() or "VND"
    payment_provider = str(body.get("payment_provider") or "MANUAL").strip().upper() or "MANUAL"

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
        "{links_text}\n{support_text}",
    ) or "").strip()
    supabase_store.create_order(
        order_id=order_id,
        telegram_user_id=telegram_user_id,
        full_name=full_name or telegram_user_id,
        plan_name=plan_name,
        amount=amount,
        sale_id=sale_id,
        original_amount=body.get("original_amount", amount),
        coupon_code=coupon_code,
        payment_currency=payment_currency,
        payment_provider=payment_provider,
        metadata={
            "manual_order": True,
            "payment_currency": payment_currency,
            "payment_provider": payment_provider,
        },
    )
    order_data = supabase_store.mark_order_paid(
        order_id,
        paid_at=paid_at.isoformat(timespec="seconds"),
        expire_at=expire_at.isoformat(timespec="seconds"),
    )

    support_link, support_error = await create_support_invite_link(user_id)
    if support_link:
        support_text = render_manual_order_support_text("", {
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
            "payment_currency": payment_currency,
            "payment_provider": payment_provider,
            "paid_at": paid_at.isoformat(timespec="seconds"),
            "expire_at": format_manual_expire_at(expire_at.isoformat(timespec="seconds")),
            "group_names": "",
            "links_text": "",
            "activation_code": activation_code,
            "activation_url": activation_url,
            "support_link": support_link,
            "support_error": support_error,
            "support_text": support_text,
            "bot_link_title": render_activation_text("MANUAL_ORDER_LINK_TITLE", "🔗 Link kích hoạt qua bot", {}),
            "bot_link_subtitle": render_activation_text("MANUAL_ORDER_LINK_SUBTITLE", "Khách bấm link này để vào bot, bot sẽ tự tạo link join group cho đơn của họ.", {}),
            "bot_link_button_label": render_activation_text("MANUAL_ORDER_LINK_BUTTON_LABEL", "Mở bot nhận link", {}),
            "bot_link_join_label": render_activation_text("MANUAL_ORDER_LINK_JOIN_LABEL", "Nhận link join group", {}),
            "bot_link_success_text": render_activation_text("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đã xác minh đơn của bạn. Bấm nút bên dưới để nhận link vào group.", {}),
            "bot_link_processing_text": render_activation_text("MANUAL_ORDER_LINK_PROCESSING_TEXT", "⏳ Bot đang xác minh đơn hàng và tạo link join group...", {}),
            "manual_order_text": render_manual_order_message_text(message_template, {
                "order_id": order_id,
                "telegram_user_id": telegram_user_id,
                "full_name": full_name or telegram_user_id,
                "plan_name": plan_name,
                "expire_at": expire_at.isoformat(timespec="seconds"),
                "links_text": "",
                "support_text": support_text,
                "support_group_name": support_group_name(),
                "support_link": support_link,
                "support_error": support_error,
                "activation_url": activation_url,
                "activation_code": activation_code,
            }),
            "failed_groups": [],
        }
    }


@app.get("/admin-api/users", dependencies=[Depends(require_admin)])
async def admin_users(limit: int = 200):
    return {"data": supabase_store.list_users(limit=limit)}


@app.get("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_config():
    return {"data": supabase_store.get_config()}


@app.patch("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_set_config(key: str, request: Request):
    body = await request.json()
    data = supabase_store.set_config(key, body.get("value", ""))
    db.cache_config[str(key).strip().upper()] = str(body.get("value", ""))
    normalized_key = str(key).strip().upper()
    if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_"):
        await set_commands()
    return {"data": data}


@app.post("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_set_config_batch(request: Request):
    body = await request.json()
    items = body.get("items", body if isinstance(body, list) else [])
    data = supabase_store.set_configs(items)
    command_changed = False
    for item in items:
        normalized_key = str(item.get("key", "")).strip().upper()
        if not normalized_key:
            continue
        db.cache_config[normalized_key] = str(item.get("value", ""))
        if normalized_key == "COUPON_COMMAND_ENABLED" or normalized_key.startswith("BOT_COMMAND_DESC_"):
            command_changed = True
    if command_changed:
        await set_commands()
    return {"data": data}


@app.delete("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_delete_config(key: str):
    data = supabase_store.delete_config(key)
    db.cache_config.pop(str(key).strip().upper(), None)
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
        print(f"⚠️ Không dựng được danh sách quét VIP group: {exc}")
        raise HTTPException(status_code=500, detail=f"Không dựng được danh sách quét VIP group: {exc}")


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
        result["get_chat"]["message"] = explain_support_invite_error(exc, gid)
        return {"data": result}

    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(gid, me.id)
        result["bot_member"] = {"ok": True, "message": str(getattr(member, "status", ""))}
    except Exception as exc:
        result["bot_member"]["message"] = explain_support_invite_error(exc, gid)

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
