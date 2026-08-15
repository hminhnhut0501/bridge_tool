import asyncio
import unittest

from new_core.cutover_gate import CutoverDecision
from new_core.limited_mutation_runner import run_limited_mutation
from new_core.mutation_gate import MutationGate


class LimitedMutationRunnerTests(unittest.TestCase):
    def test_disabled_gate_never_runs_worker(self):
        calls = []

        async def worker(**kwargs):
            calls.append(kwargs)

        result = asyncio.run(run_limited_mutation(worker, cutover=CutoverDecision(True, ()), gate=MutationGate()))
        self.assertEqual(result.status, "DISABLED")
        self.assertEqual(calls, [])

    def test_enabled_runner_is_hard_limited(self):
        calls = []

        async def worker(**kwargs):
            calls.append(kwargs)
            return "ok"

        result = asyncio.run(run_limited_mutation(worker, cutover=CutoverDecision(True, ()), gate=MutationGate(enabled=True)))
        self.assertEqual(result.status, "EXECUTED")
        self.assertEqual(calls, [{"limit": 5}])


if __name__ == "__main__":
    unittest.main()
