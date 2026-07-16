from supabase_store import SupabaseStore


def test_order_to_sheet_row_keeps_scheduler_status_and_expiry_columns_stable():
    row = SupabaseStore().order_to_sheet_row({
        "order_id": "custom-1d",
        "telegram_user_id": "42",
        "full_name": "User",
        "plan_name": "All Access - Tùy chỉnh",
        "amount": 1000,
        "status": "PAID",
        "paid_at": "2026-07-16 09:00:00",
        "expire_at": "2026-07-17 09:00:00",
    })

    assert row[5] == "PAID"
    assert row[7] == "2026-07-17 09:00:00"
