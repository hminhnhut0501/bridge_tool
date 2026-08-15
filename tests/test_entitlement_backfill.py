import unittest
from datetime import datetime, timezone

from new_core.entitlement_backfill import build_backfill_rows


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


class EntitlementBackfillTests(unittest.TestCase):
    def test_backfills_verified_timed_order(self):
        rows = build_backfill_rows([{
            "order_id": "o1", "telegram_user_id": "u1", "status": "PAID",
            "canonical_plan_family": "PRIME", "canonical_duration": "DAYS:30",
            "canonical_group_code": "PRIME", "expire_at": "2026-09-01T00:00:00+00:00",
        }], now=NOW)
        self.assertEqual(rows[0]["state"], "ACTIVE")
        self.assertEqual(rows[0]["source_quality"], "VERIFIED")

    def test_skips_cancelled_and_ambiguous_rows(self):
        rows = build_backfill_rows([
            {"order_id": "cancel", "status": "CANCELLED", "canonical_plan_family": "PRIME", "canonical_duration": "DAYS:30", "canonical_group_code": "PRIME"},
            {"order_id": "review", "status": "EXPIRED", "canonical_plan_family": "UNSUPPORTED", "canonical_duration": "REVIEW", "canonical_group_code": ""},
        ], now=NOW)
        self.assertEqual(rows, [])

    def test_skips_timed_order_without_expiry(self):
        rows = build_backfill_rows([{
            "order_id": "o1", "status": "PAID", "canonical_plan_family": "PRIME",
            "canonical_duration": "DAYS:30", "canonical_group_code": "PRIME",
        }], now=NOW)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
