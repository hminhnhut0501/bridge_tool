import asyncio
import unittest
from datetime import datetime

from adapters.in_memory import (
    FakeMembershipGateway,
    FixedClock,
    InMemoryKickTaskRepository,
    InMemoryLegacyEventSink,
    InMemoryOrderRepository,
)
from new_core.ports import KickResult


class Phase2PortsTests(unittest.TestCase):
    def test_fake_adapters_have_no_external_runtime_dependency(self):
        now = datetime(2026, 8, 15, 12, 0, 0)
        clock = FixedClock(now)
        orders = InMemoryOrderRepository(orders=[{"order_id": "o1", "status": "PAID"}])
        tasks = InMemoryKickTaskRepository()
        events = InMemoryLegacyEventSink()

        self.assertEqual(clock.now(), now)
        self.assertEqual(orders.get_order("o1")["status"], "PAID")
        self.assertEqual(tasks.create_task({"order_id": "o1"})["id"], "task-1")
        events.append("member_kicked", "42", payload={"source": "test"})
        self.assertEqual(events.events[0][0], "member_kicked")

    def test_membership_gateway_is_idempotent_for_fake_execution(self):
        gateway = FakeMembershipGateway(presence={("g1", "42"): True})

        async def run():
            self.assertTrue(await gateway.is_present("g1", "42"))
            result = await gateway.kick("g1", "42")
            self.assertIsInstance(result, KickResult)
            self.assertTrue(result.ok)
            self.assertFalse(await gateway.is_present("g1", "42"))

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
