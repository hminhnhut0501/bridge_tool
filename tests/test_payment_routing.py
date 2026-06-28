import hashlib
import hmac
from datetime import datetime
from unittest.mock import patch

from payment import payment_manager
from modules.mod_payment import has_prior_paid_vip_order, should_allow_auto_payment, auto_payment_gate_message
from modules.mod_auto_payment_schedule import auto_payment_schedule_active, apply_auto_payment_schedule


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


def test_vietnamese_can_offer_binance_pay_provider():
    with patch("payment.db.get_config", return_value="PAYOS,BINANCE_PAY"), patch.object(
        payment_manager, "provider_enabled", return_value=True
    ):
        assert payment_manager.providers_for_language("vi") == ["PAYOS", "BINANCE_PAY"]


def test_binance_pay_enabled_uses_config_token():
    config = {
        "BINANCE_PAY_SIEUTHICODE_ENABLED": "ON",
        "BINANCE_PAY_SIEUTHICODE_TOKEN": "token-from-config",
    }

    with patch("payment.db.get_config", side_effect=lambda key, default="": config.get(key, default)):
        assert payment_manager.binance_pay.enabled is True


def test_english_provider_list_does_not_fallback_to_vnd_gateway():
    with patch("payment.db.get_config", return_value="PAYPAL"), patch.object(
        payment_manager, "provider_enabled", side_effect=lambda provider: provider == "PAYOS"
    ):
        assert payment_manager.providers_for_language("en") == []


def test_english_provider_list_auto_adds_enabled_tron_usdt_for_old_config():
    with patch("payment.db.get_config", return_value="PAYPAL"), patch.object(
        payment_manager,
        "provider_enabled",
        side_effect=lambda provider: provider in {"PAYPAL", "TRON_USDT"},
    ):
        assert payment_manager.providers_for_language("en") == ["PAYPAL", "TRON_USDT"]


def test_english_default_provider_list_includes_tron_usdt():
    def config(key, default=""):
        return default

    with patch("payment.db.get_config", side_effect=config), patch.object(
        payment_manager,
        "provider_enabled",
        side_effect=lambda provider: provider in {"PAYPAL", "TRON_USDT"},
    ):
        assert payment_manager.providers_for_language("en") == ["PAYPAL", "TRON_USDT"]


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


def test_payment_manager_routes_binance_pay_status_by_order_provider():
    class Store:
        enabled = True

        @staticmethod
        def get_order(order_ref):
            return {
                "order_id": order_ref,
                "payment_provider": "BINANCE_PAY",
                "payment_provider_order_id": order_ref,
            }

    with patch("payment.supabase_store", Store), patch.object(
        payment_manager.binance_pay,
        "get_payment_status",
        return_value="PAID",
    ) as check:
        assert payment_manager.get_payment_status("123") == "PAID"
        check.assert_called_once_with("123")


def test_binance_pay_polling_scans_pending_orders():
    class Store:
        enabled = True

        @staticmethod
        def list_pending_orders(limit=1000):
            return [
                {"order_id": "1", "payment_provider": "BINANCE_PAY"},
                {"order_id": "2", "payment_provider": "PAYOS"},
            ]

        @staticmethod
        def get_order(order_ref):
            return {"order_id": order_ref, "status": "PENDING"}

    with patch("payment.supabase_store", Store), patch.object(
        payment_manager.binance_pay,
        "get_payment_status",
        side_effect=lambda order_ref: "PAID" if order_ref == "1" else "PENDING",
    ):
        assert payment_manager.scan_pending_orders("BINANCE_PAY") == ["1"]


def test_new_customer_is_blocked_from_auto_payment_by_default():
    class Store:
        enabled = True

        @staticmethod
        def list_paid_orders_for_user(user_id, limit=500):
            return []

    with patch("modules.mod_payment.supabase_store", Store), patch(
        "modules.mod_payment.db.get_config",
        side_effect=lambda key, default="": {
            "AUTO_PAYMENT_NEW_ENABLED": "OFF",
        }.get(key, default),
    ):
        assert has_prior_paid_vip_order("42") is False
        assert should_allow_auto_payment("42") is False
        assert "thanh toán tự động" in auto_payment_gate_message("42").lower()


def test_returning_customer_can_use_auto_payment_when_enabled():
    class Store:
        enabled = True

        @staticmethod
        def list_paid_orders_for_user(user_id, limit=500):
            return [{"order_id": "1", "plan_name": "VIP 30 Ngày"}]

    config = {
        "AUTO_PAYMENT_RETURNING_ENABLED": "ON",
        "AUTO_PAYMENT_RETURNING_SCHEDULE_ENABLED": "ON",
        "AUTO_PAYMENT_RETURNING_WINDOWS": "22:00-06:00",
    }

    with patch("modules.mod_payment.supabase_store", Store), patch(
        "modules.mod_payment.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ), patch(
        "modules.mod_auto_payment_schedule.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ), patch(
        "modules.mod_auto_payment_schedule.auto_payment_schedule_active_for_tier",
        return_value=True,
    ):
        assert has_prior_paid_vip_order("42") is True
        assert should_allow_auto_payment("42") is True


