from __future__ import annotations

import html
import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import bot
from config_utils import group_numbers
from database import db
from helpers import is_admin_user
from hidden_group_utils import list_hidden_groups
from sale_utils import get_price, localized_price_key
from hidden_group_utils import (
    build_hidden_plan_name,
    extract_plan_token,
    hidden_duration_days,
    hidden_duration_price,
    hidden_plan_duration_key,
    hidden_plan_group_id,
    is_hidden_plan_token,
    main_group_matches_plan,
)

router = Router()

FIELD_HINTS = {
    "telegram_user_id": "Telegram ID",
    "full_name": "Tên khách",
    "plan_name": "Tên gói",
    "note": "Ghi chú",
    "amount": "Số tiền",
    "duration_days": "Số ngày",
    "payment_currency": "Tiền tệ",
    "payment_provider": "Provider",
    "activation_code": "Xuất active code",
}


def _cfg(key: str, default: str = "") -> str:
    try:
        return str(db.get_config(key, default) or default).strip()
    except Exception:
        return default


def _backend_base_url() -> str:
    configured = _cfg("ADMIN_API_BASE_URL", os.getenv("ADMIN_API_BASE_URL", ""))
    if configured:
        return configured
    webhook_url = str(os.getenv("WEBHOOK_URL", "") or "").strip()
    if webhook_url:
        base = webhook_url.split("?", 1)[0].rsplit("/", 1)[0]
        if base:
            return base.rstrip("/")
    for key in ("PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL", "WEB_BACKEND_URL", "APP_URL"):
        value = str(os.getenv(key, "") or "").strip()
        if value:
            return value.rstrip("/")
    return "http://127.0.0.1:8000"


def _admin_secret() -> str:
    return _cfg("ADMIN_SECRET", os.getenv("ADMIN_SECRET", ""))


def _http_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    secret = _admin_secret()
    if secret:
        headers["x-admin-secret"] = secret
    return headers


def _normalize_text(value: Any) -> str:
    return html.escape(str(value or "").strip())


def _short_error_text(value: Any, limit: int = 180) -> str:
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _parse_amount(text: str) -> float:
    raw = str(text or "").strip().replace(",", ".")
    return float(raw)


def _parse_bool(text: str) -> bool:
    return str(text or "").strip().lower() in {"1", "true", "yes", "on", "y", "có", "co"}


def _field_index(field: str) -> int:
    try:
        return ALL_FIELDS.index(field)
    except ValueError:
        return 0


def _next_field(field: str) -> str:
    idx = _field_index(field)
    return ALL_FIELDS[min(idx + 1, len(ALL_FIELDS) - 1)]


def _prev_field(field: str) -> str:
    idx = _field_index(field)
    return ALL_FIELDS[max(idx - 1, 0)]


def _field_label(field: str) -> str:
    return FIELD_HINTS.get(field, field.replace("_", " ").title())


QUICK_FIELDS = ["telegram_user_id", "plan_name", "activation_code"]
EXTRA_FIELDS = ["full_name", "note", "amount", "duration_days", "payment_currency", "payment_provider"]
ALL_FIELDS = QUICK_FIELDS + EXTRA_FIELDS


def _forward_origin_user(message: Message):
    forward_origin = getattr(message, "forward_origin", None)
    if forward_origin and getattr(forward_origin, "sender_user", None):
        return forward_origin.sender_user
    return getattr(message, "forward_from", None)


def _forward_origin_chat(message: Message):
    forward_origin = getattr(message, "forward_origin", None)
    if forward_origin and getattr(forward_origin, "chat", None):
        return forward_origin.chat
    return getattr(message, "forward_from_chat", None)


