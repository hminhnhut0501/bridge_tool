import unittest
from unittest.mock import patch

from scripts.readonly_http import ReadonlyHttpError, get_json
from scripts.runtime_check import check_runtime


class ReadonlyHttpTests(unittest.TestCase):
    @patch("scripts.readonly_http.urllib.request.urlopen", side_effect=OSError("temporary"))
    @patch("scripts.readonly_http.time.sleep")
    def test_retries_then_raises_bounded_error(self, sleep, urlopen):
        with self.assertRaises(ReadonlyHttpError):
            get_json("https://example.invalid", retries=2, backoff=0)
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_runtime_check_returns_report_shape(self):
        report = check_runtime()
        self.assertIn("ok", report)
        self.assertIn("requests_available", report)


if __name__ == "__main__":
    unittest.main()
