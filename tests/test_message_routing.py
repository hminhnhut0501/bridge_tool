import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats

import bot_instance
import database
import modules.mod_admin_order as mod_admin_order
import modules.mod_coupon as mod_coupon
import modules.mod_general as mod_general
import modules.mod_payment as mod_payment
import modules.mod_support_inbox as mod_support_inbox
from message_classifier_utils import classify_message_text


def test_routing_classifier_maps_start_coupon_hidden_and_support(monkeypatch):
    assert classify_message_text("/start act_ABC123")["kind"] == "activation"
    assert classify_message_text("HANGCU_DEMO", coupon_prefixes=["HANGCU_"])["kind"] == "support"
    assert classify_message_text("HIDEVIP")["kind"] == "support"
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
    monkeypatch.setattr(mod_support_inbox, "support_inbox_enabled", lambda: True)

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
    monkeypatch.setattr(mod_support_inbox, "support_inbox_enabled", lambda: True)

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
    monkeypatch.setattr(mod_coupon, "coupon_auto_prefixes", lambda: ["HANGCU_"])

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
    monkeypatch.setattr(mod_coupon, "classify_private_message", lambda msg, coupon_prefixes=None: {"kind": "support", "code": "HANGCU_DEMO", "reason": "plain_text"})
    monkeypatch.setattr(mod_coupon, "coupon_auto_prefixes", lambda: ["HANGCU_"])

    asyncio.run(mod_coupon.coupon_auto_code_received(message))

    assert calls == []


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


def test_start_language_payload_can_force_english(monkeypatch):
    message = SimpleNamespace(
        text="/start en",
        from_user=SimpleNamespace(id=789, username="user789", full_name="User 789"),
        chat=SimpleNamespace(id=789),
        entities=[],
        answer=AsyncMock(),
    )
    set_calls = []

    async def fake_deliver(message_obj, code):
        raise AssertionError("activation delivery should not run for language payload")

    monkeypatch.setattr(mod_general, "cleanup_welcome", AsyncMock())
    monkeypatch.setattr(mod_general.db, "reload_config", lambda force=False: None)
    monkeypatch.setattr(mod_general, "record_start_event", AsyncMock())
    monkeypatch.setattr(mod_general, "send_sale_announcement", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "render_page", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_general, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_general, "bot_unavailable_reason", lambda now=None: "")
    monkeypatch.setattr(mod_general, "deliver_activation_order", fake_deliver)
    monkeypatch.setattr(mod_general, "set_user_language", lambda user_id, language: set_calls.append((user_id, language)) or language)

    asyncio.run(mod_general.cmd_start(message))

    assert set_calls == [(789, "en")]


def test_start_falls_back_when_protection_blocks(monkeypatch):
    message = SimpleNamespace(
        text="/start",
        from_user=SimpleNamespace(id=789, username="user789", full_name="User 789"),
        chat=SimpleNamespace(id=789, type="private"),
        entities=[SimpleNamespace(type="bot_command")],
        answer=AsyncMock(),
    )

    monkeypatch.setattr(mod_general, "cleanup_welcome", AsyncMock())
    monkeypatch.setattr(mod_general.db, "reload_config", lambda force=False: None)
    monkeypatch.setattr(mod_general, "record_start_event", AsyncMock())
    monkeypatch.setattr(mod_general, "send_sale_announcement", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "render_page", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "check_protection", AsyncMock(return_value=False))
    monkeypatch.setattr(mod_general, "bot_unavailable_reason", lambda now=None: "")
    monkeypatch.setattr(mod_general, "bot_runtime_state", lambda now=None: {"active": True, "source": "always"})

    asyncio.run(mod_general.cmd_start(message))

    assert message.answer.await_count == 1


def test_ping_only_responds_for_admin(monkeypatch):
    admin_message = SimpleNamespace(
        text="/ping",
        from_user=SimpleNamespace(id=887869657),
        chat=SimpleNamespace(id=789, type="private"),
        answer=AsyncMock(),
    )
    user_message = SimpleNamespace(
        text="/ping",
        from_user=SimpleNamespace(id=123),
        chat=SimpleNamespace(id=789, type="private"),
        answer=AsyncMock(),
    )

    monkeypatch.setattr(mod_general, "is_admin_user", lambda user_id: user_id == 887869657)
    monkeypatch.setattr(mod_general, "bot_runtime_state", lambda now=None: {"active": True, "source": "always"})
    monkeypatch.setattr(mod_general, "bot_unavailable_reason", lambda now=None: "")

    asyncio.run(mod_general.cmd_ping(admin_message))
    asyncio.run(mod_general.cmd_ping(user_message))

    assert admin_message.answer.await_count == 1
    assert user_message.answer.await_count == 0
    assert "runtime=" in admin_message.answer.await_args.args[0]
    assert "unavailable_reason=" in admin_message.answer.await_args.args[0]


