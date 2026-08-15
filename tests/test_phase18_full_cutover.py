import unittest

from scheduler_new_core_runtime import full_cutover_gate


class Phase18FullCutoverTests(unittest.TestCase):
    def test_gate_requires_explicit_acknowledgement(self):
        allowed, reason = full_cutover_gate({
            "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
            "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
            "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
        })
        self.assertFalse(allowed)
        self.assertIn("ACK", reason)

    def test_gate_passes_only_for_explicit_production_config(self):
        allowed, reason = full_cutover_gate({
            "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
            "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
            "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
            "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
        })
        self.assertTrue(allowed)
        self.assertEqual(reason, "full cutover gate passed")

    def test_gate_rejects_dry_run_or_limited_mode(self):
        for key, value in (("RENEWAL_NEW_CORE_DRY_RUN", "ON"), ("RENEWAL_NEW_CORE_LIMITED_MUTATION", "ON")):
            config = {
                "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
                "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
                "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
                "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
            }
            config[key] = value
            allowed, _ = full_cutover_gate(config)
            self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
