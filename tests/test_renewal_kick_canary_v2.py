import unittest

from scripts.renewal_kick_canary_v2 import TelegramReadOnly


class RenewalKickCanaryEntrypointTests(unittest.TestCase):
    def test_telegram_adapter_exposes_read_only_membership_only(self):
        adapter = TelegramReadOnly("token", timeout=1, retries=1)
        self.assertFalse(hasattr(adapter, "kick"))
        self.assertTrue(callable(adapter.is_present))


if __name__ == "__main__":
    unittest.main()
