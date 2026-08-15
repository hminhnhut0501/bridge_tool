import unittest

from new_core.state_machine import (
    InvalidStateTransition,
    transition_kick_group,
    transition_kick_task,
    transition_order,
)


class Phase1StateMachineTests(unittest.TestCase):
    def test_order_expiry_transition_is_allowed(self):
        result = transition_order("active", "expired")
        self.assertEqual((result.entity, result.previous, result.next), ("order", "active", "expired"))

    def test_order_reactivation_is_explicitly_allowed_for_renewal(self):
        self.assertEqual(transition_order("expired", "active").next, "active")

    def test_kick_task_happy_path(self):
        self.assertEqual(transition_kick_task("queued", "processing").next, "processing")
        self.assertEqual(transition_kick_task("processing", "waiting_confirm").next, "waiting_confirm")
        self.assertEqual(transition_kick_task("waiting_confirm", "done").next, "done")

    def test_kick_group_retry_path(self):
        self.assertEqual(transition_kick_group("processing", "retry_scheduled").next, "retry_scheduled")
        self.assertEqual(transition_kick_group("retry_scheduled", "processing").next, "processing")

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(InvalidStateTransition):
            transition_kick_task("done", "processing")
        with self.assertRaises(InvalidStateTransition):
            transition_kick_group("kicked", "pending")
        with self.assertRaises(InvalidStateTransition):
            transition_order("active", "not-a-state")


if __name__ == "__main__":
    unittest.main()
