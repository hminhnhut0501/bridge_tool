import unittest

from new_core.scope_contract import (
    ALLOWED_ENTITLEMENT_STATES,
    ALLOWED_JOB_STATES,
    assert_scope_contract,
)


class ScopeContractTests(unittest.TestCase):
    def test_scope_is_locked(self):
        assert_scope_contract()
        self.assertEqual(ALLOWED_ENTITLEMENT_STATES, {"ACTIVE", "EXPIRED", "CANCELLED", "REVIEW"})
        self.assertIn("PENDING", ALLOWED_JOB_STATES)
        self.assertIn("DONE", ALLOWED_JOB_STATES)


if __name__ == "__main__":
    unittest.main()
