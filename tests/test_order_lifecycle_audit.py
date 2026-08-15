import unittest
from datetime import datetime, timezone

from scripts.order_lifecycle_audit import build_report, classify_order


class OrderLifecycleAuditTests(unittest.TestCase):
    def test_detects_paid_expired_and_expired_future(self):
        now = datetime(2026, 8, 15, tzinfo=timezone.utc)
        self.assertEqual(classify_order({"status": "PAID", "expire_at": "2026-08-01T00:00:00+00:00", "canonical_duration": "DAYS:30", "canonical_plan_family": "PRIME"}, now=now), "PAID_BUT_EXPIRED_BY_DATE")
        self.assertEqual(classify_order({"status": "EXPIRED", "expire_at": "2026-09-01T00:00:00+00:00", "canonical_duration": "DAYS:30", "canonical_plan_family": "PRIME"}, now=now), "EXPIRED_BUT_FUTURE_DATE")

    def test_lifetime_without_expiry_is_valid(self):
        report = build_report([{"status": "PAID", "canonical_duration": "LIFETIME", "canonical_plan_family": "COMBO"}], now=datetime(2026, 8, 15, tzinfo=timezone.utc))
        self.assertEqual(report["counts"], {"LIFETIME_NO_EXPIRY": 1})
        self.assertEqual(report["write_count"], 0)
