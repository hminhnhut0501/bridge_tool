import asyncio
import unittest

from new_core.cutover_gate import CutoverDecision
from new_core.cutover_runner import run_one_batch


class CutoverRunnerTests(unittest.TestCase):
    def test_kill_switch_stops_runner(self):
        calls = []

        async def worker(**kwargs):
            calls.append(kwargs)

        result = asyncio.run(run_one_batch(worker, cutover=CutoverDecision(True, ()), enabled=False))
        self.assertEqual(result.status, "DISABLED")
        self.assertEqual(calls, [])

    def test_blocked_gate_stops_runner(self):
        calls = []

        async def worker(**kwargs):
            calls.append(kwargs)

        result = asyncio.run(run_one_batch(worker, cutover=CutoverDecision(False, ("review",)), enabled=True))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(calls, [])

    def test_runner_executes_one_bounded_batch(self):
        calls = []

        async def worker(**kwargs):
            calls.append(kwargs)
            return "ok"

        result = asyncio.run(run_one_batch(worker, cutover=CutoverDecision(True, ()), enabled=True, batch_limit=100))
        self.assertEqual(result.status, "EXECUTED")
        self.assertEqual(calls, [{"limit": 5}])


if __name__ == "__main__":
    unittest.main()
