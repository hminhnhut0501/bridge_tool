#!/usr/bin/env python3
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace

import config_utils
import processor
import renewal_utils
import sale_utils
import support_utils
import web_backend
from config_aliases import canonical_config_key, config_write_items
from license_utils import load_license_plan_mapping
from renewal_utils import build_early_renew_block, build_early_renew_offer


class FakeDb:
    def __init__(self, values: dict[str, str]):
        self.values = values

    def get_config(self, key, default=""):
        return self.values.get(key, default)

    def reload_config(self, force=False):
        return None


@dataclass
class FakeStore:
    order: dict
    paid_orders: list[dict] = field(default_factory=list)
    license_records: list[dict] = field(default_factory=list)
    support_events: list[dict] = field(default_factory=list)
    mark_paid_calls: list[tuple] = field(default_factory=list)
    patch_calls: list[tuple] = field(default_factory=list)

    enabled: bool = True

    def get_order(self, order_id):
        return dict(self.order)

    def list_paid_orders_for_user(self, user_id, limit=200):
        return list(self.paid_orders)

    def mark_order_paid(self, order_id, paid_at, expire_at):
        self.mark_paid_calls.append((str(order_id), paid_at, expire_at))
        self.order["status"] = "PAID"
        self.order["paid_at"] = paid_at
        self.order["expire_at"] = expire_at

    def patch_order(self, order_id, payload):
        self.patch_calls.append((str(order_id), dict(payload)))
        self.order.update(payload)
        return dict(self.order)

    def consume_coupon_for_order(self, order):
        return None

    def list_scheduler_orders(self, limit=5000):
        return [dict(self.order)]

    def order_to_sheet_row(self, order):
        return [
            str(order.get("order_id") or ""),
            str(order.get("telegram_user_id") or ""),
            str(order.get("full_name") or "Combo Tester"),
            str(order.get("plan_name") or ""),
            str(order.get("amount") or 0),
            str(order.get("status") or ""),
            str(order.get("paid_at") or ""),
            str(order.get("expire_at") or ""),
            "",
            "",
            "",
            "",
            str(order.get("coupon_code") or ""),
            str(order.get("payment_currency") or "VND"),
            str(order.get("payment_provider") or "PAYOS"),
            {},
        ]

    def list_support_events(self, limit=5000):
        return list(self.support_events)

    def record_support_event(self, event_type, user_id, **kwargs):
        self.support_events.append({"event_type": event_type, "telegram_user_id": str(user_id), **kwargs})

    def list_license_records(self, limit=1000):
        return list(self.license_records)

    def update_license_record(self, license_key, payload):
        for row in self.license_records:
            if str(row.get("license_key") or "").upper() == str(license_key).upper():
                row.update(payload)
                return row
        raise KeyError(license_key)

    def record_license_audit(self, payload):
        self.support_events.append(dict(payload))


class FakeBot:
    def __init__(self):
        self.messages = []
        self.invites = []

    async def create_chat_invite_link(self, chat_id, **kwargs):
        self.invites.append(str(chat_id))
        return SimpleNamespace(invite_link=f"https://t.me/+{chat_id}")

    async def unban_chat_member(self, **kwargs):
        return None

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)
        return SimpleNamespace(message_id=len(self.messages), chat=SimpleNamespace(id=kwargs.get("chat_id")))


