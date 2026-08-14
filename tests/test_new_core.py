import unittest
from datetime import datetime

from new_core.expiry import days_until_expire, is_order_active, is_order_expired
from new_core.kick import classify_kick_state, should_queue_kick
from new_core.workflow import plan_expired_order_actions
from new_core.state import normalize_kick_state, normalize_order_state


def parse_dt(value):
    if value is None or value == "":
        return None
    return datetime.fromisoformat(str(value))


class NewCoreTests(unittest.TestCase):
    def test_order_expired_when_paid_and_past_expire_at(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T11:59:59"}

        self.assertTrue(is_order_expired(order, now, parser=parse_dt))
        self.assertFalse(is_order_active(order, now, parser=parse_dt))

    def test_order_active_when_paid_and_not_yet_expired(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-15T12:00:00"}

        self.assertTrue(is_order_active(order, now, parser=parse_dt))
        self.assertFalse(is_order_expired(order, now, parser=parse_dt))
        self.assertEqual(days_until_expire(order, now, parser=parse_dt), 1)

    def test_lifetime_order_stays_active_and_never_expired(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        order = {"status": "PAID", "plan_name": "SVIP Trọn Đời", "expire_at": "2020-01-01T00:00:00"}

        self.assertTrue(is_order_active(order, now, parser=parse_dt))
        self.assertFalse(is_order_expired(order, now, parser=parse_dt))

    def test_non_paid_order_is_neither_active_nor_expired(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        order = {"status": "PENDING", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-15T12:00:00"}

        self.assertFalse(is_order_active(order, now, parser=parse_dt))
        self.assertFalse(is_order_expired(order, now, parser=parse_dt))

    def test_plan_expired_order_actions_returns_queue_and_reconcile(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T11:59:59"}

        result = plan_expired_order_actions(order, now, parser=parse_dt)

        self.assertEqual(result, {"queue_kick": True, "reconcile": True, "reason": "expired"})

    def test_classify_kick_state_prefers_task_state_then_group_state(self):
        self.assertEqual(classify_kick_state(renewal_task={"task_state": "done"}), "done")
        self.assertEqual(classify_kick_state(group_task={"group_state": "processing"}), "processing")
        self.assertEqual(classify_kick_state(group_task={"group_state": "review_required"}), "review_required")
        self.assertEqual(classify_kick_state(support_event_state="pending"), "none")

    def test_should_queue_kick_uses_expiry_only(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        expired_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T11:59:59"}
        active_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T12:59:59"}

        self.assertTrue(should_queue_kick(expired_order, now, parser=parse_dt))
        self.assertFalse(should_queue_kick(active_order, now, parser=parse_dt))

    def test_state_contract_normalizes_expiry_and_kick_states(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        expired_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T11:59:59"}
        active_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T12:59:59"}

        self.assertEqual(normalize_order_state(expired_order, now, parser=parse_dt).state, "expired")
        self.assertEqual(normalize_order_state(active_order, now, parser=parse_dt).state, "active")
        self.assertEqual(normalize_kick_state(renewal_task={"task_state": "queued"}), "processing")
        self.assertEqual(normalize_kick_state(group_task={"group_state": "kicked"}), "done")
        self.assertEqual(normalize_kick_state(support_event_state="review_required"), "none")

    def test_state_contract_is_used_by_workflow_and_kick(self):
        now = datetime(2026, 8, 14, 12, 0, 0)
        expired_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T11:59:59"}
        active_order = {"status": "PAID", "plan_name": "VIP 30 Ngày", "expire_at": "2026-08-14T12:59:59"}

        self.assertEqual(classify_kick_state(renewal_task={"task_state": "blocked_active_order"}), "blocked")
        self.assertEqual(classify_kick_state(group_task={"group_state": "failed_terminal"}), "failed_terminal")
        self.assertEqual(plan_expired_order_actions(expired_order, now, parser=parse_dt), {"queue_kick": True, "reconcile": True, "reason": "expired"})
        self.assertEqual(plan_expired_order_actions(active_order, now, parser=parse_dt), {"queue_kick": False, "reconcile": False, "reason": "not_expired"})


if __name__ == "__main__":
    unittest.main()
