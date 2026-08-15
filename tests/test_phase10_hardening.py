import unittest
from datetime import datetime
from types import SimpleNamespace

from new_core.observability import find_stale_tasks, metrics_from_cycle, structured_cycle_log, validate_feature_flags


class Phase10HardeningTests(unittest.TestCase):
    def test_cycle_metrics_and_structured_log(self):
        result = SimpleNamespace(
            expiry=SimpleNamespace(scanned=10, reconciled=3, tasks_created=2),
            kick=SimpleNamespace(scanned=4, kicked=2, blocked=1, review_required=1, retry_scheduled=0, failed=0),
            expiry_error="",
            kick_error="",
        )
        metrics = metrics_from_cycle(result)
        self.assertEqual(metrics.reconciled_orders, 3)
        log = structured_cycle_log(result, correlation_id="c1", occurred_at=datetime(2026, 8, 15, 12, 0))
        self.assertTrue(log["ok"])
        self.assertEqual(log["metrics"]["kick_sent"], 2)

    def test_stale_tasks_include_bad_or_missing_timestamps(self):
        now = datetime(2026, 8, 15, 12, 0)
        tasks = [
            {"id": "old", "group_state": "waiting_confirm", "last_transition_at": "2026-08-15T11:00:00"},
            {"id": "bad", "group_state": "processing", "last_transition_at": "bad-date"},
            {"id": "fresh", "group_state": "processing", "last_transition_at": "2026-08-15T11:59:00"},
        ]
        self.assertEqual([row["id"] for row in find_stale_tasks(tasks, now=now, stale_minutes=15)], ["old", "bad"])

    def test_feature_flags_are_strictly_validated(self):
        self.assertEqual(validate_feature_flags({"A": "ON", "B": "off", "C": "1"}), [])
        self.assertEqual(validate_feature_flags({"A": "maybe"}), ["A: invalid boolean value"])


if __name__ == "__main__":
    unittest.main()
