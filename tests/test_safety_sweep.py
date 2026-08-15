import unittest
from datetime import datetime, timezone

from new_core.safety_sweep import build_sweep_query, next_retry_delay


class SafetySweepTests(unittest.TestCase):
    def test_query_is_bounded_and_due_only(self):
        query = build_sweep_query(now=datetime(2026, 8, 15, tzinfo=timezone.utc), limit=500)
        self.assertEqual(query["limit"], 50)
        self.assertEqual(query["status"], "in.(PENDING,RETRY)")
        self.assertIn("lte.", query["run_at"])

    def test_retry_backoff_is_capped(self):
        self.assertEqual(next_retry_delay(0), 60)
        self.assertEqual(next_retry_delay(1), 300)
        self.assertEqual(next_retry_delay(2), 900)
        self.assertIsNone(next_retry_delay(3))


if __name__ == "__main__":
    unittest.main()
