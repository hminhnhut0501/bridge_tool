import asyncio
import logging
import re
import secrets
import string
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import bot
from config_utils import config_int, group_numbers
from database import db, normalize_key
from helpers import check_protection, is_admin_user
from hidden_group_utils import (
    get_hidden_code,
    hidden_code_available_groups,
    hidden_duration_days,
    hidden_duration_price,
    mark_hidden_code_used,
    record_hidden_code_redemption,
    resolve_plan_groups,
    validate_hidden_code_for_user,
)
from i18n import get_user_language, t
from processor import escape_html, find_current_expire, find_current_expire_from_orders, normalize_chat_id, parse_expire_datetime
from supabase_store import supabase_store
from support_utils import add_support_join_button, is_support_group, unmute_member

router = Router()
log = logging.getLogger(__name__)
coupon_lock = asyncio.Lock()
coupon_attempts = {}
coupon_locks = {}

COUPONS_SHEET = "Coupons"
REDEMPTIONS_SHEET = "CouponRedemptions"
TIME_FMT = "%Y-%m-%d %H:%M:%S"
SELECT_GROUP_1M = "SELECT_GROUP_1M"
SELECT_GROUP_LIFE = "SELECT_GROUP_LIFE"
PLACEHOLDER_RE = re.compile(r"\{\s*([a-zA-Z0-9_]+)\s*\}")
DEFAULT_LIFETIME_DAYS = 36500

COUPON_HEADERS = [
    "Code",
    "Enabled",
    "Coupon_Type",
    "Plan_Name",
    "Duration_Days",
    "Discount_Percent",
    "Applies_To",
    "Max_Uses",
    "Used_Count",
    "Valid_From",
    "Valid_Until",
    "Cleanup_After_Days",
    "Created_At",
    "Created_By",
    "Last_Used_At",
    "Last_Used_By",
    "Note",
]

REDEMPTION_HEADERS = [
    "Redeemed_At",
    "Code",
    "User_ID",
    "Username",
    "Full_Name",
    "Plan_Name",
    "Duration_Days",
    "Expire_At",
    "Status",
    "User_Order_ID",
    "Groups",
]


class CouponState(StatesGroup):
    waiting_code = State()


def now_text():
    return now_local().strftime(TIME_FMT)


