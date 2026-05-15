import asyncio
import logging
import secrets
import string
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import bot
from database import db, normalize_key
from helpers import ADMIN_ID, check_protection
from processor import escape_html, find_current_expire, find_current_expire_from_orders, normalize_chat_id, parse_expire_datetime
from supabase_store import supabase_store

router = Router()
log = logging.getLogger(__name__)
coupon_lock = asyncio.Lock()

COUPONS_SHEET = "Coupons"
REDEMPTIONS_SHEET = "CouponRedemptions"
TIME_FMT = "%Y-%m-%d %H:%M:%S"

COUPON_HEADERS = [
    "Code",
    "Enabled",
    "Plan_Name",
    "Duration_Days",
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
    return datetime.now().strftime(TIME_FMT)


def safe_int(value, default=0):
    try:
        raw = str(value or "").strip().replace(",", ".")
        if not raw:
            return default
        return int(float(raw))
    except Exception:
        return default


def normalize_code(value):
    return normalize_key(value).upper().replace(" ", "")


def truthy(value):
    return str(value or "").strip().upper() in {"ON", "TRUE", "YES", "Y", "1", "ACTIVE", "BẬT", "BAT"}


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
    target = normalize_code(code)
    coupons_sheet, headers, rows = get_coupon_rows()
    for row_index, item in rows:
        if normalize_code(item.get("Code")) == target:
            return coupons_sheet, headers, row_index, item
    return coupons_sheet, headers, None, None


def has_user_redeemed(code, user_id):
    _, _, rows = get_redemption_rows()
    target = normalize_code(code)
    uid = str(user_id)
    for _, item in rows:
        if normalize_code(item.get("Code")) == target and str(item.get("User_ID")) == uid:
            return True
    return False


def validate_coupon(item, user_id):
    if not item:
        return False, "Mã giảm giá không tồn tại hoặc đã được dọn khỏi hệ thống."

    if not truthy(item.get("Enabled", "ON")):
        return False, "Mã này đang tắt, vui lòng kiểm tra lại mã khác."

    now = datetime.now()
    valid_from = parse_expire_datetime(item.get("Valid_From"))
    valid_until = parse_expire_datetime(item.get("Valid_Until"))
    if valid_from and now < valid_from:
        return False, f"Mã này chỉ bắt đầu dùng từ {valid_from.strftime(TIME_FMT)}."
    if valid_until and now > valid_until:
        return False, "Mã này đã hết hạn sử dụng."

    max_uses = safe_int(item.get("Max_Uses"), 1)
    used_count = safe_int(item.get("Used_Count"), 0)
    if max_uses > 0 and used_count >= max_uses:
        return False, "Mã này đã hết số lượt sử dụng."

    if has_user_redeemed(item.get("Code"), user_id):
        return False, "Bạn đã sử dụng mã này trước đó rồi."

    plan_name = str(item.get("Plan_Name") or "").strip()
    duration_days = safe_int(item.get("Duration_Days"), 0)
    if not plan_name:
        return False, "Mã này chưa gắn gói thành viên trên sheet."
    if duration_days <= 0:
        return False, "Mã này chưa có số ngày sử dụng hợp lệ."

    return True, ""


def resolve_plan_name(plan_key):
    raw = str(plan_key or "").strip()
    key = raw.upper()

    plan_map = {
        "FULL_1M": db.get_config("PLAN_FULL_1M", "SVIP+ 1 THÁNG"),
        "FULL_LIFE": db.get_config("PLAN_FULL_LIFE", "SVIP+ TRỌN ĐỜI"),
        "SVIP_1M": db.get_config("PLAN_FULL_1M", "SVIP+ 1 THÁNG"),
        "SVIP_LIFE": db.get_config("PLAN_FULL_LIFE", "SVIP+ TRỌN ĐỜI"),
    }
    if key in plan_map:
        return plan_map[key]

    for group_no in range(1, 21):
        if key == f"G{group_no}_1M":
            return f"{db.get_config('PLAN_G_1M', 'Gói 1 tháng')} - {db.get_config(f'BTN_G{group_no}', f'Nhóm {group_no}')}"
        if key == f"G{group_no}_LIFE":
            return f"{db.get_config('PLAN_G_LIFE', 'Gói trọn đời')} - {db.get_config(f'BTN_G{group_no}', f'Nhóm {group_no}')}"

    return raw.replace("_", " ")


def resolve_groups(plan_name):
    groups = []
    plan_upper = str(plan_name or "").upper()

    if "FULL" in plan_upper or "SVIP" in plan_upper:
        for group_no in range(1, 21):
            gid = normalize_chat_id(db.get_config(f"ID_G{group_no}"))
            if gid:
                groups.append((gid, db.get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")))
        return groups

    for group_no in range(1, 21):
        btn_name = db.get_config(f"BTN_G{group_no}", f"Nhóm {group_no}")
        if str(btn_name).upper() in plan_upper or f"G{group_no}" in plan_upper:
            gid = normalize_chat_id(db.get_config(f"ID_G{group_no}"))
            if gid:
                groups.append((gid, btn_name))
    return groups


async def build_invite_links(user_id, plan_name):
    links_msg = ""
    group_names = []

    for gid, group_name in resolve_groups(plan_name):
        group_names.append(group_name)
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
            links_msg += f"👉 <b>{escape_html(group_name)}</b>:\n{invite.invite_link}\n\n"
        except Exception as err:
            links_msg += f"👉 <b>{escape_html(group_name)}</b>: <i>Không tạo được link ({escape_html(err)})</i>\n\n"

    return links_msg, ", ".join(group_names)


def update_coupon_usage(coupons_sheet, headers, row_index, item, user_id):
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
    db.connect()
    coupons_sheet, headers, row_index, coupon = find_coupon(code)
    valid, reason = validate_coupon(coupon, message.from_user.id)
    if not valid:
        await message.answer(f"❌ {escape_html(reason)}", parse_mode="HTML")
        return

    plan_name = coupon.get("Plan_Name")
    duration_days = safe_int(coupon.get("Duration_Days"), 30)
    if supabase_store.enabled:
        paid_orders = supabase_store.list_paid_orders_for_user(message.from_user.id, limit=200)
        base_date = find_current_expire_from_orders(paid_orders, message.from_user.id, plan_name) or datetime.now()
    else:
        users_data = db.users_sheet.get_all_values()
        base_date = find_current_expire(users_data, message.from_user.id, plan_name) or datetime.now()
    expire_at = base_date + timedelta(days=duration_days)
    expire_text = expire_at.strftime(TIME_FMT)

    links_msg, group_names = await build_invite_links(message.from_user.id, plan_name)
    if not links_msg.strip():
        await message.answer("❌ Mã hợp lệ nhưng gói này chưa cấu hình nhóm nhận link. Vui lòng báo admin kiểm tra Plan_Name/ID_G.", parse_mode="HTML")
        return

    order_id = int(datetime.now().timestamp() * 1000)
    user_full_name = (message.from_user.full_name or "").strip()
    username = message.from_user.username or ""
    paid_at = now_text()

    if supabase_store.enabled:
        supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=message.from_user.id,
            full_name=user_full_name,
            plan_name=plan_name,
            amount=0,
            sale_id=code,
            original_amount=0,
        )
        supabase_store.mark_order_paid(order_id, paid_at=paid_at, expire_at=expire_text)
    else:
        db.users_sheet.append_row([
            order_id,
            str(message.from_user.id),
            user_full_name,
            plan_name,
            "0",
            "PAID",
            paid_at,
            expire_text,
            code,
            "COUPON",
        ])

    _, redemptions_sheet = ensure_coupon_sheets()
    redemptions_sheet.append_row([
        paid_at,
        code,
        str(message.from_user.id),
        username,
        user_full_name,
        plan_name,
        str(duration_days),
        expire_text,
        "REDEEMED",
        str(order_id),
        group_names,
    ])

    update_coupon_usage(coupons_sheet, headers, row_index, coupon, message.from_user.id)

    template = db.get_config(
        "MSG_COUPON_SUCCESS",
        "<b>✅ KÍCH HOẠT MÃ THÀNH CÔNG</b>\\n\\n"
        "Mã: <code>{code}</code>\\n"
        "Gói: <b>{plan}</b>\\n"
        "Hạn dùng đến: <b>{expire}</b>\\n\\n"
        "Link tham gia của bạn:\\n{links}",
    ).replace("\\n", "\n")
    text = (
        template
        .replace("{code}", escape_html(code))
        .replace("{plan}", escape_html(plan_name))
        .replace("{expire}", expire_text)
        .replace("{links}", links_msg)
    )
    kb = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=db.get_config("BTN_BACK", "Quay lại Menu"), callback_data="back_main")
    )
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML", disable_web_page_preview=True)


