import unittest
from datetime import datetime, timezone

from new_core.entitlement_resolver import has_newer_active_entitlement, resolve_customer_group


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def entitlement(order_id, expiry, *, lifetime=False, state="ACTIVE"):
    return {
        "source_order_id": order_id,
        "telegram_user_id": "42",
        "group_code": "PRIME",
        "state": state,
        "is_lifetime": lifetime,
        "expires_at": expiry,
    }


class EntitlementResolverTests(unittest.TestCase):
    def test_selects_latest_active_expiry(self):
        result = resolve_customer_group([
            entitlement("old", "2026-08-20T00:00:00+00:00"),
            entitlement("new", "2026-09-20T00:00:00+00:00"),
        ], telegram_user_id="42", group_code="PRIME", now=NOW)
        self.assertEqual(result["source_order_id"], "new")
        self.assertEqual(result["active_count"], 2)

    def test_lifetime_wins_over_timed_access(self):
        result = resolve_customer_group([
            entitlement("timed", "2026-09-20T00:00:00+00:00"),
            entitlement("life", None, lifetime=True),
        ], telegram_user_id="42", group_code="PRIME", now=NOW)
        self.assertEqual(result["source_order_id"], "life")

    def test_old_order_has_newer_active_entitlement(self):
        rows = [entitlement("old", "2026-08-20T00:00:00+00:00"), entitlement("new", "2026-09-20T00:00:00+00:00")]
        self.assertTrue(has_newer_active_entitlement(rows, telegram_user_id="42", group_code="PRIME", source_order_id="old", now=NOW))

    def test_different_group_does_not_block(self):
        rows = [entitlement("new", "2026-09-20T00:00:00+00:00")]
        rows[0]["group_code"] = "BOY"
        self.assertFalse(has_newer_active_entitlement(rows, telegram_user_id="42", group_code="PRIME", source_order_id="old", now=NOW))


if __name__ == "__main__":
    unittest.main()
