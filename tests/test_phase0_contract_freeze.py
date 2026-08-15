import unittest

from new_core.contract import KICK_STATE_CONTRACT, ORDER_STATE_CONTRACT
from new_core.state import KICK_STATE_TASK_ALIASES, KICK_STATE_GROUP_ALIASES


class Phase0ContractFreezeTests(unittest.TestCase):
    """Guard the Phase 0 inventory from accidental state expansion."""

    def test_normalized_contract_is_frozen(self):
        self.assertEqual(ORDER_STATE_CONTRACT, {"active", "expired", "unknown"})
        self.assertEqual(
            KICK_STATE_CONTRACT,
            {"none", "processing", "done", "blocked", "review_required", "failed_terminal"},
        )

    def test_legacy_aliases_are_explicitly_tracked(self):
        expected_task_aliases = {
            "queued", "running", "pending_confirm", "retry_pending", "waiting_confirm",
            "retry_scheduled", "processing", "done", "kicked", "retained", "blocked",
            "blocked_active_order", "review_required", "failed_terminal", "error",
        }
        expected_group_aliases = {
            "pending", "selected", "processing", "waiting_confirm", "retry_scheduled",
            "unmapped", "kicked", "retained", "blocked_active_order", "review_required",
            "failed_terminal",
        }
        self.assertEqual(set(KICK_STATE_TASK_ALIASES), expected_task_aliases)
        self.assertEqual(set(KICK_STATE_GROUP_ALIASES), expected_group_aliases)


if __name__ == "__main__":
    unittest.main()