def bot_timezone():
    timezone_name = str(db.get_config("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def now_local():
    return datetime.now(bot_timezone()).replace(tzinfo=None)


def safe_int(value, default=0):
    try:
        raw = str(value or "").strip().replace(",", ".")
        if not raw:
            return default
        match = re.search(r"-?\d+(?:\.\d+)?", raw)
        if match:
            raw = match.group(0)
        return int(float(raw))
    except Exception:
        return default


def normalize_code(value):
    return normalize_key(value).upper().replace(" ", "")


def render_named_template(template, values):
    normalized = {str(key).strip().lower(): str(value) for key, value in (values or {}).items()}

    def replace(match):
        key = match.group(1).strip().lower()
        return normalized.get(key, match.group(0))

    return PLACEHOLDER_RE.sub(replace, str(template or "")).strip()


def truthy(value):
    return str(value or "").strip().upper() in {"ON", "TRUE", "YES", "Y", "1", "ACTIVE", "BẬT", "BAT"}


def config_enabled(key, default="OFF"):
    return truthy(db.get_config(key, default) or default)


def coupon_auto_prefixes():
    raw = db.get_config("COUPON_AUTO_REDEEM_PREFIXES", "HANGCU_")
    prefixes = {"HANGCU_"}
    for item in str(raw or "").replace("\n", ",").split(","):
        normalized = normalize_code(item)
        if normalized:
            prefixes.add(normalized)
    return sorted(prefixes, key=len, reverse=True)


def code_has_auto_prefix(text):
    code = normalize_code(text)
    return bool(code) and any(code.startswith(prefix) for prefix in coupon_auto_prefixes())


def code_is_hidden_exact_match(text):
    code = normalize_code(text)
    return bool(code) and bool(get_hidden_code(code))


async def check_coupon_abuse(message, code):
    user = message.from_user
    if not user or is_admin_user(user.id) or not config_enabled("COUPON_ABUSE_ENABLED", "ON"):
        return True

    now_ts = time.time()
    user_id = user.id
    locked_until = coupon_locks.get(user_id, 0)
    if locked_until > now_ts:
        minutes_left = max(int((locked_until - now_ts + 59) // 60), 1)
        if config_enabled("COUPON_ABUSE_NOTIFY_USER", "ON"):
            template = t(
                user.id,
                "MSG_COUPON_RATE_LIMITED",
                "⛔ Bạn nhập mã quá nhiều lần. Vui lòng thử lại sau {minutes} phút.",
            ).replace("\\n", "\n")
            await message.answer(template.replace("{minutes}", str(minutes_left)), parse_mode="HTML")
        return False

    window_seconds = max(safe_int(db.get_config("COUPON_WINDOW_SECONDS", "600"), 600), 30)
    max_attempts = max(safe_int(db.get_config("COUPON_MAX_ATTEMPTS", "5"), 5), 1)
    lock_minutes = max(safe_int(db.get_config("COUPON_LOCK_MINUTES", "30"), 30), 1)
    attempts = [item for item in coupon_attempts.get(user_id, []) if now_ts - item < window_seconds]
    attempts.append(now_ts)
    coupon_attempts[user_id] = attempts

    if len(attempts) <= max_attempts:
        return True

    coupon_locks[user_id] = now_ts + lock_minutes * 60
    if config_enabled("COUPON_ABUSE_AUTO_BLACKLIST", "OFF") and supabase_store.enabled:
        try:
            supabase_store.upsert_blacklist({
                "telegram_user_id": str(user.id),
                "username": user.username or "",
                "full_name": user.full_name or "",
                "reason": f"Nhập coupon quá giới hạn: {len(attempts)} lần/{window_seconds}s",
                "source": "coupon_abuse",
                "raw_data": {"last_code": code},
            })
        except Exception as exc:
            log.warning("Cannot auto blacklist coupon abuse user %s: %s", user.id, exc)

    if config_enabled("COUPON_ABUSE_NOTIFY_USER", "ON"):
        template = t(
            user.id,
            "MSG_COUPON_RATE_LIMITED",
            "⛔ Bạn nhập mã quá nhiều lần. Vui lòng thử lại sau {minutes} phút.",
        ).replace("\\n", "\n")
        await message.answer(template.replace("{minutes}", str(lock_minutes)), parse_mode="HTML")
    return False


def coupon_type(item):
    raw_type = normalize_key((item or {}).get("Coupon_Type") or (item or {}).get("Type") or "ACTIVATION").upper()
    if raw_type in {"DISCOUNT", "GIAM_GIA", "GIẢM_GIÁ", "PERCENT"}:
        return "DISCOUNT"
    return "ACTIVATION"


def normalize_plan_key(value):
    return normalize_key(value).upper().replace(" ", "")


def all_coupon_plan_keys():
    keys = ["FULL_1M", "FULL_LIFE"]
    for group_no in group_numbers():
        if db.get_config(f"BTN_G{group_no}") or db.get_config(f"ID_G{group_no}"):
            keys.extend([f"G{group_no}_1M", f"G{group_no}_LIFE"])
    return keys


def selectable_group_plan_keys(plan_name):
    key = normalize_plan_key(plan_name)
    suffix = "_LIFE" if key == SELECT_GROUP_LIFE else "_1M"
    keys = []
    for group_no in group_numbers():
        if db.get_config(f"BTN_G{group_no}") and db.get_config(f"ID_G{group_no}"):
            keys.append(f"G{group_no}{suffix}")
    return keys


def is_selectable_group_coupon_plan(plan_name):
    return normalize_plan_key(plan_name) in {SELECT_GROUP_1M, SELECT_GROUP_LIFE}


def coupon_lifetime_days():
    return max(config_int("COUPON_LIFETIME_DAYS", DEFAULT_LIFETIME_DAYS), 3650)


def is_lifetime_coupon_plan(plan_name):
    key = normalize_plan_key(plan_name)
    return key in {"FULL_LIFE", "SVIP_LIFE", SELECT_GROUP_LIFE} or key.endswith("_LIFE")


def coupon_duration_days(coupon, plan_key=None):
    if is_lifetime_coupon_plan(plan_key or (coupon or {}).get("Plan_Name")):
        return coupon_lifetime_days()
    return safe_int((coupon or {}).get("Duration_Days"), 30)


def duration_label(coupon, user_id=None, plan_key=None):
    custom = str((coupon or {}).get("Duration_Label") or (coupon or {}).get("Activation_Label") or "").strip()
    if custom:
        return custom

    days = coupon_duration_days(coupon, plan_key)
    if is_lifetime_coupon_plan(plan_key or (coupon or {}).get("Plan_Name")) or days >= 3650:
        return "trọn đời"
    return f"{days} ngày"


def coupon_applies_to(item):
    raw = str((item or {}).get("Applies_To") or "").strip()
    if not raw:
        fallback = normalize_plan_key((item or {}).get("Plan_Name"))
        return [fallback] if fallback else []
    if raw.upper() == "ALL":
        return ["ALL"]
    return [normalize_plan_key(part) for part in raw.replace(";", ",").split(",") if normalize_plan_key(part)]


def coupon_matches_plan(item, plan_key):
    applies = coupon_applies_to(item)
    return "ALL" in applies or normalize_plan_key(plan_key) in applies


def coupon_discount_percent(item):
    percent = safe_int((item or {}).get("Discount_Percent"), 0)
    return max(0, min(percent, 100))


def get_or_create_sheet(title, headers):
    try:
        sheet = db.sh.worksheet(title)
    except Exception:
        sheet = db.sh.add_worksheet(title=title, rows=1000, cols=max(len(headers), 12))
        sheet.update("A1", [headers])
        return sheet

    values = sheet.get_all_values()
    if not values:
        sheet.update("A1", [headers])
    else:
        current_headers = values[0]
        missing = [header for header in headers if header not in current_headers]
        if missing:
            sheet.update("A1", [current_headers + missing])
    return sheet


def ensure_coupon_sheets():
    if not db.sh:
        db.connect()
    return (
        get_or_create_sheet(COUPONS_SHEET, COUPON_HEADERS),
        get_or_create_sheet(REDEMPTIONS_SHEET, REDEMPTION_HEADERS),
    )


def row_to_dict(headers, row):
    return {
        str(header).strip(): str(row[idx]).strip() if idx < len(row) else ""
        for idx, header in enumerate(headers)
        if str(header).strip()
    }


def get_coupon_rows():
    coupons_sheet, _ = ensure_coupon_sheets()
    rows = coupons_sheet.get_all_values()
    if not rows:
        return coupons_sheet, [], []
    headers = rows[0]
    data = [(idx + 2, row_to_dict(headers, row)) for idx, row in enumerate(rows[1:]) if any(row)]
    return coupons_sheet, headers, data


def get_redemption_rows():
    _, redemptions_sheet = ensure_coupon_sheets()
    rows = redemptions_sheet.get_all_values()
    if not rows:
        return redemptions_sheet, [], []
    headers = rows[0]
    data = [(idx + 2, row_to_dict(headers, row)) for idx, row in enumerate(rows[1:]) if any(row)]
    return redemptions_sheet, headers, data


def find_coupon(code):
    if supabase_store.enabled:
        coupon = supabase_store.get_coupon(normalize_code(code))
        if not coupon:
            return None, [], None, None
        raw = dict(coupon.get("raw_data") or {})
        raw.setdefault("Code", coupon.get("code") or "")
        raw.setdefault("Enabled", "ON" if str(coupon.get("status") or "ACTIVE").upper() == "ACTIVE" else "OFF")
        raw.setdefault("Plan_Name", coupon.get("plan_name") or "")
        raw.setdefault("Max_Uses", coupon.get("max_uses") or "")
        raw.setdefault("Used_Count", coupon.get("used_count") or "")
        raw.setdefault("Valid_Until", coupon.get("expires_at") or raw.get("Valid_Until") or "")
        return None, [], coupon.get("code"), raw

    target = normalize_code(code)
    coupons_sheet, headers, rows = get_coupon_rows()
    for row_index, item in rows:
        if normalize_code(item.get("Code")) == target:
            return coupons_sheet, headers, row_index, item
    return coupons_sheet, headers, None, None


def has_user_redeemed(code, user_id):
    if supabase_store.enabled:
        return supabase_store.has_coupon_redemption(code, user_id)

    _, _, rows = get_redemption_rows()
    target = normalize_code(code)
    uid = str(user_id)
    for _, item in rows:
        if normalize_code(item.get("Code")) == target and str(item.get("User_ID")) == uid:
            return True
    return False


def validate_coupon_base(item, user_id):
    if not item:
        return False, t(user_id, "ALERT_COUPON_NOT_FOUND", "Mã giảm giá không tồn tại hoặc đã được dọn khỏi hệ thống.")

    if not truthy(item.get("Enabled", "ON")):
        return False, t(user_id, "ALERT_COUPON_DISABLED", "Mã này đang tắt, vui lòng kiểm tra lại mã khác.")

    now = now_local()
    valid_from = parse_expire_datetime(item.get("Valid_From"))
    valid_until = parse_expire_datetime(item.get("Valid_Until"))
    if valid_from and now < valid_from:
        return False, t(user_id, "ALERT_COUPON_NOT_STARTED", "Mã này chỉ bắt đầu dùng từ {date}.").replace("{date}", valid_from.strftime(TIME_FMT))
    if valid_until and now > valid_until:
        return False, t(user_id, "ALERT_COUPON_EXPIRED", "Mã này đã hết hạn sử dụng.")

    max_uses = safe_int(item.get("Max_Uses"), 1)
    used_count = safe_int(item.get("Used_Count"), 0)
    if max_uses > 0 and used_count >= max_uses:
        return False, t(user_id, "ALERT_COUPON_MAXED", "Mã này đã hết số lượt sử dụng.")

    if has_user_redeemed(item.get("Code"), user_id):
        return False, t(user_id, "ALERT_COUPON_ALREADY_USED", "Bạn đã sử dụng mã này trước đó rồi.")

    return True, ""


def validate_coupon(item, user_id):
    valid, reason = validate_coupon_base(item, user_id)
    if not valid:
        return False, reason

    if coupon_type(item) == "DISCOUNT":
        if coupon_discount_percent(item) <= 0:
            return False, t(user_id, "ALERT_COUPON_DISCOUNT_NOT_CONFIGURED", "Mã giảm giá chưa cấu hình phần trăm giảm.")
        if not coupon_applies_to(item):
            return False, t(user_id, "ALERT_COUPON_APPLIES_EMPTY", "Mã giảm giá chưa chọn gói áp dụng.")
        return True, ""

    plan_name = str(item.get("Plan_Name") or "").strip()
    if not plan_name:
        return False, t(user_id, "ALERT_COUPON_PLAN_EMPTY", "Mã này chưa gắn gói thành viên trên sheet.")
    duration_days = coupon_duration_days(item, plan_name)
    if duration_days <= 0:
        return False, t(user_id, "ALERT_COUPON_DURATION_INVALID", "Mã này chưa có số ngày sử dụng hợp lệ.")

    return True, ""


def localized_config(user_id, key, default=""):
    return t(user_id, key, default) if user_id else db.get_config(key, default)


def resolve_plan_name(plan_key, user_id=None):
    raw = str(plan_key or "").strip()
    key = raw.upper()

    plan_map = {
        "FULL_1M": localized_config(user_id, "PLAN_FULL_1M", "SVIP+ 30 Ngày"),
        "FULL_LIFE": localized_config(user_id, "PLAN_FULL_LIFE", "SVIP+ TRỌN ĐỜI"),
        "SVIP_1M": localized_config(user_id, "PLAN_FULL_1M", "SVIP+ 30 Ngày"),
        "SVIP_LIFE": localized_config(user_id, "PLAN_FULL_LIFE", "SVIP+ TRỌN ĐỜI"),
        SELECT_GROUP_1M: "Khách tự chọn group lẻ - 30 ngày",
        SELECT_GROUP_LIFE: "Khách tự chọn group lẻ - trọn đời",
    }
    if key in plan_map:
        return plan_map[key]

    for group_no in group_numbers():
        if key == f"G{group_no}_1M":
            return f"{localized_config(user_id, 'PLAN_G_1M', 'VIP 30 Ngày')} - {localized_config(user_id, f'BTN_G{group_no}', f'Nhóm {group_no}')}"
        if key == f"G{group_no}_LIFE":
            return f"{localized_config(user_id, 'PLAN_G_LIFE', 'Gói trọn đời')} - {localized_config(user_id, f'BTN_G{group_no}', f'Nhóm {group_no}')}"

    return raw.replace("_", " ")


def group_name_from_plan_key(plan_key, user_id=None):
    key = normalize_plan_key(plan_key)
    match = None
    if key.startswith("G") and key.endswith("_1M"):
        match = key[1:-3]
    elif key.startswith("G") and key.endswith("_LIFE"):
        match = key[1:-5]
    if not match:
        return ""
    return localized_config(user_id, f"BTN_G{match}", f"Nhóm {match}")


def render_coupon_template(template, *, coupon, plan_key, fallback_plan_name="", user_id=None):
    group_name = group_name_from_plan_key(plan_key, user_id)
    days = str(coupon_duration_days(coupon, plan_key))
    label = duration_label(coupon, user_id, plan_key)
    plan_name = fallback_plan_name or resolve_plan_name(plan_key, user_id)
    return render_named_template(template, {
        "group": group_name,
        "group_name": group_name,
        "duration_label": label,
        "duration": label,
        "days": days,
        "plan": plan_name,
        "plan_name": plan_name,
    })


def activation_coupon_plan_name(plan_key, coupon, user_id=None):
    purchase_plan_name = resolve_plan_name(plan_key, user_id)
    template = (
        (coupon or {}).get("Plan_Name_Template")
        or (coupon or {}).get("Activation_Plan_Template")
        or t(user_id, "COUPON_ACTIVATION_PLAN_TEMPLATE", "VIP {duration_label} - {group}")
    )
    template_text = str(template or "")
    label = duration_label(coupon, user_id, plan_key)
    if "{duration" not in template_text.lower() and "{days" not in template_text.lower() and label.lower() not in template_text.lower():
        template = "VIP {duration_label} - {group}"
    return render_coupon_template(template, coupon=coupon, plan_key=plan_key, fallback_plan_name=purchase_plan_name, user_id=user_id) or purchase_plan_name


def activation_coupon_button_label(plan_key, coupon, user_id=None):
    plan_name = activation_coupon_plan_name(plan_key, coupon, user_id=user_id)
    template = (
        (coupon or {}).get("Button_Template")
        or (coupon or {}).get("Activation_Button_Template")
        or t(user_id, "COUPON_ACTIVATION_BUTTON_TEMPLATE", "{plan_name}")
    )
    return render_coupon_template(template, coupon=coupon, plan_key=plan_key, fallback_plan_name=plan_name, user_id=user_id) or plan_name


def discount_plan_label(plan_key, user_id=None):
    return resolve_plan_name(plan_key, user_id)


def build_discount_coupon_keyboard(code, coupon, user_id=None):
    applies = coupon_applies_to(coupon)
    plan_keys = all_coupon_plan_keys() if "ALL" in applies else applies
    kb = InlineKeyboardBuilder()
    for plan_key in plan_keys:
        kb.row(InlineKeyboardButton(
            text=f"{discount_plan_label(plan_key, user_id=user_id)} (-{coupon_discount_percent(coupon)}%)",
            callback_data=f"couponbuy|{code}|{plan_key}",
        ))
    kb.row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", "Quay lại Menu"), callback_data="back_main"))
    return kb.as_markup()


async def send_discount_coupon_options(message: Message, code, coupon):
    percent = str(coupon_discount_percent(coupon))
    text = t(
        message.from_user.id,
        "MSG_COUPON_DISCOUNT_OPTIONS",
        "<b>✅ Mã giảm giá hợp lệ</b>\\n\\n"
        "Mã: <code>{code}</code>\\n"
        "Giảm: <b>{percent}%</b>\\n\\n"
        "Chọn gói muốn mua bên dưới, bot sẽ tạo QR đã trừ giảm giá.",
    ).replace("\\n", "\n")
    text = render_named_template(text, {
        "code": escape_html(code),
        "percent": percent,
        "discount": percent,
        "discount_percent": percent,
    })
    await message.answer(text, reply_markup=build_discount_coupon_keyboard(code, coupon, message.from_user.id), parse_mode="HTML")


def build_activation_group_keyboard(code, coupon, user_id=None):
    kb = InlineKeyboardBuilder()
    for plan_key in selectable_group_plan_keys(coupon.get("Plan_Name")):
        kb.row(InlineKeyboardButton(
            text=activation_coupon_button_label(plan_key, coupon, user_id=user_id),
            callback_data=f"cact|{code}|{plan_key}",
        ))
    kb.row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", "Quay lại Menu"), callback_data="back_main"))
    return kb.as_markup()


async def send_activation_group_options(message: Message, code, coupon):
    if not selectable_group_plan_keys(coupon.get("Plan_Name")):
        await message.answer(t(message.from_user.id, "MSG_COUPON_NO_SELECTABLE_GROUPS", "❌ Mã hợp lệ nhưng chưa có group lẻ nào được cấu hình để khách chọn. Vui lòng báo admin kiểm tra BTN_G/ID_G."), parse_mode="HTML")
        return

    text = t(
        message.from_user.id,
        "MSG_COUPON_GROUP_OPTIONS",
        "<b>✅ Mã kích hoạt hợp lệ</b>\\n\\n"
        "Mã: <code>{code}</code>\\n"
        "Thời hạn: <b>{days} ngày</b>\\n\\n"
        "Chọn group bạn muốn kích hoạt bên dưới.",
    ).replace("\\n", "\n")
    duration = escape_html(duration_label(coupon, message.from_user.id))
    text = render_named_template(text, {
        "code": escape_html(code),
        "days": str(coupon_duration_days(coupon)),
        "duration_label": duration,
        "duration": duration,
    })
    await message.answer(text, reply_markup=build_activation_group_keyboard(code, coupon, message.from_user.id), parse_mode="HTML")


def resolve_groups(plan_name):
    return resolve_plan_groups(plan_name)


async def build_invite_links(user_id, plan_name):
    links_msg = ""
    group_names = []
    failed_groups = []

    for gid, group_name in resolve_groups(plan_name):
        try:
            try:
                await bot.unban_chat_member(chat_id=gid, user_id=int(user_id), only_if_banned=True)
            except Exception as unban_err:
                if "administrator" not in str(unban_err).lower():
                    log.warning("Cannot unban coupon user %s from %s: %s", user_id, gid, unban_err)

            invite = await bot.create_chat_invite_link(
                chat_id=gid,
                member_limit=1,
                creates_join_request=False,
            )
            group_names.append(group_name)
            links_msg += f"👉 <b>{escape_html(group_name)}</b>:\n{invite.invite_link}\n\n"
            try:
                if not is_support_group(gid):
                    await unmute_member(gid, user_id)
            except Exception as unmute_err:
                log.warning("Cannot unmute coupon user %s in %s: %s", user_id, gid, unmute_err)
        except Exception as err:
            failed_groups.append(group_name)
            template = t(user_id, "MSG_INVITE_LINK_ERROR", "👉 <b>{group}</b>: <i>Không tạo được link ({error})</i>\\n\\n").replace("\\n", "\n")
            links_msg += template.replace("{group}", escape_html(group_name)).replace("{error}", escape_html(err))

    return links_msg, ", ".join(group_names), failed_groups


def hidden_buy_buttons(user_id, code, groups):
    kb = InlineKeyboardBuilder()
    currency = "USD" if get_user_language(user_id) == "en" else "VND"
    for group in groups:
        label = group.get("name") or group.get("id")
        price_1m = hidden_duration_price(group, "1M", currency)
        price_life = hidden_duration_price(group, "LIFE", currency)
        if price_1m > 0:
            price_text = f"${price_1m}" if currency == "USD" else f"{int(price_1m):,}đ".replace(",", ".")
            kb.row(InlineKeyboardButton(text=f"Mua 30 ngày - {label} - {price_text}", callback_data=f"hgbuy|{code}|{group.get('id')}|1M"))
        if price_life > 0:
            price_text = f"${price_life}" if currency == "USD" else f"{int(price_life):,}đ".replace(",", ".")
            kb.row(InlineKeyboardButton(text=f"Mua trọn đời - {label} - {price_text}", callback_data=f"hgbuy|{code}|{group.get('id')}|LIFE"))
    kb.row(InlineKeyboardButton(text=t(user_id, "BTN_BACK", "Quay lại Menu"), callback_data="back_main"))
    return kb.as_markup()


async def send_hidden_code_catalog(message: Message, code, hidden_code):
    groups = hidden_code_available_groups(hidden_code)
    if not groups:
        await message.answer(t(message.from_user.id, "MSG_HIDDEN_NO_GROUPS", "❌ Mã hidden hợp lệ nhưng hiện chưa có hidden group nào đang mở."), parse_mode="HTML")
        return
    user_id = message.from_user.id
    mark_hidden_code_used(code)
    record_hidden_code_redemption(
        code,
        user_id,
        full_name=message.from_user.full_name or "",
        username=message.from_user.username or "",
        revealed_group_ids=[item.get("id") for item in groups],
    )
    lines = [
        t(user_id, "MSG_HIDDEN_VALID_TITLE", "<b>✅ Mã hidden hợp lệ</b>"),
        "",
        t(user_id, "MSG_HIDDEN_VALID_BODY", "Chọn gói bên dưới để mua:"),
        "",
    ]
    for group in groups:
        lines.append(f"• <b>{escape_html(group.get('name') or group.get('id'))}</b>")
        if group.get("description"):
            lines.append(f"  {escape_html(group.get('description'))}")
        lines.append("")
    await message.answer("\n".join(lines).strip(), reply_markup=hidden_buy_buttons(user_id, code, groups), parse_mode="HTML")


def update_coupon_usage(coupons_sheet, headers, row_index, item, user_id):
    if supabase_store.enabled:
        used_count = safe_int(item.get("Used_Count"), 0) + 1
        supabase_store.update_coupon_raw(item.get("Code"), {
            "Used_Count": str(used_count),
            "Last_Used_At": now_text(),
            "Last_Used_By": str(user_id),
        })
        return

    header_pos = {header: idx + 1 for idx, header in enumerate(headers)}
    used_col = header_pos.get("Used_Count")
    last_at_col = header_pos.get("Last_Used_At")
    last_by_col = header_pos.get("Last_Used_By")

    used_count = safe_int(item.get("Used_Count"), 0) + 1
    if used_col:
        coupons_sheet.update_cell(row_index, used_col, used_count)
    if last_at_col:
        coupons_sheet.update_cell(row_index, last_at_col, now_text())
    if last_by_col:
        coupons_sheet.update_cell(row_index, last_by_col, str(user_id))


async def redeem_coupon(message: Message, code):
    async with coupon_lock:
        await redeem_coupon_locked(message, code)


async def redeem_coupon_locked(message: Message, code):
    code = normalize_code(code)
    if not await check_coupon_abuse(message, code):
        return
    hidden_code, hidden_reason = validate_hidden_code_for_user(code, message.from_user.id)
    if hidden_code:
        await send_hidden_code_catalog(message, code, hidden_code)
        return
    if not supabase_store.enabled:
        db.connect()
    coupons_sheet, headers, row_index, coupon = find_coupon(code)
    valid, reason = validate_coupon(coupon, message.from_user.id)
    if not valid:
        if hidden_reason and "không tồn tại" not in hidden_reason.lower():
            await message.answer(f"❌ {escape_html(hidden_reason)}", parse_mode="HTML")
            return
        await message.answer(f"❌ {escape_html(reason)}", parse_mode="HTML")
        return

    if coupon_type(coupon) == "DISCOUNT":
        await send_discount_coupon_options(message, code, coupon)
        return

    if is_selectable_group_coupon_plan(coupon.get("Plan_Name")):
        await send_activation_group_options(message, code, coupon)
        return

    await redeem_activation_coupon(message, message.from_user, code, coupon, coupons_sheet, headers, row_index)


async def redeem_activation_coupon(message: Message, user, code, coupon, coupons_sheet, headers, row_index, selected_plan_key=None):
    plan_key = selected_plan_key or coupon.get("Plan_Name")
    plan_name = activation_coupon_plan_name(plan_key, coupon, user_id=user.id)
    duration_days = coupon_duration_days(coupon, plan_key)
    if supabase_store.enabled:
        paid_orders = supabase_store.list_paid_orders_for_user(user.id, limit=200)
        base_date = find_current_expire_from_orders(paid_orders, user.id, plan_name) or now_local()
    else:
        users_data = db.users_sheet.get_all_values()
        base_date = find_current_expire(users_data, user.id, plan_name) or now_local()
    expire_at = base_date + timedelta(days=duration_days)
    expire_text = expire_at.strftime(TIME_FMT)

    links_msg, group_names, failed_groups = await build_invite_links(user.id, plan_name)
    if not group_names or failed_groups:
        await message.answer(t(message.from_user.id, "MSG_COUPON_PLAN_NOT_CONFIGURED", "❌ Mã hợp lệ nhưng gói này chưa cấu hình nhóm nhận link. Vui lòng báo admin kiểm tra Plan_Name/ID_G."), parse_mode="HTML")
        return

    order_id = int(datetime.now().timestamp() * 1000)
    user_full_name = (user.full_name or "").strip()
    username = user.username or ""
    paid_at = now_text()

    if supabase_store.enabled:
        supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=user.id,
            full_name=user_full_name,
            plan_name=plan_name,
            amount=0,
            sale_id=code,
            original_amount=0,
            coupon_code=code,
        )
        supabase_store.mark_order_paid(order_id, paid_at=paid_at, expire_at=expire_text)
    else:
        db.users_sheet.append_row([
            order_id,
            str(user.id),
            user_full_name,
            plan_name,
            "0",
            "PAID",
            paid_at,
            expire_text,
            code,
            "COUPON",
        ])

    redemption_payload = {
        "Redeemed_At": paid_at,
        "Code": code,
        "User_ID": str(user.id),
        "Username": username,
        "Full_Name": user_full_name,
        "Plan_Name": plan_name,
        "Duration_Days": str(duration_days),
        "Expire_At": expire_text,
        "Status": "REDEEMED",
        "User_Order_ID": str(order_id),
        "Groups": group_names,
    }
    if supabase_store.enabled:
        supabase_store.record_coupon_redemption(code, user.id, order_id=order_id, raw_data=redemption_payload)
    else:
        _, redemptions_sheet = ensure_coupon_sheets()
        redemptions_sheet.append_row([
            paid_at,
            code,
            str(user.id),
            username,
            user_full_name,
            plan_name,
            str(duration_days),
            expire_text,
            "REDEEMED",
            str(order_id),
            group_names,
        ])

    update_coupon_usage(coupons_sheet, headers, row_index, coupon, user.id)

    template = t(
        user.id,
        "MSG_COUPON_SUCCESS",
        "<b>✅ KÍCH HOẠT MÃ THÀNH CÔNG</b>\\n\\n"
        "Mã: <code>{code}</code>\\n"
        "Gói: <b>{plan}</b>\\n"
        "Hạn dùng đến: <b>{expire}</b>\\n\\n"
        "Link tham gia của bạn:\\n{links}",
    ).replace("\\n", "\n")
    text = render_named_template(template, {
        "code": escape_html(code),
        "plan": escape_html(plan_name),
        "plan_name": escape_html(plan_name),
        "expire": expire_text,
        "expire_at": expire_text,
        "links": links_msg,
    })
    kb = InlineKeyboardBuilder()
    support_error = await add_support_join_button(kb, user.id)
    if support_error:
        text += support_error
    kb.row(InlineKeyboardButton(text=t(user.id, "BTN_BACK", "Quay lại Menu"), callback_data="back_main"))
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)


async def send_coupon_prompt(target, state: FSMContext):
    await state.set_state(CouponState.waiting_code)
    user_id = target.from_user.id
    text = t(
        user_id,
        "MSG_COUPON_PROMPT",
        "<b>Nhập mã giảm giá / mã kích hoạt</b>\\n\\nGửi mã bạn nhận được vào đây. Ví dụ: <code>VIP2026</code>",
    ).replace("\\n", "\n")
    kb = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=t(user_id, "BTN_BACK", "Quay lại Menu"), callback_data="back_main")
    )
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.message(Command("coupon"))
async def cmd_coupon(message: Message, state: FSMContext):
    if not await check_protection(message):
        return
    if not config_enabled("COUPON_COMMAND_ENABLED", "OFF"):
        return
    if message.chat.type != "private":
        await message.answer(t(message.from_user.id, "MSG_COUPON_PRIVATE_ONLY", "Vui lòng nhắn riêng với bot để nhập mã, tránh lộ mã trong group."))
        return
    await send_coupon_prompt(message, state)


