import unittest

from scripts.renewal_historical_repair_candidates import build_candidates


class HistoricalRepairCandidatesTests(unittest.TestCase):
    def test_only_absent_members_are_eligible_for_repair(self):
        report = build_candidates(
            {
                "contract": "renewal_state_ledger_v1",
                "integrity": {
                    "orders_without_task": ["o2"],
                    "tasks_without_order": [],
                    "groups_without_parent": ["g2"],
                    "stale_locked_tasks": ["t2"],
                    "duplicate_task_keys": [],
                    "duplicate_group_keys": [],
                },
            },
            {
                "rows": [
                    {"task_id": "t1", "outcome": "absent"},
                    {"task_id": "t3", "outcome": "unknown"},
                    {"task_id": "t4", "outcome": "present"},
                ]
            },
        )
        self.assertEqual([row["task_id"] for row in report["candidates"]["membership_absent"]], ["t1"])
        self.assertEqual([row["task_id"] for row in report["candidates"]["membership_unknown"]], ["t3"])
        self.assertEqual(report["policy"]["repairable_now"], "membership_absent only")
        self.assertEqual(report["supabase_write_count"], 0)
        self.assertEqual(report["telegram_mutation_count"], 0)
