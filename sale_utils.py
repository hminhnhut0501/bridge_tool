from datetime import datetime

from database import db, normalize_key

SALE_STATUS_ACTIVE = {"ON", "TRUE", "YES", "1", "ACTIVE", "BẬT", "CO", "CÓ"}
SALE_STATUS_INACTIVE = {"OFF", "FALSE", "NO", "0", "INACTIVE", "TẮT", "TAT", "KHÔNG", "KHONG"}


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


def safe_float(value, default=0.0):
    try:
        clean = str(value or "").replace("%", "").replace(",", ".").strip()
        if not clean:
            return default
        return float(clean)
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


def strike_text(text):
    return "".join(f"{char}\u0336" if char.strip() else char for char in str(text))


def format_duration(delta):
    total_seconds = max(0, int(delta.total_seconds()))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days} ngày {hours:02d}:{minutes:02d}"
    return f"{hours:02d}:{minutes:02d}"


def sale_value(row, *keys):
    for key in keys:
        normalized = normalize_key(key).lower().replace(" ", "_")
        if normalized in row:
            return row.get(normalized, "")
    return ""


def is_enabled(row):
    status = normalize_key(sale_value(row, "enabled", "status", "trang_thai", "trạng_thái", "bật")).upper()
    if not status:
        return True
    if status in SALE_STATUS_INACTIVE:
        return False
    return status in SALE_STATUS_ACTIVE


def sale_code(row):
    return normalize_key(sale_value(row, "sale_id", "sale_code", "code", "ma_sale", "mã_sale"))


def sale_price_key(row):
    return normalize_key(sale_value(row, "price_key", "key", "config_key", "ma_gia", "mã_giá")).upper()


def count_used_slots(sale_id):
    if not sale_id or not db.users_sheet:
        return 0

    try:
        rows = db.users_sheet.get_all_values()
    except Exception:
        return 0

    used = 0
    for row in rows[1:]:
        status = normalize_key(row[5] if len(row) > 5 else "").upper()
        row_sale_id = normalize_key(row[8] if len(row) > 8 else "")
        if row_sale_id == sale_id and status in {"PENDING", "PAID"}:
            used += 1
    return used


def get_active_sale(price_key, original_price):
    price_key = normalize_key(price_key).upper()
    original_price = safe_int(original_price)
    if original_price <= 0:
        return None

    now = datetime.now()
    for row in db.sales_cache:
        if not is_enabled(row) or sale_price_key(row) != price_key:
            continue

        start_at = parse_datetime(sale_value(row, "start_at", "start", "bat_dau", "bắt_đầu"))
        end_at = parse_datetime(sale_value(row, "end_at", "end", "ket_thuc", "kết_thúc"))
        if start_at and now < start_at:
            continue
        if end_at and now > end_at:
            continue

        slot_limit = safe_int(sale_value(row, "slot_limit", "slots", "slot_sale", "so_slot", "số_slot"), 0)
        code = sale_code(row) or f"{price_key}:{end_at.isoformat() if end_at else 'NO_END'}"
        used_slots = count_used_slots(code) if slot_limit > 0 else 0
        remaining_slots = max(0, slot_limit - used_slots) if slot_limit > 0 else None
        if slot_limit > 0 and remaining_slots <= 0:
            continue

        explicit_price = safe_int(sale_value(row, "sale_price", "price_sale", "gia_sale", "giá_sale"), 0)
        discount_percent = safe_float(sale_value(row, "discount_percent", "discount", "percent", "phan_tram", "phần_trăm", "%"), 0)
        if explicit_price > 0:
            sale_price = explicit_price
            if discount_percent <= 0:
                discount_percent = round((1 - sale_price / original_price) * 100)
        elif discount_percent > 0:
            sale_price = int(round(original_price * (100 - discount_percent) / 100))
        else:
            continue

        if sale_price <= 0 or sale_price >= original_price:
            continue

        return {
            "sale_id": code,
            "price_key": price_key,
            "original_price": original_price,
            "sale_price": sale_price,
            "discount_percent": int(round(discount_percent)),
            "start_at": start_at,
            "end_at": end_at,
            "slot_limit": slot_limit,
            "used_slots": used_slots,
            "remaining_slots": remaining_slots,
            "countdown": format_duration(end_at - now) if end_at else "",
        }
    return None


def get_price(price_key, default=0):
    original_price = safe_int(db.get_config(price_key, default), default)
    sale = get_active_sale(price_key, original_price)
    if sale:
        return sale["sale_price"], sale
    return original_price, None


def format_price_label(price_key, default=0):
    original_price = safe_int(db.get_config(price_key, default), default)
    sale = get_active_sale(price_key, original_price)
    if not sale:
        return format_currency(original_price)

    old_price = strike_text(format_currency(original_price))
    label = f"{old_price} → {format_currency(sale['sale_price'])}"
    if sale["discount_percent"] > 0:
        label += f" (-{sale['discount_percent']}%)"
    return label


def sale_banner(price_key, default=0):
    original_price = safe_int(db.get_config(price_key, default), default)
    sale = get_active_sale(price_key, original_price)
    if not sale:
        return ""

    parts = [f"🔥 SALE -{sale['discount_percent']}%", f"còn {sale['countdown']}"]
    if sale["remaining_slots"] is not None:
        parts.append(f"còn {sale['remaining_slots']}/{sale['slot_limit']} slot")
    return " • ".join(parts)