@router.callback_query(F.data.in_({"coupon_enter", "coupon_code", "redeem_code"}))
async def coupon_button(callback: CallbackQuery, state: FSMContext):
    if not await check_protection(callback):
        return
    if not config_enabled("COUPON_MENU_ENABLED", "OFF"):
        await callback.answer(t(callback.from_user.id, "ALERT_COUPON_MENU_DISABLED", "Chức năng nhập mã trên menu đang được ẩn."), show_alert=True)
        return
    if callback.message.chat.type != "private":
        await callback.answer(t(callback.from_user.id, "ALERT_COUPON_PRIVATE_ONLY", "Vui lòng nhắn riêng với bot để nhập mã."), show_alert=True)
        return
    await send_coupon_prompt(callback, state)


@router.callback_query(F.data.startswith("cact|"))
async def coupon_activation_group_selected(callback: CallbackQuery):
    if not await check_protection(callback):
        return

    try:
        _, code, selected_plan_key = callback.data.split("|", 2)
    except ValueError:
        await callback.answer(t(callback.from_user.id, "ALERT_COUPON_SELECTION_INVALID", "Lựa chọn coupon không hợp lệ."), show_alert=True)
        return

    async with coupon_lock:
        code = normalize_code(code)
        if not supabase_store.enabled:
            db.connect()
        coupons_sheet, headers, row_index, coupon = find_coupon(code)
        valid, reason = validate_coupon_base(coupon, callback.from_user.id)
        if not valid:
            await callback.answer(reason, show_alert=True)
            return
        if coupon_type(coupon) != "ACTIVATION" or not is_selectable_group_coupon_plan(coupon.get("Plan_Name")):
            await callback.answer(t(callback.from_user.id, "ALERT_COUPON_NOT_GROUP_SELECT", "Mã này không phải coupon chọn group."), show_alert=True)
            return

        selected_plan_key = normalize_plan_key(selected_plan_key)
        if selected_plan_key not in selectable_group_plan_keys(coupon.get("Plan_Name")):
            await callback.answer(t(callback.from_user.id, "ALERT_COUPON_GROUP_OUT_OF_SCOPE", "Group này không nằm trong phạm vi coupon."), show_alert=True)
            return

        await callback.answer()
        await redeem_activation_coupon(
            callback.message,
            callback.from_user,
            code,
            coupon,
            coupons_sheet,
            headers,
            row_index,
            selected_plan_key=selected_plan_key,
        )


