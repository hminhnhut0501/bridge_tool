import unittest
from datetime import datetime, timedelta

from new_core.claim_finalizer import claim_group_task, finalize_group_task, idempotency_key


class ClaimFinalizerTests(unittest.TestCase):
    def test_claim_is_idempotent_and_has_lease(self):
        now = datetime(2026, 8, 15, 12, 0)
        row = {"order_id": "o1", "group_id": "g1", "telegram_user_id": "42", "group_state": "pending"}
        payload = claim_group_task(row, now)
        self.assertEqual(payload["group_state"], "processing")
        self.assertEqual(payload["lock_expires_at"], now + timedelta(minutes=10))
        self.assertEqual(payload["idempotency_key"], idempotency_key(row))

        locked = dict(row, locked_at=now, group_state="processing")
        self.assertIsNone(claim_group_task(locked, now))

    def test_finalizer_retries_then_terminal_failure(self):
        now = datetime(2026, 8, 15, 12, 0)
        row = {"attempt_count": 2}
        payload = finalize_group_task(row, now, outcome="kick_exception", reason="timeout", max_attempts=3)
        self.assertEqual(payload["group_state"], "failed_terminal")
        self.assertEqual(payload["attempt_count"], 3)
        self.assertIsNotNone(payload["resolved_at"])

    def test_unknown_outcome_requires_review(self):
        payload = finalize_group_task({}, datetime(2026, 8, 15, 12, 0), outcome="unknown")
        self.assertEqual(payload["group_state"], "review_required")
