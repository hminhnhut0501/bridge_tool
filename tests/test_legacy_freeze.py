import unittest

from new_core.legacy_freeze import legacy_mode, legacy_mutation_allowed


class LegacyFreezeTests(unittest.TestCase):
    def test_legacy_is_read_only_after_cutover(self):
        self.assertFalse(legacy_mutation_allowed(cutover_enabled=True, explicit_override=True))
        self.assertEqual(legacy_mode(cutover_enabled=True), "READ_ONLY")

    def test_legacy_requires_explicit_override_before_cutover(self):
        self.assertFalse(legacy_mutation_allowed(cutover_enabled=False))
        self.assertTrue(legacy_mutation_allowed(cutover_enabled=False, explicit_override=True))


if __name__ == "__main__":
    unittest.main()
