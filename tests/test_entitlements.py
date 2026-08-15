import unittest
from datetime import datetime, timezone

from new_core.entitlements import project_order


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


class EntitlementProjectionTests(unittest.TestCase):
    def test_future_paid_order_is_active(self):
        result = project_order({
            "order_id": "o1", "telegram_user_id": "u1", "status": "PAID",
            "canonical_plan_family": "PRIME", "canonical_group_code": "PRIME",
            "canonical_duration": "DAYS:30", "expire_at": "2026-09-01T00:00:00+00:00",
        }, now=NOW)
        self.assertEqual(result["state"], "ACTIVE")

    def test_missing_expiry_is_review_not_active(self):
        result = project_order({
            "order_id": "o1", "status": "PAID", "canonical_plan_family": "PRIME",
            "canonical_group_code": "PRIME", "canonical_duration": "DAYS:30",
        }, now=NOW)
        self.assertEqual(result["state"], "REVIEW")

    def test_unsupported_plan_cannot_be_kicked(self):
        result = project_order({
            "order_id": "o1", "status": "EXPIRED", "canonical_plan_family": "UNSUPPORTED",
            "canonical_duration": "REVIEW", "expire_at": "2026-07-01T00:00:00+00:00",
        }, now=NOW)
        self.assertEqual(result["state"], "REVIEW")

    def test_cancelled_order_is_not_entitlement(self):
        result = project_order({"order_id": "o1", "status": "CANCELLED"}, now=NOW)
        self.assertEqual(result["state"], "CANCELLED")


if __name__ == "__main__":
    unittest.main()