async def send_coupon_prompt(target, state: FSMContext):
    await state.set_state(CouponState.waiting_code)
    text = db.get_config(
        "MSG_COUPON_PROMPT",
        "<b>Nhập mã giảm giá / mã kích hoạt</b>\\n\\nGửi mã bạn nhận được vào đây. Ví dụ: <code>VIP2026</code>",
    ).replace("\\n", "\n")
    kb = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=db.get_config("BTN_BACK", "Quay lại Menu"), callback_data="back_main")
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
    if message.chat.type != "private":
        await message.answer("Vui lòng nhắn riêng với bot để nhập mã, tránh lộ mã trong group.")
        return
    await send_coupon_prompt(message, state)


@router.callback_query(F.data.in_({"coupon_enter", "coupon_code", "redeem_code"}))
async def coupon_button(callback: CallbackQuery, state: FSMContext):
    if not await check_protection(callback):
        return
    if callback.message.chat.type != "private":
        await callback.answer("Vui lòng nhắn riêng với bot để nhập mã.", show_alert=True)
        return
    await send_coupon_prompt(callback, state)


@router.message(CouponState.waiting_code)
async def coupon_code_received(message: Message, state: FSMContext):
    maintenance_status = str(db.get_config("MAINTENANCE_MODE", "OFF")).strip().upper()
    if maintenance_status in {"ON", "TRUE", "CÓ", "YES"} and message.from_user.id != ADMIN_ID:
        await message.answer(db.get_config("MSG_MAINTENANCE", "Hệ thống đang bảo trì, vui lòng quay lại sau.").replace("\\n", "\n"), parse_mode="HTML")
        return

    code = normalize_code(message.text)
    if not code or len(code) < 3:
        await message.answer("Mã không hợp lệ. Vui lòng nhập lại mã bạn nhận được.")
        return

    await state.clear()
    await redeem_coupon(message, code)


