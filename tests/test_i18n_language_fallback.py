from unittest.mock import patch

import i18n


def test_paid_usd_order_overrides_stale_vi_preference(monkeypatch):
    monkeypatch.setattr(i18n, "_language_cache", {})
    fake_store = type(
        "FakeStore",
        (),
        {
            "enabled": True,
            "get_user_preference": staticmethod(lambda user_id: {"language": "vi"}),
            "list_paid_orders_for_user": staticmethod(
                lambda user_id, limit=20: [
                    {
                        "payment_currency": "USD",
                        "payment_provider": "PAYPAL",
                        "metadata": {},
                    }
                ]
            ),
        },
    )()
    monkeypatch.setattr(i18n, "supabase_store", fake_store)

    assert i18n.get_user_language("7487060105") == "en"
