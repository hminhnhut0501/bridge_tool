import unittest

from new_core.state_ledger import build_state_ledger


class StateLedgerTests(unittest.TestCase):
    def test_ledger_is_independent_from_support_events(self):
        report = build_state_ledger(
            orders=[{"order_id": "o1", "status": "EXPIRED"}, {"order_id": "o2", "status": "PAID"}],
            tasks=[{"id": "t1", "order_id": "o1", "telegram_user_id": "42", "task_state": "running"}],
            groups=[{"id": "g1", "task_id": "t1", "group_id": "-100", "group_state": "processing"}],
            attempts=[],
        )
        self.assertFalse(report["support_events_used"])
        self.assertEqual(report["integrity"]["orders_without_task"], ["o2"])
        self.assertEqual(report["tasks_by_state"], {"processing": 1})

    def test_ledger_reports_orphans_and_duplicates(self):
        report = build_state_ledger(
            orders=[{"order_id": "o1", "status": "PAID"}],
            tasks=[
                {"id": "t1", "order_id": "o1", "telegram_user_id": "42", "task_state": "done"},
                {"id": "t2", "order_id": "o1", "telegram_user_id": "42", "task_state": "review_required"},
            ],
            groups=[{"id": "g1", "task_id": "missing", "group_id": "-100", "group_state": "blocked_active_order"}],
            attempts=[{"attempt_state": "kicked"}],
        )
        self.assertEqual(report["integrity"]["groups_without_parent"], ["missing"])
        self.assertEqual(report["integrity"]["duplicate_task_keys"][0]["count"], 2)
        self.assertEqual(report["attempts_by_state"], {"done": 1})
