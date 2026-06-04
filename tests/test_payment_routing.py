from unittest.mock import patch

from payment import payment_manager


def test_vietnamese_prefers_payos_when_both_are_enabled():
    with patch.object(payment_manager, "provider_enabled", return_value=True):
        assert payment_manager.preferred_provider("vi") == "PAYOS"


def test_english_prefers_paypal_when_both_are_enabled():
    with patch.object(payment_manager, "provider_enabled", return_value=True):
        assert payment_manager.preferred_provider("en") == "PAYPAL"


def test_disabled_preferred_provider_falls_back():
    def enabled(provider):
        return provider == "PAYOS"

    with patch.object(payment_manager, "provider_enabled", side_effect=enabled):
        assert payment_manager.preferred_provider("en") == "PAYOS"


def test_paypal_converts_vnd_to_usd():
    with patch("payment.db.get_config", return_value="25000"):
        assert payment_manager.paypal._usd_value(100000) == "4.00"


def test_paypal_approved_order_is_captured_as_paid():
    lookup = type("Response", (), {"json": lambda self: {"status": "APPROVED"}})()
    capture = type("Response", (), {"json": lambda self: {"status": "COMPLETED"}})()
    with patch.object(payment_manager.paypal, "_headers", return_value={}), patch(
        "payment.requests.get", return_value=lookup
    ), patch("payment.requests.post", return_value=capture):
        assert payment_manager.paypal.get_payment_status("PAYPAL-1") == "PAID"
