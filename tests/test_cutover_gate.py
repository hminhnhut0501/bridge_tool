import unittest

from new_core.cutover_gate import evaluate_cutover
from new_core.mutation_gate import MutationGate


class CutoverGateTests(unittest.TestCase):
    def test_blocks_when_canary_has_review(self):
        result = evaluate_cutover({"action_counts": {"WOULD_KICK": 2, "REVIEW": 1}}, gate=MutationGate(enabled=True))
        self.assertFalse(result.allowed)
        self.assertIn("canary_review_remaining", result.reasons)

    def test_allows_clean_limited_cutover(self):
        result = evaluate_cutover({"action_counts": {"WOULD_KICK": 2, "ALREADY_ABSENT": 1}}, gate=MutationGate(enabled=True))
        self.assertTrue(result.allowed)

    def test_blocks_missing_groups_or_duplicates(self):
        result = evaluate_cutover({"action_counts": {}}, duplicate_jobs=1, missing_group_ids=2, gate=MutationGate(enabled=True))
        self.assertFalse(result.allowed)
        self.assertEqual(set(result.reasons), {"duplicate_jobs", "missing_group_ids"})


if __name__ == "__main__":
    unittest.main()