def _is_forwarded_message(message: Message) -> bool:
    return bool(
        getattr(message, "forward_origin", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_from_chat", None)
        or getattr(message, "forward_date", None)
    )


def _smart_forward_text(message: Message) -> str:
    parts: list[str] = []
    user = _forward_origin_user(message)
    if user:
        uid = getattr(user, "id", None)
        if uid is not None:
            parts.append(f"ID: {uid}")
        name = " ".join(
            part
            for part in [
                str(getattr(user, "first_name", "") or "").strip(),
                str(getattr(user, "last_name", "") or "").strip(),
            ]
            if part
        ).strip()
        if name:
            parts.append(f"Name: {name}")
        username = str(getattr(user, "username", "") or "").strip()
        if username:
            parts.append(f"@{username}")

    chat = _forward_origin_chat(message)
    if chat:
        title = str(getattr(chat, "title", "") or getattr(chat, "first_name", "") or "").strip()
        if title:
            parts.append(title)
        chat_id = getattr(chat, "id", None)
        if chat_id is not None:
            parts.append(f"ChatID: {chat_id}")

    raw = str(message.text or message.caption or "").strip()
    if raw:
        parts.append(raw)

    return " | ".join(parts)


def _plan_candidates() -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(value: str):
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            candidates.append(text)

    try:
        for group_no in group_numbers():
            add(db.get_config(f"BTN_G{group_no}", ""))
    except Exception:
        pass

    try:
        for hidden_group in list_hidden_groups(include_inactive=False):
            add(hidden_group.get("name") or "")
    except Exception:
        pass

    try:
        add(_cfg("PLAN_ALL_ACCESS_30D", "All Access 30 Ngày"))
        add(_cfg("PLAN_ALL_ACCESS_LIFE", "All Access Trọn Đời"))
    except Exception:
        pass

    return candidates


def _default_currency_for_plan(plan_name: str) -> str:
    price = _resolve_plan_pricing(plan_name, "")
    currency = str(price.get("payment_currency") or "").strip().upper()
    return currency or "VND"


def _guess_lifetime(plan_name: str) -> bool:
    text = str(plan_name or "").upper()
    return any(token in text for token in {"TRỌN ĐỜI", "TRON DOI", "LIFE", "LIFETIME"})


def _resolve_plan_pricing(plan_name: str, provider: str = "") -> dict[str, Any]:
    text = str(plan_name or "").strip()
    if not text:
        return {"amount": "", "duration_days": "", "payment_currency": ""}

    currency = "USD" if str(provider or "").upper() == "PAYPAL" else "VND"
    token = extract_plan_token(text)

    if is_hidden_plan_token(token):
        group_id = hidden_plan_group_id(token)
        duration_key = hidden_plan_duration_key(token) or ("LIFE" if _guess_lifetime(text) else "1M")
        try:
            hidden_group = next((item for item in list_hidden_groups(include_inactive=False) if str(item.get("id") or "") == group_id), None)
            if hidden_group:
                resolved_currency = currency
                amount = hidden_duration_price(hidden_group, duration_key, resolved_currency)
                days = hidden_duration_days(hidden_group, duration_key)
                if amount > 0:
                    return {
                        "amount": str(amount),
                        "duration_days": str(days),
                        "payment_currency": resolved_currency,
                    }
        except Exception:
            pass
        return {"amount": "", "duration_days": "", "payment_currency": currency}

    group_no = None
    for no in group_numbers():
        if main_group_matches_plan(no, text):
            group_no = no
            break
    if group_no is None:
        return {"amount": "", "duration_days": "", "payment_currency": currency}

    life = _guess_lifetime(text)
    price_key = localized_price_key(f"PRICE_G{group_no}_{'LIFE' if life else '1M'}", currency)
    try:
        amount, _sale = get_price(price_key, 0, currency)
    except Exception:
        amount = 0
    duration_days = 3650 if life else 30
    return {
        "amount": str(amount) if amount else "",
        "duration_days": str(duration_days),
        "payment_currency": currency,
    }


@dataclass
class OrderDraft:
    admin_id: int
    source_chat_id: int | None = None
    source_message_id: int | None = None
    customer_text: str = ""
    telegram_user_id: str = ""
    full_name: str = ""
    plan_name: str = ""
    amount: str = ""
    duration_days: str = ""
    payment_currency: str = "VND"
    payment_provider: str = ""
    note: str = ""
    skip_active_code: bool = False
    activation_code: str = ""
    sale_id: str = "MANUAL"
    step: str = "telegram_user_id"
    created_at: float = field(default_factory=time.time)


_DRAFTS: dict[int, OrderDraft] = {}


def _get_draft(admin_id: int) -> OrderDraft | None:
    return _DRAFTS.get(admin_id)


def _set_draft(admin_id: int, draft: OrderDraft | None):
    if draft is None:
        _DRAFTS.pop(admin_id, None)
    else:
        _DRAFTS[admin_id] = draft


def _fmt_customer_preview(text: str) -> str:
    text = str(text or "").strip()
    return text if len(text) <= 300 else text[:297] + "..."


def _ensure_plan_name_hint(draft: OrderDraft):
    candidates = _plan_candidates()
    if not candidates:
        return
    if not draft.plan_name.strip():
        draft.plan_name = candidates[0]


def _apply_pricing_from_plan(draft: OrderDraft):
    pricing = _resolve_plan_pricing(draft.plan_name, draft.payment_provider)
    if pricing.get("amount") and not str(draft.amount or "").strip():
        draft.amount = str(pricing.get("amount") or "")
    if pricing.get("duration_days") and not str(draft.duration_days or "").strip():
        draft.duration_days = str(pricing.get("duration_days") or "")
    currency = str(pricing.get("payment_currency") or "").strip().upper()
    if currency and not str(draft.payment_currency or "").strip():
        draft.payment_currency = currency


def _apply_forward_identity(draft: OrderDraft, message: Message):
    user = _forward_origin_user(message)
    if user:
        uid = str(getattr(user, "id", "") or "").strip()
        if uid:
            draft.telegram_user_id = uid
        first_name = str(getattr(user, "first_name", "") or "").strip()
        last_name = str(getattr(user, "last_name", "") or "").strip()
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()
        if full_name:
            draft.full_name = full_name
        username = str(getattr(user, "username", "") or "").strip()
        if username and not draft.full_name:
            draft.full_name = f"@{username}"
    if not draft.full_name:
        chat = _forward_origin_chat(message)
        if chat:
            title = str(getattr(chat, "title", "") or getattr(chat, "first_name", "") or "").strip()
            if title:
                draft.full_name = title
def _advance_after_field(draft: OrderDraft, field: str):
    if field == "telegram_user_id":
        draft.step = "plan_name"
    elif field == "plan_name":
        draft.step = "activation_code"
    elif field == "activation_code":
        draft.step = "telegram_user_id"
    else:
        draft.step = "telegram_user_id"


def _apply_skip(draft: OrderDraft):
    draft.step = _next_field(draft.step)


def _set_field(draft: OrderDraft, field: str, text: str):
    if field == "telegram_user_id":
        draft.telegram_user_id = text
    elif field == "full_name":
        draft.full_name = text
    elif field == "plan_name":
        draft.plan_name = text
        _apply_pricing_from_plan(draft)
    elif field == "note":
        draft.note = text
    elif field == "amount":
        draft.amount = text
    elif field == "duration_days":
        draft.duration_days = text
    elif field == "payment_currency":
        draft.payment_currency = text.upper()
    elif field == "payment_provider":
        draft.payment_provider = text.upper()
    elif field == "activation_code":
        draft.skip_active_code = False
        draft.activation_code = text.upper()
    else:
        draft.note = text


def _draft_summary(draft: OrderDraft) -> str:
    rows = [
        "🧾 <b>Admin order wizard</b>",
        f"• Telegram ID: <code>{_normalize_text(draft.telegram_user_id or '-')}</code>",
        f"• Gói: <code>{_normalize_text(draft.plan_name or '-')}</code>",
        f"• Hạn: <code>{_normalize_text(draft.duration_days or '-')} ngày</code>",
        f"• Số tiền: <code>{_normalize_text(draft.amount or '-')}</code>",
        f"• Tiền tệ: <code>{_normalize_text(draft.payment_currency or '-')}</code>",
        f"• Gen active code: <code>{'YES' if not draft.skip_active_code else 'NO'}</code>",
        f"• Bước hiện tại: <code>{_normalize_text(draft.step)}</code>",
    ]
    candidates = _plan_candidates()
    if candidates:
        rows.append(f"• Gợi ý gói: <code>{_normalize_text(', '.join(candidates[:3]))}</code>")
    return "\n".join(rows)


def _keyboard(draft: OrderDraft):
    if draft.step == "plan_name":
        candidates = _plan_candidates()
        kb = InlineKeyboardBuilder()
        for idx, plan_name in enumerate(candidates[:12]):
            pricing = _resolve_plan_pricing(plan_name, "")
            days = str(pricing.get("duration_days") or "?")
            kb.button(text=f"{plan_name} · {days}d", callback_data=f"admin_order:use_plan:{idx}")
        if candidates:
            kb.button(text="More", callback_data="admin_order:more")
        kb.button(text="Hủy", callback_data="admin_order:cancel")
        kb.adjust(1)
        return kb.as_markup()

    kb = InlineKeyboardBuilder()
    kb.button(text="Chọn gói", callback_data="admin_order:pick_plan")
    kb.button(text="More", callback_data="admin_order:more")
    kb.button(text="Hủy", callback_data="admin_order:cancel")
    kb.adjust(2, 1)
    return kb.as_markup()


def _more_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Back", callback_data="admin_order:back_to_main")
    kb.button(text="Note", callback_data="admin_order:set:note")
    kb.adjust(2)
    return kb.as_markup()


async def _render_draft(message_or_callback, draft: OrderDraft, notice: str = ""):
    text = _draft_summary(draft)
    prompt = f"• Chờ: <b>{_normalize_text(_field_label(draft.step))}</b>"
    if notice:
        text = f"{notice}\n\n{text}\n\n{prompt}"
    else:
        text = f"{text}\n\n{prompt}"
    markup = _keyboard(draft)
    if isinstance(message_or_callback, CallbackQuery):
        try:
            await message_or_callback.answer()
        except Exception:
            pass
        try:
            await message_or_callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            await message_or_callback.message.answer(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


def _start_draft_from_message(message: Message) -> OrderDraft:
    forward_text = _smart_forward_text(message)
    draft = OrderDraft(
        admin_id=message.from_user.id,
        source_chat_id=getattr(_forward_origin_chat(message), "id", None),
        source_message_id=getattr(message, "forward_from_message_id", None),
        customer_text=_fmt_customer_preview(forward_text),
        telegram_user_id="",
    )
    _apply_forward_identity(draft, message)
    return draft


async def _create_manual_order(draft: OrderDraft) -> dict[str, Any]:
    pricing = _resolve_plan_pricing(draft.plan_name, draft.payment_provider)
    payload = {
        "telegram_user_id": draft.telegram_user_id,
        "full_name": draft.full_name,
        "plan_name": draft.plan_name,
        "amount": draft.amount or pricing.get("amount") or 0,
        "duration_days": draft.duration_days or pricing.get("duration_days") or 30,
        "payment_currency": draft.payment_currency or pricing.get("payment_currency") or "VND",
        "payment_provider": draft.payment_provider,
        "note": draft.note,
        "skip_active_code": draft.skip_active_code,
        "activation_code": draft.activation_code,
        "skip_join_link": True,
        "fast_mode": True,
        "sale_id": draft.sale_id,
    }
    resp = requests.post(
        f"{_backend_base_url().rstrip('/')}/admin-api/manual-orders",
        json=payload,
        headers=_http_headers(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("data") or {}


@router.message(Command("admin_order"))
async def cmd_admin_order(message: Message):
    if not message.from_user or not is_admin_user(message.from_user.id):
        return
    draft = OrderDraft(admin_id=message.from_user.id)
    _set_draft(message.from_user.id, draft)
    await _render_draft(message, draft, "Bắt đầu luồng tạo đơn thủ công. Nếu forward, bot sẽ tự nhận ID/tên khách.")


@router.message(Command("new"))
async def cmd_new_admin_order(message: Message):
    if not message.from_user or not is_admin_user(message.from_user.id):
        await message.answer("admin only")
        return
    draft = OrderDraft(admin_id=message.from_user.id)
    _set_draft(message.from_user.id, draft)
    await _render_draft(message, draft, "Bắt đầu tạo đơn mới. Nhập Telegram ID hoặc forward tin khách.")


@router.callback_query(F.data.startswith("admin_order:"))
async def admin_order_actions(callback: CallbackQuery):
    if not callback.from_user or not is_admin_user(callback.from_user.id):
        return
    draft = _get_draft(callback.from_user.id)
    if not draft:
        await callback.answer("Không có draft nào đang mở.", show_alert=True)
        return

    _, action, *rest = (callback.data or "").split(":")

    if action == "cancel":
        _set_draft(callback.from_user.id, None)
        await callback.message.edit_text("Đã hủy luồng tạo đơn.")
        await callback.answer()
        return

    if action == "toggle":
        await callback.answer("Không dùng trong flow nhanh.", show_alert=True)
        return

    if action == "back":
        draft.step = _prev_field(draft.step)
        await _render_draft(callback, draft, "Đã lùi về bước trước.")
        return

    if action == "more":
        await callback.message.edit_text(
            "Chọn note khi cần:",
            reply_markup=_more_keyboard(),
        )
        await callback.answer()
        return

    if action == "pick_plan":
        candidates = _plan_candidates()
        if not candidates:
            await callback.answer("Chưa có gói nào để gợi ý.", show_alert=True)
            return
        draft.step = "plan_name"
        await _render_draft(callback, draft, "Chọn gói nhanh:")
        return

    if action == "back_to_main":
        await _render_draft(callback, draft, "Quay lại wizard chính.")
        return

    if action == "use_plan":
        idx = int(rest[0]) if rest and rest[0].isdigit() else -1
        candidates = _plan_candidates()
        if idx < 0 or idx >= len(candidates):
            await callback.answer("Gói không hợp lệ.", show_alert=True)
            return
        draft.plan_name = candidates[idx]
        _apply_pricing_from_plan(draft)
        draft.step = "activation_code"
        await callback.answer()
        try:
            result = await _create_manual_order(draft)
        except Exception as exc:
            print(
                "⚠️ Manual order create failed",
                {
                    "admin_id": callback.from_user.id,
                    "backend_url": _backend_base_url(),
                    "telegram_user_id": draft.telegram_user_id,
                    "plan_name": draft.plan_name,
                    "error": str(exc),
                },
            )
            await callback.message.edit_text(
                f"❌ Lỗi tạo đơn: {_short_error_text(exc)}\n\n"
                f"Đã chọn gói: <code>{_normalize_text(draft.plan_name)}</code>\n"
                f"Bạn có thể bấm Back để chọn lại."
            )
            return
        _set_draft(callback.from_user.id, None)
        await callback.message.edit_text(
            "✅ Đã tạo đơn.\n\n"
            f"Telegram ID: <code>{_normalize_text(result.get('telegram_user_id') or draft.telegram_user_id or '-')}</code>\n"
            f"Gói: <code>{_normalize_text(result.get('plan_name') or draft.plan_name or '-')}</code>\n"
            f"Activation: <code>{_normalize_text(result.get('activation_code') or '-')}</code>\n"
            f"URL: <code>{_normalize_text(result.get('activation_url') or '-')}</code>"
        )
        return


@router.message(F.chat.type == "private")
async def admin_order_capture(message: Message):
    if not message.from_user or not is_admin_user(message.from_user.id):
        raise SkipHandler()

    if _is_forwarded_message(message):
        draft = _start_draft_from_message(message)
        _set_draft(message.from_user.id, draft)
        await _render_draft(message, draft, "Đã nhận tin forward. Chỉ cần kiểm tra rồi bấm tạo.")
        return

    draft = _get_draft(message.from_user.id)
    if not draft:
        raise SkipHandler()
    text = str(message.text or message.caption or "").strip()
    if not text or text.startswith("/"):
        raise SkipHandler()
    field = draft.step
    if field == "telegram_user_id":
        draft.telegram_user_id = text
        draft.step = "plan_name"
        await _render_draft(message, draft, "Đã cập nhật Telegram ID. Chọn gói ngay bên dưới.")
        return
    if field == "full_name":
        draft.full_name = text
        await _render_draft(message, draft, "Đã cập nhật tên khách.")
        return
    if field == "plan_name":
        draft.plan_name = text
        _apply_pricing_from_plan(draft)
        draft.step = "activation_code"
        await _render_draft(message, draft, "Đã cập nhật gói. Chọn gói xong bot sẽ xuất active code ngay.")
        return
    if field == "note":
        draft.note = text
        await _render_draft(message, draft, "Đã cập nhật ghi chú. Bạn có thể bấm tạo ngay.")
        return
    if field == "amount":
        draft.amount = text
        await _render_draft(message, draft, "Đã cập nhật số tiền.")
        return
    if field == "duration_days":
        draft.duration_days = text
        await _render_draft(message, draft, "Đã cập nhật số ngày.")
        return
    if field == "payment_currency":
        draft.payment_currency = text.upper()
        await _render_draft(message, draft, "Đã cập nhật tiền tệ.")
        return
    if field == "payment_provider":
        draft.payment_provider = text.upper()
        await _render_draft(message, draft, "Đã cập nhật provider.")
        return
    if field == "activation_code":
        draft.skip_active_code = False
        draft.activation_code = text.upper()
        await _render_draft(message, draft, "Đã cập nhật active code.")
        return
