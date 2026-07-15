import unittest

from admin_notification_utils import admin_notification_from_support_event


class AdminNotificationTests(unittest.TestCase):
    def test_delivery_success_maps_to_order_notification(self):
        item = admin_notification_from_support_event(
            {
                "id": 101,
                "event_type": "delivery_success",
                "telegram_user_id": "123456",
                "full_name": "Minh",
                "plan_name": "All Access 30 Ngày",
                "order_id": "ORD-1",
                "created_at": "2026-07-15 12:00:00",
                "raw_data": {"delivered_groups": ["Prime"]},
            }
        )

        self.assertIsNotNone(item)
        self.assertEqual(item["kind"], "order")
        self.assertEqual(item["title"], "Đơn auto-paid mới")
        self.assertIn("Minh", item["detail"])
        self.assertIn("ORD-1", item["detail"])

    def test_support_ticket_created_maps_to_message_notification(self):
        item = admin_notification_from_support_event(
            {
                "id": 202,
                "event_type": "support_ticket_created",
                "telegram_user_id": "987654",
                "full_name": "User 1",
                "order_id": "Cần hỗ trợ",
                "created_at": "2026-07-15 12:01:00",
                "raw_data": {"ticket_no": "SUP20260715120100"},
            }
        )

        self.assertIsNotNone(item)
        self.assertEqual(item["kind"], "message")
        self.assertEqual(item["title"], "Tin nhắn riêng mới")
        self.assertIn("User 1", item["detail"])
        self.assertIn("Cần hỗ trợ", item["detail"])
        self.assertIn("SUP20260715120100", item["detail"])

    def test_unrelated_event_is_ignored(self):
        self.assertIsNone(
            admin_notification_from_support_event(
                {
                    "id": 303,
                    "event_type": "member_kicked",
                    "telegram_user_id": "1",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
