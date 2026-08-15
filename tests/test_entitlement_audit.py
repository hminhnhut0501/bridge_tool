import unittest

from scripts.entitlement_audit import build_report


class EntitlementAuditTests(unittest.TestCase):
    def test_review_rows_are_candidates_but_not_kickable(self):
        report = build_report([{
            "source_order_id": "o1", "state": "REVIEW",
            "state_reason": "missing_expiry", "source_quality": "REVIEW",
        }])
        self.assertEqual(report["state_counts"], {"REVIEW": 1})
        self.assertFalse(report["candidates"][0]["automatic_kick_eligible"])

    def test_verified_expired_row_is_only_automatic_candidate(self):
        report = build_report([{
            "source_order_id": "o1", "state": "EXPIRED",
            "state_reason": "expiry_reached", "source_quality": "VERIFIED",
            "group_code": "PRIME",
        }])
        self.assertTrue(report["candidates"][0]["automatic_kick_eligible"])
        self.assertEqual(report["supabase_write_count"], 0)


if __name__ == "__main__":
    unittest.main()
