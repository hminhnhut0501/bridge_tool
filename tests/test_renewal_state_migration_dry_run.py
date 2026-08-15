import unittest

from scripts.renewal_state_migration_dry_run import build_migration_plan


class RenewalStateMigrationDryRunTests(unittest.TestCase):
    def test_maps_legacy_states_without_writes(self):
        result = build_migration_plan(
            [{"id": "t1", "task_state": "running"}, {"id": "t2", "task_state": "blocked"}],
            [{"id": "g1", "group_state": "selected"}, {"id": "g2", "group_state": "unmapped"}],
        )
        self.assertEqual(result["task_mapping"]["running->processing"], 1)
        self.assertEqual(result["group_mapping"]["selected->processing"], 1)
        self.assertEqual(result["group_mapping"]["unmapped->review_required"], 1)
        self.assertEqual(result["write_count"], 0)
        self.assertEqual(result["telegram_mutation_count"], 0)

    def test_unknown_state_is_manual_review(self):
        result = build_migration_plan([], [{"id": "g1", "group_state": "future_state"}])
        self.assertEqual(result["manual_review"], {"group:future_state": 1})
        self.assertEqual(result["group_change_count"], 0)


if __name__ == "__main__":
    unittest.main()
