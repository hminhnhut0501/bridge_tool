import unittest
from datetime import datetime

from renewal_admin_view_service import build_renewal_admin_view


def parse_dt(value):
    if value is None or value == "":
        return None
    return datetime.fromisoformat(str(value))


class RenewalAdminViewServiceTests(unittest.TestCase):
    def test_build_renewal_admin_view_filters_expired_and_summarizes_states(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        orders = [
            {
                "order_id": "o1",
                "telegram_user_id": "42",
                "full_name": "Tester",
                "plan_name": "VIP 30 Ngày",
                "status": "PAID",
                "expire_at": "2026-08-14T11:59:59",
            },
            {
                "order_id": "o2",
                "telegram_user_id": "99",
                "full_name": "Active",
                "plan_name": "VIP 30 Ngày",
                "status": "PAID",
                "expire_at": "2026-08-15T12:00:00",
            },
        ]
        tasks = [{
            "id": "t1",
            "order_id": "o1",
            "task_state": "queued",
            "updated_at": "2026-08-14T11:00:00",
            "last_transition_at": "2026-08-14T11:00:00",
            "last_error": "needs_retry",
            "review_reason": "needs_review",
        }]
        group_tasks = [
            {
                "id": "g1",
                "task_id": "t1",
                "order_id": "o1",
                "group_id": "-1001",
                "group_name": "Group 1",
                "group_state": "kicked",
                "last_error": "",
                "review_reason": "",
                "last_reason": "",
                "terminal_reason": "",
                "metadata": {"reason": "ok"},
            },
            {
                "id": "g2",
                "task_id": "t1",
                "order_id": "o1",
                "group_id": "-1002",
                "group_name": "Group 2",
                "group_state": "review_required",
                "last_error": "manual_check",
                "review_reason": "manual_check",
                "last_reason": "",
                "terminal_reason": "",
                "metadata": {"reason": "manual_check"},
            },
        ]
        attempts = [{
            "id": "a1",
            "task_id": "t1",
            "group_task_id": "g1",
            "order_id": "o1",
            "telegram_user_id": "42",
            "group_id": "-1001",
            "group_name": "Group 1",
            "attempt_no": 1,
            "attempt_state": "claimed",
            "action": "kick",
            "actor": "worker_v2",
            "reason_code": "kick_attempt",
            "error_code": None,
            "error_message": None,
            "started_at": "2026-08-14T11:05:00",
            "finished_at": None,
            "metadata": {},
        }]

        result = build_renewal_admin_view(orders, tasks, group_tasks, attempts, now, parser=parse_dt)

        self.assertEqual(result["summary"]["total"], 1)
        self.assertEqual(result["summary"]["needs_action"], 1)
        self.assertEqual(result["summary"]["review"], 1)
        self.assertEqual(result["rows"][0]["order_id"], "o1")
        self.assertEqual(result["rows"][0]["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["rows"][0]["task_state"], "queued")
        self.assertEqual(result["rows"][0]["group_count"], 2)
        self.assertEqual(result["rows"][0]["attempt_count"], 1)
        self.assertEqual(result["rows"][0]["groups"][1]["status"], "review_required")

    def test_build_renewal_admin_view_ignores_non_expired_orders(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        result = build_renewal_admin_view(
            [
                {
                    "order_id": "o1",
                    "telegram_user_id": "42",
                    "full_name": "Tester",
                    "plan_name": "VIP 30 Ngày",
                    "status": "PAID",
                    "expire_at": "2026-08-15T12:00:00",
                }
            ],
            [],
            [],
            [],
            now,
            parser=parse_dt,
        )

        self.assertEqual(result["rows"], [])
        self.assertEqual(result["summary"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
