import unittest

from scripts.normalize_plan_names import build_report, canonical_duration, canonical_plan_name


class NormalizePlanNamesTests(unittest.TestCase):
    def test_maps_old_names_to_canonical_families(self):
        self.assertEqual(canonical_plan_name("SVIP+ 30 Ngày Full 4 Nhóm")[0], "Combo 30 Ngày")
        self.assertEqual(canonical_plan_name("VIP Trọn Đời - Black")[0], "Real Trọn Đời")
        self.assertEqual(canonical_plan_name("VIP 30 Ngày - Prime")[0], "Prime 30 Ngày")

    def test_hidden_and_unknown_are_not_auto_changed(self):
        self.assertIsNone(canonical_plan_name("Pink Hidden Group")[0])
        report = build_report([{"order_id": "o1", "plan_name": "Mystery"}], source="orders")
        self.assertEqual(report["write_count"], 0)
        self.assertEqual(len(report["unmapped_or_review"]), 1)

    def test_duration_preserves_custom_lengths(self):
        self.assertEqual(canonical_duration("VIP 1 ngày - Prime"), "DAYS:1")
        self.assertEqual(canonical_duration("VIP 90 ngày - Prime"), "DAYS:90")
        self.assertEqual(canonical_duration("VIP 3 tháng - Asia"), "MONTHS:3")
        self.assertEqual(canonical_duration("Combo 1 năm"), "YEARS:1")
        self.assertEqual(canonical_duration("Combo - Tùy chỉnh"), "CUSTOM")