@router.message(Command("gen_coupon"))
async def cmd_gen_coupon(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = (message.text or "").split()
    if len(parts) < 4:
        await message.answer(
            "Cú pháp: /gen_coupon <số_lượng> <plan_key> <số_ngày> [max_uses] [prefix]\n"
            "Ví dụ: /gen_coupon 10 full_1m 30 1 VIP\n"
            "Plan key nhanh: full_1m, full_life, g1_1m, g1_life..."
        )
        return

    count = min(max(safe_int(parts[1], 1), 1), 200)
    plan_name = resolve_plan_name(parts[2])
    duration_days = max(safe_int(parts[3], 30), 1)
    max_uses = max(safe_int(parts[4], 1), 1) if len(parts) >= 5 else 1
    prefix = normalize_code(parts[5])[:8] if len(parts) >= 6 else "VIP"

    coupons_sheet, _ = ensure_coupon_sheets()
    alphabet = string.ascii_uppercase + string.digits
    created_at = now_text()
    rows = []
    codes = []
    existing = {item.get("Code") for _, item in get_coupon_rows()[2]}

    while len(rows) < count:
        code = f"{prefix}{''.join(secrets.choice(alphabet) for _ in range(8))}"
        if code in existing:
            continue
        existing.add(code)
        codes.append(code)
        rows.append([
            code,
            "ON",
            plan_name,
            str(duration_days),
            str(max_uses),
            "0",
            "",
            "",
            db.get_config("COUPON_CLEANUP_AFTER_DAYS", "7"),
            created_at,
            str(message.from_user.id),
            "",
            "",
            "Generated by /gen_coupon",
        ])

    coupons_sheet.append_rows(rows)
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
    await asyncio.sleep(30)
    while True:
        try:
            db.connect()
            cleanup_coupon_sheets()
        except Exception as err:
            log.error("Coupon cleanup failed: %s", err)
        await asyncio.sleep(12 * 60 * 60)


def cleanup_coupon_sheets():
    coupons_sheet, coupon_headers, coupon_rows = get_coupon_rows()
    redemptions_sheet, redemption_headers, redemption_rows = get_redemption_rows()

    coupon_map = {
        normalize_code(item.get("Code")): item
        for _, item in coupon_rows
    }
    now = datetime.now()
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
