import asyncio
import html
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command

from database import db
from bot_instance import bot
from bot_links import normalize_bot_link_template
from hidden_group_utils import display_plan_name
from supabase_store import supabase_store
from helpers import bot_unavailable_reason, check_protection, cleanup_welcome, is_admin_user, smart_display
from message_classifier_utils import classify_private_message
from support_utils import create_support_invite_link
from i18n import get_user_language, set_user_language, t
from modules.mod_engine import build_dynamic_keyboard, page_exists, render_page, send_with_html_fallback 
from sale_utils import build_sale_announcement
from scheduler import check_expirations_professional
from renewal_utils import is_early_renew_enabled

router = Router()


def cfg(key, default=""):
    return str(db.get_config(key, default) or default).strip()


def language_from_start_payload(payload: str) -> str | None:
    normalized = str(payload or "").strip().lower()
    if not normalized:
        return None
    for part in normalized.split("_"):
        if part == "len":
            return "en"
        if part == "lvi":
            return "vi"
    return None


def render_cfg(key, default, values=None):
    text = cfg(key, default)
    for item_key, item_value in (values or {}).items():
        text = text.replace(f"{{{item_key}}}", str(item_value or ""))
    return text.replace("\\n", "\n")


def normalize_manual_order_link_template(template: str) -> str:
    return normalize_bot_link_template(template, default_payload="act_{code}")


def build_manual_order_link(code: str) -> str:
    template = normalize_manual_order_link_template(db.get_config("MANUAL_ORDER_LINK_TEMPLATE", "") or "")
    return template.replace("{code}", str(code or "").strip())


def build_manual_order_message_link(code: str) -> str:
    template = normalize_manual_order_link_template(db.get_config("MANUAL_ORDER_MESSAGE_LINK_TEMPLATE", "") or "")
    if "start=act_{code}" in template:
        template = template.replace("start=act_{code}", "start=actmsg_{code}")
    elif "start={code}" in template:
        template = template.replace("start={code}", "start=actmsg_{code}")
    return template.replace("{code}", str(code or "").strip())


def render_manual_order_info_text(context: dict[str, object]):
    return (
        render_cfg(
            "MANUAL_ORDER_INFO_TEMPLATE",
            "🧾 Đơn hàng: {order_id}\n👤 Khách hàng: {full_name} - ID: {telegram_user_id}\n📦 Gói: {plan_name}\n⏳ Hạn dùng: {expire_at}",
            context,
        )
    )


def render_manual_order_support_text(context: dict[str, object]):
    return render_cfg("MANUAL_ORDER_SUPPORT_TEMPLATE", "💬 {support_group_name}:\n{support_link}", context)


