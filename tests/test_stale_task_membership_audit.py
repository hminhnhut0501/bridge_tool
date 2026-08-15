import unittest
from unittest.mock import patch

from scripts.stale_task_membership_audit import audit_rows


class StaleTaskMembershipAuditTests(unittest.TestCase):
    @patch("scripts.stale_task_membership_audit.telegram_get_member")
    def test_audit_is_aggregate_and_read_only(self, get_member):
        get_member.side_effect = [("present", "member"), ("absent", "left"), ("unknown", "timeout")]
        result = audit_rows(
            [
                {"group_id": "g1", "telegram_user_id": "1"},
                {"group_id": "g2", "telegram_user_id": "2"},
                {"group_id": "g3", "telegram_user_id": "3"},
            ],
            "token",
        )
        self.assertEqual(result["scanned"], 3)
        self.assertEqual(result["outcomes"], {"present": 1, "absent": 1, "unknown": 1})
        self.assertEqual(result["supabase_write_count"], 0)
        self.assertEqual(result["telegram_mutation_count"], 0)


if __name__ == "__main__":
    unittest.main()
