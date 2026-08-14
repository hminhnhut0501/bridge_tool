import unittest

from legacy_support_boundary import is_legacy_support_event_type, read_support_events_legacy, record_support_event_legacy


class FakeStore:
    enabled = True

    def __init__(self):
        self.events = []
        self.identities = {"123": {"username": "@alice", "full_name": "Alice"}}

    def get_user_identity(self, telegram_user_id):
        return self.identities.get(str(telegram_user_id))

    def record_support_event(self, event_type, telegram_user_id=None, **kwargs):
        self.events.append((event_type, str(telegram_user_id or ""), kwargs))

    def list_support_events(self, limit=1000, updated_after=None):
        return [
            {"id": 1, "event_type": "support_left", "telegram_user_id": "1", "created_at": "2026-08-13T10:00:00", "raw_data": {}},
            {"id": 2, "event_type": "member_kicked", "telegram_user_id": "2", "created_at": "2026-08-14T10:00:00", "raw_data": {}},
        ]


class LegacySupportBoundaryTests(unittest.TestCase):
    def test_record_support_event_legacy_fills_identity(self):
        store = FakeStore()

        record_support_event_legacy(store, "support_left", "123")

        self.assertEqual(len(store.events), 1)
        event_type, telegram_user_id, kwargs = store.events[0]
        self.assertEqual(event_type, "support_left")
        self.assertEqual(telegram_user_id, "123")
        self.assertEqual(kwargs["username"], "@alice")
        self.assertEqual(kwargs["full_name"], "Alice")

    def test_record_support_event_legacy_ignores_unknown_events(self):
        store = FakeStore()

        record_support_event_legacy(store, "new_future_event", "123")

        self.assertEqual(store.events, [])

    def test_event_type_contract_is_explicit(self):
        self.assertTrue(is_legacy_support_event_type("member_kicked"))
        self.assertFalse(is_legacy_support_event_type("new_future_event"))

    def test_read_support_events_legacy_delegates_to_read_model(self):
        store = FakeStore()

        result = read_support_events_legacy(store, limit=1, query="member_kicked")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["data"][0]["id"], 2)


if __name__ == "__main__":
    unittest.main()
