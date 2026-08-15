import unittest

from scripts.renewal_soak_report import build_soak_report


class RenewalSoakReportTests(unittest.TestCase):
    def test_clean_required_cycles_pass(self):
        report = build_soak_report([
            {"mode": "read_only", "supabase_write_count": 0},
            {"mode": "read_only", "supabase_write_count": 0},
            {"mode": "read_only", "supabase_write_count": 0},
            {"mode": "read_only", "supabase_write_count": 0},
        ])
        self.assertTrue(report["ok"])

    def test_unknown_or_short_soak_blocks(self):
        report = build_soak_report([{"mode": "read_only", "unknown_membership": 1}], minimum_cycles=2)
        self.assertFalse(report["ok"])
        self.assertGreaterEqual(len(report["errors"]), 2)
