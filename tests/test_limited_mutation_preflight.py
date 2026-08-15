import json
import tempfile
import unittest
from pathlib import Path

from scripts.limited_mutation_preflight import main


class LimitedMutationPreflightTests(unittest.TestCase):
    def test_clean_canary_is_allowed_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "canary.json"
            path.write_text(json.dumps({"action_counts": {"WOULD_KICK": 1}}), encoding="utf-8")
            import sys
            old = sys.argv
            sys.argv = ["preflight", str(path)]
            try:
                self.assertEqual(main(), 0)
            finally:
                sys.argv = old


if __name__ == "__main__":
    unittest.main()
