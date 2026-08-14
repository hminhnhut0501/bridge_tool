import unittest
from types import SimpleNamespace

import support_utils


class FakeDb:
    def __init__(self, config):
        self.config = config

    def get_config(self, key, default=""):
        return self.config.get(key, default)


class FakeBot:
    def __init__(self):
        self.unban_calls = []
        self.invite_calls = []

    async def unban_chat_member(self, **kwargs):
        self.unban_calls.append(kwargs)

    async def create_chat_invite_link(self, **kwargs):
        self.invite_calls.append(kwargs)
        return SimpleNamespace(invite_link=f"https://t.me/+{kwargs['chat_id']}")


class SupportInviteModeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = support_utils.db
        self.original_bot = support_utils.bot
        self.original_unmute = support_utils.unmute_member

    def tearDown(self):
        support_utils.db = self.original_db
        support_utils.bot = self.original_bot
        support_utils.unmute_member = self.original_unmute

    async def test_group_mode_keeps_unban_and_unmute_flow(self):
        fake_bot = FakeBot()
        calls = []
        support_utils.db = FakeDb({
            "SUPPORT_GROUP_ENABLED": "ON",
            "SUPPORT_GROUP_MODE": "group",
            "SUPPORT_GROUP_ID": "-1001234567890",
            "SUPPORT_GROUP_NAME": "Nhóm hỗ trợ",
        })
        support_utils.bot = fake_bot
        support_utils.unmute_member = lambda *args, **kwargs: calls.append((args, kwargs))

        link, error = await support_utils.create_support_invite_link("42")

        self.assertEqual(error, "")
        self.assertEqual(link, "https://t.me/+-1001234567890")
        self.assertEqual(len(fake_bot.unban_calls), 1)
        self.assertEqual(len(fake_bot.invite_calls), 1)
        self.assertEqual(len(calls), 1)

    async def test_channel_mode_skips_unban_and_unmute(self):
        fake_bot = FakeBot()

        async def should_not_call(*args, **kwargs):
            raise AssertionError("unmute_member should not be called in channel mode")

        support_utils.db = FakeDb({
            "SUPPORT_GROUP_ENABLED": "ON",
            "SUPPORT_GROUP_MODE": "channel",
            "SUPPORT_GROUP_ID": "-100999888777",
            "SUPPORT_GROUP_NAME": "Kênh hỗ trợ",
        })
        support_utils.bot = fake_bot
        support_utils.unmute_member = should_not_call

        link, error = await support_utils.create_support_invite_link("42")

        self.assertEqual(error, "")
        self.assertEqual(link, "https://t.me/+-100999888777")
        self.assertEqual(len(fake_bot.unban_calls), 0)
        self.assertEqual(len(fake_bot.invite_calls), 1)

    async def test_force_mode_ignores_disabled_flag_but_still_creates_link(self):
        fake_bot = FakeBot()
        calls = []
        support_utils.db = FakeDb({
            "SUPPORT_GROUP_ENABLED": "OFF",
            "SUPPORT_GROUP_MODE": "group",
            "SUPPORT_GROUP_ID": "-1001234567890",
            "SUPPORT_GROUP_NAME": "Nhóm hỗ trợ",
        })
        support_utils.bot = fake_bot
        support_utils.unmute_member = lambda *args, **kwargs: calls.append((args, kwargs))

        link, error = await support_utils.create_support_invite_link("42", force=True)

        self.assertEqual(error, "")
        self.assertEqual(link, "https://t.me/+-1001234567890")
        self.assertEqual(len(fake_bot.unban_calls), 1)
        self.assertEqual(len(fake_bot.invite_calls), 1)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
