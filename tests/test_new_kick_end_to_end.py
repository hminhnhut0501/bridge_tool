import asyncio
import unittest
from datetime import datetime, timezone

from adapters.in_memory import FakeMembershipGateway
from new_core.delayed_kick_worker import run_delayed_kick_worker
from new_core.kick_canary import run_read_only_canary
from new_core.kick_policy import evaluate_kick_eligibility


class Jobs:
    def __init__(self, rows):
        self.rows = rows
        self.updates = []

    def claim_due(self, *, before, limit):
        return self.rows[:limit]

    def update(self, job_id, payload):
        self.updates.append((job_id, payload))


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


class NewKickEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.entitlements = [{
            "source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME",
            "group_id": "-1001", "state": "EXPIRED", "source_quality": "VERIFIED",
            "expires_at": "2026-08-01T00:00:00+00:00", "is_lifetime": False,
        }]
        self.jobs = [{
            "id": "j1", "source_order_id": "o1", "telegram_user_id": "u1",
            "group_code": "PRIME", "group_id": "-1001", "status": "PENDING",
            "run_at": "2026-08-01T00:00:00+00:00", "attempts": 0,
        }]

    def test_expired_without_new_order_canary_then_kick(self):
        membership = FakeMembershipGateway(presence={("-1001", "u1"): True})
        canary = asyncio.run(run_read_only_canary(self.jobs, self.entitlements, membership, now=NOW))
        self.assertEqual(canary["action_counts"], {"WOULD_KICK": 1})
        self.assertEqual(membership.actions, [])

        repo = Jobs(self.jobs)
        result = asyncio.run(run_delayed_kick_worker(repo, membership, self.entitlements, now=NOW, limit=5))
        self.assertEqual(result.kicked, 1)
        self.assertEqual(repo.updates[0][1]["status"], "DONE")

    def test_new_order_blocks_old_order(self):
        newer = {**self.entitlements[0], "source_order_id": "o2", "state": "ACTIVE", "expires_at": "2026-09-01T00:00:00+00:00"}
        decision = evaluate_kick_eligibility(self.entitlements[0], now=NOW, newer_active_exists=True)
        self.assertEqual(decision.action, "BLOCK")
        membership = FakeMembershipGateway(presence={("-1001", "u1"): True})
        canary = asyncio.run(run_read_only_canary(self.jobs, self.entitlements + [newer], membership, now=NOW))
        self.assertEqual(canary["action_counts"], {"RETAINED": 1})
        self.assertEqual(membership.actions, [])


if __name__ == "__main__":
    unittest.main()
