import unittest

from scripts.build_release_report import build_report


class BuildReleaseReportTests(unittest.TestCase):
    def test_report_has_release_contract(self):
        report = build_report(backend_tests=1, frontend_typecheck=1, frontend_build=1, canary_cycles=3)
        self.assertEqual(report["contract"], "renewal_release_report_v1")
        self.assertEqual(report["canary_cycles"], 3)


if __name__ == "__main__":
    unittest.main()