@router.message(CouponState.waiting_code)
async def coupon_code_received(message: Message, state: FSMContext):
    if not await check_protection(message):
        return

    code = normalize_code(message.text)
    if not code or len(code) < 3:
        await message.answer(t(message.from_user.id, "MSG_COUPON_INVALID_FORMAT", "Mã không hợp lệ. Vui lòng nhập lại mã bạn nhận được."))
        return

    await state.clear()
    await redeem_coupon(message, code)


@router.message(F.text & ~F.text.startswith("/"))
async def coupon_auto_code_received(message: Message):
    if not message.text:
        return
    if not code_has_auto_prefix(message.text) and not code_is_hidden_exact_match(message.text):
        return
    if not config_enabled("COUPON_AUTO_REDEEM_ENABLED", "ON"):
        await message.answer(t(message.from_user.id, "MSG_COUPON_AUTO_DISABLED", "Tự nhận diện coupon đang tắt. Vui lòng bật lại trong dashboard hoặc dùng /coupon nếu admin cho phép."))
        return
    if not await check_protection(message):
        return
    if message.chat.type != "private":
        await message.answer(t(message.from_user.id, "MSG_COUPON_PRIVATE_ONLY", "Vui lòng nhắn riêng với bot để nhập mã, tránh lộ mã trong group."))
        return
    await redeem_coupon(message, message.text)


