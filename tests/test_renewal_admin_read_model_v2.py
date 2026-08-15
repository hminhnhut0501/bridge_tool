import unittest
from datetime import datetime, timezone

from renewal_admin_read_model_v2 import build_renewal_read_model


class RenewalAdminReadModelV2Tests(unittest.TestCase):
    def test_expiring_row_contains_reminder_state(self):
        result = build_renewal_read_model([{"id": "e1", "source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME", "group_id": "g1", "state": "ACTIVE", "expires_at": "2026-08-20T00:00:00+00:00", "is_lifetime": False}], [], [{"order_id": "o1", "full_name": "A", "plan_name": "Prime", "expired_notice_at": None}], reminder_events=[{"order_id": "o1", "status": "SENT", "sent_at": "2026-08-14T00:00:00+00:00"}], now=datetime(2026, 8, 15, tzinfo=timezone.utc))
        self.assertEqual(result["rows"][0]["reminder"]["status"], "SENT")

    def test_membership_snapshot_is_used_for_expired_row(self):
        result = build_renewal_read_model(
            [{
                "id": "e1",
                "source_order_id": "o1",
                "telegram_user_id": "u1",
                "group_code": "PRIME",
                "group_id": "g1",
                "state": "EXPIRED",
                "expires_at": "2026-08-01T00:00:00+00:00",
                "is_lifetime": False,
            }],
            [],
            [],
            membership_snapshots=[{
                "telegram_user_id": "u1",
                "group_id": "g1",
                "membership_status": "ABSENT",
                "checked_at": "2026-08-15T00:00:00+00:00",
            }],
            tab="expired",
            now=datetime(2026, 8, 15, tzinfo=timezone.utc),
        )
        self.assertEqual(result["rows"][0]["membership"], "ABSENT")

    def test_failed_reminder_preserves_error_and_attempts(self):
        result = build_renewal_read_model(
            [{
                "id": "e1",
                "source_order_id": "o1",
                "telegram_user_id": "u1",
                "group_code": "PRIME",
                "group_id": "g1",
                "state": "ACTIVE",
                "expires_at": "2026-08-20T00:00:00+00:00",
                "is_lifetime": False,
            }],
            [],
            [],
            reminder_events=[{
                "order_id": "o1",
                "status": "FAILED",
                "attempts": 3,
                "last_error": "telegram timeout",
            }],
            now=datetime(2026, 8, 15, tzinfo=timezone.utc),
        )
        self.assertEqual(result["rows"][0]["reminder"]["status"], "FAILED")
        self.assertEqual(result["rows"][0]["reminder"]["attempts"], 3)
        self.assertEqual(result["rows"][0]["reminder"]["lastError"], "telegram timeout")

    def test_expired_row_contains_kick_error(self):
        result = build_renewal_read_model([{"id": "e1", "source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME", "state": "EXPIRED", "expires_at": "2026-08-01T00:00:00+00:00", "is_lifetime": False}], [{"entitlement_id": "e1", "status": "RETRY", "attempts": 2, "last_error": "timeout"}], [], tab="expired", now=datetime(2026, 8, 15, tzinfo=timezone.utc))
        self.assertEqual(result["rows"][0]["kick"]["lastError"], "timeout")


if __name__ == "__main__":
    unittest.main()
