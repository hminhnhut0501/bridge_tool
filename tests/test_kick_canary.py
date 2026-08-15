import asyncio
import unittest
from datetime import datetime, timezone

from adapters.in_memory import FakeMembershipGateway
from new_core.kick_canary import run_read_only_canary


class KickCanaryTests(unittest.TestCase):
    def test_member_is_would_kick_without_mutation(self):
        jobs = [{"id": "j1", "source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME", "group_id": "g1", "status": "PENDING", "run_at": "2026-08-01T00:00:00+00:00"}]
        entitlements = [{"source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME", "state": "EXPIRED", "source_quality": "VERIFIED", "expires_at": "2026-08-01T00:00:00+00:00"}]
        membership = FakeMembershipGateway(presence={("g1", "u1"): True})
        report = asyncio.run(run_read_only_canary(jobs, entitlements, membership, now=datetime(2026, 8, 15, tzinfo=timezone.utc)))
        self.assertEqual(report["action_counts"], {"WOULD_KICK": 1})
        self.assertEqual(membership.actions, [])
        self.assertEqual(report["telegram_mutation_count"], 0)

    def test_newer_entitlement_is_retained(self):
        jobs = [{"id": "j1", "source_order_id": "o1", "telegram_user_id": "u1", "group_code": "PRIME", "group_id": "g1", "status": "PENDING", "run_at": "2026-08-01T00:00:00+00:00"}]
        base = {"telegram_user_id": "u1", "group_code": "PRIME", "source_quality": "VERIFIED"}
        entitlements = [{**base, "source_order_id": "o1", "state": "EXPIRED", "expires_at": "2026-08-01T00:00:00+00:00"}, {**base, "source_order_id": "o2", "state": "ACTIVE", "expires_at": "2026-09-01T00:00:00+00:00"}]
        membership = FakeMembershipGateway(presence={("g1", "u1"): True})
        report = asyncio.run(run_read_only_canary(jobs, entitlements, membership, now=datetime(2026, 8, 15, tzinfo=timezone.utc)))
        self.assertEqual(report["action_counts"], {"RETAINED": 1})


if __name__ == "__main__":
    unittest.main()
