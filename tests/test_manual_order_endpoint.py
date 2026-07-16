import os
import unittest
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import web_backend


class FakeDb:
    def __init__(self):
        self.config = {"BOT_TIMEZONE": "Asia/Ho_Chi_Minh"}

    def get_config(self, key, default=""):
        return self.config.get(key, default)

    def reload_config(self, force=False):
        return None


class FakeStore:
    enabled = True

    def __init__(self):
        self.created_orders = []
        self.paid_orders = []
        self.activation_codes = []
        self.events = []

    def get_blacklist_entry(self, telegram_user_id):
        return None

    def create_order(self, **kwargs):
        self.created_orders.append(kwargs)

    def mark_order_paid(self, order_id, paid_at, expire_at):
        self.paid_orders.append((order_id, paid_at, expire_at))
        return [{"order_id": order_id, "paid_at": paid_at, "expire_at": expire_at}]

    def create_order_activation_code(self, **kwargs):
        self.activation_codes.append(kwargs)

    def record_support_event(self, event_type, telegram_user_id, **kwargs):
        self.events.append((event_type, str(telegram_user_id), kwargs))


class FakeRequest:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


class ManualOrderEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = web_backend.db
        self.original_store = web_backend.supabase_store
        self.original_now_local = web_backend.now_local
        self.original_get_user_language = web_backend.get_user_language
        self.original_set_user_language = web_backend.set_user_language
        self.original_resolve_plan_groups = web_backend.resolve_plan_groups
        self.original_payment_manager = web_backend.payment_manager
        self.original_create_support_invite_link = web_backend.create_support_invite_link
        self.original_build_invite_links = web_backend.build_manual_order_result.__globals__["build_invite_links"] if "build_invite_links" in web_backend.build_manual_order_result.__globals__ else None
        self.original_order_is_lifetime = web_backend.order_is_lifetime
        self.original_render_activation_text = web_backend.render_activation_text

        self.db = FakeDb()
        self.store = FakeStore()
        web_backend.db = self.db
        web_backend.supabase_store = self.store
        web_backend.now_local = lambda: datetime(2026, 7, 16, 9, 0, 0)
        web_backend.get_user_language = lambda user_id: "vi"
        web_backend.set_user_language = lambda user_id, language: None
        web_backend.resolve_plan_groups = lambda plan_name: [("-100111", "Hang Cú Prime")]
        web_backend.payment_manager = SimpleNamespace(preferred_provider=lambda lang: "PAYOS")
        web_backend.create_support_invite_link = lambda user_id: ("", "")
        web_backend.order_is_lifetime = lambda plan_name: False
        web_backend.render_activation_text = lambda key, default_text, context: default_text.format(**context)
        web_backend.build_manual_order_result.__globals__["build_invite_links"] = lambda user_id, plan_name: ("", "", [], [])

    def tearDown(self):
        web_backend.db = self.original_db
        web_backend.supabase_store = self.original_store
        web_backend.now_local = self.original_now_local
        web_backend.get_user_language = self.original_get_user_language
        web_backend.set_user_language = self.original_set_user_language
        web_backend.resolve_plan_groups = self.original_resolve_plan_groups
        web_backend.payment_manager = self.original_payment_manager
        web_backend.create_support_invite_link = self.original_create_support_invite_link
        web_backend.order_is_lifetime = self.original_order_is_lifetime
        web_backend.render_activation_text = self.original_render_activation_text
        if self.original_build_invite_links is not None:
            web_backend.build_manual_order_result.__globals__["build_invite_links"] = self.original_build_invite_links

    async def test_admin_create_manual_order_falls_back_to_plan_name_when_admin_label_missing(self):
        request = FakeRequest({
            "telegram_user_id": "42",
            "full_name": "Alice",
            "plan_name": "VIP 30 Ngày - Prime",
            "amount": "78000",
            "expire_at": "2026-08-15 09:00:00",
            "skip_join_link": True,
            "fast_mode": True,
            "skip_active_code": True,
            "sale_id": "MANUAL",
        })

        result = await web_backend.admin_create_manual_order(request)

        self.assertEqual(result["data"]["admin_label"], "VIP 30 Ngày - Prime")
        self.assertEqual(self.store.created_orders[0]["metadata"]["admin_label"], "VIP 30 Ngày - Prime")
        self.assertEqual(self.store.events[0][2]["plan_name"], "VIP 30 Ngày - Prime")
        self.assertEqual(self.store.events[0][2]["raw_data"]["admin_label"], "VIP 30 Ngày - Prime")
        self.assertEqual(self.store.events[0][1], "42")


if __name__ == "__main__":
    unittest.main()
