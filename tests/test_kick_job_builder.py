import unittest

from new_core.kick_job_builder import build_kick_job


def row(**extra):
    value = {
        "id": "e1", "source_order_id": "o1", "telegram_user_id": "u1",
        "group_code": "PRIME", "group_id": "-1001", "expires_at": "2026-09-01T00:00:00+00:00",
        "state": "ACTIVE", "source_quality": "VERIFIED", "is_lifetime": False,
    }
    value.update(extra)
    return value


class KickJobBuilderTests(unittest.TestCase):
    def test_builds_delayed_job_for_complete_entitlement(self):
        job = build_kick_job(row())
        self.assertEqual(job["run_at"], "2026-09-01T00:00:00+00:00")
        self.assertEqual(job["status"], "PENDING")

    def test_missing_group_never_creates_job(self):
        self.assertIsNone(build_kick_job(row(group_id=None)))

    def test_lifetime_never_creates_job(self):
        self.assertIsNone(build_kick_job(row(is_lifetime=True, expires_at=None)))

    def test_review_never_creates_job(self):
        self.assertIsNone(build_kick_job(row(source_quality="REVIEW")))


if __name__ == "__main__":
    unittest.main()
