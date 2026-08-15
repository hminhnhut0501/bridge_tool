import asyncio
import unittest
from datetime import datetime, timezone

from adapters.in_memory import FakeMembershipGateway
from new_core.delayed_kick_worker import run_delayed_kick_worker


class Jobs:
    def __init__(self, rows):
        self.rows = rows
        self.updates = []

    def claim_due(self, *, before, limit):
        return self.rows[:limit]

    def update(self, job_id, payload):
        self.updates.append((job_id, payload))


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def entitlement(order="o1", group="PRIME"):
    return {"source_order_id": order, "telegram_user_id": "u1", "group_code": group, "state": "EXPIRED", "source_quality": "VERIFIED", "expires_at": "2026-08-01T00:00:00+00:00"}


def job(order="o1"):
    return {"id": "j1", "source_order_id": order, "telegram_user_id": "u1", "group_code": "PRIME", "group_id": "-1001", "attempts": 0}


class DelayedKickWorkerTests(unittest.TestCase):
    def test_kicks_one_due_job(self):
        jobs = Jobs([job()])
        membership = FakeMembershipGateway(presence={("-1001", "u1"): True})
        result = asyncio.run(run_delayed_kick_worker(jobs, membership, [entitlement()], now=NOW, limit=10))
        self.assertEqual(result.kicked, 1)
        self.assertEqual(jobs.updates[0][1]["status"], "DONE")

    def test_active_newer_order_retains_user(self):
        jobs = Jobs([job()])
        membership = FakeMembershipGateway(presence={("-1001", "u1"): True})
        rows = [entitlement(), {**entitlement("o2"), "state": "ACTIVE", "expires_at": "2026-09-01T00:00:00+00:00"}]
        result = asyncio.run(run_delayed_kick_worker(jobs, membership, rows, now=NOW, limit=10))
        self.assertEqual(result.retained, 1)
        self.assertEqual(membership.actions, [])


if __name__ == "__main__":
    unittest.main()
