import os
import unittest


class LegacySuiteTests(unittest.TestCase):
    def test_legacy_suite_is_explicit(self):
        self.assertIn(str(os.getenv("PRIVE_RUN_LEGACY_TESTS", "0")).strip().lower(), {"1", "true", "yes", "on", "0", "false", "no", "off"})
        self.skipTest("Legacy support_events suite is only run when PRIVE_RUN_LEGACY_TESTS=1.")


if __name__ == "__main__":
    unittest.main()