@router.message(Command("gen_coupon"))
async def cmd_gen_coupon(message: Message):
    if not is_admin_user(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) < 4:
        await message.answer(
            "Cú pháp: /gen_coupon <số_lượng> <plan_key> <số_ngày> [max_uses] [prefix]\n"
            "Ví dụ: /gen_coupon 10 full_1m 30 1 HANGCU_\n"
            "Plan key nhanh: full_1m, full_life, g1_1m, g1_life..."
        )
        return

    count = min(max(safe_int(parts[1], 1), 1), 200)
    plan_name = resolve_plan_name(parts[2])
    duration_days = max(safe_int(parts[3], 30), 1)
    max_uses = max(safe_int(parts[4], 1), 1) if len(parts) >= 5 else 1
    prefix = normalize_code(parts[5])[:16] if len(parts) >= 6 else "HANGCU_"

    alphabet = string.ascii_uppercase + string.digits
    created_at = now_text()
    rows = []
    codes = []
    if supabase_store.enabled:
        existing = {str(item.get("code") or "").upper() for item in supabase_store.list_coupons()}
    else:
        coupons_sheet, _ = ensure_coupon_sheets()
        existing = {item.get("Code") for _, item in get_coupon_rows()[2]}

    while len(rows) < count:
        code = f"{prefix}{''.join(secrets.choice(alphabet) for _ in range(8))}"
        if code in existing:
            continue
        existing.add(code)
        codes.append(code)
        raw = {
            "Code": code,
            "Enabled": "ON",
            "Coupon_Type": "ACTIVATION",
            "Plan_Name": plan_name,
            "Duration_Days": str(duration_days),
            "Discount_Percent": "",
            "Applies_To": "",
            "Max_Uses": str(max_uses),
            "Used_Count": "0",
            "Valid_From": "",
            "Valid_Until": "",
            "Cleanup_After_Days": db.get_config("COUPON_CLEANUP_AFTER_DAYS", "7"),
            "Created_At": created_at,
            "Created_By": str(message.from_user.id),
            "Last_Used_At": "",
            "Last_Used_By": "",
            "Note": "Generated by /gen_coupon",
        }
        rows.append(raw)

    if supabase_store.enabled:
        for raw in rows:
            supabase_store.create_coupon_from_sheet_row(raw)
    else:
        coupons_sheet.append_rows([[raw.get(header, "") for header in COUPON_HEADERS] for raw in rows])
    preview = "\n".join(f"<code>{escape_html(code)}</code>" for code in codes[:20])
    more = "" if len(codes) <= 20 else f"\n... và {len(codes) - 20} mã nữa"
    await message.answer(
        f"✅ Đã tạo {len(codes)} mã coupon.\n"
        f"Gói: <b>{escape_html(plan_name)}</b>\n"
        f"Hạn dùng mỗi mã: <b>{duration_days} ngày</b>\n"
        f"Lượt dùng/mã: <b>{max_uses}</b>\n\n{preview}{more}",
        parse_mode="HTML",
    )


