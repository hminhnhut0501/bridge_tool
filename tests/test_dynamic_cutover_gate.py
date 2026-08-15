import unittest

from new_core.observability import dynamic_cutover_gate


class DynamicCutoverGateTests(unittest.TestCase):
    def test_gate_requires_clean_operational_evidence(self):
        allowed, failures = dynamic_cutover_gate({
            "baseline_available": True,
            "duplicate_claims": 0,
            "orphan_tasks": 0,
            "attempt_write_failures": 0,
            "finalizer_failures": 0,
            "mutation_outside_cohort": 0,
            "unknown_membership": 0,
        })
        self.assertTrue(allowed)
        self.assertEqual(failures, [])

    def test_gate_blocks_unknown_and_out_of_cohort_mutation(self):
        allowed, failures = dynamic_cutover_gate({
            "baseline_available": True,
            "unknown_membership": 1,
            "mutation_outside_cohort": 2,
        })
        self.assertFalse(allowed)
        self.assertIn("unknown membership remains", failures)
        self.assertIn("mutation occurred outside cohort", failures)
