import unittest
from datetime import datetime

from adapters.in_memory import FixedClock, InMemoryKickTaskRepository, InMemoryOrderRepository
from new_core.expiry_workflow import reconcile_expired_orders


def parse_dt(value):
    return datetime.fromisoformat(str(value)) if value else None


class Phase3ExpiryWorkflowTests(unittest.TestCase):
    def test_paid_expired_order_is_reconciled_and_queued_once(self):
        now = datetime(2026, 8, 15, 12, 0, 0)
        orders = InMemoryOrderRepository(
            orders=[
                {
                    "order_id": "o1",
                    "telegram_user_id": "42",
                    "plan_name": "VIP 30 Ngày",
                    "status": "PAID",
                    "expire_at": "2026-08-15T11:59:59",
                }
            ]
        )
        tasks = InMemoryKickTaskRepository()

        result = reconcile_expired_orders(orders, tasks, FixedClock(now), parser=parse_dt)

        self.assertEqual(result.reconciled, 1)
        self.assertEqual(result.tasks_created, 1)
        self.assertEqual(orders.orders[0]["status"], "EXPIRED")
        self.assertEqual(tasks.tasks[0]["task_state"], "queued")

        second = reconcile_expired_orders(orders, tasks, FixedClock(now), parser=parse_dt)
        self.assertEqual(second.reconciled, 0)
        self.assertEqual(second.tasks_created, 0)
        self.assertEqual(second.tasks_existing, 1)

    def test_active_and_lifetime_orders_are_not_reconciled(self):
        now = datetime(2026, 8, 15, 12, 0, 0)
        orders = InMemoryOrderRepository(
            orders=[
                {"order_id": "active", "telegram_user_id": "1", "status": "PAID", "plan_name": "VIP", "expire_at": "2026-08-16T12:00:00"},
                {"order_id": "life", "telegram_user_id": "2", "status": "PAID", "plan_name": "SVIP Trọn Đời", "expire_at": "2020-01-01T00:00:00"},
            ]
        )
        tasks = InMemoryKickTaskRepository()

        result = reconcile_expired_orders(orders, tasks, FixedClock(now), parser=parse_dt)

        self.assertEqual(result.expired, 0)
        self.assertEqual(result.tasks_created, 0)
        self.assertEqual(orders.updates, [])

    def test_malformed_order_identity_is_not_written(self):
        now = datetime(2026, 8, 15, 12, 0, 0)
        orders = InMemoryOrderRepository(
            orders=[{"status": "EXPIRED", "plan_name": "VIP", "expire_at": "2026-08-14T12:00:00"}]
        )
        result = reconcile_expired_orders(orders, InMemoryKickTaskRepository(), FixedClock(now), parser=parse_dt)
        self.assertEqual(result.invalid, 1)

    def test_group_planner_expands_parent_task(self):
        now = datetime(2026, 8, 15, 12, 0, 0)
        orders = InMemoryOrderRepository(orders=[
            {"order_id": "o1", "telegram_user_id": "42", "plan_name": "VIP", "status": "PAID", "expire_at": "2026-08-15T11:00:00"},
        ])
        tasks = InMemoryKickTaskRepository()
        reconcile_expired_orders(orders, tasks, FixedClock(now), parser=parse_dt, plan_group_resolver=lambda _: ["-1001", "-1002"])
        self.assertEqual([row["group_id"] for row in tasks.group_tasks], ["-1001", "-1002"])


if __name__ == "__main__":
    unittest.main()
