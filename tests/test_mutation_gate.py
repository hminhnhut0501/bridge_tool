import unittest

from new_core.mutation_gate import MutationGate, mutation_status


class MutationGateTests(unittest.TestCase):
    def test_disabled_by_default(self):
        gate = MutationGate()
        self.assertFalse(gate.allow(1))
        self.assertEqual(gate.limit(100), 5)

    def test_enabled_gate_requires_single_concurrency(self):
        self.assertTrue(MutationGate(enabled=True).allow(1))
        self.assertFalse(MutationGate(enabled=True, concurrency=2).allow(1))

    def test_status_is_observable(self):
        status = mutation_status(MutationGate(enabled=True))
        self.assertTrue(status["safe_to_mutate"])
        self.assertEqual(status["max_batch"], 5)


if __name__ == "__main__":
    unittest.main()
