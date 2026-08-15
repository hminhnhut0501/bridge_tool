import asyncio
import unittest
from datetime import datetime

from scheduler_new_core_runtime import build_runtime


class Store:
    def list_scheduler_due_rows(self, before, limit):
        return []

    def list_due_renewal_kick_group_tasks_v2(self, **kwargs):
        return []


class Bot:
    pass


class Clock:
    def now(self):
        return datetime(2026, 8, 15, 12, 0)


class Phase7SchedulerCutoverTests(unittest.TestCase):
    def test_runtime_factory_wires_only_adapters_into_core(self):
        runtime = build_runtime(
            store=Store(),
            bot=Bot(),
            clock=Clock(),
            parse_datetime=lambda value: None,
            active_order_check=lambda *_: False,
        )
        self.assertEqual(runtime.orders.__class__.__name__, "SupabaseRenewalRepository")
        self.assertEqual(runtime.tasks.__class__.__name__, "SupabaseKickTaskRepository")
        self.assertEqual(runtime.membership.__class__.__name__, "TelegramMembershipGateway")
        self.assertIsNone(runtime.plan_group_resolver)

    def test_empty_canary_cycle_is_safe(self):
        from scheduler_new_core_runtime import run_cycle

        result = asyncio.run(
            run_cycle(
                store=Store(),
                bot=Bot(),
                clock=Clock(),
                parse_datetime=lambda value: None,
                active_order_check=lambda *_: False,
            )
        )
        self.assertEqual(result.expiry.scanned, 0)
        self.assertEqual(result.kick.scanned, 0)


if __name__ == "__main__":
    unittest.main()
