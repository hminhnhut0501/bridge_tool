import hashlib
import hmac
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


def test_paypal_uses_configured_usd_price_without_conversion():
    assert payment_manager.paypal._usd_value(4.99) == "4.99"


def test_vietnamese_can_offer_both_payment_providers():
    with patch("payment.db.get_config", return_value="PAYOS,PAYPAL"), patch.object(
        payment_manager, "provider_enabled", return_value=True
    ):
        assert payment_manager.providers_for_language("vi") == ["PAYOS", "PAYPAL"]


def test_vietnamese_can_offer_crypto_provider():
    with patch("payment.db.get_config", return_value="PAYOS,NOWPAYMENTS"), patch.object(
        payment_manager, "provider_enabled", return_value=True
    ):
        assert payment_manager.providers_for_language("vi") == ["PAYOS", "NOWPAYMENTS"]


def test_vietnamese_can_offer_tron_usdt_provider():
    with patch("payment.db.get_config", return_value="PAYOS,TRON_USDT"), patch.object(
        payment_manager, "provider_enabled", return_value=True
    ):
        assert payment_manager.providers_for_language("vi") == ["PAYOS", "TRON_USDT"]


def test_english_provider_list_does_not_fallback_to_vnd_gateway():
    with patch("payment.db.get_config", return_value="PAYPAL"), patch.object(
        payment_manager, "provider_enabled", side_effect=lambda provider: provider == "PAYOS"
    ):
        assert payment_manager.providers_for_language("en") == []


def test_paypal_approved_order_is_captured_as_paid():
    lookup = type("Response", (), {"json": lambda self: {"status": "APPROVED"}})()
    capture = type("Response", (), {"json": lambda self: {"status": "COMPLETED"}})()
    with patch.object(payment_manager.paypal, "_headers", return_value={}), patch(
        "payment.requests.get", return_value=lookup
    ), patch("payment.requests.post", return_value=capture):
        assert payment_manager.paypal.get_payment_status("PAYPAL-1") == "PAID"


def test_nowpayments_finished_status_is_paid():
    assert payment_manager.nowpayments.normalize_status("finished") == "PAID"
    assert payment_manager.nowpayments.normalize_status("confirmed") == "PENDING"
    assert payment_manager.nowpayments.normalize_status("partially_paid") == "PENDING"
    assert payment_manager.nowpayments.normalize_status("expired") == "ERROR"


def test_nowpayments_invoice_returns_checkout_url():
    response = type(
        "Response",
        (),
        {
            "ok": True,
            "json": lambda self: {"id": "INV-1", "invoice_url": "https://nowpayments.io/invoice/INV-1"},
        },
    )()
    with patch.object(type(payment_manager.nowpayments), "enabled", property(lambda self: True)), patch(
        "payment.db.get_config",
        side_effect=lambda key, default="": {"NOWPAYMENTS_PRICE_CURRENCY": "USD"}.get(key, default),
    ), patch("payment.requests.post", return_value=response):
        data = payment_manager.nowpayments.create_payment_link("123", 9.99, "PRIVE123")
        assert data["provider"] == "NOWPAYMENTS"
        assert data["provider_order_id"] == "INV-1"
        assert data["approval_url"] == "https://nowpayments.io/invoice/INV-1"
        assert data["currency_code"] == "USD"


def test_nowpayments_ipn_signature_accepts_valid_raw_payload():
    payload = b'{"order_id":"123","payment_status":"finished"}'
    signature = hmac.new(b"secret", payload, hashlib.sha512).hexdigest()
    assert payment_manager.nowpayments.verify_ipn_signature(payload, signature, "secret")
    assert not payment_manager.nowpayments.verify_ipn_signature(payload, signature, "wrong-secret")


def test_payment_manager_routes_nowpayments_status_by_order_provider():
    class Store:
        enabled = True

        @staticmethod
        def get_order(order_ref):
            return {
                "order_id": order_ref,
                "payment_provider": "NOWPAYMENTS",
                "payment_provider_order_id": "INV-1",
            }

    with patch("payment.supabase_store", Store), patch.object(
        payment_manager.nowpayments,
        "get_payment_status",
        return_value="PAID",
    ) as check:
        assert payment_manager.get_payment_status("123") == "PAID"
        check.assert_called_once_with("INV-1")


def test_tron_usdt_unique_amount_uses_six_decimals():
    with patch("payment.db.get_config", side_effect=lambda key, default="": {
        "TRON_USDT_UNIQUE_AMOUNT_ENABLED": "ON",
    }.get(key, default)):
        assert str(payment_manager.tron_usdt.usdt_amount("1779547112", 9.99)) == "9.990441"


def test_payment_manager_routes_tron_usdt_status_by_order_provider():
    class Store:
        enabled = True

        @staticmethod
        def get_order(order_ref):
            return {
                "order_id": order_ref,
                "payment_provider": "TRON_USDT",
                "payment_provider_order_id": order_ref,
            }

    with patch("payment.supabase_store", Store), patch.object(
        payment_manager.tron_usdt,
        "get_payment_status",
        return_value="PAID",
    ) as check:
        assert payment_manager.get_payment_status("123") == "PAID"
        check.assert_called_once_with("123")
