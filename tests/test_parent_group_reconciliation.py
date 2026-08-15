import unittest

from new_core.reconciliation import build_parent_group_reconciliation


class ParentGroupReconciliationTests(unittest.TestCase):
    def test_reports_orphans_missing_groups_and_user_mismatch(self):
        report = build_parent_group_reconciliation(
            orders=[{"order_id": "o1", "telegram_user_id": "42"}],
            tasks=[
                {"id": "t1", "order_id": "o1", "telegram_user_id": "42", "task_state": "processing"},
                {"id": "t2", "order_id": "o1", "telegram_user_id": "42", "task_state": "blocked"},
            ],
            groups=[
                {"id": "g1", "task_id": "t1", "telegram_user_id": "99", "group_id": "-100"},
                {"id": "g2", "task_id": "missing", "telegram_user_id": "42", "group_id": "-101"},
            ],
        )
        self.assertEqual(len(report["orphan_group_tasks"]), 1)
        self.assertEqual([row["task_id"] for row in report["tasks_without_groups"]], ["t2"])
        self.assertEqual(len(report["mismatched_group_users"]), 1)
        self.assertEqual(report["supabase_write_count"], 0)

    def test_reports_duplicate_group_key(self):
        report = build_parent_group_reconciliation(
            orders=[],
            tasks=[{"id": "t1", "order_id": "o1"}],
            groups=[
                {"id": "g1", "task_id": "t1", "group_id": "-100"},
                {"id": "g2", "task_id": "t1", "group_id": "-100"},
            ],
        )
        self.assertEqual(report["duplicate_group_keys"][0]["count"], 2)
