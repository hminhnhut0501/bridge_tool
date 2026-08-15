import unittest

from new_core.contract import (
    KICK_STATE_CONTRACT,
    ORDER_STATE_CONTRACT,
    assert_contract_membership,
    normalize_contract_kick_state,
    normalize_contract_kick_state_alias,
    normalize_contract_order_state,
)


class NewCoreContractTests(unittest.TestCase):
    def test_contract_sets_are_tight(self):
        self.assertEqual(ORDER_STATE_CONTRACT, {"active", "expired", "unknown"})
        self.assertEqual(KICK_STATE_CONTRACT, {"none", "processing", "done", "blocked", "review_required", "failed_terminal"})

    def test_contract_normalizers_fallback_to_safe_defaults(self):
        self.assertEqual(normalize_contract_order_state("ACTIVE"), "active")
        self.assertEqual(normalize_contract_order_state("weird"), "unknown")
        self.assertEqual(normalize_contract_kick_state("done"), "done")
        self.assertEqual(normalize_contract_kick_state("legacy_state"), "none")
        self.assertEqual(normalize_contract_kick_state_alias("queued"), "processing")
        self.assertEqual(normalize_contract_kick_state_alias("waiting_confirm"), "processing")
        self.assertEqual(normalize_contract_kick_state_alias("kicked"), "done")
        self.assertEqual(assert_contract_membership("processing", KICK_STATE_CONTRACT, default="none"), "processing")


if __name__ == "__main__":
    unittest.main()
