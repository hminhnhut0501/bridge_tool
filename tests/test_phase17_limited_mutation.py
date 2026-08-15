import asyncio
import unittest
from datetime import datetime

from adapters.in_memory import FakeMembershipGateway, FixedClock, InMemoryKickTaskRepository
from scheduler_new_core_runtime import CohortTaskRepository, run_limited_mutation_cycle


class Phase17LimitedMutationTests(unittest.TestCase):
    def test_cohort_filters_by_user_or_order(self):
        repo = InMemoryKickTaskRepository(group_tasks=[
            {"id": "g1", "telegram_user_id": "1", "order_id": "o1"},
            {"id": "g2", "telegram_user_id": "2", "order_id": "o2"},
        ])
        filtered = CohortTaskRepository(repo, user_ids={"1"})
        self.assertEqual([row["id"] for row in filtered.list_due_group_tasks(before=datetime.now(), limit=10)], ["g1"])

    def test_empty_cohort_is_rejected(self):
        async def run():
            with self.assertRaises(ValueError):
                await run_limited_mutation_cycle(
                    store=object(), bot=object(), clock=FixedClock(datetime.now()),
                    active_order_check=lambda *_: False,
                )
        asyncio.run(run())

    def test_limited_mutation_only_processes_selected_user(self):
        class Store:
            def list_due_renewal_kick_group_tasks_v2(self, **kwargs):
                return [{"id": "g1", "telegram_user_id": "1", "order_id": "o1", "group_id": "g1", "group_state": "pending"}]

            def update_renewal_kick_group_task_v2(self, task_id, payload):
                return [{"id": task_id, **payload}]

        class Bot:
            async def get_chat_member(self, **kwargs):
                return type("Member", (), {"status": "member"})()

            async def ban_chat_member(self, **kwargs):
                self.banned = True

            async def unban_chat_member(self, **kwargs):
                self.unbanned = True

        result = asyncio.run(run_limited_mutation_cycle(
            store=Store(), bot=Bot(), clock=FixedClock(datetime.now()),
            active_order_check=lambda *_: False, cohort_user_ids={"1"},
        ))
        self.assertEqual(result["mode"], "limited_mutation")
        self.assertEqual(result["result"].kicked, 1)


if __name__ == "__main__":
    unittest.main()
