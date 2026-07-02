import os
import unittest
from datetime import datetime

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import database
import scheduler
import vip_group_audit_utils
import support_utils


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "GROUP_COUNT": "1",
            "BTN_G1": "Hang Cú Prime",
            "ID_G1": "-100111",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)

    def reload_config(self, force=False):
        return None

    def record_support_event(self, *args, **kwargs):
        return None

    def get_user_identity(self, telegram_user_id):
        return {"username": "", "full_name": ""}


class FakeStore:
    enabled = True

    def __init__(self, orders, events, activation_codes=None):
        self.orders = orders
        self.events = events
        self.activation_codes = activation_codes or []
        self.updated = []

    def list_scheduler_orders(self, limit=5000):
        return self.orders

    def list_support_events(self, limit=10000):
        return self.events

    def list_order_activation_codes(self, limit=5000):
        return self.activation_codes

    def update_order_activation_code(self, code, raw):
        self.updated.append((code, raw))
        return [{"code": code, **raw}]


class VipMemberAuditTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fake_db = FakeDb()
        self.original_database_db = database.db
        self.original_config_db = config_utils.db
        self.original_vip_db = vip_group_audit_utils.db
        self.original_vip_store = vip_group_audit_utils.supabase_store
        self.original_scheduler_store = scheduler.supabase_store
        self.original_scheduler_db = scheduler.db
        self.original_scheduler_is_support_group = scheduler.is_support_group
        self.original_support_store = support_utils.supabase_store
        self.original_scheduler_now_local = scheduler.now_local
        self.original_vip_now_local = vip_group_audit_utils.now_local
        database.db = self.fake_db
        config_utils.db = self.fake_db
        vip_group_audit_utils.db = self.fake_db
        scheduler.db = self.fake_db
        scheduler.is_support_group = lambda chat_id: False
        support_utils.supabase_store = self.fake_db
        scheduler.now_local = lambda: datetime(2026, 7, 2, 12, 0, 0)
        vip_group_audit_utils.now_local = scheduler.now_local

    def tearDown(self):
        database.db = self.original_database_db
        config_utils.db = self.original_config_db
        vip_group_audit_utils.db = self.original_vip_db
        vip_group_audit_utils.supabase_store = self.original_vip_store
        scheduler.db = self.original_scheduler_db
        scheduler.is_support_group = self.original_scheduler_is_support_group
        scheduler.supabase_store = self.original_scheduler_store
        support_utils.supabase_store = self.original_support_store
        scheduler.now_local = self.original_scheduler_now_local
        vip_group_audit_utils.now_local = self.original_vip_now_local

    async def test_vip_member_audit_returns_expired_and_no_order_members(self):
        fake_store = FakeStore(
            orders=[
                {
                    "order_id": "expired-1",
                    "telegram_user_id": "42",
                    "full_name": "Expired User",
                    "plan_name": "VIP 30 Ngày - Hang Cú Prime",
                    "status": "PAID",
                    "expire_at": "2026-06-01 00:00:00",
                },
                {
                    "order_id": "active-1",
                    "telegram_user_id": "99",
                    "full_name": "Active User",
                    "plan_name": "VIP 30 Ngày - Hang Cú Prime",
                    "status": "PAID",
                    "expire_at": "2036-06-01 00:00:00",
                },
            ],
            events=[
                {
                    "event_type": "vip_joined",
                    "telegram_user_id": "42",
                    "full_name": "Expired User",
                    "chat_id": "-100111",
                    "chat_title": "Hang Cú Prime",
                    "created_at": "2026-06-02T00:00:00",
                    "raw_data": {"new_status": "member"},
                },
                {
                    "event_type": "vip_joined",
                    "telegram_user_id": "55",
                    "full_name": "No Order",
                    "chat_id": "-100111",
                    "chat_title": "Hang Cú Prime",
                    "created_at": "2026-06-03T00:00:00",
                    "raw_data": {"new_status": "member"},
                },
                {
                    "event_type": "vip_joined",
                    "telegram_user_id": "99",
                    "full_name": "Active User",
                    "chat_id": "-100111",
                    "chat_title": "Hang Cú Prime",
                    "created_at": "2026-06-04T00:00:00",
                    "raw_data": {"new_status": "member"},
                },
            ],
        )
        vip_group_audit_utils.supabase_store = fake_store

        rows = await vip_group_audit_utils.build_vip_member_risk_rows(live=False)

        risk_types = [row["risk_type"] for row in rows]
        self.assertEqual(risk_types, ["EXPIRED_ORDER", "NO_ORDER"])
        self.assertEqual(rows[0]["telegram_user_id"], "42")
        self.assertEqual(rows[1]["telegram_user_id"], "55")

    async def test_cleanup_order_invite_links_revoke_tracked_links(self):
        fake_store = FakeStore(
            orders=[],
            events=[],
            activation_codes=[
                {
                    "code": "ABC",
                    "activation_status": "USED",
                    "telegram_user_id": "42",
                    "full_name": "Expired User",
                    "order_id": "order-1",
                    "plan_name": "VIP 30 Ngày - Hang Cú Prime",
                    "used_at": "2026-06-01 00:00:00",
                    "raw_data": {
                        "invite_results": [
                            {"ok": True, "group_id": "-100111", "group_name": "Hang Cú Prime", "invite_link": "https://t.me/+abc"},
                            {"ok": True, "group_id": "-100999", "group_name": "Hang Cú Boy", "invite_link": "https://t.me/+def"},
                        ]
                    },
                }
            ],
        )
        vip_group_audit_utils.supabase_store = fake_store
        scheduler.supabase_store = fake_store
        revoked = []

        async def fake_revoke(chat_id, invite_link):
            revoked.append((str(chat_id), invite_link))
            return True, ""

        original_revoke = scheduler.revoke_support_invite_link
        scheduler.revoke_support_invite_link = fake_revoke
        try:
            result = await scheduler.cleanup_order_invite_links(group_id="-100111", force=True)
        finally:
            scheduler.revoke_support_invite_link = original_revoke

        self.assertEqual(revoked, [("-100111", "https://t.me/+abc")])
        self.assertEqual(result["success"], 1)
        self.assertEqual(result["failed"], 0)


if __name__ == "__main__":
    unittest.main()
