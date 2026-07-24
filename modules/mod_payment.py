import asyncio
import hashlib
import hmac
import json
import os
import time
from collections import deque
import urllib.parse
import requests
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from payment import payment_manager
from processor import expire_pending_payment, parse_int_config, process_successful_payment, auto_check_loop, cancelled_orders
from bot_instance import bot
from hidden_group_utils import (
    build_hidden_plan_name,
    display_plan_name,
    extract_plan_token,
    get_hidden_group,
    hidden_code_available_groups,
    hidden_duration_days,
    hidden_duration_price,
    validate_hidden_code_for_user,
)
from supabase_store import supabase_store

from helpers import check_protection, format_currency, smart_display, cleanup_welcome, safe_delete_private_message, create_background_task, strip_html_tags
from i18n import get_user_language, localized_default, t
from modules.mod_engine import render_page
from sale_utils import format_currency as format_money, format_price_label, get_price, localized_price_key, parse_price, sale_banner
from renewal_utils import build_early_renew_offer, is_early_renew_enabled
from message_classifier_utils import classify_message_text
from support_utils import (
    record_support_event,
    support_inbox_enabled,
)
from bot_links import bot_version
from license_utils import license_backend_url, build_license_deeplink

router = Router()

BANK_NAMES = {
    "970422": "MB Bank", "970415": "VietinBank", "970436": "Vietcombank",
    "970418": "BIDV", "970423": "TPBank", "970407": "Techcombank",
    "970432": "VPBank", "970416": "ACB", "970405": "Agribank"
}

def vietqr_template():
    template = str(db.get_config("PAYOS_VIETQR_TEMPLATE", "qr_only") or "qr_only").strip().lower()
    return template if template in {"qr_only", "compact", "compact2", "print"} else "qr_only"


def vietqr_show_account_name():
    return str(db.get_config("PAYOS_VIETQR_SHOW_ACCOUNT_NAME", "OFF") or "OFF").strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}

# 🛡 BIẾN LƯU TRỮ CHỐNG SPAM
payment_spam_attempts = {}
payment_spam_block_until = {}
payment_spam_inflight = set()


def payment_cooldown_key(user_id, action, provider, message_id=""):
    return f"{user_id}:{str(provider or '').upper()}:{str(action or '')}:{str(message_id or '')}"


async def enforce_payment_cooldown(callback, action, provider):
    message_id = getattr(getattr(callback, "message", None), "message_id", "") or ""
    key = payment_cooldown_key(callback.from_user.id, action, provider, message_id=message_id)
    current_time = time.time()
    window_seconds = max(5, parse_int_config("PAYMENT_SPAM_WINDOW_SECONDS", 10))
    max_attempts = max(1, parse_int_config("PAYMENT_SPAM_MAX_ATTEMPTS", 2))
    block_seconds = max(5, parse_int_config("PAYMENT_SPAM_BLOCK_SECONDS", 15))

    blocked_until = float(payment_spam_block_until.get(key, 0) or 0)
    if blocked_until > current_time:
        remaining = max(1, int(blocked_until - current_time))
        fallback = (
            f"⏳ Slow down a bit. Too many payment attempts in a short time. Please wait {remaining}s."
            if get_user_language(callback.from_user.id) == "en"
            else f"⏳ Thao tác quá nhanh! Hãy chờ {remaining}s rồi thử lại."
        )
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", fallback), show_alert=True)
        return False

    bucket = payment_spam_attempts.get(key)
    if bucket is None:
        bucket = deque()
        payment_spam_attempts[key] = bucket
    while bucket and current_time - bucket[0] > window_seconds:
        bucket.popleft()
    bucket.append(current_time)
    if len(bucket) > max_attempts:
        payment_spam_block_until[key] = current_time + block_seconds
        bucket.clear()
        fallback = (
            f"⏳ Slow down a bit. Too many payment attempts in a short time. Please wait {block_seconds}s."
            if get_user_language(callback.from_user.id) == "en"
            else f"⏳ Thao tác quá nhanh! Hãy chờ {block_seconds}s rồi thử lại."
        )
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", fallback), show_alert=True)
        return False
    return True


def payment_spam_inflight_key(callback, action, provider):
    message_id = getattr(getattr(callback, "message", None), "message_id", "") or ""
    return payment_cooldown_key(callback.from_user.id, action, provider, message_id=message_id)

def safe_int(value_str):
    """Hàm thông minh: Tự động loại bỏ dấu chấm, dấu phẩy, chữ Đ để chống crash ValueError"""
    try:
        clean_str = str(value_str).replace('Đ', '').replace('đ', '').strip()
        if clean_str.endswith(".0") or clean_str.endswith(",0"):
            return int(float(clean_str.replace(",", ".")))
        if "." in clean_str and "," not in clean_str and len(clean_str.rsplit(".", 1)[-1]) == 3:
            clean_str = clean_str.replace(".", "")
        elif "," in clean_str and "." not in clean_str and len(clean_str.rsplit(",", 1)[-1]) == 3:
            clean_str = clean_str.replace(",", "")
        else:
            clean_str = clean_str.replace(",", ".")
        return int(float(clean_str))
    except Exception:
        return 999  # Trả về giá mặc định nếu lỗi

def currency_for_provider(provider):
    normalized = str(provider or "").upper()
    return "VND" if normalized == "PAYOS" else "USD"


def default_currency_for_user(user_id):
    return "USD" if get_user_language(user_id) == "en" else "VND"


def price_label_for_user(user_id, price_key, default=0):
    currency = default_currency_for_user(user_id)
    default_value = "0" if currency == "USD" else default
    return format_price_label(price_key, default_value, currency)


def sale_text_for_price(price_key, default=0, currency="VND"):
    banner = sale_banner(localized_price_key(price_key, currency), default)
    return f"\n\n{banner}" if banner else ""


def hidden_offer_for_action(action, user_id=None, provider=""):
    try:
        _, code, hidden_group_id, duration_key = action.split("|", 3)
    except ValueError:
        return {}
    classified = classify_message_text(code)
    if classified["kind"] not in {"hidden", "other"}:
        return {"error": "Mã hidden không hợp lệ."}
    hidden_code, reason = validate_hidden_code_for_user(code, user_id)
    if not hidden_code:
        return {"error": reason or "Mã hidden không hợp lệ."}
    hidden_group = get_hidden_group(hidden_group_id)
    if not hidden_group or not hidden_group.get("is_active"):
        return {"error": "Nhóm ẩn không tồn tại hoặc đang tắt."}
    if hidden_group_id not in {item.get("id") for item in hidden_code_available_groups(hidden_code)}:
        return {"error": "Nhóm ẩn không thuộc phạm vi mã này."}
    currency = currency_for_provider(provider) if provider else default_currency_for_user(user_id)
    amount = hidden_duration_price(hidden_group, duration_key, currency)
    if amount <= 0:
        return {"error": "Nhóm ẩn chưa cấu hình giá cho phương thức này."}
    plan_name = build_hidden_plan_name(hidden_group, duration_key)
    return {
        "plan_name": plan_name,
        "display_name": display_plan_name(plan_name, user_id),
        "plan_token": extract_plan_token(plan_name),
        "price_key": "",
        "amount": amount,
        "sale_info": None,
        "original_amount": amount,
        "currency": currency,
        "source_ref": str(code or "").strip().upper(),
        "metadata": {
            "hidden_code": str(code or "").strip().upper(),
            "hidden_group_id": hidden_group_id,
            "duration_key": duration_key.upper(),
            "duration_days": hidden_duration_days(hidden_group, duration_key),
        },
    }

