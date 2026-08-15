import unittest

from new_core.legacy_sunset_gate import evaluate_sunset


class LegacySunsetGateTests(unittest.TestCase):
    def test_requires_observation_window(self):
        result = evaluate_sunset(observation_cycles=2)
        self.assertFalse(result.allowed)

    def test_blocks_on_any_safety_issue(self):
        result = evaluate_sunset(observation_cycles=3, unresolved_reviews=1, legacy_mutations=1)
        self.assertFalse(result.allowed)
        self.assertIn("unresolved_reviews", result.reasons)

    def test_allows_clean_sunset(self):
        result = evaluate_sunset(observation_cycles=3)
        self.assertTrue(result.allowed)


if __name__ == "__main__":
    unittest.main()
