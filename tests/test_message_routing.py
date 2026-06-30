import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import modules.mod_coupon as mod_coupon
import modules.mod_general as mod_general
import modules.mod_payment as mod_payment
import modules.mod_support_inbox as mod_support_inbox
from message_classifier_utils import classify_message_text


def test_routing_classifier_maps_start_coupon_hidden_and_support(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: {"code": code} if code == "HIDEVIP" else None)

    assert classify_message_text("/start act_ABC123")["kind"] == "activation"
    assert classify_message_text("HANGCU_DEMO", coupon_prefixes=["HANGCU_"])["kind"] == "coupon"
    assert classify_message_text("HIDEVIP")["kind"] == "hidden"
    assert classify_message_text("Xin chào admin")["kind"] == "support"


def test_support_inbox_skips_coupon_and_hidden_messages(monkeypatch):
    message = SimpleNamespace(
        text="HANGCU_DEMO",
        caption="",
        from_user=SimpleNamespace(id=123, is_bot=False),
        chat=SimpleNamespace(type="private"),
    )
    monkeypatch.setattr(mod_support_inbox, "supabase_store", SimpleNamespace(enabled=True))
    monkeypatch.setattr(mod_support_inbox, "has_open_support_ticket", lambda user_id: True)
    monkeypatch.setattr(mod_support_inbox, "classify_private_message", lambda msg: {"kind": "coupon", "reason": "coupon_prefix"})

    assert not mod_support_inbox._is_support_inbox_private_message(message)


def test_support_inbox_accepts_plain_text_when_ticket_open(monkeypatch):
    message = SimpleNamespace(
        text="Chào admin",
        caption="",
        from_user=SimpleNamespace(id=123, is_bot=False),
        chat=SimpleNamespace(type="private"),
    )
    monkeypatch.setattr(mod_support_inbox, "supabase_store", SimpleNamespace(enabled=True))
    monkeypatch.setattr(mod_support_inbox, "has_open_support_ticket", lambda user_id: True)
    monkeypatch.setattr(mod_support_inbox, "classify_private_message", lambda msg: {"kind": "support", "reason": "plain_text"})

    assert mod_support_inbox._is_support_inbox_private_message(message)


def test_coupon_auto_handler_ignores_plain_text(monkeypatch):
    calls = []

    async def fake_redeem(message, code):
        calls.append(code)

    message = SimpleNamespace(
        text="Xin chào admin",
        from_user=SimpleNamespace(id=456),
        chat=SimpleNamespace(type="private"),
        answer=AsyncMock(),
    )
    monkeypatch.setattr(mod_coupon, "redeem_coupon", fake_redeem)
    monkeypatch.setattr(mod_coupon, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_coupon, "config_enabled", lambda key, default="OFF": True)
    monkeypatch.setattr(mod_coupon, "classify_private_message", lambda msg, coupon_prefixes=None: {"kind": "support", "reason": "plain_text"})

    asyncio.run(mod_coupon.coupon_auto_code_received(message))

    assert calls == []


def test_coupon_auto_handler_routes_coupon_codes(monkeypatch):
    calls = []

    async def fake_redeem(message, code):
        calls.append(code)

    message = SimpleNamespace(
        text="HANGCU_DEMO",
        from_user=SimpleNamespace(id=456),
        chat=SimpleNamespace(type="private"),
        answer=AsyncMock(),
    )
    monkeypatch.setattr(mod_coupon, "redeem_coupon", fake_redeem)
    monkeypatch.setattr(mod_coupon, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_coupon, "config_enabled", lambda key, default="OFF": True)
    monkeypatch.setattr(mod_coupon, "classify_private_message", lambda msg, coupon_prefixes=None: {"kind": "coupon", "code": "HANGCU_DEMO", "reason": "coupon_prefix"})

    asyncio.run(mod_coupon.coupon_auto_code_received(message))

    assert calls == ["HANGCU_DEMO"]


def test_start_activation_payload_routes_to_activation_delivery(monkeypatch):
    message = SimpleNamespace(
        text="/start act_manual_123",
        from_user=SimpleNamespace(id=789, username="user789", full_name="User 789"),
        chat=SimpleNamespace(id=789),
        entities=[],
        answer=AsyncMock(),
    )
    calls = []

    async def fake_deliver(message_obj, code):
        calls.append(code)

    monkeypatch.setattr(mod_general, "cleanup_welcome", AsyncMock())
    monkeypatch.setattr(mod_general.db, "reload_config", lambda force=False: None)
    monkeypatch.setattr(mod_general, "record_start_event", AsyncMock())
    monkeypatch.setattr(mod_general, "send_sale_announcement", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "render_page", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_general, "bot_unavailable_reason", lambda now=None: "")
    monkeypatch.setattr(mod_general, "deliver_activation_order", fake_deliver)

    asyncio.run(mod_general.cmd_start(message))

    assert calls == ["manual_123"]


def test_start_manual_message_payload_routes_to_manual_message_delivery(monkeypatch):
    message = SimpleNamespace(
        text="/start actmsg_manual_456",
        from_user=SimpleNamespace(id=789, username="user789", full_name="User 789"),
        chat=SimpleNamespace(id=789),
        entities=[],
        answer=AsyncMock(),
    )
    calls = []

    async def fake_deliver(message_obj, code):
        calls.append(code)

    monkeypatch.setattr(mod_general, "cleanup_welcome", AsyncMock())
    monkeypatch.setattr(mod_general.db, "reload_config", lambda force=False: None)
    monkeypatch.setattr(mod_general, "record_start_event", AsyncMock())
    monkeypatch.setattr(mod_general, "send_sale_announcement", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "render_page", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_general, "bot_unavailable_reason", lambda now=None: "")
    monkeypatch.setattr(mod_general, "deliver_manual_order_message", fake_deliver)

    asyncio.run(mod_general.cmd_start(message))

    assert calls == ["manual_456"]


def test_hidden_offer_for_action_uses_shared_classifier(monkeypatch):
    monkeypatch.setattr(mod_payment, "classify_message_text", lambda text, coupon_prefixes=None: {"kind": "hidden", "code": "HIDEVIP", "reason": "hidden_match"})
    monkeypatch.setattr(mod_payment, "validate_hidden_code_for_user", lambda code, user_id: ({"code": code, "is_active": True}, ""))
    monkeypatch.setattr(mod_payment, "get_hidden_group", lambda group_id: {"id": group_id, "name": "Prime", "is_active": True})
    monkeypatch.setattr(mod_payment, "hidden_code_available_groups", lambda hidden_code: [{"id": "prime", "name": "Prime"}])
    monkeypatch.setattr(mod_payment, "hidden_duration_price", lambda group, duration_key, currency: 99000)
    monkeypatch.setattr(mod_payment, "hidden_duration_days", lambda group, duration_key: 30)
    monkeypatch.setattr(mod_payment, "build_hidden_plan_name", lambda group, duration_key: "Hidden - Prime - 30 Ngày")
    monkeypatch.setattr(mod_payment, "display_plan_name", lambda plan_name, user_id: plan_name)
    monkeypatch.setattr(mod_payment, "extract_plan_token", lambda plan_name: "TOKEN")
    monkeypatch.setattr(mod_payment, "default_currency_for_user", lambda user_id: "VND")

    result = mod_payment.hidden_offer_for_action("hgbuy|HIDEVIP|prime|1M", user_id=123, provider="PAYOS")

    assert result["plan_name"] == "Hidden - Prime - 30 Ngày"
    assert result["amount"] == 99000
    assert result["metadata"]["hidden_code"] == "HIDEVIP"
