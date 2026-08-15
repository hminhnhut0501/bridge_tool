import unittest


GROUP_MAP = {
    "PRIME": "-1003857691232",
    "BOY": "-1003835994262",
    "REAL": "-1003895162881",
    "ASIA": "-1003865232620",
    "PINK_SPECIAL": "-1004434723714",
}


class GroupMappingContractTests(unittest.TestCase):
    def test_single_group_codes_have_verified_ids(self):
        self.assertEqual(set(GROUP_MAP), {"PRIME", "BOY", "REAL", "ASIA", "PINK_SPECIAL"})
        self.assertEqual(len(set(GROUP_MAP.values())), 5)

    def test_combo_requires_expansion(self):
        self.assertNotIn("COMBO_FULL", GROUP_MAP)


if __name__ == "__main__":
    unittest.main()