def render_manual_order_message_text(context: dict[str, object]):
    return render_cfg(
        "MANUAL_ORDER_MESSAGE_TEMPLATE",
        "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}\n\n{support_text}",
        context,
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


def language_switch_keyboard(current_language):
    kb = InlineKeyboardBuilder()
    if current_language == "en":
        kb.row(InlineKeyboardButton(text="🇻🇳 Tiếng Việt", callback_data="set_lang:vi"))
    else:
        kb.row(InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"))
    kb.row(InlineKeyboardButton(text="🏠 Main menu", callback_data="back_main"))
    return kb.as_markup()

def format_membership_expire(value, user_id=None):
    raw = str(value or "").strip()
    if not raw:
        return "-"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
            try:
                timezone = ZoneInfo(timezone_name)
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                parsed = None
        if not parsed:
            return raw.replace("T", " ").replace("+00:00", "")

    return parsed.strftime("%d/%m/%Y %H:%M")


def format_manual_expire(value):
    raw = str(value or "").strip()
    if not raw:
        return "-"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
            try:
                timezone = ZoneInfo(timezone_name)
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                parsed = None
        if not parsed:
            return raw.replace("T", " ").replace("+00:00", "")
    return parsed.strftime("%H:%M %d/%m/%Y")


def is_lifetime_plan_name(plan_name: str) -> bool:
    text = str(plan_name or "").strip().lower()
    return any(part in text for part in ("trọn đời", "tron doi", "lifetime", "life"))


def parse_membership_expire_dt(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
            try:
                timezone = ZoneInfo(timezone_name)
            except Exception:
                timezone = ZoneInfo("Asia/Ho_Chi_Minh")
            parsed = parsed.astimezone(timezone).replace(tzinfo=None)
        return parsed
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None

def order_to_me_item(order):
    return [
        order.get("order_id", ""),
        order.get("telegram_user_id", ""),
        order.get("full_name", ""),
        order.get("plan_name", ""),
        order.get("amount", ""),
        order.get("status", ""),
        order.get("paid_at", ""),
        order.get("expire_at", ""),
    ]

# [1] HÀM CŨ DỰ PHÒNG CHỐNG LỖI IMPORT
async def send_welcome_messages(event):
    await cmd_start(event)

# [2] LỆNH RELOAD
@router.message(Command("reload"))
async def cmd_reload(message: Message):
    if is_admin_user(message.from_user.id):
        db.reload_config(force=True)
        await message.reply(db.get_config("MSG_RELOAD_DONE", "🔄 Đã nạp lại toàn bộ dữ liệu & giao diện từ hệ thống!"))
    else:
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))

@router.message(Command("check_expiry"))
async def cmd_check_expiry(message: Message):
    if not is_admin_user(message.from_user.id):
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))
        return

    await message.reply(db.get_config("MSG_CHECK_EXPIRY_STARTED", "⏳ Đang quét hạn dùng ngay bây giờ..."))
    await check_expirations_professional()
    await message.reply(db.get_config("MSG_CHECK_EXPIRY_DONE", "✅ Đã chạy xong một vòng quét hạn dùng. Xem log server để biết dòng nào đã gửi/kick hoặc bị bỏ qua."))

