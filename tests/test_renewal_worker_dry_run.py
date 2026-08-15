import unittest
from unittest.mock import patch

from scripts.renewal_worker_dry_run import build_dry_run


class RenewalWorkerDryRunTests(unittest.TestCase):
    @patch("scripts.renewal_worker_dry_run.plan_groups", return_value={"g1"})
    @patch("scripts.renewal_worker_dry_run.telegram_get_member", return_value=("present", "member"))
    def test_present_member_is_only_would_kick(self, get_member, groups):
        result = build_dry_run(
            [{"telegram_user_id": "42", "group_id": "g1", "plan_name": "VIP", "group_state": "processing"}],
            [],
            "token",
        )
        self.assertEqual(result["outcomes"], {"would_kick": 1})
        self.assertEqual(result["telegram_mutation_count"], 0)

    @patch("scripts.renewal_worker_dry_run.plan_groups", return_value=set())
    def test_missing_plan_mapping_forces_review(self, groups):
        result = build_dry_run(
            [{"telegram_user_id": "42", "group_id": "g1", "plan_name": "VIP", "group_state": "processing"}],
            [{"telegram_user_id": "42", "status": "PAID", "plan_name": "VIP"}],
            "token",
        )
        self.assertEqual(result["outcomes"], {"review_mapping_unavailable": 1})


if __name__ == "__main__":
    unittest.main()
