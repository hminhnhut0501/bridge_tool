import os
import unittest
from datetime import datetime, timedelta

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import scheduler
import support_utils
import config_utils

ORIGINAL_NOW_LOCAL = scheduler.now_local


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "SUPPORT_GROUP_ENABLED": "ON",
            "SUPPORT_GROUP_MUTE_ENABLED": "ON",
            "SUPPORT_GROUP_ID": "-100999",
            "SUPPORT_GROUP_GRACE_DAYS": "14",
            "BTN_G1": "Hang Cú Prime",
            "ID_G1": "-100111",
            "BTN_G2": "Hang Cú Boy",
            "ID_G2": "-100222",
            "BTN_G3": "Hang Cú Black",
            "ID_G3": "-100333",
            "BTN_G4": "Hang Cú Asia",
            "ID_G4": "-100444",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)


class FakeStore:
    enabled = True

    def __init__(self):
        self.events = []
        self.orders = []
        self.expired_orders = []

    def get_user_identity(self, telegram_user_id):
        return {}

    def latest_support_event(self, event_type, telegram_user_id=None, order_id=None, chat_id=None):
        matches = [
            event
            for event in self.events
            if event["event_type"] == event_type
            and (telegram_user_id is None or str(event.get("telegram_user_id")) == str(telegram_user_id))
            and (order_id is None or str(event.get("order_id")) == str(order_id))
            and (chat_id is None or str(event.get("chat_id")) == str(chat_id))
        ]
        return matches[-1] if matches else None

    def record_support_event(self, event_type, telegram_user_id=None, **kwargs):
        self.events.append({
            "event_type": event_type,
            "telegram_user_id": str(telegram_user_id),
            "created_at": kwargs.pop("created_at", datetime(2026, 5, 25, 12, 0, 0).isoformat()),
            **kwargs,
        })

    def list_scheduler_orders(self, limit=5000):
        return list(self.orders)

    def order_to_sheet_row(self, order):
        return [
            order.get("order_id", ""),
            order.get("telegram_user_id", ""),
            order.get("full_name", ""),
            order.get("plan_name", ""),
            order.get("amount", ""),
            order.get("status", ""),
            order.get("paid_at", ""),
            order.get("expire_at", ""),
            order.get("sale_id", ""),
            order.get("original_amount", ""),
            order.get("last_reminder_date", ""),
            order.get("expired_notice_at", ""),
        ]

    def mark_order_expired(self, order_id, expired_notice_at=None):
        self.expired_orders.append(str(order_id))


class FakeBot:
    def __init__(self):
        self.kicked = []
        self.present = {}

    async def get_chat_member(self, chat_id, user_id):
        present = self.present.get((str(chat_id), str(user_id)), True)

        class Member:
            status = "member" if present else "left"
            is_member = present

        return Member()

    async def ban_chat_member(self, chat_id, user_id):
        self.kicked.append((str(chat_id), str(user_id)))
        self.present[(str(chat_id), str(user_id))] = False

    async def unban_chat_member(self, chat_id, user_id):
        return None


class SchedulerLogicTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = FakeDb()
        self.store = FakeStore()
        self.bot = FakeBot()
        scheduler.db = self.db
        scheduler.supabase_store = self.store
        scheduler.bot = self.bot
        support_utils.db = self.db
        support_utils.supabase_store = self.store
        config_utils.db = self.db
        scheduler.record_support_event = support_utils.record_support_event
        self.muted = []
        self.unmuted = []

        async def fake_mute(chat_id, user_id):
            self.muted.append((str(chat_id), str(user_id)))

        async def fake_unmute(chat_id, user_id):
            self.unmuted.append((str(chat_id), str(user_id)))

        scheduler.mute_member = fake_mute
        scheduler.unmute_member = fake_unmute
        scheduler.recent_kicks.clear()

    def tearDown(self):
        scheduler.now_local = ORIGINAL_NOW_LOCAL

    async def test_expired_vip_kicks_only_expired_group_when_other_group_active(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        rows = [
            ["old", "42", "User", "VIP 1 ngày - Hang Cú Boy", "0", "PAID", "", "2026-05-24 12:00:00"],
            ["active", "42", "User", "VIP 30 Ngày - Hang Cú Asia", "0", "PAID", "", "2026-06-24 12:00:00"],
        ]

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-24 12:00:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100222"])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [("-100222", "42")])

    async def test_expired_vip_does_not_kick_group_retained_by_active_order(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        rows = [
            ["old", "42", "User", "VIP 1 ngày - Hang Cú Boy", "0", "PAID", "", "2026-05-24 12:00:00"],
            ["active", "42", "User", "VIP 30 Ngày - Hang Cú Boy", "0", "PAID", "", "2026-06-24 12:00:00"],
        ]

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-24 12:00:00", rows, now
        )

        self.assertEqual(expired_groups, [])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [])

    async def test_coupon_plan_matches_group_when_template_omits_prive_word(self):
        self.db.config["BTN_G4"] = "Hang Cú Privé Asia"
        now = datetime(2026, 5, 25, 21, 20, 0)
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "PAID", "", "2026-05-25 21:19:00"]]

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100444"])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [("-100444", "42")])

    async def test_recent_kick_event_prevents_duplicate_vip_kick(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "PAID", "", "2026-05-25 21:19:00"]]
        self.bot.present[("-100444", "42")] = True
        self.store.events.append({
            "event_type": "member_kicked",
            "telegram_user_id": "42",
            "chat_id": "-100444",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Asia",
            "created_at": now.isoformat(),
        })

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100444"])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [])
        self.assertEqual(len([event for event in self.store.events if event["event_type"] == "member_kicked"]), 1)

    async def test_recent_group_kick_prevents_duplicate_across_old_orders(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        rows = [
            ["old-a", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "EXPIRED", "", "2026-05-24 21:19:00"],
            ["old-b", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "EXPIRED", "", "2026-05-25 21:19:00"],
        ]
        self.bot.present[("-100444", "42")] = True
        self.store.events.append({
            "event_type": "member_kicked",
            "telegram_user_id": "42",
            "chat_id": "-100444",
            "order_id": "old-a",
            "plan_name": "VIP 1 ngày - Hang Cú Asia",
            "created_at": now.isoformat(),
        })

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old-b", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100444"])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [])
        self.assertEqual(len([event for event in self.store.events if event["event_type"] == "member_kicked"]), 1)

    async def test_active_renewal_prevents_rejoin_kick(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        rows = [
            ["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "EXPIRED", "", "2026-05-25 21:19:00"],
            ["active", "42", "User", "VIP 30 ngày - Hang Cú Asia", "0", "PAID", "", "2026-06-25 21:19:00"],
        ]
        self.bot.present[("-100444", "42")] = True
        self.store.events.append({
            "event_type": "member_kicked",
            "telegram_user_id": "42",
            "chat_id": "-100444",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Asia",
            "created_at": (now - timedelta(days=2)).isoformat(),
        })

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, [])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [])

    async def test_invalid_active_expire_prevents_auto_kick(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        rows = [
            ["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "EXPIRED", "", "2026-05-25 21:19:00"],
            ["active-bad-date", "42", "User", "VIP 30 ngày - Hang Cú Asia", "0", "PAID", "", "bad-date"],
        ]

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, [])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [])

    async def test_old_kick_event_allows_recheck_when_member_present(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "PAID", "", "2026-05-25 21:19:00"]]
        self.bot.present[("-100444", "42")] = True
        self.store.events.append({
            "event_type": "member_kicked",
            "telegram_user_id": "42",
            "chat_id": "-100444",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Asia",
            "created_at": (now - timedelta(days=2)).isoformat(),
        })

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100444"])
        self.assertEqual(errors, [])
        self.assertEqual(self.bot.kicked, [("-100444", "42")])
        self.assertEqual(self.store.events[-1]["raw_data"]["source"], "recheck_member_present")

    async def test_support_group_mutes_once_before_grace_kick(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Boy", "0", "EXPIRED", "", "2026-05-10 12:00:00"]]

        await scheduler.process_support_grace_for_expired_order("42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-10 12:00:00", rows, now)
        await scheduler.process_support_grace_for_expired_order("42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-10 12:00:00", rows, now)

        self.assertEqual(self.muted, [("-100999", "42")])
        self.assertEqual([event["event_type"] for event in self.store.events], ["member_muted"])
        self.assertEqual(self.bot.kicked, [])

    async def test_support_group_kicks_after_grace(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Boy", "0", "EXPIRED", "", "2026-05-01 12:00:00"]]
        self.store.events.append({
            "event_type": "member_muted",
            "telegram_user_id": "42",
            "chat_id": "-100999",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Boy",
            "created_at": (now - timedelta(days=15)).isoformat(),
        })

        await scheduler.process_support_grace_for_expired_order("42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-01 12:00:00", rows, now)

        self.assertEqual(self.bot.kicked, [("-100999", "42")])
        self.assertEqual(self.store.events[-1]["event_type"], "member_kicked")

    async def test_support_group_rejoin_after_kick_is_kicked_again(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Boy", "0", "EXPIRED", "", "2026-05-01 12:00:00"]]
        self.store.events.append({
            "event_type": "member_kicked",
            "telegram_user_id": "42",
            "chat_id": "-100999",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Boy",
            "created_at": (now - timedelta(days=1)).isoformat(),
        })
        self.bot.present[("-100999", "42")] = True

        await scheduler.process_support_grace_for_expired_order("42", "old", "VIP 1 ngày - Hang Cú Boy", "2026-05-01 12:00:00", rows, now)

        self.assertEqual(self.bot.kicked, [("-100999", "42")])
        self.assertEqual(self.store.events[-1]["raw_data"]["reason"], "support_rejoined_after_kick")

    async def test_unmapped_expired_plan_is_not_closed_or_notified(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        scheduler.now_local = lambda: now
        self.store.orders = [{
            "order_id": "unknown-plan",
            "telegram_user_id": "42",
            "full_name": "User",
            "plan_name": "VIP Mystery Group",
            "status": "PAID",
            "expire_at": "2026-05-24 12:00:00",
        }]

        await scheduler.check_expirations_professional()

        self.assertEqual(self.store.expired_orders, [])
        self.assertEqual(self.bot.kicked, [])
        self.assertFalse(any(event["event_type"] == "expired_notice_sent" for event in self.store.events))

    async def test_unmapped_already_expired_plan_does_not_mute_support(self):
        now = datetime(2026, 5, 25, 12, 0, 0)
        scheduler.now_local = lambda: now
        self.store.orders = [{
            "order_id": "unknown-expired",
            "telegram_user_id": "42",
            "full_name": "User",
            "plan_name": "VIP Mystery Group",
            "status": "EXPIRED",
            "expire_at": "2026-05-24 12:00:00",
        }]

        await scheduler.check_expirations_professional()

        self.assertEqual(self.muted, [])
        self.assertEqual(self.bot.kicked, [])


if __name__ == "__main__":
    unittest.main()
