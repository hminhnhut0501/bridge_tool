import os
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import scheduler
import support_utils
import web_backend


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "GROUP_COUNT": "1",
            "BTN_G1": "Hang Cú Asia",
            "ID_G1": "-100444",
            "SUPPORT_GROUP_ID": "-100999",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)

    def reload_config(self, force=False):
        return None


class FakeStore:
    enabled = True

    def __init__(self, orders, events):
        self.orders = orders
        self.events = events

    def list_scheduler_orders(self, limit=5000):
        return self.orders

    def order_to_sheet_row(self, order):
        return [
            order.get("order_id") or "",
            order.get("telegram_user_id") or "",
            order.get("full_name") or "",
            order.get("plan_name") or "",
            order.get("amount") or "",
            order.get("status") or "",
            order.get("paid_at") or "",
            order.get("expire_at") or "",
            order.get("sale_id") or "",
            order.get("coupon_code") or "",
            order.get("last_reminder_date") or "",
            order.get("expired_notice_at") or "",
        ]

    def list_support_events(self, limit=5000):
        return self.events


class KickAuditLogicTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = FakeDb()
        self.original_now_local = web_backend.now_local
        self.original_web_db = web_backend.db
        self.original_web_store = web_backend.supabase_store
        self.original_scheduler_db = scheduler.db
        self.original_support_db = support_utils.db
        self.original_config_db = config_utils.db
        web_backend.db = self.db
        scheduler.db = self.db
        support_utils.db = self.db
        config_utils.db = self.db
        web_backend.now_local = lambda: datetime(2026, 5, 26, 12, 0, 0)

    def tearDown(self):
        web_backend.now_local = self.original_now_local
        web_backend.db = self.original_web_db
        web_backend.supabase_store = self.original_web_store
        scheduler.db = self.original_scheduler_db
        support_utils.db = self.original_support_db
        config_utils.db = self.original_config_db

    async def test_invalid_expire_at_is_visible_in_kick_audit(self):
        web_backend.supabase_store = FakeStore(
            [{
                "order_id": "bad-date",
                "telegram_user_id": "42",
                "full_name": "User",
                "plan_name": "VIP 30 ngày - Hang Cú Asia",
                "status": "PAID",
                "expire_at": "bad-date",
            }],
            [],
        )

        rows = await web_backend.build_kick_audit_rows()

        self.assertEqual(rows[0]["status"], "INVALID_EXPIRE_AT")
        self.assertTrue(rows[0]["needs_action"])
        self.assertIn("Không đọc được expire_at", rows[0]["latest_error"])

    async def test_group_kick_event_covers_other_old_orders_in_audit(self):
        web_backend.supabase_store = FakeStore(
            [{
                "order_id": "old-b",
                "telegram_user_id": "42",
                "full_name": "User",
                "plan_name": "VIP 1 ngày - Hang Cú Asia",
                "status": "EXPIRED",
                "expire_at": "2026-05-25 21:19:00",
            }],
            [{
                "event_type": "member_kicked",
                "telegram_user_id": "42",
                "chat_id": "-100444",
                "order_id": "old-a",
                "plan_name": "VIP 1 ngày - Hang Cú Asia",
                "created_at": "2026-05-25T21:20:00",
            }],
        )

        rows = await web_backend.build_kick_audit_rows()

        self.assertEqual(rows[0]["status"], "KICKED")
        self.assertEqual(rows[0]["status_label"], "Đã kick cùng group")
        self.assertFalse(rows[0]["needs_action"])

    async def test_active_retained_audit_shows_reason_and_related_order(self):
        web_backend.supabase_store = FakeStore(
            [
                {
                    "order_id": "old-expired",
                    "telegram_user_id": "42",
                    "full_name": "User",
                    "plan_name": "VIP 1 ngày - Hang Cú Asia",
                    "status": "EXPIRED",
                    "expire_at": "2026-05-25 21:19:00",
                },
                {
                    "order_id": "active-keep",
                    "telegram_user_id": "42",
                    "full_name": "User",
                    "plan_name": "VIP 30 ngày - Hang Cú Asia",
                    "status": "PAID",
                    "expire_at": "2026-06-25 21:19:00",
                },
            ],
            [],
        )

        rows = await web_backend.build_kick_audit_rows()

        retained = [row for row in rows if row["status"] == "ACTIVE_RETAINED"]
        self.assertTrue(retained)
        self.assertIn("Còn", retained[0]["retained_reason"])
        self.assertEqual(retained[0]["retained_orders"], ["active-keep"])

    async def test_empty_timezone_falls_back_and_kick_audit_builds(self):
        self.db.config["BOT_TIMEZONE"] = ""
        web_backend.now_local = self.original_now_local
        web_backend.supabase_store = FakeStore([], [])

        rows = await web_backend.build_kick_audit_rows()

        self.assertEqual(rows, [])
        self.assertEqual(web_backend.backend_timezone(), ZoneInfo("Asia/Ho_Chi_Minh"))

    def test_invalid_timezone_falls_back_for_manual_expire_parser(self):
        self.db.config["BOT_TIMEZONE"] = "not/a-real-timezone"

        parsed = web_backend.parse_manual_expire_at("2026-06-04T12:30")

        self.assertEqual(parsed.tzinfo, ZoneInfo("Asia/Ho_Chi_Minh"))


if __name__ == "__main__":
    unittest.main()
