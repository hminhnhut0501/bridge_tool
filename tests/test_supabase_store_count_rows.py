import unittest
from types import SimpleNamespace

import supabase_store as supabase_store_module


class CountRowsTests(unittest.TestCase):
    def test_hidden_codes_uses_code_column(self):
        store = supabase_store_module.SupabaseStore()
        store.url = "https://example.supabase.co"
        store.key = "service-role-key"

        captured = {}

        def fake_get(url, headers=None, params=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["params"] = params
            return SimpleNamespace(status_code=200, headers={"content-range": "0-0/12"}, text='[{"code":"ABC"}]', json=lambda: [{"code": "ABC"}])

        original_get = supabase_store_module.requests.get
        supabase_store_module.requests.get = fake_get
        try:
            result = store.count_rows("hidden_codes")
        finally:
            supabase_store_module.requests.get = original_get

        self.assertEqual(result, 12)
        self.assertEqual(captured["params"]["select"], "code")
        self.assertEqual(captured["params"]["limit"], "1")
        self.assertEqual(captured["params"]["select"], "code")


if __name__ == "__main__":
    unittest.main()
