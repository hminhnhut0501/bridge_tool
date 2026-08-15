import unittest

from scripts.final_product_gate import evaluate


BASE = {
    "duplicate_jobs": 0, "invalid_timed_entitlements": 0,
    "unsupported_kickable_entitlements": 0, "incorrect_kicks": 0,
    "legacy_mutations": 0, "data_loss_events": 0, "canary_cycles": 3,
    "frontend_typecheck": 1, "frontend_build": 1, "backend_tests": 1,
}


class FinalProductGateTests(unittest.TestCase):
    def test_clean_report_allows_release(self):
        self.assertEqual(evaluate(BASE), (True, []))

    def test_any_safety_failure_blocks_release(self):
        report = dict(BASE, incorrect_kicks=1)
        allowed, reasons = evaluate(report)
        self.assertFalse(allowed)
        self.assertIn("incorrect_kicks != 0", reasons)


if __name__ == "__main__":
    unittest.main()
