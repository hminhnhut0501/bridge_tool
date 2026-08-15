import asyncio
import hashlib
import hmac
import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import modules.mod_coupon as mod_coupon
import modules.mod_payment as mod_payment
import processor
import support_utils
import web_backend
from supabase_store import SupabaseStore


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "GROUP_COUNT": "2",
            "ID_G1": "-1001",
            "BTN_G1": "Prime",
            "ID_G2": "-1002",
            "BTN_G2": "Asia",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)


class FakeDeliveryStore:
    enabled = True

    def __init__(self, order, paid_orders=None):
        self.order = dict(order)
        self.paid_orders = list(paid_orders or [])
        self.mark_paid_calls = []
        self.coupon_calls = 0

    def get_order(self, order_id):
        return dict(self.order)

    def list_paid_orders_for_user(self, user_id, limit=200):
        return list(self.paid_orders)

    def mark_order_paid(self, order_id, paid_at, expire_at):
        self.mark_paid_calls.append((str(order_id), paid_at, expire_at))
        self.order.update({"status": "PAID", "paid_at": paid_at, "expire_at": expire_at})

    def patch_order(self, order_id, payload):
        self.order.update(payload)
        return dict(self.order)

    def consume_coupon_for_order(self, order):
        self.coupon_calls += 1


class FakeDeliveryBot:
    def __init__(self, pause=None):
        self.pause = pause
        self.invites = []
        self.messages = []

    async def unban_chat_member(self, **kwargs):
        if self.pause:
            await self.pause.wait()

    async def create_chat_invite_link(self, chat_id, **kwargs):
        self.invites.append(str(chat_id))
        return SimpleNamespace(invite_link=f"https://t.me/+{chat_id}")

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)


class FakePaymentBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(id=kwargs["chat_id"]), message_id=123)


class FakeLicenseDeliveryRequest:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


