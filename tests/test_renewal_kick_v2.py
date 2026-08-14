import os
import unittest
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import scheduler
import web_backend


class FakeRequest:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


class FakeDb:
    def reload_config(self, force=False):
        return None

    def get_config(self, key, default=""):
        config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
        }
        return config.get(key, default)


class FakeStore:
    enabled = True

    def __init__(self, orders=None, tasks=None, group_tasks=None, attempts=None):
        self.orders = orders or []
        self.tasks = tasks or []
        self.group_tasks = group_tasks or []
        self.attempts = attempts or []
        self.updated_tasks = []

    def list_scheduler_orders(self, limit=5000, updated_after=None):
        return list(self.orders)

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

    def list_renewal_kick_tasks_v2(self, limit=5000):
        return list(self.tasks)

    def _request(self, method, table, params=None):
        if table == "renewal_kick_group_tasks_v2":
            return list(self.group_tasks)
        if table == "renewal_kick_attempts_v2":
            return list(self.attempts)
        return []

    def update_renewal_kick_task_v2(self, task_id, payload):
        self.updated_tasks.append((task_id, payload))
        return payload


class RenewalKickV2Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = web_backend.db
        self.original_store = web_backend.supabase_store
        self.original_scheduler_db = scheduler.db
        self.original_plan_group_ids = scheduler.plan_group_ids
        self.original_user_active_group_ids = scheduler.user_active_group_ids
        self.original_group_label_for_chat_id = web_backend.group_label_for_chat_id
        self.original_now_local = web_backend.now_local
        web_backend.db = FakeDb()
        scheduler.db = web_backend.db
        web_backend.now_local = lambda: datetime(2026, 8, 13, 12, 0, 0)
        scheduler.plan_group_ids = lambda plan_name: ["-100111"] if "prime" in str(plan_name).lower() else ["-100222"]
        scheduler.user_active_group_ids = lambda user_id, order_id, users_data, now, plan_group_cache=None: set()
        web_backend.group_label_for_chat_id = lambda chat_id: f"group {chat_id}"

    def tearDown(self):
        web_backend.db = self.original_db
        web_backend.supabase_store = self.original_store
        scheduler.db = self.original_scheduler_db
        scheduler.plan_group_ids = self.original_plan_group_ids
        scheduler.user_active_group_ids = self.original_user_active_group_ids
        web_backend.group_label_for_chat_id = self.original_group_label_for_chat_id
        web_backend.now_local = self.original_now_local

    async def test_finalize_v2_state_machine(self):
        now = datetime(2026, 8, 13, 12, 0, 0)
        cases = [
            ("done", [{"group_state": "kicked"}], "done"),
            ("running", [{"group_state": "processing"}], "running"),
            ("review", [{"group_state": "review_required"}], "review_required"),
            ("blocked", [{"group_state": "blocked_active_order"}], "blocked"),
            ("failed", [{"group_state": "failed_terminal"}], "failed_terminal"),
        ]
        for name, groups, expected in cases:
            with self.subTest(name=name):
                next_state, payload = scheduler.finalize_renewal_kick_task_v2_from_groups({"metadata": {}}, groups, now)
                self.assertEqual(next_state, expected)
                self.assertEqual(payload["task_state"], expected)

    async def test_build_kick_audit_rows_uses_v2_task_and_group_state(self):
        store = FakeStore(
            orders=[{
                "order_id": "o1",
                "telegram_user_id": "42",
                "full_name": "Tester",
                "plan_name": "VIP 30 Ngày - Prime",
                "status": "EXPIRED",
                "expire_at": "2026-08-12 12:00:00",
            }],
            tasks=[{
                "id": "t1",
                "order_id": "o1",
                "task_state": "review_required",
                "last_error": "telegram_error",
                "metadata": {"reason": "manual_check"},
            }],
            group_tasks=[{
                "id": "g1",
                "task_id": "t1",
                "order_id": "o1",
                "group_id": "-100111",
                "group_state": "review_required",
                "review_reason": "manual_check",
                "last_error": "telegram_error",
                "metadata": {"reason": "manual_check"},
            }],
            attempts=[{
                "id": "a1",
                "task_id": "t1",
                "group_task_id": "g1",
                "attempt_no": 1,
                "attempt_state": "failed",
                "actor": "worker_v2",
                "action": "kick",
                "reason_code": "telegram_error",
                "error_message": "timeout",
                "metadata": {"retry": 1},
                "started_at": "2026-08-13 11:59:00",
            }],
        )
        web_backend.supabase_store = store
        scheduler.supabase_store = store
        scheduler.plan_group_ids = lambda plan_name: ["-100111"]
        scheduler.user_active_group_ids = lambda user_id, order_id, users_data, now, plan_group_cache=None: set()
        rows = await web_backend.build_kick_audit_rows()

        self.assertEqual(rows[0]["status"], "REVIEW_REQUIRED")
        self.assertEqual(rows[0]["status_label"], "Cần review")
        self.assertEqual(rows[0]["latest_error"], "telegram_error")
        self.assertFalse(rows[0]["needs_action"] is False and rows[0]["status"] == "REVIEW_REQUIRED")

    async def test_review_api_returns_single_row(self):
        task = {
            "id": "t1",
            "order_id": "o1",
            "telegram_user_id": "42",
            "task_state": "review_required",
        }
        store = FakeStore(tasks=[task], group_tasks=[{"task_id": "t1", "group_id": "-100111", "group_state": "review_required"}])
        web_backend.supabase_store = store

        result = await web_backend.admin_renewal_kick_v2_review(FakeRequest({"order_id": "o1", "telegram_user_id": "42", "action": "requeue"}))

        self.assertIn("data", result)
        self.assertIsInstance(result["data"], dict)
        self.assertEqual(result["data"]["task_state"], "queued")

    async def test_manual_order_delivery_text_uses_delivery_template(self):
        original_safe_db_config = web_backend.safe_db_config
        try:
            web_backend.safe_db_config = lambda key, default="": (
                "{success_text}\n\n{order_text}\n\n{links_text}\n\n{partial_text}\n\n{support_text}"
                if key == "MANUAL_ORDER_DELIVERY_TEMPLATE"
                else default
            )
            text = web_backend.build_manual_order_delivery_text({
                "order_id": "o1",
                "telegram_user_id": "42",
                "full_name": "Tester",
                "plan_name": "VIP 30 Ngày - Prime",
                "expire_at": "2026-08-13 12:00:00",
                "links_text": "LINKS",
                "partial_text": "PARTIAL",
                "support_text": "SUPPORT",
                "support_group_name": "Nhóm hỗ trợ",
                "support_link": "https://t.me/+abc",
            })
        finally:
            web_backend.safe_db_config = original_safe_db_config

        self.assertIn("Đơn của bạn đã được xác minh", text)
        self.assertIn("LINKS", text)
        self.assertIn("PARTIAL", text)
        self.assertIn("SUPPORT", text)

    async def test_manual_active_code_includes_support_text_when_available(self):
        original_safe_db_config = web_backend.safe_db_config
        original_create_support_invite_link = web_backend.create_support_invite_link
        original_safe_support_group_name = web_backend.safe_support_group_name
        try:
            web_backend.safe_db_config = lambda key, default="": (
                "{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}\n\n{links_text}\n\n{support_text}"
                if key == "MANUAL_ORDER_DELIVERY_TEMPLATE"
                else default
            )
            web_backend.safe_support_group_name = lambda default="Nhóm hỗ trợ": "Nhóm hỗ trợ"

            async def fake_create_support_invite_link(_user_id, force=False):
                return "https://t.me/+support", ""

            web_backend.create_support_invite_link = fake_create_support_invite_link
            result = await web_backend.admin_generate_manual_active_code(FakeRequest({
                "order_id": "o1",
                "telegram_user_id": "42",
                "full_name": "Tester",
                "plan_name": "VIP 30 Ngày - Prime",
                "expire_at": "2026-08-13 12:00:00",
                "expire_at_iso": "2026-08-13T12:00:00",
            }))
        finally:
            web_backend.safe_db_config = original_safe_db_config
            web_backend.create_support_invite_link = original_create_support_invite_link
            web_backend.safe_support_group_name = original_safe_support_group_name

        self.assertIn("Nhóm hỗ trợ", result["data"]["manual_order_text"])
        self.assertIn("https://t.me/+support", result["data"]["manual_order_text"])


if __name__ == "__main__":
    unittest.main()
