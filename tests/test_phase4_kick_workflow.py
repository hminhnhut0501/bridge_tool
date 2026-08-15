import asyncio
import unittest
from datetime import datetime

from adapters.in_memory import FakeMembershipGateway, FixedClock, InMemoryKickTaskRepository
from new_core.kick_workflow import process_due_kick_groups


class Phase4KickWorkflowTests(unittest.TestCase):
    def test_due_group_is_kicked_then_waits_for_confirmation(self):
        tasks = InMemoryKickTaskRepository(group_tasks=[
            {"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "pending"},
        ])
        membership = FakeMembershipGateway(presence={("-1001", "42"): True})

        result = asyncio.run(process_due_kick_groups(tasks, membership, FixedClock(datetime(2026, 8, 15, 12, 0)), active_order_check=lambda user, order, group: False))

        self.assertEqual(result.kicked, 1)
        self.assertEqual(tasks.group_tasks[0]["group_state"], "waiting_confirm")
        self.assertEqual(membership.actions, [("kick", "-1001", "42")])

    def test_confirmed_absence_resolves_group(self):
        tasks = InMemoryKickTaskRepository(group_tasks=[
            {"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "waiting_confirm"},
        ])
        membership = FakeMembershipGateway(presence={("-1001", "42"): False})

        result = asyncio.run(process_due_kick_groups(tasks, membership, FixedClock(datetime(2026, 8, 15, 12, 0)), active_order_check=lambda *_: False))

        self.assertEqual(result.kicked, 1)
        self.assertEqual(tasks.group_tasks[0]["group_state"], "kicked")

    def test_active_order_blocks_kick(self):
        tasks = InMemoryKickTaskRepository(group_tasks=[
            {"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "pending"},
        ])
        membership = FakeMembershipGateway(presence={("-1001", "42"): True})

        result = asyncio.run(process_due_kick_groups(tasks, membership, FixedClock(datetime(2026, 8, 15, 12, 0)), active_order_check=lambda *_: True))

        self.assertEqual(result.blocked, 1)
        self.assertEqual(tasks.group_tasks[0]["group_state"], "blocked_active_order")
        self.assertEqual(membership.actions, [])

    def test_unknown_confirmation_goes_to_review(self):
        tasks = InMemoryKickTaskRepository(group_tasks=[
            {"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "waiting_confirm"},
        ])
        membership = FakeMembershipGateway()

        result = asyncio.run(process_due_kick_groups(tasks, membership, FixedClock(datetime(2026, 8, 15, 12, 0)), active_order_check=lambda *_: False))

        self.assertEqual(result.review_required, 1)
        self.assertEqual(tasks.group_tasks[0]["group_state"], "review_required")


if __name__ == "__main__":
    unittest.main()
