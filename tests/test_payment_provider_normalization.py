from supabase_store import _normalize_payment_provider


def test_infer_payos_from_payment_approval_url():
    order = {"payment_provider": "", "payment_approval_url": "https://payos.vn/payment-link/abc"}

    normalized = _normalize_payment_provider(order)

    assert normalized["payment_provider"] == "PAYOS"


def test_infer_paypal_from_metadata_when_provider_missing():
    order = {"payment_provider": None, "metadata": {"payment_provider": "paypal"}}

    normalized = _normalize_payment_provider(order)

    assert normalized["payment_provider"] == "PAYPAL"


def test_keep_manual_when_explicit():
    order = {"payment_provider": "manual", "metadata": {"payment_provider": "payos"}}

    normalized = _normalize_payment_provider(order)

    assert normalized["payment_provider"] == "MANUAL"


def test_infer_binance_pay_from_metadata_when_provider_missing():
    order = {"payment_provider": "", "metadata": {"payment_provider": "binance_pay"}}

    normalized = _normalize_payment_provider(order)

    assert normalized["payment_provider"] == "BINANCE_PAY"
