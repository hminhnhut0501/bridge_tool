import asyncio
import os
import unittest
from unittest.mock import patch

from scripts.renewal_readonly_canary import run_once, validate_config, validate_result


class RenewalReadonlyCanaryTests(unittest.TestCase):
    def test_config_fails_closed_when_mutation_is_enabled(self):
        errors = validate_config({"canary": "ON", "dry_run": "ON", "limited_mutation": "ON", "full_cutover": "OFF"})
        self.assertTrue(errors)

    def test_result_requires_read_only_zero_mutations(self):
        self.assertEqual(validate_result({"mode": "read_only", "supabase_write_count": 0, "telegram_mutation_count": 0}), [])
        self.assertTrue(validate_result({"mode": "limited_mutation", "supabase_write_count": 1, "telegram_mutation_count": 0}))

    def test_run_once_blocks_without_flags(self):
        with patch.dict(os.environ, {"RENEWAL_NEW_CORE_CANARY": "OFF", "RENEWAL_NEW_CORE_DRY_RUN": "ON"}, clear=False):
            report = asyncio.run(run_once())
        self.assertEqual(report["mode"], "blocked")
        self.assertTrue(report["errors"])
