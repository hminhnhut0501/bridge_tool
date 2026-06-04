import asyncio
import os
import unittest
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import modules.mod_coupon as mod_coupon
import processor
import support_utils
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


class DeliveryPaymentFlowTests(unittest.IsolatedAsyncioTestCase):
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
        self.events = []
        processor.record_support_event = lambda event_type, user_id, **kwargs: self.events.append((event_type, kwargs))

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
        config_utils.db = self.originals["config_db"]
        mod_coupon.db = self.originals["coupon_db"]
        mod_coupon.bot = self.originals["coupon_bot"]
        mod_coupon.t = self.originals["coupon_t"]
        mod_coupon.unmute_member = self.originals["coupon_unmute"]
        support_utils.db = self.originals["support_db"]
        processor.processing_orders.clear()

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

    async def test_coupon_invite_result_reports_all_failed_groups(self):
        class FailedBot(FakeDeliveryBot):
            async def create_chat_invite_link(self, chat_id, **kwargs):
                raise RuntimeError("chat not found")

        mod_coupon.bot = FailedBot()
        links, groups, failures = await mod_coupon.build_invite_links("42", "SVIP+ Full")

        self.assertIn("chat not found", links)
        self.assertEqual(groups, "")
        self.assertEqual(failures, ["Prime", "Asia"])

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

    def test_paypal_order_does_not_fallback_without_provider_columns(self):
        store = SupabaseStore()
        calls = []

        def request(*args, **kwargs):
            calls.append(kwargs.get("json"))
            raise RuntimeError("column payment_provider does not exist")

        store._request = request
        with self.assertRaises(RuntimeError):
            store.create_order("1", "42", "User", "Plan", 100, payment_provider="PAYPAL")
        self.assertEqual(len(calls), 1)

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


if __name__ == "__main__":
    unittest.main()