def test_english_customer_uses_separate_auto_payment_flow():
    class Store:
        enabled = True

        @staticmethod
        def list_paid_orders_for_user(user_id, limit=500):
            return [{"order_id": "1", "plan_name": "VIP 30 Ngày"}]

    config = {
        "AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON",
        "AUTO_PAYMENT_EN_RETURNING_SCHEDULE_ENABLED": "ON",
        "AUTO_PAYMENT_EN_RETURNING_WINDOWS": "22:00-06:00",
    }

    with patch("modules.mod_payment.supabase_store", Store), patch(
        "modules.mod_payment.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ), patch(
        "modules.mod_auto_payment_schedule.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ), patch(
        "modules.mod_auto_payment_schedule.customer_segment_key",
        return_value="en",
    ), patch(
        "modules.mod_auto_payment_schedule.auto_payment_schedule_active_for_tier",
        return_value=True,
    ):
        assert has_prior_paid_vip_order("42") is True
        assert should_allow_auto_payment("42") is True


def test_auto_payment_gate_can_use_explicit_language_override():
    class Store:
        enabled = True

        @staticmethod
        def list_paid_orders_for_user(user_id, limit=500):
            return [{"order_id": "1", "plan_name": "VIP 30 Ngày"}]

    config = {
        "AUTO_PAYMENT_VI_RETURNING_ENABLED": "OFF",
        "AUTO_PAYMENT_EN_RETURNING_ENABLED": "ON",
        "AUTO_PAYMENT_EN_RETURNING_SCHEDULE_ENABLED": "ON",
        "AUTO_PAYMENT_EN_RETURNING_WINDOWS": "00:00-23:59",
    }

    with patch("modules.mod_payment.supabase_store", Store), patch(
        "modules.mod_payment.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ), patch(
        "modules.mod_auto_payment_schedule.db.get_config",
        side_effect=lambda key, default="": config.get(key, default),
    ):
        assert should_allow_auto_payment("42", preferred_language="en") is True


def test_create_payment_for_user_blocks_new_customer_when_auto_payment_is_off():
    with patch("modules.mod_payment.should_allow_auto_payment", return_value=False), patch(
        "modules.mod_payment.auto_payment_gate_message",
        return_value="blocked",
    ), patch("modules.mod_payment.payment_manager.create_payment_link") as create_link:
        from modules.mod_payment import create_payment_for_user

        assert create_payment_for_user("42", 100, 99000, "PRIVE100") is None
        create_link.assert_not_called()


def test_create_payment_for_user_allows_returning_customer():
    with patch("modules.mod_payment.should_allow_auto_payment", return_value=True), patch(
        "modules.mod_payment.get_user_language",
        return_value="vi",
    ), patch("modules.mod_payment.payment_manager.preferred_provider", return_value="PAYOS"), patch(
        "modules.mod_payment.payment_manager.create_payment_link",
        return_value={"provider": "PAYOS"},
    ) as create_link:
        from modules.mod_payment import create_payment_for_user

        result = create_payment_for_user("42", 100, 99000, "PRIVE100")
        assert result == {"provider": "PAYOS"}
        create_link.assert_called_once_with(100, 99000, "PRIVE100", provider="PAYOS")


def test_enforce_auto_payment_gate_sends_redirect_message():
    class Message:
        def __init__(self):
            self.sent = []

        async def answer(self, text, reply_markup=None):
            self.sent.append((text, reply_markup))

    class Callback:
        def __init__(self):
            self.from_user = type("U", (), {"id": 42})()
            self.message = Message()
            self.alerts = []

        async def answer(self, text, show_alert=False):
            self.alerts.append((text, show_alert))

    with patch("modules.mod_payment.should_allow_auto_payment", return_value=False), patch(
        "modules.mod_payment.manual_support_keyboard", return_value="keyboard"
    ), patch(
        "modules.mod_payment.db.get_config",
        return_value="redirect text",
    ):
        from modules.mod_payment import enforce_auto_payment_gate

        cb = Callback()
        import asyncio

        ok = asyncio.run(enforce_auto_payment_gate(cb))
        assert ok is False
        assert cb.alerts == []
        assert cb.message.sent == [("redirect text", "keyboard")]


def test_manual_support_bot_url_uses_deep_link_payload():
    with patch("modules.mod_payment.db.get_config", return_value="https://t.me/cuhotro_bot?start={payload}"):
        from modules.mod_payment import manual_support_bot_url

        assert manual_support_bot_url(42) == "https://t.me/cuhotro_bot?start=act_apg_aVND_lvi"


