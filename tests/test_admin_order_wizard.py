from types import SimpleNamespace
import asyncio
from unittest.mock import AsyncMock

import modules.mod_admin_order as mod_admin_order


def test_admin_forward_starts_draft(monkeypatch):
    message = SimpleNamespace(
        text="Khách hỏi đơn",
        caption="",
        from_user=SimpleNamespace(id=887869657),
        forward_date=1,
        forward_origin=SimpleNamespace(
            type="user",
            sender_user=SimpleNamespace(id=555, first_name="An", last_name="Nguyen", username="an_n"),
        ),
    )
    draft = mod_admin_order._start_draft_from_message(message)

    assert draft.telegram_user_id == "555"
    assert "ID: 555" in draft.customer_text
    assert draft.step == "telegram_user_id"


def test_admin_new_command_starts_empty_draft():
    draft = mod_admin_order.OrderDraft(admin_id=1)

    assert draft.telegram_user_id == ""
    assert draft.plan_name == ""
    assert draft.note == ""
    assert draft.step == "telegram_user_id"


def test_new_command_replies_admin_only_for_non_admin():
    message = SimpleNamespace(
        text="/new",
        from_user=SimpleNamespace(id=123),
        chat=SimpleNamespace(id=789, type="private"),
        answer=AsyncMock(),
    )

    mod_admin_order.is_admin_user = lambda user_id: False
    asyncio.run(mod_admin_order.cmd_new_admin_order(message))

    assert message.answer.await_count == 1
    assert message.answer.await_args.args[0] == "admin only"


def test_admin_order_back_skip_and_plan_candidates(monkeypatch):
    monkeypatch.setattr(mod_admin_order, "_plan_candidates", lambda: ["VIP 30 Ngày", "SVIP+ 1 Tháng"])
    monkeypatch.setattr(mod_admin_order, "main_group_matches_plan", lambda no, name: str(no) == "1")
    monkeypatch.setattr(mod_admin_order, "get_price", lambda price_key, default=0, currency="VND": (150000, None))

    draft = mod_admin_order.OrderDraft(admin_id=1, step="plan_name")
    mod_admin_order._advance_after_field(draft, "telegram_user_id")
    assert draft.step == "plan_name"

    mod_admin_order._apply_skip(draft)
    assert draft.step == "note"

    assert mod_admin_order._prev_field("plan_name") == "telegram_user_id"
    assert mod_admin_order._next_field("plan_name") == "note"
    mod_admin_order._ensure_plan_name_hint(draft)
    assert draft.plan_name == "VIP 30 Ngày"


def test_plan_pricing_inference_autofills_hidden_or_main_plan(monkeypatch):
    monkeypatch.setattr(mod_admin_order, "main_group_matches_plan", lambda no, name: False)
    monkeypatch.setattr(mod_admin_order, "hidden_plan_group_id", lambda token: "prime_x")
    monkeypatch.setattr(mod_admin_order, "hidden_plan_duration_key", lambda token: "LIFE")
    monkeypatch.setattr(mod_admin_order, "is_hidden_plan_token", lambda token: True)
    monkeypatch.setattr(mod_admin_order, "extract_plan_token", lambda name: "HG:prime_x:LIFE")
    monkeypatch.setattr(mod_admin_order, "list_hidden_groups", lambda include_inactive=False: [{
        "id": "prime_x",
        "name": "Prime X",
        "price_1m_vnd": 150000,
        "price_life_vnd": 900000,
        "price_1m_usd": 9.99,
        "price_life_usd": 49.99,
        "duration_1m_days": 30,
        "lifetime_days": 3650,
    }])

    pricing = mod_admin_order._resolve_plan_pricing("Hidden - Prime X - Trọn Đời [PT:HG:prime_x:LIFE]", "PAYOS")

    assert pricing["payment_currency"] == "VND"
    assert pricing["duration_days"] == "3650"
    assert pricing["amount"] == "900000"


def test_admin_order_toggle_and_payload(monkeypatch):
    draft = mod_admin_order.OrderDraft(
        admin_id=1,
        telegram_user_id="123",
        plan_name="VIP 30 Ngày",
        note="ghi chu",
    )

    monkeypatch.setattr(mod_admin_order, "_backend_base_url", lambda: "http://backend")
    monkeypatch.setattr(mod_admin_order, "_admin_secret", lambda: "secret")
    monkeypatch.setattr(mod_admin_order, "_resolve_plan_pricing", lambda plan_name, provider="": {"amount": "100000", "duration_days": "30", "payment_currency": "VND"})

    captured = {}

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"order_id": "1", "activation_code": "ABC123"}}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResp()

    monkeypatch.setattr(mod_admin_order.requests, "post", fake_post)

    result = asyncio.run(mod_admin_order._create_manual_order(draft))

    assert result["order_id"] == "1"
    assert captured["url"] == "http://backend/admin-api/manual-orders"
    assert captured["json"]["telegram_user_id"] == "123"
    assert captured["headers"]["x-admin-secret"] == "secret"
    assert "activation_url" not in result
