import unittest

from support_event_read_model import build_support_events_read_model


class SupportEventReadModelTests(unittest.TestCase):
    def test_filters_and_sorts_support_events(self):
        rows = [
            {
                "id": 1,
                "event_type": "support_left",
                "telegram_user_id": "42",
                "full_name": "Old",
                "created_at": "2026-08-13T10:00:00",
                "raw_data": {"reason": "bye"},
            },
            {
                "id": 2,
                "event_type": "member_kicked",
                "telegram_user_id": "99",
                "full_name": "New",
                "created_at": "2026-08-14T10:00:00",
                "raw_data": {"reason": "kick"},
            },
        ]

        result = build_support_events_read_model(rows, limit=10, updated_after="2026-08-13T12:00:00", query="99")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["data"][0]["id"], 2)
        self.assertEqual(result["data"][0]["event_type"], "member_kicked")

    def test_limit_applies_after_sorting(self):
        rows = [
            {"id": 1, "event_type": "support_left", "created_at": "2026-08-13T10:00:00", "raw_data": {}},
            {"id": 2, "event_type": "member_kicked", "created_at": "2026-08-14T10:00:00", "raw_data": {}},
            {"id": 3, "event_type": "support_joined", "created_at": "2026-08-14T11:00:00", "raw_data": {}},
        ]

        result = build_support_events_read_model(rows, limit=2)

        self.assertEqual([item["id"] for item in result["data"]], [3, 2])


if __name__ == "__main__":
    unittest.main()