def test_auto_payment_schedule_is_active_during_night_window():
    class Db:
        @staticmethod
        def get_config(key, default=""):
            return {
                "AUTO_PAYMENT_NEW_ENABLED": "ON",
                "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
                "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
            }.get(key, default)

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import auto_payment_schedule_active_for_tier

        assert auto_payment_schedule_active_for_tier("new", datetime(2026, 6, 22, 23, 30, 0)) is True
        assert auto_payment_schedule_active_for_tier("new", datetime(2026, 6, 22, 7, 0, 0)) is False


def test_auto_payment_schedule_uses_new_and_returning_tiers_separately():
    class Db:
        values = {
            "AUTO_PAYMENT_NEW_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
            "AUTO_PAYMENT_RETURNING_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_WINDOWS": "06:00-12:00",
        }

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

        @staticmethod
        def set_config(key, value):
            Db.values[key] = value

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import apply_auto_payment_schedule

        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 30, 0))
        assert result["new_active"] is True
        assert result["returning_active"] is False


def test_auto_payment_schedule_leaves_returning_customer_flag_alone_when_window_turns_off():
    class Db:
        values = {
            "AUTO_PAYMENT_NEW_ENABLED": "OFF",
            "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
            "AUTO_PAYMENT_RETURNING_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_WINDOWS": "22:00-06:00",
        }

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

        @staticmethod
        def set_config(key, value):
            Db.values[key] = value

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import apply_auto_payment_schedule

        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 0, 0))
        assert result["new_active"] is False
        assert result["returning_active"] is True


def test_auto_payment_schedule_worker_should_not_force_state_at_boot():
    class Db:
        values = {
            "AUTO_PAYMENT_NEW_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
        }

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

        @staticmethod
        def set_config(key, value):
            Db.values[key] = value

    class Store:
        enabled = False

    with patch("modules.mod_auto_payment_schedule.db", Db), patch("modules.mod_auto_payment_schedule.supabase_store", Store):
        from modules.mod_auto_payment_schedule import apply_auto_payment_schedule

        before = dict(Db.values)
        assert Db.values == before
        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 30, 0))
        assert result["new_active"] is True


def test_auto_payment_schedule_lock_prevents_worker_from_reenabling_new_customer_flag():
    class Db:
        values = {
            "AUTO_PAYMENT_NEW_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
        }

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

        @staticmethod
        def set_config(key, value):
            Db.values[key] = value

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import apply_auto_payment_schedule, auto_payment_schedule_active

        assert auto_payment_schedule_active(datetime(2026, 6, 22, 23, 30, 0)) is True
        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 30, 0))
        assert result["new_active"] is True


def test_auto_payment_schedule_does_not_spam_audit_when_state_is_unchanged():
    class Db:
        values = {
            "AUTO_PAYMENT_NEW_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_NEW_WINDOWS": "22:00-06:00",
            "AUTO_PAYMENT_RETURNING_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_SCHEDULE_ENABLED": "ON",
            "AUTO_PAYMENT_RETURNING_WINDOWS": "22:00-06:00",
        }

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

        @staticmethod
        def set_config(key, value):
            Db.values[key] = value

    class Store:
        enabled = True
        events = []

        @staticmethod
        def record_support_event(*args, **kwargs):
            Store.events.append((args, kwargs))

    with patch("modules.mod_auto_payment_schedule.db", Db), patch("modules.mod_auto_payment_schedule.supabase_store", Store):
        from modules.mod_auto_payment_schedule import apply_auto_payment_schedule
        import modules.mod_auto_payment_schedule as schedule_module

        schedule_module._LAST_SCHEDULE_STATE = {"vi": {"new": None, "returning": None}, "en": {"new": None, "returning": None}}

        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 30, 0))
        assert result["new_active"] is True
        assert result["state_changed"] is True
        assert len(Store.events) == 1

        Store.events.clear()
        result = apply_auto_payment_schedule(datetime(2026, 6, 22, 23, 40, 0))
        assert result["state_changed"] is False
        assert len(Store.events) == 0


def test_auto_payment_schedule_poll_interval_uses_configured_floor():
    class Db:
        values = {"AUTO_PAYMENT_SCHEDULE_POLL_SECONDS": "45"}

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import poll_interval_seconds

        assert poll_interval_seconds() == 45


def test_auto_payment_schedule_poll_interval_has_minimum():
    class Db:
        values = {"AUTO_PAYMENT_SCHEDULE_POLL_SECONDS": "10"}

        @staticmethod
        def get_config(key, default=""):
            return Db.values.get(key, default)

    with patch("modules.mod_auto_payment_schedule.db", Db):
        from modules.mod_auto_payment_schedule import poll_interval_seconds

        assert poll_interval_seconds() == 30