@router.message(Command("early_renew"))
async def cmd_early_renew(message: Message):
    if not is_admin_user(message.from_user.id):
        await message.reply(db.get_config("MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        status = "ON" if is_early_renew_enabled() else "OFF"
        await message.reply(
            db.get_config("MSG_EARLY_RENEW_STATUS", "EARLY_RENEW hiện đang: <b>{status}</b>\\nDùng: /early_renew on hoặc /early_renew off").replace("\\n", "\n").replace("{status}", status),
            parse_mode="HTML",
        )
        return

    action = parts[1].strip().lower()
    if action in {"on", "1", "true", "yes", "bat", "bật"}:
        db.set_config("EARLY_RENEW_ENABLED", "ON")
        await message.reply(db.get_config("MSG_EARLY_RENEW_ON", "✅ Đã bật EARLY_RENEW. Tin nhắc gia hạn sẽ kèm ưu đãi nếu đủ điều kiện."))
    elif action in {"off", "0", "false", "no", "tat", "tắt"}:
        db.set_config("EARLY_RENEW_ENABLED", "OFF")
        await message.reply(db.get_config("MSG_EARLY_RENEW_OFF", "✅ Đã tắt EARLY_RENEW. Tin nhắc gia hạn sẽ dùng nội dung và nút gia hạn thường."))
    else:
        await message.reply(db.get_config("MSG_EARLY_RENEW_USAGE", "Cú pháp: /early_renew on hoặc /early_renew off"))

async def send_sale_announcement(message: Message):
    enabled = str(db.get_config("SALE_ANNOUNCE_ENABLED", "ON")).strip().upper()
    if enabled in ["OFF", "FALSE", "NO", "0", "TẮT", "TAT"]:
        return False

    text = build_sale_announcement()
    if not text:
        return False

    img = str(db.get_config("IMG_SALE_BANNER", "")).strip()
    layout = db.get_config(
        "SALE_ANNOUNCE_BUTTONS",
        "🔥 Mua SVIP Trọn Đời => buy_full_life\n💎 Mua SVIP 30 Ngày => buy_full_1m\n📋 Xem toàn bộ gói => nav:main_menu",
    ).replace("\\n", "\n")
    reply_markup = build_dynamic_keyboard(layout) if layout.strip() else None

    try:
        if img and len(img) > 10:
            await send_with_html_fallback(message, photo=img, text=text, reply_markup=reply_markup)
        else:
            await send_with_html_fallback(message, text=text, reply_markup=reply_markup)
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi thông báo sale: {e}")
        return False


async def record_start_event(message: Message, payload: str, event_type: str, *, source_ref: str = "", activation_code: str = "", legacy: bool = False):
    event_payload = {
        "event_type": event_type,
        "command": "start",
        "start_payload": payload,
        "source_ref": source_ref,
        "activation_code": activation_code,
        "legacy": bool(legacy),
        "user_id": str(message.from_user.id) if message.from_user else "",
        "username": message.from_user.username or "" if message.from_user else "",
        "full_name": message.from_user.full_name or "" if message.from_user else "",
        "chat_id": str(message.chat.id) if message.chat else "",
        "chat_type": message.chat.type if message.chat else "",
    }
    try:
        supabase_store.insert_analytics_events([event_payload])
    except Exception as exc:
        print(f"⚠️ Không ghi được start event {event_type}: {exc}")


async def deliver_activation_order(message: Message, code: str):
    from modules.mod_coupon import build_invite_links

    activation = supabase_store.get_order_activation_code(code) if supabase_store.enabled else None
    if not activation:
        await message.answer(render_cfg("MANUAL_ORDER_LINK_INVALID_TEXT", "❌ Mã kích hoạt không hợp lệ hoặc đã bị vô hiệu hoá."))
        return

    status = str(activation.get("activation_status") or "PENDING").upper()
    telegram_user_id = str(activation.get("telegram_user_id") or "").strip()
    expire_at = str(activation.get("expire_at") or "").strip()
    now_user_id = str(message.from_user.id)
    raw_data = activation.get("raw_data") if isinstance(activation.get("raw_data"), dict) else {}
    inferred_language = infer_language_from_payment_context(
        payment_currency=activation.get("payment_currency", ""),
        payment_provider=activation.get("payment_provider", ""),
        raw_data=raw_data,
    )
    if inferred_language:
        set_user_language(message.from_user.id, inferred_language)
        if telegram_user_id:
            set_user_language(telegram_user_id, inferred_language)

    if telegram_user_id and telegram_user_id != now_user_id:
        await message.answer(render_cfg("MANUAL_ORDER_LINK_WRONG_USER_TEXT", "❌ Mã này không dành cho tài khoản Telegram hiện tại."))
        return

    if expire_at:
        try:
            parsed_expire = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
            if parsed_expire.tzinfo:
                parsed_expire = parsed_expire.astimezone(ZoneInfo(str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh"))).replace(tzinfo=None)
            if parsed_expire < datetime.now():
                await message.answer(render_cfg("MANUAL_ORDER_LINK_EXPIRED_TEXT", "⏰ Mã kích hoạt đã hết hạn. Vui lòng liên hệ admin."))
                return
        except Exception:
            pass

    processing_message = await message.answer(render_cfg("MANUAL_ORDER_LINK_PROCESSING_TEXT", "⏳ Bot đang xác minh đơn hàng và tạo link join group..."))
    try:
        plan_name = str(activation.get("plan_name") or "").strip()
        links_text, group_names, failed_groups, invite_results = await build_invite_links(message.from_user.id, plan_name)
        if failed_groups or not group_names:
            try:
                supabase_store.record_support_event(
                    "manual_activation_link_failed",
                    telegram_user_id,
                    full_name=activation.get("full_name", ""),
                    order_id=activation.get("order_id", ""),
                    plan_name=plan_name,
                    raw_data={
                        "activation_code": code,
                        "failed_groups": failed_groups,
                        "invite_results": invite_results,
                        "links_text": links_text,
                        "status": "failed" if not group_names else "partial",
                    },
                )
            except Exception as exc:
                print(f"⚠️ Không ghi được manual_activation_link_failed cho {code}: {exc}")
            if not group_names:
                await message.answer(render_cfg("MANUAL_ORDER_LINK_FAIL_TEXT", "❌ Bot chưa tạo được link join group. Vui lòng thử lại sau."))
                return

        activation_update_at = datetime.now().isoformat(timespec="seconds")
        try:
            raw_data = dict(activation.get("raw_data") or {})
            raw_data.update({
                "activation_code": code,
                "group_names": group_names,
                "failed_groups": failed_groups,
                "invite_results": invite_results,
                "invite_cleanup_after_days": int(db.get_config("ACTIVATION_LINK_CLEANUP_DAYS", "7") or 7),
                "invite_cleanup_due_at": (datetime.now() + timedelta(days=max(1, int(db.get_config("ACTIVATION_LINK_CLEANUP_DAYS", "7") or 7)))).isoformat(timespec="seconds"),
            })
            update_payload = {
                "raw_data": raw_data,
                "activation_status": "USED",
                "activated_at": activation_update_at,
                "activated_by_user_id": message.from_user.id,
                "used_at": activation_update_at,
                "used_by_user_id": message.from_user.id,
            }
            supabase_store.update_order_activation_code(code, update_payload)
            if activation.get("order_id"):
                supabase_store.update_order_activation_code_by_order(activation.get("order_id"), update_payload)
            supabase_store.mark_order_activation_used(code, message.from_user.id, activated_at=activation_update_at)
        except Exception as exc:
            print(f"⚠️ Không ghi được activation used cho {code}: {exc}")

        render_context = {
            "order_id": activation.get("order_id", ""),
            "telegram_user_id": telegram_user_id,
            "full_name": activation.get("full_name", ""),
            "plan_name": plan_name,
            "expire_at": format_manual_expire(expire_at),
            "support_group_name": db.get_config("SUPPORT_GROUP_NAME", "support group"),
        }
        support_link, support_error = await create_support_invite_link(message.from_user.id)
        render_context["support_link"] = support_link or ""
        render_context["support_error"] = support_error or ""
        support_text = render_cfg("MANUAL_ORDER_SUPPORT_TEMPLATE", "💬 {support_group_name}:\n{support_link}", render_context)
        if not support_text and support_error:
            support_text = render_cfg(
                "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
                "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
                render_context,
            )
        render_context["support_text"] = support_text
        try:
            supabase_store.record_support_event(
                "manual_activation_link_generated",
                telegram_user_id,
                full_name=activation.get("full_name", ""),
                order_id=activation.get("order_id", ""),
                plan_name=plan_name,
                raw_data={
                    "activation_code": code,
                    "group_names": group_names,
                    "failed_groups": failed_groups,
                    "invite_results": invite_results,
                    "support_link_created": bool(support_link),
                    "support_error": support_error,
                    "activation_status": "partial" if failed_groups else "ok",
                },
            )
        except Exception as exc:
            print(f"⚠️ Không ghi được manual_activation_link_generated cho {code}: {exc}")
        if failed_groups:
            failed_group_text = ", ".join(failed_groups)
            failed_notice = render_cfg(
                "MANUAL_ORDER_LINK_PARTIAL_TEXT",
                "⚠️ Một số group chưa tạo được link: {failed_groups}",
                {"failed_groups": failed_group_text},
            )
            render_context["partial_text"] = failed_notice
        else:
            render_context["partial_text"] = ""
        delivery_text = render_cfg(
            "MANUAL_ORDER_DELIVERY_TEMPLATE",
            "{success_text}\n\n{order_text}\n\n{links_text}\n\n{partial_text}\n\n{support_text}",
            {
                **render_context,
                "success_text": render_cfg("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh."),
                "links_text": links_text,
                "links_status": "partial" if failed_groups else "ok",
                "order_text": render_cfg(
                    "MANUAL_ORDER_INFO_TEMPLATE",
                    "🧾 Đơn hàng: {order_id}\n👤 Khách hàng: {full_name} - ID: {telegram_user_id}\n📦 Gói: {plan_name}\n⏳ Hạn dùng: {expire_at}",
                    render_context,
                ),
            },
        )
        await message.answer(delivery_text, parse_mode="HTML")
    finally:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        except Exception:
            pass


async def deliver_manual_order_message(message: Message, code: str):
    activation = supabase_store.get_order_activation_code(code) if supabase_store.enabled else None
    if not activation:
        await message.answer(render_cfg("MANUAL_ORDER_LINK_INVALID_TEXT", "❌ Mã kích hoạt không hợp lệ hoặc đã bị vô hiệu hoá."))
        return

    status = str(activation.get("activation_status") or "PENDING").upper()
    telegram_user_id = str(activation.get("telegram_user_id") or "").strip()
    expire_at = str(activation.get("expire_at") or "").strip()
    now_user_id = str(message.from_user.id)

    if telegram_user_id and telegram_user_id != now_user_id:
        await message.answer(render_cfg("MANUAL_ORDER_LINK_WRONG_USER_TEXT", "❌ Mã này không dành cho tài khoản Telegram hiện tại."))
        return
    if status == "USED":
        await message.answer(render_cfg("MANUAL_ORDER_LINK_USED_TEXT", "ℹ️ Mã này đã được kích hoạt rồi. Nếu cần, admin hãy tạo lại link mới."))
        return

    if expire_at:
        try:
            parsed_expire = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
            if parsed_expire.tzinfo:
                parsed_expire = parsed_expire.astimezone(ZoneInfo(str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh"))).replace(tzinfo=None)
            if parsed_expire < datetime.now():
                await message.answer(render_cfg("MANUAL_ORDER_LINK_EXPIRED_TEXT", "⏰ Mã kích hoạt đã hết hạn. Vui lòng liên hệ admin."))
                return
        except Exception:
            pass

    render_context = {
        "order_id": activation.get("order_id", ""),
        "telegram_user_id": telegram_user_id,
        "full_name": activation.get("full_name", ""),
        "plan_name": activation.get("plan_name", ""),
        "expire_at": format_manual_expire(expire_at),
        "support_group_name": db.get_config("SUPPORT_GROUP_NAME", "support group"),
    }

    try:
        support_link, support_error = await create_support_invite_link(message.from_user.id)
        render_context["support_link"] = support_link or ""
        render_context["support_error"] = support_error or ""
    except Exception as exc:
        render_context["support_link"] = ""
        render_context["support_error"] = str(exc)
        print(f"⚠️ Không tạo được support link cho manual order message {code}: {exc}")

    support_text = render_cfg("MANUAL_ORDER_SUPPORT_TEMPLATE", "💬 {support_group_name}:\n{support_link}", render_context)
    if not support_text and render_context.get("support_error"):
        support_text = render_cfg(
            "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
            "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
            render_context,
        )
    render_context["support_text"] = support_text
    render_context["activation_url"] = build_manual_order_link(code)
    render_context["message_url"] = build_manual_order_message_link(code)
    render_context["success_text"] = render_cfg("MANUAL_ORDER_LINK_SUCCESS_TEXT", "✅ Đơn của bạn đã được xác minh.", {})
    render_context["bot_link_title"] = render_cfg("MANUAL_ORDER_LINK_TITLE", "🔗 Link kích hoạt", {})
    render_context["bot_link_subtitle"] = render_cfg("MANUAL_ORDER_LINK_SUBTITLE", "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", {})
    render_context["order_text"] = render_manual_order_info_text(render_context)
    render_context["links_text"] = render_cfg(
        "MANUAL_ORDER_MESSAGE_LINK_TEXT",
        "🔗 Link kích hoạt: {activation_url}\n💬 Link mở bot chi tiết: {message_url}",
        render_context,
    )
    render_context["partial_text"] = ""
    delivery_text = render_cfg(
        "MANUAL_ORDER_MESSAGE_TEMPLATE",
        "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{message_url}\n\n{bot_link_subtitle}\n\n{support_text}",
        render_context,
    )
    await message.answer(delivery_text, parse_mode="HTML")

# [3] LỆNH START & QUAY LẠI MENU CHÍNH
@router.message(CommandStart())
async def cmd_start(message: Message):
    payload_preview = (message.text or "").replace("\n", " ")[:120]
    entity_types = [getattr(entity, "type", "") for entity in (getattr(message, "entities", None) or [])]
    print(
        "🚀 cmd_start entered "
        f"user={message.from_user.id} chat={message.chat.id} text={payload_preview} entities={entity_types}"
    )

    async def _send_start_fallback(reason: str = ""):
        fallback_text = db.get_config(
            "MSG_START_FALLBACK",
            "👋 Chào mừng bạn quay lại bot.\nDùng /menu để mở trang chính hoặc /support nếu cần hỗ trợ.",
        ).replace("\\n", "\n")
        if reason:
            print(f"⚠️ /start fallback for user {message.from_user.id}: {reason}")
        try:
            await message.answer(fallback_text)
        except Exception as exc:
            print(f"❌ Không gửi được fallback /start cho user {message.from_user.id}: {exc}")

    try:
        db.reload_config(force=True)
        await cleanup_welcome(message.from_user.id, message.chat.id)
        parts = (message.text or "").split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        print(f"🚀 cmd_start payload user={message.from_user.id} payload={payload[:120]}")
        if payload:
            normalized = payload.strip()
            inferred_language = language_from_start_payload(normalized)
            if inferred_language:
                set_user_language(message.from_user.id, inferred_language)
            classified = classify_private_message(message)
            if classified["kind"] == "other" and classified["reason"] == "start_source":
                print(f"🚀 cmd_start source payload user={message.from_user.id} source_ref={normalized[4:].strip()}")
                await record_start_event(
                    message,
                    normalized,
                    "start_source",
                    source_ref=normalized[4:].strip(),
                )
                if await send_sale_announcement(message):
                    return
                rendered = await render_page(message, "main_menu")
                if rendered:
                    return
                await _send_start_fallback("render_page returned False for src_ payload")
                return
            if normalized.lower().startswith("actmsg_"):
                activation_code = normalized[7:].strip()
                print(f"🚀 cmd_start manual message payload user={message.from_user.id} activation_code={activation_code}")
                await record_start_event(
                    message,
                    normalized,
                    "start_manual_message",
                    activation_code=activation_code,
                )
                await deliver_manual_order_message(message, activation_code)
                return
            if classified["kind"] == "activation":
                activation_code = classified["code"]
                print(f"🚀 cmd_start activation payload user={message.from_user.id} activation_code={activation_code}")
                await record_start_event(
                    message,
                    normalized,
                    "start_activation",
                    activation_code=activation_code,
                )
                await deliver_activation_order(message, activation_code)
                return
            await record_start_event(
                message,
                normalized,
                "start_activation_legacy",
                activation_code=normalized,
                legacy=True,
            )
            print(f"🚀 cmd_start legacy activation user={message.from_user.id} activation_code={normalized}")
            await deliver_activation_order(message, normalized)
            return
        unavailable_reason = bot_unavailable_reason()
        if unavailable_reason and not is_admin_user(message.from_user.id):
            print(f"🚀 cmd_start maintenance branch user={message.from_user.id} reason={unavailable_reason}")
            if unavailable_reason == "schedule":
                notice = db.get_config(
                    "MSG_OUTSIDE_ACTIVE_HOURS",
                    "🛠 <b>BOT ĐANG NGOÀI GIỜ HOẠT ĐỘNG</b>\n\nBot hiện ở chế độ bảo trì. Vui lòng quay lại trong khung giờ hoạt động.",
                ).replace("\\n", "\n")
            else:
                notice = db.get_config(
                    "MSG_MAINTENANCE",
                    "🛠 <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nAdmin đang nâng cấp hệ thống. Bạn vui lòng quay lại sau ít phút nhé!",
                ).replace("\\n", "\n")
            try:
                await message.answer(notice, parse_mode="HTML")
            except Exception as exc:
                await _send_start_fallback(f"maintenance reply failed: {exc}")
            return

        if not await check_protection(message):
            print(f"🚀 cmd_start stopped by protection user={message.from_user.id}")
            return
        if await send_sale_announcement(message):
            print(f"🚀 cmd_start sale announcement sent user={message.from_user.id}")
            return
        rendered = await render_page(message, "main_menu")
        if rendered:
            print(f"🚀 cmd_start main menu rendered user={message.from_user.id}")
            return
        await _send_start_fallback("render_page returned False for main_menu")
    except Exception as exc:
        print(f"❌ /start error for user {message.from_user.id}: {exc}")
        await _send_start_fallback(str(exc))

@router.message(Command("menu"))
@router.message(Command("home"))
async def cmd_menu(message: Message):
    if not await check_protection(message): return
    db.reload_config(force=True)
    await cleanup_welcome(message.from_user.id, message.chat.id)
    await render_page(message, "main_menu")

@router.message(Command("lang"))
@router.message(Command("language"))
async def cmd_language(message: Message):
    if not await check_protection(message): return
    current_language = get_user_language(message.from_user.id)
    text = (
        "Choose your language and I’ll bring you back to the main menu."
        if current_language == "en"
        else "Chọn ngôn ngữ để quay lại menu chính."
    )
    await message.answer(text, reply_markup=language_switch_keyboard(current_language))

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not await check_protection(callback): return
    await render_page(callback, "main_menu")

@router.callback_query(F.data.startswith("set_lang:"))
async def change_language(callback: CallbackQuery):
    if not await check_protection(callback):
        return
    language = set_user_language(callback.from_user.id, callback.data.split(":", 1)[1])
    try:
        await callback.answer("Language updated." if language == "en" else "Đã đổi ngôn ngữ.")
    except Exception as exc:
        if "query is too old" not in str(exc).lower() and "query id is invalid" not in str(exc).lower():
            raise
    try:
        rendered = await render_page(callback, "main_menu")
        if rendered:
            return
    except Exception as exc:
        print(f"❌ Lỗi render menu sau khi đổi ngôn ngữ user {callback.from_user.id}: {exc}")

    fallback = "Language updated, but the menu could not be loaded. Please send /start." if language == "en" else "Đã đổi ngôn ngữ nhưng chưa tải được menu. Vui lòng gửi /start."
    await callback.message.answer(fallback)

# [4] TRANG QUY ĐỊNH (PHỤC HỒI CODE CŨ + BỔ SUNG LỆNH)
@router.message(Command("policy"))
@router.callback_query(F.data == "policy")
@router.callback_query(F.data == "policy_page")
@router.callback_query(F.data == "nav:policy_page")
async def view_policy(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    # Ưu tiên gọi giao diện động hiện có trong hệ thống. Nếu thiếu page thì lùi về nội dung fallback.
    try:
        if not page_exists("policy_page"):
            db.reload_config(force=True)
        if page_exists("policy_page"):
            rendered = await render_page(event, "policy_page")
            if rendered:
                return
    except Exception as e:
        print(f"❌ Lỗi render policy_page: {e}")

    try:
        text = t(event.from_user.id, "MSG_POLICY", "Chính sách đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_POLICY"))
    except Exception as e:
        print(f"❌ Lỗi fallback /policy: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer(t(event.from_user.id, "ALERT_POLICY_UNAVAILABLE", "Không thể mở trang quy định lúc này."), show_alert=True)

# [5] TRANG HỖ TRỢ (PHỤC HỒI CODE CŨ + BỔ SUNG LỆNH)
@router.message(Command("support"))
@router.callback_query(F.data == "support_info")
@router.callback_query(F.data == "nav:support_page")
async def view_support(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    # Ưu tiên gọi giao diện động hiện có trong hệ thống. Nếu thiếu page thì lùi về nội dung fallback.
    try:
        if not page_exists("support_page"):
            db.reload_config(force=True)
        if page_exists("support_page"):
            rendered = await render_page(event, "support_page")
            if rendered:
                return
    except Exception as e:
        print(f"❌ Lỗi render support_page: {e}")

    try:
        text = t(event.from_user.id, "MSG_SUPPORT", "Hỗ trợ đang cập nhật...")
        kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại"), callback_data="back_main"))
        await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_SUPPORT"))
    except Exception as e:
        print(f"❌ Lỗi fallback /support: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer(t(event.from_user.id, "ALERT_SUPPORT_UNAVAILABLE", "Không thể mở trang hỗ trợ lúc này."), show_alert=True)

# [6] TRANG THÔNG TIN TÀI KHOẢN (/ME)
@router.message(Command("me"))
@router.callback_query(F.data == "my_info")
async def cmd_me(event):
    if not await check_protection(event): return
    chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
    await cleanup_welcome(event.from_user.id, chat_id)
    
    user_id = str(event.from_user.id)
    if supabase_store.enabled:
        my_plans = [
            order_to_me_item(order)
            for order in supabase_store.list_paid_orders_for_user(user_id, limit=100)
        ]
    else:
        db.connect()
        all_data = db.users_sheet.get_all_values()
        my_plans = [row for row in all_data if len(row) > 7 and str(row[1]) == user_id and row[5] == "PAID"]
    
    text = t(event.from_user.id, "MSG_ME_TITLE", "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\n\n").replace("\\n", "\n")
    active_plans = []
    expired_plans = []
    if not my_plans: 
        text += t(event.from_user.id, "MSG_ME_EMPTY", "❌ Bạn chưa có gói VIP nào.")
    else:
        now = datetime.now()
        for p in my_plans:
            expire_dt = parse_membership_expire_dt(p[7])
            if is_lifetime_plan_name(str(p[3])) or (expire_dt and expire_dt > now):
                active_plans.append(p)
            else:
                expired_plans.append(p)
        for p in my_plans: 
            expire_text = format_membership_expire(p[7], event.from_user.id)
            text += t(event.from_user.id, "MSG_ME_ITEM", "🎁 Gói: <b>{plan}</b>\n📅 Hạn: <code>{date}</code>\n\n").replace("\\n", "\n").replace("{plan}", display_plan_name(str(p[3]), event.from_user.id)).replace("{date}", expire_text)
            
    kb = InlineKeyboardBuilder()
    if my_plans:
        latest_plan = active_plans[0] if active_plans else my_plans[0]
        latest_plan_name = str(latest_plan[3] or "").strip()
        latest_order_id = str(latest_plan[0] or "").strip()
        if is_lifetime_plan_name(latest_plan_name):
            if latest_order_id:
                kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_RENEW", "🔄 Gia hạn nhanh"), callback_data=f"renew_order_{latest_order_id}"))
            kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
        elif "svip" in latest_plan_name.lower() or "full" in latest_plan_name.lower():
            if latest_order_id:
                kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_RENEW", "🔄 Gia hạn nhanh"), callback_data=f"renew_order_{latest_order_id}"))
            kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_UPGRADE", "🌟 Nâng cấp lên Trọn đời"), callback_data="buy_full_life"))
            kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
        else:
            if latest_order_id:
                kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_RENEW", "🔄 Gia hạn nhanh"), callback_data=f"renew_order_{latest_order_id}"))
            kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_UPGRADE_SVIP", "🌟 Xem gói SVIP+"), callback_data="view_svip_page"))
            kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    else:
        kb.row(InlineKeyboardButton(text=t(event.from_user.id, "BTN_BACK", "🔙 Quay lại Menu"), callback_data="back_main"))
    
    await smart_display(event, text, kb.as_markup(), img=db.get_config("IMG_ME", ""))

# [7] CÔNG CỤ ADMIN: LẤY FILE_ID CỦA ẢNH
@router.message(F.photo)
async def get_file_id(message: Message):
    if message.chat.type != "private":
        return
    if is_admin_user(message.from_user.id):
        await message.reply(f"<code>{message.photo[-1].file_id}</code>", parse_mode="HTML")
