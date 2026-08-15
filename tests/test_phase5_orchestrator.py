import asyncio
import unittest
from datetime import datetime

from adapters.in_memory import FakeMembershipGateway, FixedClock, InMemoryKickTaskRepository, InMemoryOrderRepository
from new_core.orchestrator import RenewalRuntime, run_renewal_cycle


def parse_dt(value):
    return datetime.fromisoformat(str(value)) if value else None


class Phase5OrchestratorTests(unittest.TestCase):
    def _runtime(self, *, orders, group_tasks=None, membership=None):
        return RenewalRuntime(
            orders=InMemoryOrderRepository(orders=orders),
            tasks=InMemoryKickTaskRepository(group_tasks=group_tasks or []),
            membership=membership or FakeMembershipGateway(),
            clock=FixedClock(datetime(2026, 8, 15, 12, 0)),
            parse_datetime=parse_dt,
            active_order_check=lambda *_: False,
        )

    def test_cycle_runs_expiry_before_kick(self):
        runtime = self._runtime(
            orders=[{"order_id": "o1", "telegram_user_id": "42", "plan_name": "VIP", "status": "PAID", "expire_at": "2026-08-15T11:00:00"}],
            membership=FakeMembershipGateway(presence={("-1001", "42"): True}),
        )
        runtime.tasks.group_tasks.append({"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "pending"})

        result = asyncio.run(run_renewal_cycle(runtime))

        self.assertEqual(result.expiry.reconciled, 1)
        self.assertEqual(result.kick.kicked, 1)
        self.assertEqual(runtime.orders.orders[0]["status"], "EXPIRED")

    def test_expiry_failure_stops_before_kick(self):
        class BrokenOrders:
            def list_expiry_candidates(self, *, before, limit):
                raise RuntimeError("orders unavailable")

        runtime = RenewalRuntime(
            orders=BrokenOrders(),
            tasks=InMemoryKickTaskRepository(),
            membership=FakeMembershipGateway(),
            clock=FixedClock(datetime(2026, 8, 15, 12, 0)),
            parse_datetime=parse_dt,
            active_order_check=lambda *_: False,
        )
        result = asyncio.run(run_renewal_cycle(runtime))
        self.assertIn("orders unavailable", result.expiry_error)
        self.assertIsNone(result.kick)

    def test_kick_failure_keeps_expiry_result(self):
        runtime = self._runtime(
            orders=[{"order_id": "o1", "telegram_user_id": "42", "plan_name": "VIP", "status": "PAID", "expire_at": "2026-08-15T11:00:00"}],
            group_tasks=[{"id": "g1", "order_id": "o1", "telegram_user_id": "42", "group_id": "-1001", "group_state": "pending"}],
        )
        runtime = RenewalRuntime(
            orders=runtime.orders,
            tasks=runtime.tasks,
            membership=None,
            clock=runtime.clock,
            parse_datetime=runtime.parse_datetime,
            active_order_check=runtime.active_order_check,
        )
        result = asyncio.run(run_renewal_cycle(runtime))
        self.assertEqual(result.expiry.reconciled, 1)
        self.assertEqual(result.kick.retry_scheduled, 1)


if __name__ == "__main__":
    unittest.main()
