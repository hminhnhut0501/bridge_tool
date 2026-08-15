import unittest

from scripts.production_plan_mapping import build_group_map, build_report


class ProductionPlanMappingTests(unittest.TestCase):
    def test_matches_group_plan_and_combo(self):
        config = [
            {"key": "GROUP_COUNT", "value": "2"},
            {"key": "ID_G1", "value": "g1"},
            {"key": "BTN_G1", "value": "Asia"},
            {"key": "ID_G2", "value": "g2"},
            {"key": "BTN_G2", "value": "Europe"},
        ]
        result = build_group_map(config, ["VIP Asia", "VIP 30 Ngày - Combo"])
        self.assertEqual(result["VIP Asia"], ["g1"])
        self.assertEqual(result["VIP 30 Ngày - Combo"], ["g1", "g2"])

    def test_report_counts_unmapped_task_plans(self):
        result = build_report(
            [{"key": "GROUP_COUNT", "value": "1"}, {"key": "ID_G1", "value": "g1"}, {"key": "BTN_G1", "value": "Asia"}],
            [{"plan_name": "VIP Asia", "status": "EXPIRED"}],
            [{"plan_name": "VIP Unknown"}],
        )
        self.assertEqual(result["mapped_plans"], 1)
        self.assertEqual(result["task_plans_unmapped"], 1)
        self.assertEqual(result["write_count"], 0)


if __name__ == "__main__":
    unittest.main()
