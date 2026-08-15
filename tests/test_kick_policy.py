import unittest
from datetime import datetime, timezone

from new_core.kick_policy import evaluate_kick_eligibility


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def expired(**extra):
    value = {
        "state": "EXPIRED", "source_quality": "VERIFIED",
        "group_code": "PRIME", "expires_at": "2026-08-01T00:00:00+00:00",
    }
    value.update(extra)
    return value


class KickPolicyTests(unittest.TestCase):
    def test_verified_expired_entitlement_is_kickable(self):
        result = evaluate_kick_eligibility(expired(), now=NOW)
        self.assertEqual((result.eligible, result.action), (True, "KICK"))

    def test_newer_active_entitlement_blocks_kick(self):
        result = evaluate_kick_eligibility(expired(), now=NOW, newer_active_exists=True)
        self.assertEqual(result.reason, "newer_active_entitlement")

    def test_review_and_unsupported_data_never_kick(self):
        for row in (expired(source_quality="REVIEW"), expired(group_code=None), expired(expires_at=None)):
            self.assertFalse(evaluate_kick_eligibility(row, now=NOW).eligible)

    def test_future_expiry_never_kicks(self):
        result = evaluate_kick_eligibility(expired(expires_at="2026-09-01T00:00:00+00:00"), now=NOW)
        self.assertFalse(result.eligible)


if __name__ == "__main__":
    unittest.main()
