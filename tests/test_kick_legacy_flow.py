import unittest


class LegacyKickFlowTests(unittest.TestCase):
    def test_legacy_kick_flow_placeholder(self):
        self.skipTest(
            "Legacy support_events/old kick flow tests are intentionally separated from v2 coverage. "
            "Run the legacy suite explicitly when validating backward-compat behavior."
        )


if __name__ == "__main__":
    unittest.main()
