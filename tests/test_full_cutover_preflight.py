import unittest

from scripts.full_cutover_preflight import build_preflight


class FullCutoverPreflightTests(unittest.TestCase):
    def test_static_and_dynamic_gates_must_both_pass(self):
        config = {
            "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
            "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
            "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
            "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
        }
        health = {
            "baseline_available": True,
            "duplicate_claims": 0,
            "orphan_tasks": 0,
            "attempt_write_failures": 0,
            "finalizer_failures": 0,
            "unknown_membership": 0,
            "mutation_outside_cohort": 0,
        }
        report = build_preflight(config, health)
        self.assertTrue(report["ok"])
        self.assertEqual(report["supabase_write_count"], 0)

    def test_unknown_membership_blocks_cutover(self):
        config = {
            "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
            "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
            "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
            "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
        }
        report = build_preflight(config, {"baseline_available": True, "unknown_membership": 1})
        self.assertFalse(report["ok"])
        self.assertIn("unknown membership remains", report["errors"])
