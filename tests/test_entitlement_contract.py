import unittest
from datetime import datetime, timezone

from new_core.entitlement_contract import Entitlement, entitlement_key


class EntitlementContractTests(unittest.TestCase):
    def test_timed_entitlement_requires_expiry(self):
        value = Entitlement("o1", "u1", "PRIME", None, None, None, False, "ACTIVE", "VERIFIED")
        with self.assertRaises(ValueError):
            value.validate()

    def test_lifetime_can_have_no_expiry(self):
        value = Entitlement("o1", "u1", "PRIME", None, None, None, True, "ACTIVE", "VERIFIED")
        self.assertEqual(entitlement_key(value), ("o1", "PRIME"))

    def test_unknown_group_is_rejected(self):
        value = Entitlement("o1", "u1", "SIGNATURE", None, None, datetime.now(timezone.utc), False, "REVIEW", "REVIEW")
        with self.assertRaises(ValueError):
            value.validate()


if __name__ == "__main__":
    unittest.main()
