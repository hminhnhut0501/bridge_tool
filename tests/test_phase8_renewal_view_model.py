import unittest
from datetime import datetime

from new_core.renewal_view_model import build_renewal_view_model


def parse_dt(value):
    return datetime.fromisoformat(str(value)) if value else None


class Phase8RenewalViewModelTests(unittest.TestCase):
    def test_view_model_is_task_first_and_has_stable_schema(self):
        result = build_renewal_view_model(
            [{"order_id": "o1", "telegram_user_id": "42", "full_name": "A", "plan_name": "VIP", "status": "EXPIRED", "expire_at": "2026-08-14T12:00:00"}],
            [{"id": "t1", "order_id": "o1", "task_state": "review_required", "review_reason": "confirm_unknown", "updated_at": "2026-08-15T12:00:00"}],
            [{"id": "g1", "task_id": "t1", "group_state": "review_required"}],
            [{"group_task_id": "g1", "attempt_state": "confirm_failed", "started_at": "2026-08-15T11:59:00"}],
            now=datetime(2026, 8, 15, 12, 0),
            parser=parse_dt,
        )
        row = result["rows"][0]
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(row["task_state"], "review_required")
        self.assertEqual(row["next_action"], "review")
        self.assertEqual(row["blocked_reason"], "confirm_unknown")
        self.assertEqual(row["last_attempt"]["attempt_state"], "confirm_failed")

    def test_active_order_is_retained_without_support_events(self):
        result = build_renewal_view_model(
            [{"order_id": "o1", "telegram_user_id": "42", "plan_name": "VIP", "status": "PAID", "expire_at": "2026-08-16T12:00:00"}],
            [{"id": "t1", "order_id": "o1", "task_state": "queued"}],
            [],
            [],
            now=datetime(2026, 8, 15, 12, 0),
            parser=parse_dt,
        )
        self.assertEqual(result["rows"][0]["order_state"], "active")
        self.assertEqual(result["rows"][0]["next_action"], "retain")
        self.assertEqual(result["rows"][0]["blocked_reason"], "active_order")


if __name__ == "__main__":
    unittest.main()
