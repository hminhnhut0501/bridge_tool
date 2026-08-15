import unittest


COMBO_TARGETS = {"PRIME", "BOY", "REAL", "ASIA"}


class ComboExpansionTests(unittest.TestCase):
    def test_combo_has_four_target_groups(self):
        self.assertEqual(COMBO_TARGETS, {"PRIME", "BOY", "REAL", "ASIA"})

    def test_parent_code_is_not_a_kick_target(self):
        self.assertNotIn("COMBO_FULL", COMBO_TARGETS)


if __name__ == "__main__":
    unittest.main()