def test_admin_order_capture_skips_system_commands(monkeypatch):
    message = SimpleNamespace(
        text="/start",
        caption="",
        from_user=SimpleNamespace(id=123, is_bot=False),
        chat=SimpleNamespace(type="private"),
        answer=AsyncMock(),
    )

    monkeypatch.setattr(mod_admin_order, "is_admin_user", lambda user_id: False)

    try:
        asyncio.run(mod_admin_order.admin_order_capture(message))
        raise AssertionError("admin_order_capture should skip system commands")
    except SkipHandler:
        pass


def test_admin_order_capture_skips_me_command_for_admin_without_draft(monkeypatch):
    message = SimpleNamespace(
        text="/me",
        caption="",
        from_user=SimpleNamespace(id=123, is_bot=False),
        chat=SimpleNamespace(type="private"),
        answer=AsyncMock(),
    )

    monkeypatch.setattr(mod_admin_order, "is_admin_user", lambda user_id: True)
    monkeypatch.setattr(mod_admin_order, "_get_draft", lambda admin_id: None)

    try:
        asyncio.run(mod_admin_order.admin_order_capture(message))
        raise AssertionError("admin_order_capture should skip /me without draft")
    except SkipHandler:
        pass


def test_private_menu_has_single_coupon_entry(monkeypatch):
    config = {
        "COUPON_COMMAND_ENABLED": "ON",
        "BOT_MENU_PRIVATE_COUPON_ENABLED": "ON",
        "BOT_MENU_PRIVATE_START_ENABLED": "ON",
        "BOT_MENU_PRIVATE_LANG_ENABLED": "ON",
        "BOT_MENU_PRIVATE_ME_ENABLED": "ON",
        "BOT_MENU_PRIVATE_SUPPORT_ENABLED": "ON",
        "BOT_MENU_PRIVATE_POLICY_ENABLED": "ON",
        "BOT_COMMAND_DESC_CODE": "Nhập mã / code / hidden code",
    }
    calls = []

    async def fake_set_my_commands(commands, scope=None):
        calls.append((commands, scope))

    monkeypatch.setattr(database.db, "get_config", lambda key, default="": config.get(key, default))
    monkeypatch.setattr(bot_instance.bot, "set_my_commands", fake_set_my_commands)

    asyncio.run(bot_instance.set_commands())

    private_calls = [item for item in calls if isinstance(item[1], BotCommandScopeAllPrivateChats)]
    assert private_calls, "private command scope should be set"
    private_commands = private_calls[-1][0]
    assert [cmd.command for cmd in private_commands].count("code") == 1
    assert [cmd.command for cmd in private_commands].count("coupon") == 0
    assert "activation" not in [cmd.command for cmd in private_commands]
    assert "hidden" not in [cmd.command for cmd in private_commands]


def test_admin_order_forward_prefills_identity(monkeypatch):
    message = SimpleNamespace(
        text="hi",
        caption="",
        from_user=SimpleNamespace(id=999, is_bot=False),
        chat=SimpleNamespace(type="private"),
        forward_origin=SimpleNamespace(
            sender_user=SimpleNamespace(id=7508222302, first_name="Ut", last_name="Cu", username="utc"),
            chat=None,
        ),
        forward_from=None,
        forward_from_chat=None,
        forward_date="2026-07-12",
    )

    draft = mod_admin_order._start_draft_from_message(message)

    assert draft.telegram_user_id == "7508222302"
    assert draft.full_name == "Ut Cu"
    assert "ID: 7508222302" in draft.customer_text
    assert "@utc" in draft.customer_text


def test_admin_order_plan_selection_autofills_pricing(monkeypatch):
    monkeypatch.setattr(mod_admin_order, "_plan_candidates", lambda: ["Prime"])
    monkeypatch.setattr(mod_admin_order, "main_group_matches_plan", lambda no, text: text == "Prime")
    monkeypatch.setattr(mod_admin_order, "group_numbers", lambda: [1])
    monkeypatch.setattr(mod_admin_order, "localized_price_key", lambda key, currency: key)
    monkeypatch.setattr(mod_admin_order, "get_price", lambda price_key, default, currency: (99000, 0))

    draft = mod_admin_order.OrderDraft(admin_id=1, plan_name="Prime")
    mod_admin_order._apply_pricing_from_plan(draft)

    assert draft.amount == "99000"
    assert draft.duration_days == "30"
    assert draft.payment_currency == "VND"


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
