import unittest

from new_core.worker_metrics import WorkerMetrics, metrics_safe_to_cutover


class WorkerMetricsTests(unittest.TestCase):
    def test_metrics_have_stable_names(self):
        metrics = WorkerMetrics()
        metrics.increment("jobs_done", 2)
        self.assertEqual(metrics.snapshot()["jobs_done"], 2)

    def test_unknown_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            WorkerMetrics().increment("legacy_events")

    def test_cutover_requires_no_duplicates_or_rate_limits(self):
        self.assertTrue(metrics_safe_to_cutover({"duplicate_jobs": 0, "telegram_rate_limit": 0}))
        self.assertFalse(metrics_safe_to_cutover({"duplicate_jobs": 1, "telegram_rate_limit": 0}))


if __name__ == "__main__":
    unittest.main()
