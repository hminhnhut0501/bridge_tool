import asyncio
import os
import unittest
from datetime import datetime

from scheduler_new_core_runtime import run_limited_mutation_cycle, run_cycle


class RenewalMutationFreezeTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("RENEWAL_MUTATION_FREEZE")
        os.environ["RENEWAL_MUTATION_FREEZE"] = "ON"

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("RENEWAL_MUTATION_FREEZE", None)
        else:
            os.environ["RENEWAL_MUTATION_FREEZE"] = self.previous

    def test_limited_mutation_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "mutation freeze"):
            asyncio.run(run_limited_mutation_cycle(
                store=object(),
                bot=object(),
                clock=object(),
                active_order_check=lambda *_: False,
                cohort_user_ids={"42"},
            ))

    def test_full_cycle_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "mutation freeze"):
            asyncio.run(run_cycle(
                store=object(),
                bot=object(),
                clock=object(),
                parse_datetime=lambda value: datetime.now(),
                active_order_check=lambda *_: False,
            ))
