import unittest

from renewal_baseline import build_renewal_baseline


class RenewalBaselineTests(unittest.TestCase):
    def test_builds_read_only_migration_snapshot(self):
        result = build_renewal_baseline(
            orders=[{"status": "PAID"}, {"status": "EXPIRED"}],
            tasks=[{"task_state": "review_required", "locked_at": "x"}],
            group_tasks=[{"group_state": "pending"}],
            support_events=[{"event_type": "member_kicked"}],
        )
        self.assertEqual(result["orders_by_status"], {"PAID": 1, "EXPIRED": 1})
        self.assertEqual(result["review_required_count"], 1)
        self.assertEqual(result["totals"]["support_events"], 1)


if __name__ == "__main__":
    unittest.main()