def create_pending_order(
    order_id,
    user_id,
    full_name,
    plan_name,
    amount,
    sale_id="",
    original_amount=None,
    coupon_code="",
    coupon_discount_percent=0,
    coupon_discount_amount=0,
    payment_provider="",
    payment_provider_order_id="",
    payment_approval_url="",
    payment_currency="VND",
    activation_code="",
    customer_ref="",
    plan_code="",
    payment_locale="",
    plan_token="",
    plan_category="",
    source_type="",
    source_ref="",
    metadata=None,
):
    version = bot_version()
    if not source_type:
        source_type = "BOT_LEGACY" if version == "legacy" else "BOT_NEW"
    metadata_payload = metadata if isinstance(metadata, dict) else metadata
    if isinstance(metadata_payload, dict):
        metadata_payload = dict(metadata_payload)
        metadata_payload.setdefault("bot_version", version)
        if activation_code and not metadata_payload.get("activation_code"):
            metadata_payload["activation_code"] = str(activation_code).strip().upper()
        if customer_ref and not metadata_payload.get("customer_ref"):
            metadata_payload["customer_ref"] = str(customer_ref).strip()
        if plan_code and not metadata_payload.get("plan_code"):
            metadata_payload["plan_code"] = str(plan_code).strip().upper()
        if payment_locale and not metadata_payload.get("payment_locale"):
            metadata_payload["payment_locale"] = str(payment_locale).strip()
    elif activation_code:
        metadata_payload = {"activation_code": str(activation_code).strip().upper(), "bot_version": version}
        if customer_ref:
            metadata_payload["customer_ref"] = str(customer_ref).strip()
        if plan_code:
            metadata_payload["plan_code"] = str(plan_code).strip().upper()
        if payment_locale:
            metadata_payload["payment_locale"] = str(payment_locale).strip()
    if supabase_store.enabled:
        return supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=user_id,
            full_name=full_name,
            plan_name=plan_name,
            amount=amount,
            sale_id=sale_id,
            original_amount=original_amount or amount,
            coupon_code=coupon_code,
            coupon_discount_percent=coupon_discount_percent,
            coupon_discount_amount=coupon_discount_amount,
            payment_provider=payment_provider,
            payment_provider_order_id=payment_provider_order_id,
            payment_approval_url=payment_approval_url,
            payment_currency=payment_currency,
            plan_token=plan_token,
            plan_category=plan_category,
            source_type=source_type,
            source_ref=source_ref,
            metadata=metadata_payload,
        )

    db.users_sheet.append_row([
        order_id,
        str(user_id),
        full_name,
        plan_name,
        amount,
        "PENDING",
        "",
        "",
        sale_id,
        original_amount or amount,
    ])


def buy_data_from_plan_key(plan_key):
    key = str(plan_key or "").strip().upper()
    if key == "FULL_1M":
        return "buy_full_1m"
    if key == "FULL_LIFE":
        return "buy_full_life"
    if key.startswith("G") and key.endswith("_1M"):
        return f"buy_{key[:-3]}_1m"
    if key.startswith("G") and key.endswith("_LIFE"):
        return f"buy_{key[:-5]}_life"
    return ""


def plan_token_for_offer(data):
    key = str(data or "").strip().lower()
    if key == "buy_full_1m":
        return "FULL_1M"
    if key == "buy_full_life":
        return "FULL_LIFE"
    if key.startswith("buy_g") and key.endswith("_1m"):
        return f"G{key[5:-3]}:1M"
    if key.startswith("buy_g") and key.endswith("_life"):
        return f"G{key[5:-5]}:LIFE"
    return ""


def config_text(user_id, key, default=""):
    return t(user_id, key, default) if user_id else db.get_config(key, default)


def resolve_purchase_offer(data, user_id=None, provider=""):
    sale_info = None
    original_amount = None
    price_key = ""
    normalized_provider = str(provider or "").strip().upper()
    if normalized_provider == "WEB":
        currency = default_currency_for_user(user_id)
    else:
        currency = currency_for_provider(normalized_provider) if normalized_provider else default_currency_for_user(user_id)
    default_group = "0" if currency == "USD" else "50000"
    default_svip = "0" if currency == "USD" else "999"
    data = data.replace("confirm_", "buy_")
    plan_token = ""

    if "upsell_full" in data:
        plan_token = "FULL_LIFE"
        plan_name = config_text(
            user_id,
            "PLAN_UPSELL_ALL_ACCESS",
            localized_default(user_id, "All Access Trọn Đời (Nâng cấp)", "All Access Lifetime (Upgrade)"),
        )
        price_life, sale_life = get_price("PRICE_ALL_ACCESS_LIFE", default_svip, currency)
        price_1m, sale_1m = get_price("PRICE_ALL_ACCESS_30D", default_svip, currency)
        amount = max(0, price_life - price_1m)
        sale_info = sale_life or sale_1m
        original_amount = max(0, parse_price(db.get_config(localized_price_key("PRICE_ALL_ACCESS_LIFE", currency), default_svip), default_svip, currency) - parse_price(db.get_config(localized_price_key("PRICE_ALL_ACCESS_30D", currency), default_svip), default_svip, currency))
    elif "upsell_G" in data:
        num = data.split("_")[1][1:]
        plan_token = f"G{num}:LIFE"
        plan_name = f"{config_text(user_id, 'PLAN_UPSELL_COLLECTION', localized_default(user_id, 'Collection Trọn Đời (Nâng cấp)', 'Collection Lifetime (Upgrade)'))} - {config_text(user_id, f'BTN_G{num}', localized_default(user_id, f'Nhóm {num}', f'Group {num}'))}"
        price_life, sale_life = get_price(f"PRICE_G{num}_LIFE", default_group, currency)
        price_1m, sale_1m = get_price(f"PRICE_G{num}_1M", default_group, currency)
        amount = max(0, price_life - price_1m)
        sale_info = sale_life or sale_1m
        original_amount = max(0, parse_price(db.get_config(localized_price_key(f"PRICE_G{num}_LIFE", currency), default_group), default_group, currency) - parse_price(db.get_config(localized_price_key(f"PRICE_G{num}_1M", currency), default_group), default_group, currency))
    elif "full" in data:
        is_1m = "1m" in data
        plan_token = "FULL_1M" if is_1m else "FULL_LIFE"
        plan_name = config_text(
            user_id,
            "PLAN_ALL_ACCESS_30D" if is_1m else "PLAN_ALL_ACCESS_LIFE",
            localized_default(
                user_id,
                "All Access 30 Ngày" if is_1m else "All Access Trọn Đời",
                "All Access 30 Days" if is_1m else "All Access Lifetime",
            ),
        )
        price_key = "PRICE_ALL_ACCESS_30D" if is_1m else "PRICE_ALL_ACCESS_LIFE"
        amount, sale_info = get_price(price_key, default_svip, currency)
        original_amount = parse_price(db.get_config(localized_price_key(price_key, currency), default_svip), default_svip, currency)
    else:
        parts = data.split("_")
        num, type_p = parts[1][1:], parts[2].upper()
        plan_token = f"G{num}:{type_p}"
        plan_name = f"{config_text(user_id, 'PLAN_COLLECTION_30D' if type_p == '1M' else 'PLAN_COLLECTION_LIFE', localized_default(user_id, 'Collection 30 Ngày', 'Collection 30 Days' if type_p == '1M' else 'Collection Lifetime'))} - {config_text(user_id, f'BTN_G{num}', localized_default(user_id, f'Nhóm {num}', f'Group {num}'))}"
        price_key = f"PRICE_G{num}_{type_p}"
        amount, sale_info = get_price(price_key, default_group, currency)
        original_amount = parse_price(db.get_config(localized_price_key(price_key, currency), default_group), default_group, currency)

    return {
        "plan_name": plan_name,
        "price_key": price_key,
        "amount": amount,
        "sale_info": sale_info,
        "original_amount": original_amount or amount,
        "currency": currency,
        "plan_token": plan_token or plan_token_for_offer(data),
    }


def sale_caption(sale_info, original_amount, amount, currency="VND"):
    if not sale_info:
        return ""
    text = f"\n🔥 <b>SALE:</b> <s>{format_money(original_amount, currency)}</s> → <b>{format_money(amount, currency)}</b> (-{sale_info['discount_percent']}%)"
    if sale_info["remaining_slots"] is not None:
        remaining_after_order = max(0, sale_info["remaining_slots"] - 1)
        text += f"\n🎟 Slot sale còn lại sau đơn này: {remaining_after_order}/{sale_info['slot_limit']}"
    if sale_info["countdown"]:
        text += f"\n⏳ Sale còn: {sale_info['countdown']}"
    return text


