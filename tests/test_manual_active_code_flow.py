from manual_order_helpers import should_skip_manual_active_code
from supabase_store import SupabaseStore


def test_manual_active_code_defaults_to_skip():
    assert should_skip_manual_active_code({}) is True
    assert should_skip_manual_active_code({"skip_active_code": None}) is True
    assert should_skip_manual_active_code({"skip_active_code": True}) is True
    assert should_skip_manual_active_code({"skip_active_code": False}) is False


def test_activation_code_row_normalizes_to_used_when_used_at_present():
    store = SupabaseStore.__new__(SupabaseStore)
    row = {
        "code": "ABC123",
        "activation_status": "PENDING",
        "used_at": "2026-07-05T12:00:00+07:00",
        "activated_at": "",
    }

    normalized = store._normalize_order_activation_code_row(row)

    assert normalized["activation_status"] == "USED"
