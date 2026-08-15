import asyncio
import os
import unittest
from unittest.mock import patch

from scripts.renewal_limited_mutation import run_once, validate_config


class RenewalLimitedMutationTests(unittest.TestCase):
    def test_requires_explicit_cohort_and_ack(self):
        errors = validate_config({
            "canary": "ON",
            "dry_run": "OFF",
            "limited_mutation": "ON",
            "full_cutover": "OFF",
            "ack": "",
            "cohort_user_ids": "",
            "cohort_order_ids": "",
        })
        self.assertEqual(len(errors), 3)

    def test_blocks_when_dry_run_remains_on(self):
        config = {
            "canary": "ON",
            "dry_run": "ON",
            "limited_mutation": "ON",
            "full_cutover": "OFF",
            "ack": "I_UNDERSTAND_LIMITED_MUTATION",
            "cohort_user_ids": "42",
            "cohort_order_ids": "",
        }
        self.assertIn("dry_run must be OFF", validate_config(config))

    def test_run_once_blocks_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            report = asyncio.run(run_once())
        self.assertEqual(report["mode"], "blocked")