async def send_payment_bill(callback, order_id, plan_name, amount, description, pay_data, extra_caption=""):
    pretty_plan_name = display_plan_name(plan_name, callback.from_user.id)
    provider = str(pay_data.get("provider") or "PAYOS").upper()
    if provider == "TRON_USDT":
        caption = t(
            callback.from_user.id,
            "MSG_TRON_USDT_BILL_TEMPLATE",
            "₮ <b>THANH TOÁN USDT TRC20</b>\n\n🎁 Gói: <b>{plan}</b>\n💵 Số tiền: <code>{usdt_amount} USDT</code>\n🌐 Network: <b>TRC20</b>\n👛 Ví nhận:\n<code>{wallet}</code>\n🧾 Đơn: <code>{desc}</code>\n\nVui lòng chuyển đúng số USDT trên. Bot sẽ tự quét blockchain và cấp quyền sau khi giao dịch xác nhận.",
        ).replace("\\n", "\n")
        caption = (
            caption.replace("{plan}", str(pretty_plan_name))
            .replace("{amount}", format_money(amount, "USD"))
            .replace("{usdt_amount}", str(pay_data.get("usdt_amount") or ""))
            .replace("{wallet}", str(pay_data.get("wallet_address") or ""))
            .replace("{desc}", description)
        )
        caption += extra_caption
        kb = InlineKeyboardBuilder()
        if pay_data.get("approval_url"):
            kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_TRONSCAN_ADDRESS", "🔎 Xem ví trên Tronscan"), url=str(pay_data.get("approval_url"))))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CHECK_PAYMENT", localized_default(callback.from_user.id, "🔄 Tôi đã chuyển USDT", "🔄 I've sent the USDT")), callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CANCEL_ORDER", localized_default(callback.from_user.id, "❌ Hủy", "❌ Cancel order")), callback_data=f"cancel_order_{order_id}"))
        sent = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=caption,
            reply_markup=kb.as_markup(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        if supabase_store.enabled and sent:
            supabase_store.set_payment_message(order_id, sent.chat.id, sent.message_id)
        return sent

    if provider == "PAYPAL":
        approval_url = str(pay_data.get("approval_url") or "").strip()
        caption = t(
            callback.from_user.id,
            "MSG_PAYPAL_BILL_TEMPLATE",
            "💳 <b>PAYPAL PAYMENT</b>\n\n🎁 Plan: <b>{plan}</b>\n💵 Amount: <b>{amount}</b>\n🧾 Order: <code>{desc}</code>",
        ).replace("\\n", "\n")
        caption = (
            caption.replace("{plan}", str(pretty_plan_name))
            .replace("{amount}", format_money(amount, str(pay_data.get("currency_code") or "USD")))
            .replace("{paypal_amount}", str(pay_data.get("paypal_amount") or ""))
            .replace("${paypal_amount} USD", format_money(amount, str(pay_data.get("currency_code") or "USD")))
            .replace("{desc}", description)
        )
        caption += extra_caption
        kb = InlineKeyboardBuilder()
        checkout_label = t(callback.from_user.id, "BTN_PAYPAL_CHECKOUT", "💳 Pay with PayPal")
        kb.row(InlineKeyboardButton(text=checkout_label, url=approval_url))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CHECK_PAYMENT", localized_default(callback.from_user.id, "🔄 Tôi đã thanh toán", "🔄 I've paid")), callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CANCEL_ORDER", localized_default(callback.from_user.id, "❌ Hủy", "❌ Cancel")), callback_data=f"cancel_order_{order_id}"))
        sent = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=caption,
            reply_markup=kb.as_markup(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        if supabase_store.enabled and sent:
            supabase_store.set_payment_message(order_id, sent.chat.id, sent.message_id)
        return sent

    if provider == "WEB":
        checkout_url = str(pay_data.get("approval_url") or pay_data.get("checkout_url") or "").strip()
        license_code = str(
            pay_data.get("license_code")
            or pay_data.get("licenseCode")
            or pay_data.get("activation_code")
            or pay_data.get("activationCode")
            or ""
        ).strip().upper()
        activate_url = build_license_deeplink(license_code) if license_code else ""
        caption = t(
            callback.from_user.id,
            "MSG_WEB_PAYMENT_BILL_TEMPLATE",
            "🌐 <b>WEB PAYMENT</b>\n\n🎁 Gói: <b>{plan}</b>\n💵 Số tiền: <b>{amount}</b>\n🧾 Đơn: <code>{desc}</code>\n\nBấm nút bên dưới để thanh toán trên web. Sau khi thanh toán xong, hệ thống sẽ tự kích hoạt như luồng cũ.",
        ).replace("\\n", "\n")
        caption = (
            caption.replace("{plan}", str(pretty_plan_name))
            .replace("{amount}", format_money(amount, str(pay_data.get("currency_code") or default_currency_for_user(callback.from_user.id))))
            .replace("{desc}", description)
        )
        caption += "\n\n🔒 <i>Link kích hoạt sẽ được gửi sau khi thanh toán thành công.</i>"
        caption += extra_caption
        kb = InlineKeyboardBuilder()
        if checkout_url:
            checkout_label = t(callback.from_user.id, "BTN_WEB_CHECKOUT", "🌐 Mở trang thanh toán")
            kb.row(InlineKeyboardButton(text=checkout_label, url=checkout_url))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CHECK_PAYMENT", localized_default(callback.from_user.id, "🔄 Tôi đã thanh toán", "🔄 I've paid")), callback_data=f"check_{order_id}"))
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CANCEL_ORDER", localized_default(callback.from_user.id, "❌ Hủy", "❌ Cancel")), callback_data=f"cancel_order_{order_id}"))
        sent = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=caption,
            reply_markup=kb.as_markup(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        if supabase_store.enabled and sent:
            supabase_store.set_payment_message(order_id, sent.chat.id, sent.message_id)
        return sent

    raw_bin = str(pay_data.get('bin', ''))
    bank_display = BANK_NAMES.get(raw_bin, f"Bank ({raw_bin})")
    actual_stk = pay_data.get('accountNumber', 'N/A')
    template = vietqr_template()
    qr_url = f"https://img.vietqr.io/image/{raw_bin}-{actual_stk}-{template}.png?amount={amount}&addInfo={urllib.parse.quote(description)}"
    if vietqr_show_account_name() and pay_data.get("accountName"):
        qr_url += f"&accountName={urllib.parse.quote(str(pay_data['accountName']))}"
    
    if vietqr_show_account_name() and pay_data.get("accountName"):
        caption_template = "🧾 Mã đơn: {desc}\n💵 Số tiền: {amount}\n🏦 Ngân hàng: {bank}\n👤 Chủ TK: {name}\n🔢 Số TK: {stk}"
        caption = t(callback.from_user.id, "MSG_BILL_TEMPLATE", caption_template).replace("\\n", "\n")
        caption = caption.replace("{name}", str(pay_data["accountName"])).replace("{stk}", actual_stk)
    else:
        caption = t(callback.from_user.id, "MSG_BILL_TEMPLATE", "🧾 Mã đơn: {desc}\n💵 Số tiền: {amount}").replace("\\n", "\n")
        caption = caption.replace("{name}", "").replace("{stk}", "")
    caption = caption.replace("{plan}", str(pretty_plan_name)).replace("{amount}", format_money(amount, "VND")).replace("{bank}", bank_display).replace("{desc}", description)
    caption += extra_caption
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CHECK_PAYMENT", "🔄 Đã chuyển khoản"), callback_data=f"check_{order_id}"))
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_CANCEL_ORDER", "❌ Hủy"), callback_data=f"cancel_order_{order_id}"))
    
    try:
        sent = await bot.send_photo(chat_id=callback.message.chat.id, photo=qr_url, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
    except:
        kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_VIEW_QR", "🖼 Xem QR"), url=qr_url))
        sent = await bot.send_message(chat_id=callback.message.chat.id, text=caption, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
    if supabase_store.enabled and sent:
        try:
            supabase_store.set_payment_message(order_id, sent.chat.id, sent.message_id)
        except Exception as e:
            print(f"⚠️ Không lưu được payment message cho đơn {order_id}: {e}")
    return sent


def _payment_provider_fallbacks(user_id, provider=""):
    language = get_user_language(user_id)
    primary = str(provider or "").strip().upper()
    candidates = []
    if primary:
        candidates.append(primary)
    for item in payment_manager.providers_for_language(language):
        if item and item not in candidates:
            candidates.append(item)
    for item in payment_manager.enabled_providers():
        if item and item not in candidates:
            candidates.append(item)
    return candidates


def create_payment_for_user(user_id, order_id, amount, description, provider="", preferred_language=None, plan_name="", plan_token=""):
    if str(provider or "").strip().upper() == "WEB":
        pay_data = create_web_payment_for_user(
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            description=description,
            plan_name=plan_name or description,
            plan_token=plan_token,
            preferred_language=preferred_language,
        )
        if pay_data:
            return pay_data
        print(f"❌ WEB payment failed for user {user_id}, order {order_id}: giữ nguyên WEB, không fallback sang provider khác")
        return None
    language = resolve_user_language(user_id, preferred_language)
    if not should_allow_auto_payment(user_id, preferred_language=language):
        try:
            gate_snapshot = auto_payment_gate_snapshot(user_id, preferred_language=language)
        except Exception as exc:
            gate_snapshot = {"allowed": False, "reason": f"snapshot_error:{exc}", "segment": language}
        print(f"⛔ Chặn tạo payment cho user {user_id}: gate={gate_snapshot}")
        return None
    attempts = _payment_provider_fallbacks(user_id, provider or payment_manager.preferred_provider(language))
    last_error = ""
    for candidate in attempts:
        pay_data = payment_manager.create_payment_link(order_id, amount, description, provider=candidate)
        if pay_data:
            if candidate != str(provider or "").strip().upper():
                print(f"ℹ️ Payment fallback for user {user_id}, order {order_id}: {provider or 'AUTO'} -> {candidate}")
            return pay_data
        last_error = candidate
        print(f"⚠️ Payment provider failed for user {user_id}, order {order_id}: {candidate}")
    if last_error:
        print(f"❌ Không tạo được payment link cho user {user_id}, order {order_id}. Candidates={attempts}")
    return None


def payment_meta(pay_data):
    provider = str(pay_data.get("provider") or "PAYOS").upper()
    default_currency = "VND" if provider == "PAYOS" else "USDT" if provider == "TRON_USDT" else "USD"
    return {
        "payment_provider": provider,
        "payment_provider_order_id": pay_data.get("provider_order_id", ""),
        "payment_approval_url": pay_data.get("approval_url", ""),
        "payment_currency": pay_data.get("currency_code", default_currency),
        "activation_code": pay_data.get("activation_code", ""),
        "customer_ref": pay_data.get("customer_ref", ""),
        "plan_code": pay_data.get("plan_code", ""),
        "payment_locale": pay_data.get("locale", ""),
    }


def order_status_from_store(order_id):
    if not supabase_store.enabled:
        return None
    try:
        order = supabase_store.get_order(order_id)
    except Exception as exc:
        print(f"⚠️ Không đọc được trạng thái đơn {order_id} từ Supabase: {exc}")
        return None
    if not order:
        return None
    return str(order.get("status", "")).strip().upper()


def payment_choice_keyboard(user_id, action, prefix, preferred_language=None):
    language = resolve_user_language(user_id, preferred_language)
    actions = get_available_payment_actions(user_id, language, include_web=True)
    rails = [item for item in actions if item != "WEB"]
    web_available = "WEB" in actions
    if not rails and not web_available:
        return None, "__NONE__"
    if len(rails) <= 1 and not web_available:
        return None, rails[0] if rails else ""

    kb = InlineKeyboardBuilder()
    added = 0
    for provider in rails:
        callback_data = f"{prefix}|{provider}|{action}"
        if len(callback_data.encode("utf-8")) <= 64:
            kb.row(InlineKeyboardButton(text=payment_button_label(provider, language), callback_data=callback_data))
            added += 1
    if web_available:
        web_callback_data = f"{prefix}|WEB|{action}"
        if len(web_callback_data.encode("utf-8")) <= 64:
            kb.row(InlineKeyboardButton(text=payment_button_label("WEB", language), callback_data=web_callback_data))
            added += 1
    if not added:
        return None, rails[0] if rails else ("WEB" if web_available else "")
    kb.row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", localized_default(user_id, "🔙 Quay lại", "🔙 Back to menu")), callback_data="back_main"))
    return kb.as_markup(), ""


def truthy_config(key, default="OFF"):
    value = str(db.get_config(key, default) or default).strip().upper()
    return value in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def web_payment_enabled():
    return truthy_config("WEB_PAYMENT_ENABLED", "OFF")


def web_payment_base_url():
    return license_backend_url()


def web_payment_label(language=None):
    lang = str(language or "").lower()
    key = "WEB_PAYMENT_LABEL_EN" if lang == "en" else "WEB_PAYMENT_LABEL_VI"
    default = "🌐 Web checkout" if lang == "en" else "🌐 Thanh toán web"
    return str(db.get_config(key, default) or default).strip() or default


def get_available_payment_actions(user_id, preferred_language=None, include_web=True):
    language = resolve_user_language(user_id, preferred_language)
    return payment_manager.available_actions(language, include_web=include_web)


def payment_button_label(provider, language):
    labels = {
        "PAYOS": "🏦 VietQR / PayOS",
        "PAYPAL": "💳 PayPal (USD)",
        "NOWPAYMENTS": "🪙 NOWPayments",
        "TRON_USDT": "₮ USDT TRC20",
        "BINANCE_PAY": "🟡 Binance Pay",
        "WEB": web_payment_label(language),
    }
    return labels.get(provider, provider)


def _sign_web_checkout_request(payload: dict[str, object], secret: str) -> str:
    message = "|".join(
        [
            str(payload.get("orderId", "") or ""),
            str(payload.get("telegramUserId", "") or ""),
            str(payload.get("timestamp", "") or ""),
            str(payload.get("nonce", "") or ""),
        ]
    )
    return hmac.new(str(secret or "").encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def create_web_payment_for_user(user_id, order_id, amount, description, plan_name, plan_token="", preferred_language=None):
    base_url = web_payment_base_url()
    if not base_url or not web_payment_enabled():
        return None

    language = resolve_user_language(user_id, preferred_language)
    currency = "USD" if language == "en" else "VND"
    if currency not in {"VND", "USD"}:
        currency = "VND"
    print(f"🌐 WEB checkout currency resolved: user={user_id} language={language} currency={currency} plan={plan_token or plan_name}")

    now_ts = int(time.time())
    nonce = f"{order_id}{user_id}{now_ts}"[-24:]
    payload = {
        "orderId": str(order_id),
        "amountMinor": int(amount),
        "currency": currency,
        "timestamp": now_ts,
        "nonce": nonce,
        "paymentSessionId": f"ps_{str(order_id).replace('-', '')}_{now_ts}",
    }
    secret = str(db.get_config("WEB_PAYMENT_SECRET", "") or os.getenv("WEB_PAYMENT_SECRET", "") or "").strip()
    if not secret:
        secret = str(os.getenv("LICENSE_WEBHOOK_SECRET", "") or os.getenv("BOT_API_SECRET", "") or "").strip()
    if not secret:
        return None
    payload["signature"] = _sign_web_checkout_request(payload, secret)
    try:
        response = requests.post(f"{base_url}/license/checkout", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return None
        payload_data = data.get("data") if isinstance(data.get("data"), dict) else data
        if not isinstance(payload_data, dict):
            return None
        license_code = str(
            payload_data.get("licenseCode")
            or payload_data.get("license_code")
            or payload_data.get("activationCode")
            or ""
        ).strip().upper()
        checkout_context = {
            "order": str(payload_data.get("orderNumber") or payload_data.get("order_number") or payload["orderId"]),
            "planCode": "BOT_PAYMENT",
            "plan": str(plan_name or "Telegram payment"),
            "amount": str(payload_data.get("amount") or amount),
            "amountMinor": str(payload_data.get("amountMinor") or payload_data.get("amount_minor") or amount),
            "currency": str(payload_data.get("currency") or currency).upper(),
            "checkout": str(payload_data.get("checkoutId") or payload_data.get("checkout_id") or payload_data.get("providerCheckoutId") or payload_data.get("provider_checkout_id") or payload["orderId"]),
            "session": str(payload_data.get("paymentSessionId") or payload_data.get("payment_session_id") or payload["paymentSessionId"]),
            "botOrderId": str(payload["orderId"]),
        }
        web_checkout_base = urllib.parse.urljoin(base_url.rstrip("/") + "/", "checkout")
        web_checkout_url = f"{web_checkout_base}?{urllib.parse.urlencode(checkout_context)}"
        return {
            "provider": "WEB",
            "provider_order_id": str(payload_data.get("orderId") or payload_data.get("order_id") or order_id),
            "approval_url": web_checkout_url,
            "currency_code": str(payload_data.get("currency") or currency).upper(),
            "checkout_url": web_checkout_url,
            "activation_code": "",
            "license_code": license_code,
            "customer_ref": str(payload_data.get("customerRef") or payload_data.get("customer_ref") or payload["customerRef"]),
            "plan_code": "BOT_PAYMENT",
            "locale": str(payload_data.get("locale") or payload["locale"]),
            "payment_session_id": str(payload_data.get("paymentSessionId") or payload_data.get("payment_session_id") or payload["paymentSessionId"]),
            "bot_order_id": str(payload["orderId"]),
            "entitlements": payload_data.get("entitlements", []),
        }
    except requests.HTTPError as exc:
        response = getattr(exc, "response", None)
        body = ""
        if response is not None:
            try:
                body = response.text[:1000]
            except Exception:
                body = ""
        print(
            f"⚠️ WEB payment checkout failed for user {user_id}, order {order_id}: "
            f"status={getattr(response, 'status_code', 'unknown')} body={body or 'empty'}"
        )
        return None
    except Exception as exc:
        print(f"⚠️ WEB payment checkout failed for user {user_id}, order {order_id}: {exc}")
        return None


def support_payload_token(value, max_len=24):
    token = "".join(ch for ch in str(value or "").strip().upper() if ch.isalnum())
    return token[:max_len]


def compact_plan_key_from_action(action):
    data = str(action or "").strip()
    if data.startswith("confirm_"):
        data = data.replace("confirm_", "buy_", 1)
    if data.startswith("couponbuy|"):
        try:
            _, code, plan_key = data.split("|", 2)
        except ValueError:
            return ""
        return f"C{support_payload_token(code, 10)}P{support_payload_token(plan_key, 12)}"
    if data.startswith("hgbuy|"):
        try:
            _, code, hidden_group_id, duration_key = data.split("|", 3)
        except ValueError:
            return ""
        return f"H{support_payload_token(hidden_group_id, 8)}{support_payload_token(duration_key, 4)}C{support_payload_token(code, 8)}"
    if "upsell_full" in data:
        return "UPSVIP"
    if "upsell_G" in data:
        num = data.split("_")[1][1:] if "_" in data else ""
        return f"UPG{support_payload_token(num, 4)}"
    if "full" in data:
        return "SVIP30" if "1m" in data.lower() else "SVIPLIFE"
    parts = data.split("_")
    if len(parts) >= 3 and parts[0] == "buy":
        group = support_payload_token(parts[1], 8)
        duration = support_payload_token(parts[2], 6)
        return f"{group}{duration}"
    if data.startswith("renew_"):
        return "RENEW"
    return support_payload_token(data, 16)


def support_payload_amount(amount, currency):
    try:
        number = float(amount or 0)
    except (TypeError, ValueError):
        number = 0
    currency_token = support_payload_token(currency, 5)
    if number <= 0:
        return currency_token
    if float(number).is_integer():
        amount_token = str(int(number))
    else:
        amount_token = str(number).replace(".", "P")[:10]
    return f"{amount_token}{currency_token}"


def support_offer_from_action(action, user_id=None, provider=""):
    data = str(action or "").strip()
    try:
        if data.startswith("couponbuy|"):
            try:
                _, _, plan_key = data.split("|", 2)
            except ValueError:
                return {}
            buy_data = buy_data_from_plan_key(plan_key)
            return resolve_purchase_offer(buy_data, user_id, provider) if buy_data else {}
        if data.startswith("hgbuy|"):
            return hidden_offer_for_action(data, user_id, provider)
        if data.startswith("renew_"):
            return {}
        if data.startswith(("buy_", "confirm_", "upsell_")):
            return resolve_purchase_offer(data, user_id, provider)
    except Exception as exc:
        print(f"⚠️ Không build được payload bot hỗ trợ cho action {data}: {exc}")
    return {}


def manual_support_payload(user_id=None, action="", provider="", preferred_language=None):
    language = resolve_user_language(user_id, preferred_language) if user_id else resolve_user_language(None, preferred_language)
    prefix = "apgen" if language == "en" else "apg"
    if not user_id:
        return f"act_{prefix}"
    plan_key = compact_plan_key_from_action(action)
    offer = support_offer_from_action(action, user_id, provider)
    currency = offer.get("currency") or (currency_for_provider(provider) if provider else default_currency_for_user(user_id))
    amount = support_payload_amount(offer.get("amount"), currency)
    parts = [f"act_{prefix}"]
    if truthy_config("MANUAL_SUPPORT_PAYLOAD_INCLUDE_USER_ID", "OFF"):
        parts.append(f"u{user_id}")
    if plan_key:
        parts.append(f"p{plan_key}")
    if amount:
        parts.append(f"a{amount}")
    parts.append(f"l{language}")
    payload = "_".join(parts)
    return payload[:64]


def has_prior_paid_vip_order(user_id):
    target = str(user_id).strip()
    if not target:
        return False
    try:
        if supabase_store.enabled:
            orders = supabase_store.list_paid_orders_for_user(target, limit=500)
            return any(str(order.get("plan_name") or "").strip() for order in orders)
        db.connect()
        users_data = db.users_sheet.get_all_values()
        for row in users_data[1:]:
            if len(row) < 8:
                continue
            if str(row[1]).strip() != target:
                continue
            if str(row[5]).strip().upper() != "PAID":
                continue
            if str(row[3]).strip():
                return True
    except Exception as exc:
        print(f"⚠️ Không kiểm tra được lịch sử mua của user {target}: {exc}")
    return False


def should_allow_auto_payment(user_id, preferred_language=None):
    from modules.mod_auto_payment_schedule import auto_payment_allowed_for_user

    return auto_payment_allowed_for_user(user_id, preferred_language=preferred_language)


def auto_payment_gate_snapshot(user_id, preferred_language=None):
    from modules.mod_auto_payment_schedule import auto_payment_gate_snapshot_for_user

    return auto_payment_gate_snapshot_for_user(user_id, preferred_language=preferred_language)


def resolve_user_language(user_id=None, preferred_language=None):
    language = str(preferred_language or "").strip().lower()
    if language in {"vi", "en"}:
        return language
    return get_user_language(user_id)


def auto_payment_gate_message(user_id, preferred_language=None):
    language = resolve_user_language(user_id, preferred_language)
    if language == "en":
        return t(
            user_id,
            "MSG_MANUAL_SUPPORT_REDIRECT_EN",
            db.get_config(
                "MSG_NEW_CUSTOMER_MANUAL_ONLY_EN",
                "👋 Auto payment is off for this account.\nTap the button below and we’ll handle it manually.",
            ),
        )
    return t(
        user_id,
        "MSG_MANUAL_SUPPORT_REDIRECT",
        db.get_config(
            "MSG_NEW_CUSTOMER_MANUAL_ONLY",
            "👋 Auto payment đang tắt cho tài khoản này.\nNhấn nút bên dưới để bot hỗ trợ xử lý thủ công.",
        ),
    )


def manual_support_bot_url(user_id=None, action="", provider="", preferred_language=None):
    language = resolve_user_language(user_id, preferred_language) if user_id else resolve_user_language(None, preferred_language)
    if language == "en":
        template = str(
            db.get_config(
                "MANUAL_SUPPORT_CONTACT_URL_EN",
                db.get_config(
                    "MANUAL_SUPPORT_BOT_URL_EN",
                    db.get_config(
                        "MANUAL_SUPPORT_CONTACT_URL",
                        db.get_config("MANUAL_SUPPORT_BOT_URL", "https://t.me/cuhotro_bot?start={payload}") or "https://t.me/cuhotro_bot?start={payload}",
                    ),
                )
                or "https://t.me/cuhotro_bot?start={payload}",
            )
            or "https://t.me/cuhotro_bot?start={payload}"
        ).strip()
    else:
        template = str(
            db.get_config(
                "MANUAL_SUPPORT_CONTACT_URL",
                db.get_config("MANUAL_SUPPORT_BOT_URL", "https://t.me/cuhotro_bot?start={payload}") or "https://t.me/cuhotro_bot?start={payload}",
            )
            or "https://t.me/cuhotro_bot?start={payload}"
        ).strip()
    payload = manual_support_payload(user_id, action, provider, preferred_language=language)
    if "{payload}" in template:
        return template.replace("{payload}", urllib.parse.quote(payload, safe="_"))
    if template.endswith(("start=act_", "start=src_")):
        return f"{template}{urllib.parse.quote(payload.removeprefix('act_'), safe='_')}"
    return template


def manual_support_bot_label():
    return str(db.get_config("MANUAL_SUPPORT_BOT_LABEL", "💬 Liên hệ hỗ trợ") or "💬 Liên hệ hỗ trợ").strip()


def manual_support_bot_label_en():
    return str(
        db.get_config(
            "MANUAL_SUPPORT_BOT_LABEL_EN",
            db.get_config("MANUAL_SUPPORT_BOT_LABEL", "💬 Contact support") or "💬 Contact support",
        )
        or "💬 Contact support"
    ).strip()


def manual_support_language_switch_enabled():
    return str(db.get_config("MANUAL_SUPPORT_REDIRECT_LANGUAGE_SWITCH_ENABLED", "ON") or "ON").strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def manual_support_language_switch_label(language):
    if str(language or "").lower() == "en":
        return str(db.get_config("LANGUAGE_SWITCH_LABEL_VI", "🇻🇳 Vietnamese") or "🇻🇳 Vietnamese").strip()
    return str(db.get_config("LANGUAGE_SWITCH_LABEL_EN", "🇬🇧 English") or "🇬🇧 English").strip()


def manual_support_keyboard(user_id=None, action="", provider="", preferred_language=None, include_language_switch=False):
    language = resolve_user_language(user_id, preferred_language)
    url = manual_support_bot_url(user_id, action, provider, preferred_language=language)
    if not url:
        return None
    kb = InlineKeyboardBuilder()
    label = manual_support_bot_label_en() if language == "en" else manual_support_bot_label()
    kb.row(InlineKeyboardButton(text=label, url=url))
    if include_language_switch and manual_support_language_switch_enabled():
        kb.row(InlineKeyboardButton(
            text=manual_support_language_switch_label(language),
            callback_data="set_lang:en" if language != "en" else "set_lang:vi",
        ))
    return kb.as_markup()


async def enforce_auto_payment_gate(callback: CallbackQuery, action="", provider=""):
    language = resolve_user_language(callback.from_user.id)
    if should_allow_auto_payment(
        callback.from_user.id,
        preferred_language=language,
    ):
        return True
    callback_action = action or getattr(callback, "data", "")
    try:
        gate_snapshot = auto_payment_gate_snapshot(callback.from_user.id, preferred_language=language)
    except Exception as exc:
        gate_snapshot = {"allowed": False, "reason": f"snapshot_error:{exc}", "segment": language}
    keyboard = manual_support_keyboard(callback.from_user.id, callback_action, provider, preferred_language=language, include_language_switch=True)
    if callback.message:
        gate_text = auto_payment_gate_message(callback.from_user.id, preferred_language=language)
        try:
            await callback.message.answer(gate_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as exc:
            print(f"⚠️ Không gửi được nút chuyển sang bot hỗ trợ dạng HTML: {exc}")
            try:
                await callback.message.answer(strip_html_tags(gate_text), reply_markup=keyboard)
            except Exception as fallback_exc:
                print(f"⚠️ Không gửi được nút chuyển sang bot hỗ trợ: {fallback_exc}")
    try:
        record_support_event(
            "auto_payment_redirect",
            callback.from_user.id,
            username=callback.from_user.username or "",
            full_name=callback.from_user.full_name or "",
            chat_id=str(callback.message.chat.id if callback.message else ""),
            raw_data={
                "action": callback_action,
                "provider": provider,
                "language": language,
                "support_inbox_enabled": support_inbox_enabled(),
                "gate": gate_snapshot,
            },
        )
    except Exception:
        pass
    try:
        await callback.answer()
    except Exception:
        pass
    return False


@router.callback_query(F.data.startswith("renew_") | F.data.startswith("payrenew|"))
async def process_early_renew(callback: CallbackQuery):
    if not await check_protection(callback): return

    provider = ""
    action = callback.data
    if callback.data.startswith("payrenew|"):
        try:
            _, provider, action = callback.data.split("|", 2)
        except ValueError:
            await callback.answer("Phương thức thanh toán không hợp lệ.", show_alert=True)
            return
    else:
        keyboard, provider = payment_choice_keyboard(callback.from_user.id, action, "payrenew", preferred_language=resolve_user_language(callback.from_user.id))
        if keyboard:
            if not await enforce_auto_payment_gate(callback, action, provider):
                return
            await callback.message.answer(
                t(callback.from_user.id, "MSG_CHOOSE_PAYMENT_PROVIDER", "Chọn phương thức thanh toán. VietQR dùng VND; PayPal và Crypto dùng giá USD riêng."),
                reply_markup=keyboard,
            )
            return
        if provider == "__NONE__":
            await callback.answer(t(callback.from_user.id, "ALERT_PAYMENT_METHOD_UNAVAILABLE", "Hiện chưa có phương thức thanh toán phù hợp được bật."), show_alert=True)
            return

    if not await enforce_auto_payment_gate(callback, action, provider):
        return

    if not is_early_renew_enabled():
        await callback.answer(t(callback.from_user.id, "ALERT_EARLY_RENEW_OFF", "Ưu đãi gia hạn sớm đang tắt. Vui lòng gia hạn theo giá thường."), show_alert=True)
        await render_page(callback, "main_menu")
        return

    row_index = None
    row = None
    if action.startswith("renew_order_"):
        source_order_id = action.replace("renew_order_", "", 1).strip()
        if supabase_store.enabled:
            order = supabase_store.get_order(source_order_id)
            row = supabase_store.order_to_sheet_row(order)
            row_index = source_order_id
    else:
        try:
            row_index = int(action.split("_", 1)[1])
        except Exception:
            await callback.answer(t(callback.from_user.id, "ALERT_RENEW_CODE_INVALID", "Mã gia hạn không hợp lệ."), show_alert=True)
            return

        users_data = db.users_sheet.get_all_values()
        if row_index < 2 or row_index > len(users_data):
            await callback.answer(t(callback.from_user.id, "ALERT_RENEW_OFFER_INVALID", "Ưu đãi gia hạn không còn hợp lệ."), show_alert=True)
            return
        row = users_data[row_index - 1]

    if not row:
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_OFFER_INVALID", "Ưu đãi gia hạn không còn hợp lệ."), show_alert=True)
        return

    if len(row) < 8 or str(row[1]).strip() != str(callback.from_user.id):
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_NOT_OWNER", "Ưu đãi này không thuộc tài khoản của bạn."), show_alert=True)
        return

    currency = currency_for_provider(provider) if provider else default_currency_for_user(callback.from_user.id)
    offer = build_early_renew_offer(row, row_index, currency=currency)
    if not offer:
        await callback.answer(t(callback.from_user.id, "ALERT_RENEW_EXPIRED", "Ưu đãi gia hạn sớm đã hết hạn hoặc không còn hợp lệ."), show_alert=True)
        return

    inflight_key = payment_spam_inflight_key(callback, action, provider)
    if inflight_key in payment_spam_inflight:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Please wait a moment. I’m still creating your previous payment."), show_alert=True)
        return
    payment_spam_inflight.add(inflight_key)
    try:
        if not await enforce_payment_cooldown(callback, action, provider):
            return

        msg_wait = await callback.message.answer(
            t(
                callback.from_user.id,
                "MSG_WAIT_WEB_CHECKOUT",
                "🌐 Đang mở trang thanh toán web...",
            )
            if str(provider).upper() == "WEB"
            else t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR...")
        )
        order_id = int(time.time())
        description = f"PRIVE{order_id}"[-20:]
        amount = offer["renew_price"]

        pay_data = create_payment_for_user(
            callback.from_user.id,
            order_id,
            amount,
            description,
            provider,
            preferred_language=resolve_user_language(callback.from_user.id),
            plan_name=plan_name,
            plan_token=offer.get("plan_token", ""),
        )
        if not pay_data:
            await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
            return

        create_pending_order(
            order_id=order_id,
            user_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            plan_name=offer["plan_name"],
            amount=amount,
            sale_id=offer["offer_id"],
            original_amount=offer["original_price"],
            **payment_meta(pay_data),
        )

        extra_caption = (
            f"\n🔥 <b>ƯU ĐÃI GIA HẠN SỚM:</b> <s>{format_money(offer['original_price'], currency)}</s> → "
            f"<b>{format_money(amount, currency)}</b> (-{offer['discount_percent']}%)"
            f"\n⏳ Ưu đãi hết khi VIP hết hạn: <code>{offer['expire_at'].strftime('%d/%m/%Y %H:%M:%S')}</code>"
        )
        await send_payment_bill(callback, order_id, offer["plan_name"], amount, description, pay_data, extra_caption)
        await safe_delete_private_message(msg_wait)
        await safe_delete_private_message(callback.message)
        create_background_task(auto_check_loop(order_id, callback.from_user.id), name=f"auto_check_loop_{order_id}", context="renew_offer")
    finally:
        payment_spam_inflight.discard(inflight_key)

@router.callback_query(F.data.startswith("group_"))
async def view_group_detail(callback: CallbackQuery):
    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    num = callback.data.split("_")[1]
    currency = default_currency_for_user(callback.from_user.id)
    desc = t(callback.from_user.id, f"DESC_G{num}", "Đang cập nhật...").replace("\\n", "\n")
    desc += sale_text_for_price(f"PRICE_G{num}_1M", "50000", currency)
    desc += sale_text_for_price(f"PRICE_G{num}_LIFE", "149000", currency)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{t(callback.from_user.id, 'BTN_BUY_COLLECTION_30D', '💎 COLLECTION 30 NGÀY')} • {price_label_for_user(callback.from_user.id, f'PRICE_G{num}_1M', '50000')}", callback_data=f"buy_G{num}_1m"))
    kb.row(InlineKeyboardButton(text=f"{t(callback.from_user.id, 'BTN_BUY_COLLECTION_LIFE', '👑 COLLECTION TRỌN ĐỜI')} • {price_label_for_user(callback.from_user.id, f'PRICE_G{num}_LIFE', '149000')}", callback_data=f"buy_G{num}_life"))
    # Nút dẫn sang trang All Access Page
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_VIEW_ALL_ACCESS_PAGE", localized_default(callback.from_user.id, "🌟 XEM ALL ACCESS", "🌟 View All Access")), callback_data="view_all_access_page"))
    kb.row(InlineKeyboardButton(text=t(callback.from_user.id, "BTN_BACK", localized_default(callback.from_user.id, "🔙 Quay lại", "🔙 Back to menu")), callback_data="back_main"))
    
    await smart_display(callback, desc, kb.as_markup(), img=db.get_config(f"IMG_G{num}"))

# ==========================================
# 🌟 TRANG CHI TIẾT ALL ACCESS (GIỮ NGUYÊN CODE CỦA BẠN - ĐÃ FIX LỖI VÒNG LẶP)
# ==========================================
# 🛠 FIX 1: Loại bỏ "buy_full_life" và "buy_full_1m" khỏi F.data.in_ để không tranh sóng với hàm tạo QR
@router.callback_query(F.data.in_(["view_all_access_page", "view_svip_page", "view_full_life", "view_full_1m"]))
async def show_all_access_page(callback: CallbackQuery):
    """Hiển thị trang giới thiệu All Access với ảnh cover và mô tả"""
    if callback.data.startswith("confirm_"):
        return

    if not await check_protection(callback): return
    await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
    
    img_url = db.get_config("IMG_ALL_ACCESS_PAGE", "https://via.placeholder.com/800x450.png?text=All+Access")
    description = t(callback.from_user.id, "TXT_ALL_ACCESS_DESCRIPTION", "🔥 <b>ĐẶC QUYỀN ALL ACCESS</b> 🔥\n\n✅ Truy cập toàn bộ các collection VIP.\n✅ Cập nhật nội dung mới mỗi ngày.\n✅ Hỗ trợ ưu tiên 24/7.\n\n👇 <i>Chọn gói đăng ký bên dưới:</i>").replace("\\n", "\n")
    currency = default_currency_for_user(callback.from_user.id)
    description += sale_text_for_price("PRICE_ALL_ACCESS_LIFE", "3000", currency)
    description += sale_text_for_price("PRICE_ALL_ACCESS_30D", "2000", currency)
    
    btn_life_text = t(callback.from_user.id, "BTN_BUY_ALL_ACCESS_LIFE", "🔥 MUA ALL ACCESS TRỌN ĐỜI")
    btn_30d_text = t(callback.from_user.id, "BTN_BUY_ALL_ACCESS_30D", "💎 MUA ALL ACCESS 30 NGÀY")
    
    btn_back_text = t(callback.from_user.id, "BTN_BACK", localized_default(callback.from_user.id, "🔙 Quay lại", "🔙 Back to menu"))

    kb = InlineKeyboardBuilder()
    # TRUYỀN TÍN HIỆU BUY ĐỂ GỌI HÀM TẠO MÃ QR BÊN DƯỚI
    kb.row(InlineKeyboardButton(text=f"{btn_life_text} • {price_label_for_user(callback.from_user.id, 'PRICE_ALL_ACCESS_LIFE', '3000')}", callback_data="buy_full_life"))
    kb.row(InlineKeyboardButton(text=f"{btn_30d_text} • {price_label_for_user(callback.from_user.id, 'PRICE_ALL_ACCESS_30D', '2000')}", callback_data="buy_full_1m"))
    kb.row(InlineKeyboardButton(text=btn_back_text, callback_data="back_main"))

    await smart_display(callback, description, kb.as_markup(), img=img_url)

# ==========================================
# 💳 XỬ LÝ THANH TOÁN & CHỐNG SPAM
# ==========================================
@router.callback_query(F.data.startswith("confirm_") | F.data.startswith("buy_") | F.data.startswith("upsell_") | F.data.startswith("paybuy|"))
async def process_buy_request(callback: CallbackQuery):
    if not await check_protection(callback): return

    provider = ""
    action = callback.data
    if callback.data.startswith("paybuy|"):
        try:
            _, provider, action = callback.data.split("|", 2)
        except ValueError:
            await callback.answer("Phương thức thanh toán không hợp lệ.", show_alert=True)
            return
    else:
        keyboard, provider = payment_choice_keyboard(callback.from_user.id, action, "paybuy", preferred_language=resolve_user_language(callback.from_user.id))
        if keyboard:
            if not await enforce_auto_payment_gate(callback, action, provider):
                return
            await callback.message.answer(
                t(callback.from_user.id, "MSG_CHOOSE_PAYMENT_PROVIDER", "Chọn phương thức thanh toán. VietQR dùng VND; PayPal và Crypto dùng giá USD riêng."),
                reply_markup=keyboard,
            )
            return
        if provider == "__NONE__":
            await callback.answer(t(callback.from_user.id, "ALERT_PAYMENT_METHOD_UNAVAILABLE", "Hiện chưa có phương thức thanh toán phù hợp được bật."), show_alert=True)
            return

    if not await enforce_auto_payment_gate(callback, action, provider):
        return

    inflight_key = payment_spam_inflight_key(callback, action, provider)
    if inflight_key in payment_spam_inflight:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Please wait a moment. I’m still creating your previous payment."), show_alert=True)
        return
    payment_spam_inflight.add(inflight_key)

    try:
        if not await enforce_payment_cooldown(callback, action, provider):
            return

        await cleanup_welcome(callback.from_user.id, callback.message.chat.id)
        
        offer = resolve_purchase_offer(action, callback.from_user.id, provider)
        plan_name = offer["plan_name"]
        amount = offer["amount"]
        sale_info = offer["sale_info"]
        original_amount = offer["original_amount"]
        if amount <= 0:
            await callback.answer(t(callback.from_user.id, "ALERT_PRICE_NOT_CONFIGURED", "Gói này chưa được cấu hình giá cho phương thức thanh toán đã chọn."), show_alert=True)
            return

        msg_wait = await callback.message.answer(
            t(
                callback.from_user.id,
                "MSG_WAIT_WEB_CHECKOUT",
                "🌐 Đang mở trang thanh toán web...",
            )
            if str(provider).upper() == "WEB"
            else t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR...")
        )
        order_id = int(time.time())
        description = f"PRIVE{order_id}"[-20:]
        
        pay_data = create_payment_for_user(
            callback.from_user.id,
            order_id,
            amount,
            description,
            provider,
            preferred_language=resolve_user_language(callback.from_user.id),
            plan_name=plan_name,
            plan_token=offer.get("plan_token", ""),
        )
        
        if pay_data:
            sale_id = sale_info["sale_id"] if sale_info else ""
            create_pending_order(
                order_id=order_id,
                user_id=callback.from_user.id,
                full_name=callback.from_user.full_name,
                plan_name=plan_name,
                amount=amount,
                sale_id=sale_id,
                original_amount=original_amount or amount,
                plan_token=offer.get("plan_token", ""),
                **payment_meta(pay_data),
            )
            extra_caption = sale_caption(sale_info, original_amount, amount, offer["currency"])

            await send_payment_bill(callback, order_id, plan_name, amount, description, pay_data, extra_caption)
                
            await safe_delete_private_message(msg_wait)
            await safe_delete_private_message(callback.message)
                
            create_background_task(auto_check_loop(order_id, callback.from_user.id), name=f"auto_check_loop_{order_id}", context="buy_request")
        else: await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
    finally:
        payment_spam_inflight.discard(inflight_key)


@router.callback_query(F.data.startswith("hgbuy|") | F.data.startswith("payhgbuy|"))
async def process_hidden_buy_request(callback: CallbackQuery):
    if not await check_protection(callback):
        return

    provider = ""
    action = callback.data
    if callback.data.startswith("payhgbuy|"):
        try:
            _, provider, action = callback.data.split("|", 2)
        except ValueError:
            await callback.answer("Phương thức thanh toán không hợp lệ.", show_alert=True)
            return
    else:
        keyboard, provider = payment_choice_keyboard(callback.from_user.id, action, "payhgbuy", preferred_language=resolve_user_language(callback.from_user.id))
        if keyboard:
            if not await enforce_auto_payment_gate(callback, action, provider):
                return
            await callback.message.answer(
                t(callback.from_user.id, "MSG_CHOOSE_PAYMENT_PROVIDER", "Chọn phương thức thanh toán. VietQR dùng VND; PayPal và Crypto dùng giá USD riêng."),
                reply_markup=keyboard,
            )
            return
        if provider == "__NONE__":
            await callback.answer(t(callback.from_user.id, "ALERT_PAYMENT_METHOD_UNAVAILABLE", "Hiện chưa có phương thức thanh toán phù hợp được bật."), show_alert=True)
            return

    if not await enforce_auto_payment_gate(callback, action, provider):
        return

    inflight_key = payment_spam_inflight_key(callback, action, provider)
    if inflight_key in payment_spam_inflight:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Please wait a moment. I’m still creating your previous payment."), show_alert=True)
        return
    payment_spam_inflight.add(inflight_key)
    try:
        if not await enforce_payment_cooldown(callback, action, provider):
            return

        await cleanup_welcome(callback.from_user.id, callback.message.chat.id)

        offer = hidden_offer_for_action(action, callback.from_user.id, provider)
        if offer.get("error"):
            await callback.answer(str(offer["error"]), show_alert=True)
            return

        plan_name = offer["plan_name"]
        amount = offer["amount"]
        msg_wait = await callback.message.answer(
            t(
                callback.from_user.id,
                "MSG_WAIT_WEB_CHECKOUT",
                "🌐 Đang mở trang thanh toán web...",
            )
            if str(provider).upper() == "WEB"
            else t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR...")
        )
        order_id = int(time.time())
        description = f"PRIVE{order_id}"[-20:]

        pay_data = create_payment_for_user(
            callback.from_user.id,
            order_id,
            amount,
            description,
            provider,
            preferred_language=resolve_user_language(callback.from_user.id),
            plan_name=offer["plan_name"],
            plan_token=offer.get("plan_token", ""),
        )
        if not pay_data:
            await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
            return

        create_pending_order(
            order_id=order_id,
            user_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            plan_name=plan_name,
            amount=amount,
            original_amount=offer["original_amount"],
            plan_token=offer.get("plan_token", ""),
            plan_category="HIDDEN",
            source_type="HIDDEN_CODE",
            source_ref=offer.get("source_ref", ""),
            metadata=offer.get("metadata"),
            **payment_meta(pay_data),
        )

        await send_payment_bill(callback, order_id, plan_name, amount, description, pay_data)
        await safe_delete_private_message(msg_wait)
        await safe_delete_private_message(callback.message)
        create_background_task(auto_check_loop(order_id, callback.from_user.id), name=f"auto_check_loop_{order_id}", context="hidden_buy_request")
    finally:
        payment_spam_inflight.discard(inflight_key)


@router.callback_query(F.data.startswith("couponbuy|") | F.data.startswith("paycoupon|"))
async def process_coupon_buy_request(callback: CallbackQuery):
    if not await check_protection(callback):
        return

    provider = ""
    action = callback.data
    if callback.data.startswith("paycoupon|"):
        try:
            _, provider, action = callback.data.split("|", 2)
        except ValueError:
            await callback.answer("Phương thức thanh toán không hợp lệ.", show_alert=True)
            return
    else:
        keyboard, provider = payment_choice_keyboard(callback.from_user.id, action, "paycoupon", preferred_language=resolve_user_language(callback.from_user.id))
        if keyboard:
            if not await enforce_auto_payment_gate(callback, action, provider):
                return
            await callback.message.answer(
                t(callback.from_user.id, "MSG_CHOOSE_PAYMENT_PROVIDER", "Chọn phương thức thanh toán. VietQR dùng VND; PayPal và Crypto dùng giá USD riêng."),
                reply_markup=keyboard,
            )
            return
        if provider == "__NONE__":
            await callback.answer(t(callback.from_user.id, "ALERT_PAYMENT_METHOD_UNAVAILABLE", "Hiện chưa có phương thức thanh toán phù hợp được bật."), show_alert=True)
            return

    if not await enforce_auto_payment_gate(callback, action, provider):
        return

    try:
        _, code, plan_key = action.split("|", 2)
    except ValueError:
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_INVALID", "Mã giảm giá không hợp lệ."), show_alert=True)
        return

    from modules.mod_coupon import (
        coupon_discount_percent,
        coupon_matches_plan,
        coupon_type,
        find_coupon,
        normalize_code,
        validate_coupon_base,
    )

    code = normalize_code(code)
    _, _, _, coupon = find_coupon(code)
    valid, reason = validate_coupon_base(coupon, callback.from_user.id)
    if not valid:
        await callback.answer(reason, show_alert=True)
        return
    if coupon_type(coupon) != "DISCOUNT" or not coupon_matches_plan(coupon, plan_key):
        await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_NOT_APPLICABLE", "Mã này không áp dụng cho gói đã chọn."), show_alert=True)
        return

    inflight_key = payment_spam_inflight_key(callback, action, provider)
    if inflight_key in payment_spam_inflight:
        await callback.answer(t(callback.from_user.id, "ALERT_SPAM_QR", "⏳ Please wait a moment. I’m still creating your previous payment."), show_alert=True)
        return
    payment_spam_inflight.add(inflight_key)
    try:
        if not await enforce_payment_cooldown(callback, action, provider):
            return
        buy_data = buy_data_from_plan_key(plan_key)
        if not buy_data:
            await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_PLAN_INVALID", "Gói áp dụng không hợp lệ."), show_alert=True)
            return

        offer = resolve_purchase_offer(buy_data, callback.from_user.id, provider)
        percent = coupon_discount_percent(coupon)
        before_coupon = offer["amount"]
        discount_amount = round(before_coupon * percent / 100, 2) if offer["currency"] == "USD" else int(round(before_coupon * percent / 100))
        amount = max(0, before_coupon - discount_amount)
        if amount <= 0:
            await callback.answer(t(callback.from_user.id, "ALERT_DISCOUNT_ZERO_AMOUNT", "Mã giảm giá làm đơn về 0đ. Hãy dùng coupon kích hoạt thay vì coupon giảm giá."), show_alert=True)
            return

        msg_wait = await callback.message.answer(
            t(
                callback.from_user.id,
                "MSG_WAIT_WEB_CHECKOUT",
                "🌐 Đang mở trang thanh toán web...",
            )
            if str(provider).upper() == "WEB"
            else t(callback.from_user.id, "MSG_WAIT_QR", "⏳ Đang tạo mã QR...")
        )
        order_id = int(time.time())
        description = f"PRIVE{order_id}"[-20:]
        pay_data = create_payment_for_user(
            callback.from_user.id,
            order_id,
            amount,
            description,
            provider,
            preferred_language=resolve_user_language(callback.from_user.id),
            plan_name=offer["plan_name"],
            plan_token=offer.get("plan_token", ""),
        )

        if not pay_data:
            await msg_wait.edit_text(t(callback.from_user.id, "MSG_QR_ERROR", "❌ Lỗi cổng thanh toán!"))
            return

        sale_info = offer["sale_info"]
        sale_id = sale_info["sale_id"] if sale_info else ""
        create_pending_order(
            order_id=order_id,
            user_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            plan_name=offer["plan_name"],
            amount=amount,
            sale_id=sale_id,
            original_amount=offer["original_amount"],
            plan_token=offer.get("plan_token", ""),
            coupon_code=code,
            coupon_discount_percent=percent,
            coupon_discount_amount=discount_amount,
            **payment_meta(pay_data),
        )
        extra_caption = sale_caption(sale_info, offer["original_amount"], before_coupon, offer["currency"])
        extra_caption += f"\n🎟 <b>COUPON {code}:</b> -{percent}% (-{format_money(discount_amount, offer['currency'])})"
        extra_caption += f"\n💳 <b>Cần thanh toán:</b> {format_money(amount, offer['currency'])}"

        await send_payment_bill(callback, order_id, offer["plan_name"], amount, description, pay_data, extra_caption)
        await safe_delete_private_message(msg_wait)
        await safe_delete_private_message(callback.message)
        create_background_task(auto_check_loop(order_id, callback.from_user.id), name=f"auto_check_loop_{order_id}", context="coupon_buy_request")
    finally:
        payment_spam_inflight.discard(inflight_key)

@router.callback_query(F.data.startswith("check_"))
async def manual_check_payment(callback: CallbackQuery):
    if not await check_protection(callback): return
    order_id = callback.data.split("_")[1]

    order = supabase_store.get_order(order_id) if supabase_store.enabled else None
    provider = str((order or {}).get("payment_provider") or "PAYOS").upper()
    ttl_key = "TRON_USDT_TTL_SECONDS" if provider == "TRON_USDT" else "QR_TTL_SECONDS"
    ttl_default = 7200 if provider == "TRON_USDT" else 300
    qr_ttl_seconds = max(60, parse_int_config(ttl_key, ttl_default))
    try:
        if int(time.time()) - int(order_id) > qr_ttl_seconds:
            await callback.answer(t(callback.from_user.id, "ALERT_QR_EXPIRED", "⏳ Mã QR đã hết hạn. Vui lòng tạo đơn mới."), show_alert=True)
            await expire_pending_payment(order_id, callback.from_user.id)
            await safe_delete_private_message(callback.message)
            return
    except ValueError:
        pass
    
    if order_status_from_store(order_id) == "PAID" or payment_manager.get_payment_status(order_id) == "PAID":
        await callback.answer(t(callback.from_user.id, "ALERT_PAID_SUCCESS", "✅ Giao dịch thành công!"), show_alert=True)
        await process_successful_payment(order_id)
        await safe_delete_private_message(callback.message)
    else: await callback.answer(t(callback.from_user.id, "ALERT_NOT_PAID", "⏳ Hệ thống chưa nhận được tiền!").replace("\\n", "\n"), show_alert=True)


@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = str(callback.data.split("_")[-1])
    cancelled_orders.add(order_id)
    if supabase_store.enabled:
        try:
            supabase_store.update_order_status(order_id, "CANCELLED")
        except Exception as e:
            print(f"⚠️ Không thể cập nhật CANCELLED cho đơn {order_id}: {e}")
    await safe_delete_private_message(callback.message)
    await callback.answer(t(callback.from_user.id, "ALERT_CANCELLED", "🚫 Đã hủy đơn."), show_alert=True)
    await render_page(callback, "main_menu")