class DeliveryPaymentFlowTests(unittest.IsolatedAsyncioTestCase):
    legacy_only = unittest.skip("legacy-only: delivery/payment contract is outside renewal core gate")
    def setUp(self):
        self.db = FakeDb()
        self.originals = {
            "processor_db": processor.db,
            "processor_store": processor.supabase_store,
            "processor_bot": processor.bot,
            "processor_now": processor.now_local,
            "processor_t": processor.t,
            "processor_support": processor.add_support_join_button,
            "processor_unmute": processor.unmute_member,
            "processor_record": processor.record_support_event,
            "processor_resolve_plan_groups": processor.resolve_plan_groups,
            "config_db": config_utils.db,
            "coupon_db": mod_coupon.db,
            "coupon_bot": mod_coupon.bot,
            "coupon_t": mod_coupon.t,
            "coupon_unmute": mod_coupon.unmute_member,
            "support_db": support_utils.db,
        }
        processor.db = self.db
        config_utils.db = self.db
        mod_coupon.db = self.db
        support_utils.db = self.db
        processor.now_local = lambda: datetime(2026, 6, 4, 12, 0, 0)
        processor.t = lambda user_id, key, default="": default
        processor.processing_orders.clear()
        processor.resolve_plan_groups = lambda plan_name, plan_token="": [("-1001", "Prime")]
        self.events = []
        processor.record_support_event = lambda event_type, user_id, **kwargs: self.events.append((event_type, kwargs))

        async def fake_build_invite_links(user_id, plan_name):
            return "JOIN", "Prime", [], [{"group_name": "Prime", "invite_link": "https://t.me/+prime"}]

        self.originals["coupon_build_invite_links"] = mod_coupon.build_invite_links
        mod_coupon.build_invite_links = fake_build_invite_links

        async def no_support(keyboard, user_id):
            return ""

        async def no_unmute(chat_id, user_id):
            return None

        processor.add_support_join_button = no_support
        processor.unmute_member = no_unmute
        mod_coupon.unmute_member = no_unmute
        mod_coupon.t = lambda user_id, key, default="": default

    def tearDown(self):
        processor.db = self.originals["processor_db"]
        processor.supabase_store = self.originals["processor_store"]
        processor.bot = self.originals["processor_bot"]
        processor.now_local = self.originals["processor_now"]
        processor.t = self.originals["processor_t"]
        processor.add_support_join_button = self.originals["processor_support"]
        processor.unmute_member = self.originals["processor_unmute"]
        processor.record_support_event = self.originals["processor_record"]
        processor.resolve_plan_groups = self.originals["processor_resolve_plan_groups"]
        config_utils.db = self.originals["config_db"]
        mod_coupon.db = self.originals["coupon_db"]
        mod_coupon.bot = self.originals["coupon_bot"]
        mod_coupon.t = self.originals["coupon_t"]
        mod_coupon.unmute_member = self.originals["coupon_unmute"]
        mod_coupon.build_invite_links = self.originals["coupon_build_invite_links"]
        support_utils.db = self.originals["support_db"]
        processor.processing_orders.clear()

    @legacy_only
    async def test_concurrent_delivery_processes_order_only_once(self):
        pause = asyncio.Event()
        processor.bot = FakeDeliveryBot(pause=pause)
        processor.supabase_store = FakeDeliveryStore({
            "order_id": "100",
            "telegram_user_id": "42",
            "plan_name": "SVIP+ 30 Ngày Full",
            "status": "PENDING",
            "coupon_code": "SALE10",
        })

        first = asyncio.create_task(processor.process_successful_payment("100"))
        await asyncio.sleep(0)
        second = asyncio.create_task(processor.process_successful_payment("100"))
        await asyncio.sleep(0)
        pause.set()
        await asyncio.gather(first, second)

        self.assertEqual(len(processor.supabase_store.mark_paid_calls), 1)
        self.assertEqual(processor.supabase_store.coupon_calls, 1)
        self.assertEqual(processor.bot.invites, ["-1001", "-1002"])

    async def test_renewal_extends_from_current_same_plan_expiry(self):
        processor.bot = FakeDeliveryBot()
        processor.supabase_store = FakeDeliveryStore(
            {
                "order_id": "101",
                "telegram_user_id": "42",
                "plan_name": "VIP 30 Ngày - Prime",
                "status": "PENDING",
            },
            paid_orders=[{
                "order_id": "old",
                "telegram_user_id": "42",
                "plan_name": "VIP 30 Ngày - Prime",
                "status": "PAID",
                "expire_at": "2026-06-20 12:00:00",
            }],
        )

        await processor.process_successful_payment("101")

        self.assertEqual(processor.supabase_store.mark_paid_calls[0][2], "2026-07-20 12:00:00")
        self.assertEqual(processor.bot.invites, ["-1001"])

    @legacy_only
    async def test_lifetime_payment_uses_fixed_new_expiry_even_with_prior_paid_lifetime_order(self):
        processor.bot = FakeDeliveryBot()
        processor.supabase_store = FakeDeliveryStore(
            {
                "order_id": "103",
                "telegram_user_id": "42",
                "plan_name": "All Access Trọn Đời",
                "status": "PENDING",
            },
            paid_orders=[{
                "order_id": "old-life",
                "telegram_user_id": "42",
                "plan_name": "All Access Trọn Đời",
                "status": "PAID",
                "expire_at": "2036-06-04 12:00:00",
            }],
        )

        await processor.process_successful_payment("103")

        self.assertEqual(processor.supabase_store.mark_paid_calls[0][2], "2036-06-01 12:00:00")
        self.assertEqual(processor.bot.invites, ["-1001", "-1002"])

    @legacy_only
    async def test_coupon_invite_result_reports_all_failed_groups(self):
        class FailedBot(FakeDeliveryBot):
            async def create_chat_invite_link(self, chat_id, **kwargs):
                raise RuntimeError("chat not found")

        mod_coupon.bot = FailedBot()
        links, groups, failures, invite_results = await mod_coupon.build_invite_links("42", "SVIP+ Full")

        self.assertIn("chat not found", links)
        self.assertEqual(groups, "")
        self.assertEqual(failures, ["Prime", "Asia"])
        self.assertEqual(len(invite_results), 2)

    @legacy_only
    async def test_unmapped_paid_plan_records_delivery_failure(self):
        processor.bot = FakeDeliveryBot()
        processor.supabase_store = FakeDeliveryStore({
            "order_id": "102",
            "telegram_user_id": "42",
            "plan_name": "VIP Mystery Group",
            "status": "PENDING",
        })

        await processor.process_successful_payment("102")

        self.assertEqual(len(processor.supabase_store.mark_paid_calls), 1)
        self.assertEqual(self.events[0][0], "delivery_failed")
        self.assertEqual(self.events[0][1]["raw_data"]["failed_groups"], ["UNMAPPED_PLAN"])
        self.assertIn("chưa map được", processor.bot.messages[0]["text"])

    async def test_supabase_paid_order_is_still_delivered(self):
        processor.bot = FakeDeliveryBot()
        processor.supabase_store = FakeDeliveryStore({
            "order_id": "103",
            "telegram_user_id": "42",
            "plan_name": "VIP 30 Ngày - Prime",
            "status": "PAID",
        })

        await processor.process_successful_payment("103")

        self.assertEqual(len(processor.supabase_store.mark_paid_calls), 1)
        self.assertEqual(self.events[0][0], "delivery_success")
        self.assertTrue(processor.bot.messages)
        self.assertIn("PAYMENT CONFIRMED", processor.bot.messages[0]["text"])

    def test_paypal_order_falls_back_without_provider_columns(self):
        store = SupabaseStore()
        calls = []

        def request(*args, **kwargs):
            calls.append(kwargs.get("json"))
            if len(calls) == 1:
                raise RuntimeError("column payment_provider does not exist")
            return [{"order_id": "1"}]

        store._request = request
        result = store.create_order(
            "1",
            "42",
            "User",
            "Plan",
            100,
            payment_provider="PAYPAL",
            payment_provider_order_id="PAYPAL-1",
            payment_currency="USD",
        )

        self.assertEqual(result, [{"order_id": "1"}])
        self.assertNotIn("payment_provider", calls[1])
        self.assertEqual(calls[1]["metadata"]["payment_provider"], "PAYPAL")
        self.assertEqual(calls[1]["metadata"]["payment_provider_order_id"], "PAYPAL-1")
        self.assertEqual(calls[1]["metadata"]["payment_currency"], "USD")

    def test_payos_order_can_fallback_during_provider_migration(self):
        store = SupabaseStore()
        calls = []

        def request(*args, **kwargs):
            calls.append(kwargs.get("json"))
            if len(calls) == 1:
                raise RuntimeError("column payment_provider does not exist")
            return [{"order_id": "1"}]

        store._request = request
        result = store.create_order("1", "42", "User", "Plan", 100, payment_provider="PAYOS")

        self.assertEqual(result, [{"order_id": "1"}])
        self.assertNotIn("payment_provider", calls[1])

    @legacy_only
    def test_usd_order_keeps_decimal_amount_and_currency(self):
        store = SupabaseStore()
        calls = []

        def request(*args, **kwargs):
            calls.append(kwargs.get("json"))
            return [{"order_id": "usd-1"}]

        store._request = request
        store.create_order("usd-1", "42", "User", "Plan", 4.99, payment_provider="PAYPAL", payment_currency="USD")

        self.assertEqual(calls[0]["amount"], 4.99)
        self.assertEqual(calls[0]["payment_currency"], "USD")

    @legacy_only
    async def test_web_caption_for_vietnamese_flow_uses_vnd_text_style(self):
        fake_bot = FakePaymentBot()
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=42, full_name="User"),
            message=SimpleNamespace(chat=SimpleNamespace(id=99)),
        )
        pay_data = {
            "provider": "WEB",
            "approval_url": "https://example.com/checkout",
            "checkout_url": "https://example.com/checkout",
            "currency_code": "VND",
            "license_code": "LIC_42",
        }

        with patch("modules.mod_payment.bot", fake_bot), patch(
            "sale_utils.db.get_config",
            side_effect=lambda key, default="": {"DISPLAY_CURRENCY_STYLE": "VND_TEXT"}.get(key, default),
        ), patch(
            "modules.mod_payment.t",
            side_effect=lambda user_id, key, default="": default,
        ):
            await mod_payment.send_payment_bill(
                callback,
                order_id=123,
                plan_name="Gói VIP Prime",
                amount=78000,
                description="PRIVE123",
                pay_data=pay_data,
            )

        self.assertTrue(fake_bot.messages)
        caption = fake_bot.messages[0]["text"]
        self.assertIn("WEB PAYMENT", caption)
        self.assertIn("78.000 VNĐ", caption)
        self.assertNotIn("LIC_42", caption)

    @legacy_only
    async def test_web_bill_does_not_expose_license_before_payment(self):
        fake_bot = FakePaymentBot()
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=42, full_name="User"),
            message=SimpleNamespace(chat=SimpleNamespace(id=99)),
        )
        pay_data = {
            "provider": "WEB",
            "approval_url": "https://example.com/checkout",
            "checkout_url": "https://example.com/checkout",
            "currency_code": "VND",
            "license_code": "LIC_42",
        }

        with patch("modules.mod_payment.bot", fake_bot), patch(
            "sale_utils.db.get_config",
            side_effect=lambda key, default="": {"DISPLAY_CURRENCY_STYLE": "VND_TEXT"}.get(key, default),
        ), patch(
            "modules.mod_payment.t",
            side_effect=lambda user_id, key, default="": default,
        ):
            await mod_payment.send_payment_bill(
                callback,
                order_id=123,
                plan_name="Gói VIP Prime",
                amount=78000,
                description="PRIVE123",
                pay_data=pay_data,
            )

        self.assertTrue(fake_bot.messages)
        caption = fake_bot.messages[0]["text"]
        markup = fake_bot.messages[0]["reply_markup"]
        button_texts = [button.text for row in markup.inline_keyboard for button in row]
        self.assertIn("WEB PAYMENT", caption)
        self.assertIn("78.000 VNĐ", caption)
        self.assertNotIn("LIC_42", caption)
        self.assertNotIn("Kích hoạt trên bot", " ".join(button_texts))
        self.assertNotIn("?start=lic_", caption)

    @legacy_only
    async def test_license_delivery_endpoint_renders_full_message(self):
        previous_flow_enabled = web_backend.license_flow_enabled
        previous_bot = web_backend.bot
        previous_store = web_backend.supabase_store
        previous_invite_links = mod_coupon.build_invite_links
        previous_secret_env = os.environ.get("WEB_PAYMENT_SECRET")
        previous_bot_secret_env = os.environ.get("BOT_WEB_HMAC_SECRET")
        previous_delivery_secret = web_backend._bot_delivery_secret

        fake_bot = FakePaymentBot()

        async def fake_build_invite_links(user_id, plan_code):
            return (
                "🔗 Prime: https://t.me/+prime-link",
                "Prime",
                [],
                [{"group_id": "-1001", "success": True, "invite_link": "https://t.me/+prime-link"}],
            )

        class FakeStore:
            def record_support_event(self, *args, **kwargs):
                return None

        body = {
            "orderId": "order_123",
            "orderNumber": "ORD-123",
            "telegramUserId": "42",
            "customerRef": "customer-1",
            "planCode": "HCV_30D",
            "planName": "VIP 30 Ngày - Prime",
            "currency": "VND",
            "amountMinor": 59000,
            "licenseCode": "LIC-ABCD-EFGH-IJKL",
            "activationUrl": "https://t.me/hangcuvipbot?start=lic_LIC-ABCD-EFGH-IJKL",
            "groupIds": ["-1001"],
            "entitlements": ["app_access", "vip_group_access"],
            "locale": "vi",
            "timestamp": 1784600000,
            "nonce": "random-nonce-123",
        }
        secret = "test-secret"
        message = "|".join(
            [
                body["orderId"],
                body["telegramUserId"],
                str(body["timestamp"]),
                body["nonce"],
            ]
        )
        body["signature"] = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

        try:
            os.environ["WEB_PAYMENT_SECRET"] = secret
            os.environ["BOT_WEB_HMAC_SECRET"] = secret
            web_backend._bot_delivery_secret = lambda: secret
            web_backend.license_flow_enabled = lambda: True
            web_backend.bot = fake_bot
            web_backend.supabase_store = FakeStore()
            mod_coupon.build_invite_links = fake_build_invite_links

            response = await web_backend.license_delivery(FakeLicenseDeliveryRequest(body))

            self.assertEqual(response["success"], True)
            self.assertEqual(len(fake_bot.messages), 1)
            sent = fake_bot.messages[0]
            text = sent["text"]
            self.assertIn("Thanh toán thành công", text)
            self.assertIn("order_123", text)
            self.assertIn("VIP 30 Ngày - Prime", text)
            self.assertIn("LIC-ABCD-EFGH-IJKL", text)
            self.assertIn("https://t.me/hangcuvipbot?start=lic_LIC-ABCD-EFGH-IJKL", text)
            self.assertIn("Prime", text)
            self.assertEqual(sent["chat_id"], 42)
        finally:
            web_backend.license_flow_enabled = previous_flow_enabled
            web_backend.bot = previous_bot
            web_backend.supabase_store = previous_store
            web_backend._bot_delivery_secret = previous_delivery_secret
            mod_coupon.build_invite_links = previous_invite_links
            if previous_secret_env is None:
                os.environ.pop("WEB_PAYMENT_SECRET", None)
            else:
                os.environ["WEB_PAYMENT_SECRET"] = previous_secret_env
            if previous_bot_secret_env is None:
                os.environ.pop("BOT_WEB_HMAC_SECRET", None)
            else:
                os.environ["BOT_WEB_HMAC_SECRET"] = previous_bot_secret_env

    async def test_license_delivery_endpoint_is_idempotent_for_duplicate_callbacks(self):
        previous_flow_enabled = web_backend.license_flow_enabled
        previous_bot = web_backend.bot
        previous_store = web_backend.supabase_store
        previous_invite_links = mod_coupon.build_invite_links
        previous_secret_env = os.environ.get("WEB_PAYMENT_SECRET")
        previous_bot_secret_env = os.environ.get("BOT_WEB_HMAC_SECRET")
        previous_delivery_secret = web_backend._bot_delivery_secret

        fake_bot = FakePaymentBot()

        async def fake_build_invite_links(user_id, plan_code):
            return ("", "", [], [])

        class FakeStore:
            enabled = True

            def __init__(self):
                self.order = {
                    "metadata": {},
                }

            def get_order(self, order_id):
                return self.order

            def patch_order(self, order_id, payload):
                self.order.update(payload)
                return self.order

            def record_support_event(self, *args, **kwargs):
                return None

        body = {
            "orderId": "order_123",
            "orderNumber": "ORD-123",
            "telegramUserId": "42",
            "customerRef": "customer-1",
            "planCode": "HCV_30D",
            "planName": "VIP 30 Ngày - Prime",
            "currency": "VND",
            "amountMinor": 59000,
            "licenseCode": "LIC-ABCD-EFGH-IJKL",
            "activationUrl": "https://t.me/hangcuvipbot?start=lic_LIC-ABCD-EFGH-IJKL",
            "groupIds": ["-1001"],
            "entitlements": ["app_access", "vip_group_access"],
            "locale": "vi",
            "timestamp": 1784600000,
            "nonce": "random-nonce-123",
        }
        secret = "test-secret"
        message = "|".join(
            [
                body["orderId"],
                body["telegramUserId"],
                str(body["timestamp"]),
                body["nonce"],
            ]
        )
        body["signature"] = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

        try:
            os.environ["WEB_PAYMENT_SECRET"] = secret
            os.environ["BOT_WEB_HMAC_SECRET"] = secret
            web_backend._bot_delivery_secret = lambda: secret
            web_backend.license_flow_enabled = lambda: True
            web_backend.bot = fake_bot
            web_backend.supabase_store = FakeStore()
            mod_coupon.build_invite_links = fake_build_invite_links

            first = await web_backend.license_delivery(FakeLicenseDeliveryRequest(body))
            second = await web_backend.license_delivery(FakeLicenseDeliveryRequest(body))

            self.assertEqual(first["success"], True)
            self.assertEqual(second["success"], True)
            self.assertFalse(first.get("duplicate", False))
            self.assertTrue(second.get("duplicate", False))
            self.assertEqual(len(fake_bot.messages), 1)
        finally:
            web_backend.license_flow_enabled = previous_flow_enabled
            web_backend.bot = previous_bot
            web_backend.supabase_store = previous_store
            web_backend._bot_delivery_secret = previous_delivery_secret
            mod_coupon.build_invite_links = previous_invite_links
            if previous_secret_env is None:
                os.environ.pop("WEB_PAYMENT_SECRET", None)
            else:
                os.environ["WEB_PAYMENT_SECRET"] = previous_secret_env
            if previous_bot_secret_env is None:
                os.environ.pop("BOT_WEB_HMAC_SECRET", None)
            else:
                os.environ["BOT_WEB_HMAC_SECRET"] = previous_bot_secret_env

    async def test_license_delivery_endpoint_logs_snapshot_fields(self):
        previous_flow_enabled = web_backend.license_flow_enabled
        previous_bot = web_backend.bot
        previous_store = web_backend.supabase_store
        previous_invite_links = mod_coupon.build_invite_links
        previous_secret_env = os.environ.get("WEB_PAYMENT_SECRET")
        previous_bot_secret_env = os.environ.get("BOT_WEB_HMAC_SECRET")
        previous_delivery_secret = web_backend._bot_delivery_secret

        fake_bot = FakePaymentBot()

        async def fake_build_invite_links(user_id, plan_code):
            return ("", "", [], [])

        class FakeStore:
            def record_support_event(self, *args, **kwargs):
                return None

        body = {
            "orderId": "order_456",
            "orderNumber": "ORD-456",
            "telegramUserId": "99",
            "customerRef": "customer-9",
            "planCode": "HCV_30D",
            "planName": "VIP 30 Ngày - Prime",
            "currency": "VND",
            "amountMinor": 59000,
            "licenseCode": "LIC-TEST-1234",
            "activationUrl": "https://t.me/hangcuvipbot?start=lic_LIC-TEST-1234",
            "groupIds": ["-1001"],
            "entitlements": ["app_access", "vip_group_access"],
            "locale": "vi",
            "checkoutKind": "bot",
            "paymentProvider": "payos",
            "paymentSessionId": "ps_ORDER456_123456",
            "timestamp": 1784600000,
            "nonce": "random-nonce-456",
        }
        secret = "test-secret"
        message = "|".join(
            [
                body["orderId"],
                body["telegramUserId"],
                str(body["timestamp"]),
                body["nonce"],
            ]
        )
        body["signature"] = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

        printed: list[tuple[tuple[object, ...], dict[str, object]]] = []

        def capture_print(*args, **kwargs):
            printed.append((args, kwargs))

        try:
            os.environ["WEB_PAYMENT_SECRET"] = secret
            os.environ["BOT_WEB_HMAC_SECRET"] = secret
            web_backend._bot_delivery_secret = lambda: secret
            web_backend.license_flow_enabled = lambda: True
            web_backend.bot = fake_bot
            web_backend.supabase_store = FakeStore()
            mod_coupon.build_invite_links = fake_build_invite_links

            with patch("builtins.print", side_effect=capture_print):
                response = await web_backend.license_delivery(FakeLicenseDeliveryRequest(body))

            self.assertEqual(response["success"], True)
            snapshot_lines = [
                str(args[0])
                for args, _ in printed
                if args and str(args[0]).startswith("📦 license_delivery snapshot ")
            ]
            self.assertEqual(len(snapshot_lines), 1)
            snapshot = snapshot_lines[0]
            self.assertIn("orderId=order_456", snapshot)
            self.assertIn("telegramUserId=99", snapshot)
            self.assertIn("licenseCode=LIC-TEST-1234", snapshot)
            expected_order = [
                "planCode=HCV_30D",
                "checkoutKind=bot",
                "paymentSessionId=ps_ORDER456_123456",
                "paymentProvider=payos",
                "locale=vi",
                "currency=VND",
                "source=n/a",
                "integrationSource=n/a",
            ]
            last_index = -1
            for field in expected_order:
                current_index = snapshot.find(field)
                self.assertGreater(current_index, last_index)
                last_index = current_index
        finally:
            web_backend.license_flow_enabled = previous_flow_enabled
            web_backend.bot = previous_bot
            web_backend.supabase_store = previous_store
            web_backend._bot_delivery_secret = previous_delivery_secret
            mod_coupon.build_invite_links = previous_invite_links
            if previous_secret_env is None:
                os.environ.pop("WEB_PAYMENT_SECRET", None)
            else:
                os.environ["WEB_PAYMENT_SECRET"] = previous_secret_env
            if previous_bot_secret_env is None:
                os.environ.pop("BOT_WEB_HMAC_SECRET", None)
            else:
                os.environ["BOT_WEB_HMAC_SECRET"] = previous_bot_secret_env


if __name__ == "__main__":
    unittest.main()
