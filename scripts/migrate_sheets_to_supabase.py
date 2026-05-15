import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import db, normalize_key  # noqa: E402
from supabase_store import supabase_store  # noqa: E402


def row_value(row, index, default=""):
    return str(row[index]).strip() if len(row) > index else default


def as_int(value, default=0):
    try:
        raw = str(value or "").strip().replace(".", "").replace(",", "")
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def migrate_config():
    count = 0
    rows = db.config_sheet.get_all_values() if db.config_sheet else []
    for row in rows:
        key = normalize_key(row_value(row, 0)).upper()
        if not key:
            continue
        supabase_store.set_config(key, row_value(row, 1))
        count += 1
    print(f"migrated bot_config: {count}")


def migrate_menu_pages():
    count = 0
    rows = db.menu_sheet.get_all_values() if db.menu_sheet else []
    for row in rows[1:]:
        page_id = normalize_key(row_value(row, 0))
        if not page_id:
            continue
        supabase_store.upsert_menu_page(
            page_id=page_id,
            image_url=row_value(row, 1),
            body=row_value(row, 2),
            layout=row_value(row, 3),
        )
        count += 1
    print(f"migrated menu_pages: {count}")


def migrate_orders():
    count = 0
    rows = db.users_sheet.get_all_values() if db.users_sheet else []
    for row in rows[1:]:
        order_id = row_value(row, 0)
        user_id = row_value(row, 1)
        if not order_id or not user_id:
            continue

        supabase_store.create_order(
            order_id=order_id,
            telegram_user_id=user_id,
            full_name=row_value(row, 2),
            plan_name=row_value(row, 3),
            amount=as_int(row_value(row, 4)),
            sale_id=row_value(row, 8),
            original_amount=as_int(row_value(row, 9), as_int(row_value(row, 4))),
        )
        status = row_value(row, 5, "PENDING").upper()
        supabase_store.update_order_status(
            order_id=order_id,
            status=status,
            paid_at=row_value(row, 6) or None,
            expire_at=row_value(row, 7) or None,
        )
        count += 1
    print(f"migrated orders: {count}")


def migrate_coupons():
    try:
        sheet = db.sh.worksheet("Coupons")
    except Exception:
        print("skip coupons: sheet not found")
        return

    rows = sheet.get_all_values()
    if len(rows) < 2:
        print("skip coupons: empty sheet")
        return

    headers = [normalize_key(h).lower().replace(" ", "_") for h in rows[0]]
    count = 0
    for row in rows[1:]:
        raw = {
            header: row_value(row, idx)
            for idx, header in enumerate(headers)
            if header
        }
        code = raw.get("code") or raw.get("coupon") or raw.get("ma") or raw.get("mã")
        if not code:
            continue
        payload = {
            "code": str(code).strip().upper(),
            "plan_name": raw.get("plan_name") or raw.get("plan") or raw.get("goi"),
            "amount": as_int(raw.get("amount") or raw.get("price") or raw.get("gia")),
            "status": (raw.get("status") or "ACTIVE").upper(),
            "raw_data": raw,
        }
        supabase_store.upsert_coupon(payload)
        count += 1
    print(f"migrated coupons: {count}")


def main():
    if not supabase_store.enabled:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    db.connect()
    supabase_store.connect()
    migrate_config()
    migrate_menu_pages()
    migrate_orders()
    migrate_coupons()
    print("done")


if __name__ == "__main__":
    main()
