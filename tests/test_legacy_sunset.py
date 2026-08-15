import os
import unittest
from unittest.mock import patch

from legacy_support_boundary import record_support_event_legacy


class Store:
    enabled = True

    def __init__(self):
        self.events = []

    def record_support_event(self, event_type, user_id, **kwargs):
        self.events.append((event_type, user_id, kwargs))


class LegacySunsetTests(unittest.TestCase):
    def test_renewal_legacy_event_is_blocked_after_sunset(self):
        store = Store()
        with patch.dict(os.environ, {"RENEWAL_LEGACY_SUNSET": "ON"}):
            record_support_event_legacy(store, "member_kicked", "42")
        self.assertEqual(store.events, [])

    def test_non_renewal_support_event_still_logs(self):
        store = Store()
        with patch.dict(os.environ, {"RENEWAL_LEGACY_SUNSET": "ON"}):
            record_support_event_legacy(store, "support_joined", "42")
        self.assertEqual(len(store.events), 1)


if __name__ == "__main__":
    unittest.main()
