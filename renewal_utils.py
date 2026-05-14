from datetime import datetime

from database import db, normalize_key


def safe_int(value, default=0):
    try:
        clean = str(value or "").replace("Đ", "").replace("đ", "").strip()
        if not clean:
            return default
        if clean.endswith(".0") or clean.endswith(",0"):
            return int(float(clean.replace(",", ".")))
        if "." in clean and "," not in clean and len(clean.rsplit(".", 1)[-1]) == 3:
            clean = clean.replace(".", "")
        elif "," in clean and "." not in clean and len(clean.rsplit(",", 1)[-1]) == 3:
            clean = clean.replace(",", "")
        else:
            clean = clean.replace(",", ".")
        return int(float(clean))
    except (TypeError, ValueError):
        return default


def parse_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def format_currency(amount):
    try:
        return "{:,.0f}Đ".format(float(amount)).replace(",", ".")
    except (TypeError, ValueError):
        return f"{amount}Đ"


def format_duration(delta):
    total_seconds = max(0, int(delta.total_seconds()))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days} ngày {hours:02d}:{minutes:02d}"
    return f"{hours:02d}:{minutes:02d}"


def get_discount_percent():
    return safe_int(
        db.get_config("EARLY_RENEW_DISCOUNT_PERCENT", db.get_config("RENEWAL_DISCOUNT_PERCENT", "10")),
        10,
    )


def get_notice_days():
    return safe_int(db.get_config("EARLY_RENEW_DAYS", db.get_config("REMINDER_DAYS", "3")), 3)


def resolve_price_key(plan_name):
    plan = normalize_key(plan_name).upper()
    if "TRỌN ĐỜI" in plan or "LIFE" in plan:
        return None

    if "FULL" in plan or "SVIP" in plan:
        return "PRICE_SVIP_30D"

    for group in range(1, 21):
        btn_name = normalize_key(db.get_config(f"BTN_G{group}", f"Nhóm {group}")).upper()
        if btn_name and (btn_name in plan or f"G{group}" in plan):
            return f"PRICE_G{group}_1M"
    return None


def build_early_renew_offer(row, row_index=None, now=None):
    now = now or datetime.now()
    if len(row) < 8:
        return None

    user_id = normalize_key(row[1])
    plan_name = normalize_key(row[3])
    status = normalize_key(row[5]).upper()
    expire_at = parse_datetime(row[7])
    if status != "PAID" or not user_id or not plan_name or not expire_at:
        return None
    if expire_at <= now:
        return None

    days_remaining = (expire_at.date() - now.date()).days
    notice_days = get_notice_days()
    if days_remaining < 0 or days_remaining > notice_days:
        return None

    discount_percent = get_discount_percent()
    if discount_percent <= 0:
        return None

    price_key = resolve_price_key(plan_name)
    if not price_key:
        return None

    original_price = safe_int(db.get_config(price_key, row[4] if len(row) > 4 else "0"), 0)
    if original_price <= 0:
        original_price = safe_int(row[4] if len(row) > 4 else "0", 0)
    if original_price <= 0:
        return None

    renew_price = max(1, int(round(original_price * (100 - discount_percent) / 100)))
    return {
        "row_index": row_index,
        "user_id": user_id,
        "plan_name": plan_name,
        "price_key": price_key,
        "original_price": original_price,
        "renew_price": renew_price,
        "discount_percent": discount_percent,
        "expire_at": expire_at,
        "days_remaining": days_remaining,
        "countdown": format_duration(expire_at - now),
        "offer_id": f"EARLY_RENEW:{row_index or user_id}:{price_key}",
    }


def render_early_renew_template(template, offer):
    values = {
        "{plan}": offer["plan_name"],
        "{price_key}": offer["price_key"],
        "{old_price}": format_currency(offer["original_price"]),
        "{original_price}": format_currency(offer["original_price"]),
        "{renew_price}": format_currency(offer["renew_price"]),
        "{sale_price}": format_currency(offer["renew_price"]),
        "{discount_percent}": str(offer["discount_percent"]),
        "{days}": str(offer["days_remaining"]),
        "{date}": offer["expire_at"].strftime("%d/%m/%Y %H:%M:%S"),
        "{countdown}": offer["countdown"],
    }
    rendered = str(template or "")
    for key, value in values.items():
        rendered = rendered.replace(key, value)
    return rendered


def build_early_renew_block(offer):
    if not offer:
        return ""

    template = db.get_config(
        "MSG_EARLY_RENEW_OFFER",
        "\n\n🔥 <b>ƯU ĐÃI GIA HẠN SỚM</b>\n"
        "Gói hiện tại: <b>{plan}</b>\n"
        "Giá gốc: <s>{old_price}</s>\n"
        "Giá gia hạn sớm: <b>{renew_price}</b> (-{discount_percent}%)\n"
        "⏳ Ưu đãi hết hiệu lực khi gói VIP hết hạn: <code>{date}</code>\n"
        "Còn lại: <b>{countdown}</b>\n\n"
        "Gia hạn trước khi hết hạn để giữ quyền truy cập không gián đoạn.",
    ).replace("\\n", "\n")
    return render_early_renew_template(template, offer)
