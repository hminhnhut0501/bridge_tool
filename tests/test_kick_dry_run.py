import unittest
from datetime import datetime, timezone

from new_core.kick_dry_run import evaluate_dry_run


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


class KickDryRunTests(unittest.TestCase):
    def test_old_expiry_is_blocked_by_new_active_order(self):
        rows = [
            {"source_order_id": "old", "telegram_user_id": "42", "group_code": "PRIME", "state": "EXPIRED", "source_quality": "VERIFIED", "expires_at": "2026-08-01T00:00:00+00:00"},
            {"source_order_id": "new", "telegram_user_id": "42", "group_code": "PRIME", "state": "ACTIVE", "source_quality": "VERIFIED", "expires_at": "2026-09-01T00:00:00+00:00"},
        ]
        report = evaluate_dry_run(rows, now=NOW)
        self.assertEqual(report["action_counts"], {"BLOCK": 1})
        self.assertEqual(report["supabase_write_count"], 0)

    def test_verified_expired_order_is_kick_candidate(self):
        rows = [{"source_order_id": "old", "telegram_user_id": "42", "group_code": "PRIME", "state": "EXPIRED", "source_quality": "VERIFIED", "expires_at": "2026-08-01T00:00:00+00:00"}]
        report = evaluate_dry_run(rows, now=NOW)
        self.assertEqual(report["action_counts"], {"KICK": 1})
        self.assertEqual(report["telegram_mutation_count"], 0)

    def test_unmapped_expired_order_is_review(self):
        rows = [{"source_order_id": "old", "telegram_user_id": "42", "group_code": None, "state": "EXPIRED", "source_quality": "REVIEW", "expires_at": "2026-08-01T00:00:00+00:00"}]
        report = evaluate_dry_run(rows, now=NOW)
        self.assertEqual(report["action_counts"], {"REVIEW": 1})


if __name__ == "__main__":
    unittest.main()