async def main():
    fake_db = FakeDb(
        {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "GROUP_COUNT": "2",
            "ID_G1": "-1001",
            "BTN_G1": "Prime",
            "ID_G2": "-1002",
            "BTN_G2": "Asia",
            "PLAN_COMBO_30D": "Combo 30 Ngày",
            "PLAN_COMBO_LIFE": "Combo Trọn Đời",
            "PRICE_COMBO_30D": "99000",
            "PRICE_COMBO_LIFE": "499000",
            "PRICE_COMBO_30D_USD": "4.99",
            "PRICE_COMBO_LIFE_USD": "19.99",
            "EARLY_RENEW_ENABLED": "ON",
            "EARLY_RENEW_DAYS": "3",
            "EARLY_RENEW_DISCOUNT_PERCENT": "10",
            "REMINDER_DAYS": "3",
            "REMINDER_ENABLED": "ON",
            "MSG_EARLY_RENEW_OFFER": "🔥 <b>ƯU ĐÃI GIA HẠN SỚM</b>\nGói hiện tại: <b>{plan}</b>\nGiá gốc: <s>{old_price}</s>\nGiá gia hạn sớm: <b>{renew_price}</b> (-{discount_percent}%)\n⏳ Còn lại: <b>{countdown}</b>",
            "MSG_LICENSE_REMINDER": "⏰ License <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa.",
            "MSG_LICENSE_REVOKED": "⛔ License <b>{plan}</b> của bạn đã bị thu hồi.",
            "BTN_LICENSE_RENEW": "🔄 Gia hạn license",
        }
    )
    fake_store = FakeStore(
        order={
            "order_id": "CMB-001",
            "telegram_user_id": "42",
            "full_name": "Combo Tester",
            "plan_name": "Combo 30 Ngày - Prime",
            "amount": 99000,
            "status": "PENDING",
            "coupon_code": "",
            "payment_currency": "VND",
            "payment_provider": "PAYOS",
        },
        paid_orders=[{
            "order_id": "CMB-OLD",
            "telegram_user_id": "42",
            "plan_name": "Combo 30 Ngày - Prime",
            "status": "PAID",
            "expire_at": "2026-06-20 12:00:00",
        }],
        license_records=[{
            "license_key": "LIC-COMBO-1234",
            "telegram_user_id": "42",
            "order_id": "CMB-LIC-001",
            "plan_code": "COMBO_30D",
            "plan_slug": "combo-30d",
            "status": "active",
            "is_lifetime": False,
            "expires_at": "2026-07-30 12:00:00",
            "source": "web",
            "raw_data": {},
        }],
    )
    fake_bot = FakeBot()

    original = {
        "processor_db": processor.db,
        "processor_store": processor.supabase_store,
        "processor_bot": processor.bot,
        "processor_now": processor.now_local,
        "processor_t": processor.t,
        "processor_support": processor.add_support_join_button,
        "processor_unmute": processor.unmute_member,
        "processor_record": processor.record_support_event,
        "processor_resolve_plan_groups": processor.resolve_plan_groups,
        "web_db": web_backend.db,
        "web_store": web_backend.supabase_store,
        "web_bot": web_backend.bot,
        "web_now": web_backend.now_local,
        "config_db": config_utils.db,
        "sale_db": sale_utils.db,
        "support_db": support_utils.db,
    }
    try:
        processor.db = fake_db
        config_utils.db = fake_db
        renewal_utils.db = fake_db
        sale_utils.db = fake_db
        support_utils.db = fake_db
        processor.supabase_store = fake_store
        processor.bot = fake_bot
        processor.now_local = lambda: datetime(2026, 6, 4, 12, 0, 0)
        processor.t = lambda user_id, key, default="": default

        async def noop_support(*args, **kwargs):
            return ""

        async def noop_unmute(*args, **kwargs):
            return None

        processor.add_support_join_button = noop_support
        processor.unmute_member = noop_unmute
        processor.record_support_event = fake_store.record_support_event
        processor.resolve_plan_groups = lambda plan_name, plan_token="": [("-1001", "Prime"), ("-1002", "Asia")]

        await processor.process_successful_payment("CMB-001")
        assert fake_store.mark_paid_calls, "create order flow did not mark order paid"
        assert fake_bot.invites == ["-1001", "-1002"], fake_bot.invites

        offer = build_early_renew_offer(
            [
                "CMB-001",
                "42",
                "Combo Tester",
                "Combo 30 Ngày - Prime",
                "99000",
                "PAID",
                "2026-06-01 12:00:00",
                "2026-06-06 12:00:00",
            ],
            row_index=1,
            now=datetime(2026, 6, 4, 12, 0, 0),
            currency="VND",
        )
        assert offer, "renew flow did not produce an early renew offer"
        assert "ƯU ĐÃI GIA HẠN SỚM" in build_early_renew_block(offer)

        web_backend.db = fake_db
        web_backend.supabase_store = fake_store
        web_backend.bot = fake_bot
        web_backend.now_local = lambda: datetime(2026, 7, 27, 12, 0, 0)
        kick_rows = await web_backend.build_kick_audit_rows()
        assert kick_rows and kick_rows[0]["group_id"] in {"-1001", "-1002"}

        license_row = fake_store.license_records[0]
        reminder_stamp = datetime(2026, 7, 27, 12, 0, 0).isoformat(timespec="seconds")
        fake_store.update_license_record(license_row["license_key"], {"renew_reminder_sent_at": reminder_stamp, "raw_data": {"renew_reminder_sent_at": reminder_stamp}})
        fake_store.update_license_record(license_row["license_key"], {"revoked_notice_sent_at": reminder_stamp, "raw_data": {"revoked_notice_sent_at": reminder_stamp}})
        assert fake_store.license_records[0]["renew_reminder_sent_at"] == reminder_stamp
        assert fake_store.license_records[0]["revoked_notice_sent_at"] == reminder_stamp

        plan_map = load_license_plan_mapping(FakeDb({"LICENSE_PLAN_MAPPING_JSON": '{"COMBO_30D":{"groups":["-1001","-1002"],"duration_days":30,"allow_renew":true,"aliases":["ALL_ACCESS_30D"]},"COMBO_LIFE":{"groups":["-1001","-1002","-1003"],"duration_days":null,"allow_renew":false}}'}))
        assert "COMBO_30D" in plan_map and "ALL_ACCESS_30D" in plan_map

        print("OK: Combo lifecycle smoke-test passed")
        print("canonical:", canonical_config_key("PLAN_ALL_ACCESS_30D"))
        print("write keys:", [item["key"] for item in config_write_items("PLAN_ALL_ACCESS_30D", "Combo 30 Ngày")][:3])
    finally:
        processor.db = original["processor_db"]
        processor.supabase_store = original["processor_store"]
        processor.bot = original["processor_bot"]
        processor.now_local = original["processor_now"]
        processor.t = original["processor_t"]
        processor.add_support_join_button = original["processor_support"]
        processor.unmute_member = original["processor_unmute"]
        processor.record_support_event = original["processor_record"]
        processor.resolve_plan_groups = original["processor_resolve_plan_groups"]
        web_backend.db = original["web_db"]
        web_backend.supabase_store = original["web_store"]
        web_backend.bot = original["web_bot"]
        web_backend.now_local = original["web_now"]
        config_utils.db = original["config_db"]
        renewal_utils.db = original["config_db"]
        sale_utils.db = original["sale_db"]
        support_utils.db = original["support_db"]


if __name__ == "__main__":
    asyncio.run(main())
