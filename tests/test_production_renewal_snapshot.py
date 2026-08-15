import unittest

from scripts.production_renewal_snapshot import _duplicate_count, count_values


class ProductionRenewalSnapshotTests(unittest.TestCase):
    def test_counts_are_aggregate_only(self):
        rows = [{"status": "paid"}, {"status": "EXPIRED"}, {}]
        self.assertEqual(count_values(rows, "status", upper=True), {"PAID": 1, "EXPIRED": 1, "UNKNOWN": 1})

    def test_duplicate_count_uses_business_key(self):
        rows = [
            {"order_id": "o1", "telegram_user_id": "42"},
            {"order_id": "o1", "telegram_user_id": "42"},
            {"order_id": "o2", "telegram_user_id": "42"},
        ]
        self.assertEqual(_duplicate_count(rows, ("order_id", "telegram_user_id")), 1)


if __name__ == "__main__":
    unittest.main()
