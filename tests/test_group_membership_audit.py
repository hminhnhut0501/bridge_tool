import os
import unittest
from datetime import datetime

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import web_backend
import scheduler


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "BTN_G1": "Hang Cú Prime",
            "ID_G1": "-100111",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)

    def reload_config(self, force=False):
        return None


class FakeStore:
    enabled = True

    def __init__(self, orders):
        self.orders = orders

    def list_scheduler_orders(self, limit=5000):
        return self.orders


class GroupMembershipAuditTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = web_backend.db
        self.original_config_db = config_utils.db
        self.original_store = web_backend.supabase_store
        self.original_scheduler_db = scheduler.db
        self.original_now_local = web_backend.now_local
        self.fake_db = FakeDb()
        web_backend.db = self.fake_db
        scheduler.db = self.fake_db
        config_utils.db = self.fake_db
        web_backend.now_local = lambda: datetime(2026, 8, 14, 10, 0, 0)

    def tearDown(self):
        web_backend.db = self.original_db
        config_utils.db = self.original_config_db
        web_backend.supabase_store = self.original_store
        scheduler.db = self.original_scheduler_db
        web_backend.now_local = self.original_now_local

    async def test_group_membership_audit_flags_expired_no_order_and_active_rows(self):
        web_backend.supabase_store = FakeStore(
            [
                {
                    "order_id": "expired-1",
                    "telegram_user_id": "42",
                    "full_name": "Expired User",
                    "plan_name": "VIP 30 Ngày - Hang Cú Prime",
                    "status": "PAID",
                    "expire_at": "2026-08-01 00:00:00",
                },
                {
                    "order_id": "active-1",
                    "telegram_user_id": "99",
                    "full_name": "Active User",
                    "plan_name": "VIP 30 Ngày - Hang Cú Prime",
                    "status": "PAID",
                    "expire_at": "2026-09-01 00:00:00",
                },
            ]
        )

        csv_text = """ID,Name,Username
42,Expired User,expired_user
99,Active User,active_user
55,No Order,noop
"""

        result = await web_backend.build_group_membership_audit_rows("-100111", csv_text, group_name="Hang Cú Prime", live=False)
        summary = result["summary"]
        rows = {row["telegram_user_id"]: row for row in result["rows"]}

        self.assertEqual(summary["total_csv_rows"], 3)
        self.assertEqual(summary["kickable_rows"], 1)
        self.assertEqual(summary["active_rows"], 1)
        self.assertEqual(summary["no_order_rows"], 1)
        self.assertEqual(rows["42"]["verdict"], "EXPIRED_SHOULD_KICK")
        self.assertTrue(rows["42"]["needs_action"])
        self.assertEqual(rows["99"]["verdict"], "KEEP_ACTIVE")
        self.assertFalse(rows["99"]["needs_action"])
        self.assertEqual(rows["55"]["verdict"], "NO_ORDER")
        self.assertTrue(rows["55"]["needs_action"])

    async def test_group_membership_audit_supports_lowercase_headers(self):
        web_backend.supabase_store = FakeStore([])

        csv_text = """telegram_user_id,name,username
777,Lower,lower_user
"""

        result = await web_backend.build_group_membership_audit_rows("-100111", csv_text, live=False)

        self.assertEqual(result["summary"]["total_csv_rows"], 1)
        self.assertEqual(result["rows"][0]["telegram_user_id"], "777")
        self.assertEqual(result["rows"][0]["customer_name"], "Lower")


if __name__ == "__main__":
    unittest.main()
