import asyncio
import unittest
from datetime import datetime

from scheduler_new_core_runtime import run_read_only_cycle


class Store:
    def __init__(self):
        self.writes = 0

    def list_scheduler_orders(self, limit=5000):
        return []

    def list_renewal_kick_tasks_v2(self, limit=5000):
        return []

    def list_due_renewal_kick_group_tasks_v2(self, limit=10000):
        return [{"telegram_user_id": "42", "order_id": "o1", "group_id": "g1"}]


class Bot:
    async def get_chat_member(self, **kwargs):
        class Member:
            status = "member"
        return Member()

    async def ban_chat_member(self, **kwargs):
        raise AssertionError("read-only canary must not ban")

    async def unban_chat_member(self, **kwargs):
        raise AssertionError("read-only canary must not unban")


class Clock:
    def now(self):
        return datetime(2026, 8, 15, 12, 0)


class Phase16ReadOnlyCanaryTests(unittest.TestCase):
    def test_read_only_cycle_reads_membership_without_mutation(self):
        result = asyncio.run(
            run_read_only_cycle(
                store=Store(),
                bot=Bot(),
                clock=Clock(),
                active_order_check=lambda *_: False,
            )
        )
        self.assertEqual(result["mode"], "read_only")
        self.assertEqual(result["counts"]["present"], 1)
        self.assertEqual(result["supabase_write_count"], 0)
        self.assertEqual(result["telegram_mutation_count"], 0)


if __name__ == "__main__":
    unittest.main()
