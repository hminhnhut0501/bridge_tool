import unittest

from adapters.telegram_membership import classify_telegram_error


class TelegramMembershipAdapterTests(unittest.TestCase):
    def test_classifies_absence(self):
        self.assertEqual(classify_telegram_error(Exception("Bad Request: user not found")), "member_absent")

    def test_classifies_rate_limit(self):
        self.assertEqual(classify_telegram_error(Exception("Too Many Requests: retry after 5")), "rate_limited")

    def test_classifies_permission(self):
        self.assertEqual(classify_telegram_error(Exception("Forbidden: bot is not an administrator")), "permission_denied")

    def test_unknown_errors_are_not_absence(self):
        self.assertEqual(classify_telegram_error(Exception("connection timeout")), "timeout")


if __name__ == "__main__":
    unittest.main()