async def coupon_cleanup_worker():
    await asyncio.sleep(config_int("COUPON_CLEANUP_INITIAL_DELAY_SECONDS", 30, minimum=0))
    while True:
        interval_seconds = config_int("COUPON_CLEANUP_INTERVAL_HOURS", 12, minimum=1) * 60 * 60
        try:
            if supabase_store.enabled:
                log.info("Coupon cleanup skipped: Supabase retains coupon history.")
                await asyncio.sleep(interval_seconds)
                continue
            db.connect()
            cleanup_coupon_sheets()
        except Exception as err:
            log.error("Coupon cleanup failed: %s", err)
        await asyncio.sleep(interval_seconds)


def cleanup_coupon_sheets():
    coupons_sheet, coupon_headers, coupon_rows = get_coupon_rows()
    redemptions_sheet, redemption_headers, redemption_rows = get_redemption_rows()

    coupon_map = {
        normalize_code(item.get("Code")): item
        for _, item in coupon_rows
    }
    now = now_local()
    active_or_retained_codes = set()
    redemption_rows_to_delete = []

    for row_index, redemption in redemption_rows:
        code = normalize_code(redemption.get("Code"))
        coupon = coupon_map.get(code, {})
        cleanup_days = safe_int(coupon.get("Cleanup_After_Days"), safe_int(db.get_config("COUPON_CLEANUP_AFTER_DAYS", "7"), 7))
        expire_at = parse_expire_datetime(redemption.get("Expire_At"))
        if expire_at and now > expire_at + timedelta(days=max(cleanup_days, 0)):
            redemption_rows_to_delete.append(row_index)
        else:
            active_or_retained_codes.add(code)

    for row_index in sorted(redemption_rows_to_delete, reverse=True):
        redemptions_sheet.delete_rows(row_index)

    coupon_rows_to_delete = []
    for row_index, coupon in coupon_rows:
        code = normalize_code(coupon.get("Code"))
        max_uses = safe_int(coupon.get("Max_Uses"), 1)
        used_count = safe_int(coupon.get("Used_Count"), 0)
        if max_uses <= 0 or used_count < max_uses or code in active_or_retained_codes:
            continue

        cleanup_days = safe_int(coupon.get("Cleanup_After_Days"), safe_int(db.get_config("COUPON_CLEANUP_AFTER_DAYS", "7"), 7))
        last_used_at = parse_expire_datetime(coupon.get("Last_Used_At"))
        valid_until = parse_expire_datetime(coupon.get("Valid_Until"))
        marker = last_used_at or valid_until
        if marker and now > marker + timedelta(days=max(cleanup_days, 0)):
            coupon_rows_to_delete.append(row_index)

    for row_index in sorted(coupon_rows_to_delete, reverse=True):
        coupons_sheet.delete_rows(row_index)

    if redemption_rows_to_delete or coupon_rows_to_delete:
        log.info(
            "Coupon cleanup removed %s redemptions and %s coupons",
            len(redemption_rows_to_delete),
            len(coupon_rows_to_delete),
        )
