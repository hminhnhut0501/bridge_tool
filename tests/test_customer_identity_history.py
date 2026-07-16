import unittest

class DummyStore:
    enabled = True

    def __init__(self):
        self.support_events = []
        self.identity_rows = []

    def record_support_event(self, event_type, telegram_user_id=None, **kwargs):
        self.support_events.append((event_type, str(telegram_user_id or ""), kwargs))
        self.record_customer_identity_history(
            telegram_user_id,
            username=kwargs.get("username") or "",
            full_name=kwargs.get("full_name") or "",
            source_event_type=event_type,
            source_order_id=kwargs.get("order_id") or "",
            source_chat_id=kwargs.get("chat_id") or "",
            raw_data=kwargs.get("raw_data") or {},
        )
        return [{"ok": True}]

    def get_customer_identity_history_latest(self, telegram_user_id):
        return self.identity_rows[-1] if self.identity_rows else None

    def record_customer_identity_history(self, telegram_user_id, **kwargs):
        prev = self.identity_rows[-1] if self.identity_rows else None
        username = str(kwargs.get("username") or "").strip().lstrip("@")
        full_name = str(kwargs.get("full_name") or "").strip()
        row = {
            "telegram_user_id": str(telegram_user_id),
            "username": username,
            "full_name": full_name,
            "previous_username": (prev or {}).get("username") or "",
            "previous_full_name": (prev or {}).get("full_name") or "",
            "changed_fields": kwargs.get("changed_fields") or ["username", "full_name"],
            "source_event_type": kwargs.get("source_event_type") or "",
            "source_order_id": kwargs.get("source_order_id") or "",
            "source_chat_id": kwargs.get("source_chat_id") or "",
            "raw_data": kwargs.get("raw_data") or {},
            "created_at": "2026-07-15T00:00:00+07:00",
            "id": str(len(self.identity_rows) + 1),
        }
        self.identity_rows.append(row)
        return [row]


class CustomerIdentityHistoryTests(unittest.TestCase):
    def test_record_support_event_also_snapshots_identity(self):
        dummy = DummyStore()
        dummy.record_support_event("support_ticket_created", "123", username="@old", full_name="Old Name")
        dummy.record_support_event("support_ticket_created", "123", username="@new", full_name="New Name")

        self.assertEqual(len(dummy.support_events), 2)
        self.assertEqual(len(dummy.identity_rows), 2)
        self.assertEqual(dummy.identity_rows[-1]["previous_full_name"], "Old Name")
        self.assertEqual(dummy.identity_rows[-1]["previous_username"], "old")
        self.assertEqual(dummy.identity_rows[-1]["full_name"], "New Name")
        self.assertEqual(dummy.identity_rows[-1]["username"], "new")


if __name__ == "__main__":
    unittest.main()
